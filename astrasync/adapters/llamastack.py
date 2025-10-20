"""
Meta Llama Stack adapter for AstraSync agent registration.
Supports Llama Stack agents, tools, and memory configurations.
"""

import logging
from typing import Dict, Any, List, Optional, Union
from ..utils.trust_score import calculate_trust_score
from ..core import AstraSync

logger = logging.getLogger(__name__)


def normalize_agent_data(agent_data: Any) -> Dict[str, Any]:
    """
    Normalize Llama Stack agent data to AstraSync standard format.
    
    Supports:
    - Llama Stack agentic API configurations
    - Tool definitions and memory stores
    - Multi-turn agent interactions
    """
    # Start with empty normalized structure
    normalized = {
        'agentType': 'llamastack',
        'version': '1.0',
        'capabilities': [],
        'metadata': {}
    }
    
    # Handle Llama Stack agent objects (not plain dicts)
    if hasattr(agent_data, '__class__') and not isinstance(agent_data, dict):
        class_name = agent_data.__class__.__name__
        module_name = getattr(agent_data.__class__, '__module__', '')
        
        if 'llamastack' in module_name.lower() or 'llama_stack' in module_name.lower():
            normalized['name'] = getattr(agent_data, 'name', f'{class_name} Instance')
            normalized['metadata']['agentClass'] = class_name
            
            # Extract agent configuration
            if hasattr(agent_data, 'config'):
                config = agent_data.config
                if isinstance(config, dict):
                    if 'model' in config:
                        normalized['metadata']['model'] = config['model']
                        normalized['capabilities'].append(f"model:{config['model']}")
                    if 'tools' in config:
                        _extract_tools(config['tools'], normalized)
                        
            # Extract memory configuration
            if hasattr(agent_data, 'memory'):
                normalized['capabilities'].append('memory:enabled')
                if hasattr(agent_data.memory, 'type'):
                    normalized['metadata']['memoryType'] = agent_data.memory.type
                    
    # Handle dictionary-based definitions
    elif isinstance(agent_data, dict):
        # Direct field mappings
        for field in ['name', 'description', 'owner', 'version']:
            if field in agent_data:
                normalized[field] = agent_data[field]
                
        # Llama Stack agent configuration
        if 'agent_config' in agent_data or 'agent' in agent_data:
            agent_config = agent_data.get('agent_config', agent_data.get('agent', {}))
            
            if 'system_prompt' in agent_config:
                normalized['metadata']['systemPrompt'] = agent_config['system_prompt']
                normalized['description'] = agent_config['system_prompt'][:200] + '...' if len(agent_config['system_prompt']) > 200 else agent_config['system_prompt']
                
            if 'model' in agent_config:
                normalized['metadata']['model'] = agent_config['model']
                normalized['capabilities'].append(f"model:{agent_config['model']}")
                
            if 'temperature' in agent_config:
                normalized['metadata']['temperature'] = agent_config['temperature']
                
        # Tools configuration
        if 'tools' in agent_data:
            _extract_tools(agent_data['tools'], normalized)
            
        # Memory configuration
        if 'memory' in agent_data:
            memory_config = agent_data['memory']
            if memory_config:
                normalized['capabilities'].append('memory:enabled')
                if isinstance(memory_config, dict):
                    if 'type' in memory_config:
                        normalized['metadata']['memoryType'] = memory_config['type']
                    if 'store' in memory_config:
                        normalized['metadata']['memoryStore'] = memory_config['store']
                        
        # Safety configuration
        if 'safety' in agent_data:
            normalized['capabilities'].append('safety:enabled')
            safety_config = agent_data['safety']
            if isinstance(safety_config, dict):
                if 'shields' in safety_config:
                    shields = safety_config['shields']
                    if isinstance(shields, list):
                        normalized['metadata']['shields'] = shields
                        normalized['capabilities'].append(f'shields:{len(shields)}')
                        
        # Multi-turn configuration
        if 'multi_turn' in agent_data or 'turn_config' in agent_data:
            normalized['capabilities'].append('multi_turn:enabled')
            turn_config = agent_data.get('multi_turn', agent_data.get('turn_config'))
            if isinstance(turn_config, dict):
                if 'max_turns' in turn_config:
                    normalized['metadata']['maxTurns'] = turn_config['max_turns']
                    
        # Code execution
        if 'code_execution' in agent_data:
            if agent_data['code_execution']:
                normalized['capabilities'].append('code_execution:enabled')
                
    # Ensure capabilities are unique
    normalized['capabilities'] = list(set(normalized['capabilities']))
    
    # Set defaults for missing required fields
    if 'name' not in normalized:
        normalized['name'] = 'Unnamed Llama Stack Agent'
    if 'description' not in normalized:
        normalized['description'] = 'Meta Llama Stack agentic application'
    if 'owner' not in normalized:
        normalized['owner'] = 'Unknown'
    if 'version' not in normalized:
        normalized['version'] = '1.0'
    
    # Calculate trust score with Llama Stack-specific bonuses
    trust_score = calculate_trust_score(normalized)
    
    # Llama Stack-specific trust score bonuses
    if normalized['capabilities']:
        trust_score += min(5, len(normalized['capabilities']))
    if 'memory:enabled' in normalized['capabilities']:
        trust_score += 5
    if 'safety:enabled' in normalized['capabilities']:
        trust_score += 5  # Bonus for safety features
    if 'code_execution:enabled' in normalized['capabilities']:
        trust_score += 5
    if normalized['metadata'].get('toolCount', 0) > 3:
        trust_score += 3
    if 'multi_turn:enabled' in normalized['capabilities']:
        trust_score += 3
        
    normalized['trustScore'] = min(trust_score, 100)  # Production scoring
    
    return normalized


