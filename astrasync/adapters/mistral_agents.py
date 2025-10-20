"""
Mistral Agents adapter for AstraSync agent registration.
Supports Mistral AI agent framework (Le Chat) with function calling.
"""

import logging
from typing import Dict, Any, List, Optional, Union
from ..utils.trust_score import calculate_trust_score
from ..core import AstraSync

logger = logging.getLogger(__name__)


def normalize_agent_data(agent_data: Any) -> Dict[str, Any]:
    """
    Normalize Mistral Agents data to AstraSync standard format.
    
    Supports:
    - Mistral AI agents with Le Chat capabilities
    - Function calling and tool use
    - JSON mode and structured outputs
    - Safety filtering and moderation
    """
    # Start with empty normalized structure
    normalized = {
        'agentType': 'mistral_agents',
        'version': '1.0',
        'capabilities': [],
        'metadata': {}
    }
    
    # Handle Mistral agent objects (not plain dicts)
    if hasattr(agent_data, '__class__') and not isinstance(agent_data, dict):
        class_name = agent_data.__class__.__name__
        module_name = getattr(agent_data.__class__, '__module__', '')
        
        if 'mistral' in module_name.lower() or 'lechat' in module_name.lower():
            normalized['name'] = getattr(agent_data, 'name', f'{class_name} Instance')
            normalized['metadata']['agentClass'] = class_name
            
            # Check for specific agent types
            if 'MistralAgent' in class_name or 'LeChat' in class_name:
                normalized['description'] = getattr(agent_data, 'description', 'Mistral AI agent')
                normalized['capabilities'].append('agent:enabled')
                
                # Extract system prompt
                if hasattr(agent_data, 'system_prompt'):
                    system_prompt = agent_data.system_prompt
                    normalized['metadata']['systemPrompt'] = system_prompt
                    normalized['description'] = system_prompt[:200] + '...' if len(system_prompt) > 200 else system_prompt
                    
                # Extract model configuration
                if hasattr(agent_data, 'model'):
                    normalized['metadata']['model'] = agent_data.model
                    normalized['capabilities'].append(f'model:{agent_data.model}')
                    
                # Check for function calling
                if hasattr(agent_data, 'functions') or hasattr(agent_data, 'tools'):
                    functions = getattr(agent_data, 'functions', getattr(agent_data, 'tools', []))
                    if functions:
                        _extract_functions(functions, normalized)
                        
                # Check for JSON mode
                if hasattr(agent_data, 'json_mode'):
                    if agent_data.json_mode:
                        normalized['capabilities'].append('json_mode:enabled')
                        
                # Check for safety mode
                if hasattr(agent_data, 'safe_mode') or hasattr(agent_data, 'safety_mode'):
                    if getattr(agent_data, 'safe_mode', getattr(agent_data, 'safety_mode', False)):
                        normalized['capabilities'].append('safe_mode:enabled')
                        
    # Handle dictionary-based definitions
    elif isinstance(agent_data, dict):
        # Direct field mappings
        for field in ['name', 'description', 'owner', 'version']:
            if field in agent_data:
                normalized[field] = agent_data[field]
                
        # Mistral-specific fields
        if 'system_prompt' in agent_data:
            system_prompt = agent_data['system_prompt']
            normalized['metadata']['systemPrompt'] = system_prompt
            if 'description' not in normalized or not normalized['description']:
                normalized['description'] = system_prompt[:200] + '...' if len(system_prompt) > 200 else system_prompt
                
        if 'model' in agent_data:
            normalized['metadata']['model'] = agent_data['model']
            normalized['capabilities'].append(f"model:{agent_data['model']}")
            
        # Functions/tools configuration
        if 'functions' in agent_data:
            _extract_functions(agent_data['functions'], normalized)
        if 'tools' in agent_data:
            _extract_functions(agent_data['tools'], normalized)
            
        # JSON mode configuration
        if 'json_mode' in agent_data:
            if agent_data['json_mode']:
                normalized['capabilities'].append('json_mode:enabled')
                
        # Response format
        if 'response_format' in agent_data:
            response_format = agent_data['response_format']
            if isinstance(response_format, dict):
                if response_format.get('type') == 'json_object':
                    normalized['capabilities'].append('json_mode:enabled')
                normalized['metadata']['responseFormat'] = response_format
                
        # Safety configuration
        if 'safe_mode' in agent_data or 'safety_mode' in agent_data:
            if agent_data.get('safe_mode', agent_data.get('safety_mode')):
                normalized['capabilities'].append('safe_mode:enabled')
                
        if 'safety_settings' in agent_data:
            safety = agent_data['safety_settings']
            if isinstance(safety, dict):
                normalized['metadata']['safetySettings'] = safety
                if safety.get('enabled', True):
                    normalized['capabilities'].append('safe_mode:enabled')
                    
        # Temperature and other params
        if 'temperature' in agent_data:
            normalized['metadata']['temperature'] = agent_data['temperature']
        if 'max_tokens' in agent_data:
            normalized['metadata']['maxTokens'] = agent_data['max_tokens']
            
        # Streaming configuration
        if 'stream' in agent_data:
            if agent_data['stream']:
                normalized['capabilities'].append('streaming:enabled')
                
        # Le Chat specific features
        if 'lechat_config' in agent_data or 'le_chat' in agent_data:
            lechat = agent_data.get('lechat_config', agent_data.get('le_chat', {}))
            if isinstance(lechat, dict):
                if 'web_search' in lechat and lechat['web_search']:
                    normalized['capabilities'].append('web_search:enabled')
                if 'code_interpreter' in lechat and lechat['code_interpreter']:
                    normalized['capabilities'].append('code_interpreter:enabled')
                    
    # Ensure capabilities are unique
    normalized['capabilities'] = list(set(normalized['capabilities']))
    
    # Set defaults for missing required fields
    if 'name' not in normalized:
        normalized['name'] = 'Unnamed Mistral Agent'
    if 'description' not in normalized:
        normalized['description'] = 'Mistral AI agent with advanced capabilities'
    if 'owner' not in normalized:
        normalized['owner'] = 'Unknown'
    if 'version' not in normalized:
        normalized['version'] = '1.0'
    
    # Calculate trust score with Mistral-specific bonuses
    trust_score = calculate_trust_score(normalized)
    
    # Mistral-specific trust score bonuses
    if normalized['capabilities']:
        trust_score += min(5, len(normalized['capabilities']))
    if 'function_calling:enabled' in normalized['capabilities']:
        trust_score += 5  # Bonus for function calling
    if 'json_mode:enabled' in normalized['capabilities']:
        trust_score += 5  # Bonus for structured outputs
    if 'safe_mode:enabled' in normalized['capabilities']:
        trust_score += 5  # Bonus for safety features
    if normalized['metadata'].get('functionCount', 0) > 3:
        trust_score += 3
    if 'streaming:enabled' in normalized['capabilities']:
        trust_score += 2
        
    normalized['trustScore'] = min(trust_score, 100)  # Production scoring
    
    return normalized