def _extract_tools(tools: Any, normalized: Dict[str, Any]) -> None:
    """Extract tool information from Llama Stack tools configuration."""
    if isinstance(tools, list):
        tool_names = []
        for tool in tools:
            if isinstance(tool, str):
                tool_names.append(tool)
                normalized['capabilities'].append(f'tool:{tool}')
                # Check for special tool names
                if tool == 'web_search':
                    normalized['capabilities'].append('web_search:enabled')
                elif tool == 'code_interpreter':
                    normalized['capabilities'].append('code_execution:enabled')
            elif isinstance(tool, dict):
                tool_name = tool.get('name', tool.get('type', 'unknown'))
                tool_names.append(tool_name)
                normalized['capabilities'].append(f'tool:{tool_name}')
                
                # Check for special tool types
                if tool.get('type') == 'code_interpreter':
                    normalized['capabilities'].append('code_execution:enabled')
                elif tool.get('type') == 'web_search':
                    normalized['capabilities'].append('web_search:enabled')
                    
        if tool_names:
            normalized['metadata']['tools'] = tool_names
            normalized['metadata']['toolCount'] = len(tool_names)
            normalized['capabilities'].append(f'tools:{len(tool_names)}')


def register_llamastack(agent: Any, email: str, owner: Optional[str] = None) -> Dict[str, Any]:
    """
    Register a Llama Stack agent with AstraSync.
    
    Args:
        agent: Llama Stack agent object or configuration
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
        logger.error(f"Failed to register Llama Stack agent: {e}")
        raise


def create_registration_decorator(email: str, owner: Optional[str] = None):
    """
    Create a decorator for automatic Llama Stack agent registration.
    
    Usage:
        @register_with_astrasync(email="dev@example.com")
        class MyLlamaStackAgent:
            ...
    """
    def decorator(cls):
        original_init = cls.__init__
        
        def new_init(self, *args, **kwargs):
            original_init(self, *args, **kwargs)
            try:
                result = register_llamastack(self, email=email, owner=owner)
                self.astrasync_id = result.get('agentId')
                self.astrasync_trust_score = result.get('trustScore')
                logger.info(f"Auto-registered Llama Stack agent: {self.astrasync_id}")
            except Exception as e:
                logger.warning(f"Failed to auto-register agent: {e}")
                self.astrasync_id = None
                self.astrasync_trust_score = None
                
        cls.__init__ = new_init
        return cls
        
    return decorator


# Convenience function alias
register_with_astrasync = create_registration_decorator