def _extract_functions(functions: Any, normalized: Dict[str, Any]) -> None:
    """Extract function/tool information from Mistral configuration."""
    if isinstance(functions, list):
        function_names = []
        for func in functions:
            if isinstance(func, str):
                function_names.append(func)
                normalized['capabilities'].append(f'function:{func}')
            elif isinstance(func, dict):
                func_name = func.get('name', func.get('function', 'unknown'))
                function_names.append(func_name)
                normalized['capabilities'].append(f'function:{func_name}')
                
                # Check for specific function types
                if 'type' in func:
                    if func['type'] == 'code_interpreter':
                        normalized['capabilities'].append('code_interpreter:enabled')
                    elif func['type'] == 'web_search':
                        normalized['capabilities'].append('web_search:enabled')
                        
            elif hasattr(func, 'name'):
                function_names.append(func.name)
                normalized['capabilities'].append(f'function:{func.name}')
                
        if function_names:
            normalized['metadata']['functions'] = function_names
            normalized['metadata']['functionCount'] = len(function_names)
            normalized['capabilities'].append(f'functions:{len(function_names)}')
            normalized['capabilities'].append('function_calling:enabled')


def register_mistral_agents(agent: Any, email: str, owner: Optional[str] = None) -> Dict[str, Any]:
    """
    Register a Mistral agent with AstraSync.
    
    Args:
        agent: Mistral agent object or configuration
        email: Developer email for registration
        owner: Optional owner name (defaults to email domain)
        
    Returns:
        Registration response with agent ID and trust score
    """
    try:
        client = AstraSync(email=email)
        normalized_data = normalize_agent_data(agent)
        
        if owner:
            normalized_data['owner'] = owner
            
        return client.register(normalized_data, owner=owner)
    except Exception as e:
        logger.error(f"Failed to register Mistral agent: {e}")
        raise


def create_registration_decorator(email: str, owner: Optional[str] = None):
    """
    Create a decorator for automatic Mistral agent registration.
    
    Usage:
        @register_with_astrasync(email="dev@example.com")
        class MyMistralAgent:
            ...
    """
    def decorator(cls):
        original_init = cls.__init__
        
        def new_init(self, *args, **kwargs):
            original_init(self, *args, **kwargs)
            try:
                result = register_mistral_agents(self, email=email, owner=owner)
                self.astrasync_id = result.get('agentId')
                self.astrasync_trust_score = result.get('trustScore')
                logger.info(f"Auto-registered Mistral agent: {self.astrasync_id}")
            except Exception as e:
                logger.warning(f"Failed to auto-register agent: {e}")
                self.astrasync_id = None
                self.astrasync_trust_score = None
                
        cls.__init__ = new_init
        return cls
        
    return decorator


# Convenience function alias
register_with_astrasync = create_registration_decorator