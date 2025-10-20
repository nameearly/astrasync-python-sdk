"""
Microsoft AutoGen adapter for AstraSync agent registration.
Supports AutoGen agents, multi-agent conversations, and orchestration.
"""

import logging
from typing import Dict, Any, List, Optional, Union
from ..utils.trust_score import calculate_trust_score
from ..core import AstraSync

logger = logging.getLogger(__name__)


def normalize_agent_data(agent_data: Any) -> Dict[str, Any]:
    """
    Normalize AutoGen agent data to AstraSync standard format.
    
    Supports:
    - AutoGen AssistantAgent, UserProxyAgent, GroupChatManager
    - Multi-agent conversations
    - Function calling and code execution
    """
    # Start with empty normalized structure
    normalized = {
        'agentType': 'autogen',
        'version': '1.0',
        'capabilities': [],
        'metadata': {}
    }
    
    # Handle AutoGen agent objects (not plain dicts)
    if hasattr(agent_data, '__class__') and not isinstance(agent_data, dict):
        class_name = agent_data.__class__.__name__
        module_name = getattr(agent_data.__class__, '__module__', '')
        
        if 'autogen' in module_name.lower():
            normalized['name'] = getattr(agent_data, 'name', f'{class_name} Instance')
            
            # Extract agent configuration
            if hasattr(agent_data, '_config'):
                config = agent_data._config
                normalized['metadata']['config'] = config
                
            # Common AutoGen agent types
            if 'AssistantAgent' in class_name:
                normalized['description'] = getattr(agent_data, 'system_message', 'AutoGen Assistant Agent')
                normalized['capabilities'].append('assistant:enabled')
                normalized['metadata']['agentClass'] = 'AssistantAgent'
                
                # Check for code execution
                if hasattr(agent_data, 'code_execution_config'):
                    if agent_data.code_execution_config:
                        normalized['capabilities'].append('code_execution:enabled')
                        normalized['metadata']['codeExecution'] = True
                
            elif 'UserProxyAgent' in class_name:
                normalized['description'] = 'AutoGen User Proxy Agent for human interaction'
                normalized['capabilities'].append('user_proxy:enabled')
                normalized['metadata']['agentClass'] = 'UserProxyAgent'
                
                # Check for code execution
                if hasattr(agent_data, 'code_execution_config'):
                    if agent_data.code_execution_config:
                        normalized['capabilities'].append('code_execution:enabled')
                        normalized['metadata']['codeExecution'] = True
                        
            elif 'GroupChatManager' in class_name:
                normalized['description'] = 'AutoGen Group Chat Manager for multi-agent coordination'
                normalized['capabilities'].append('group_chat:enabled')
                normalized['metadata']['agentClass'] = 'GroupChatManager'
                
            # Extract LLM config
            if hasattr(agent_data, 'llm_config'):
                llm_config = agent_data.llm_config
                if llm_config:
                    if 'model' in llm_config:
                        normalized['metadata']['model'] = llm_config['model']
                        normalized['capabilities'].append(f"model:{llm_config['model']}")
                    if 'temperature' in llm_config:
                        normalized['metadata']['temperature'] = llm_config['temperature']
                    if 'functions' in llm_config:
                        normalized['capabilities'].append('function_calling:enabled')
                        function_count = len(llm_config['functions'])
                        normalized['metadata']['functionCount'] = function_count
                        normalized['capabilities'].append(f'functions:{function_count}')
                        
            # Extract other properties
            if hasattr(agent_data, 'max_consecutive_auto_reply'):
                normalized['metadata']['maxConsecutiveAutoReply'] = agent_data.max_consecutive_auto_reply
                
    # Handle dictionary-based agent definitions
    elif isinstance(agent_data, dict):
        # Direct field mappings
        for field in ['name', 'description', 'owner', 'version']:
            if field in agent_data:
                normalized[field] = agent_data[field]
                
        # AutoGen-specific fields
        if 'system_message' in agent_data:
            # Only override description if not already set
            if 'description' not in normalized or not normalized['description']:
                normalized['description'] = agent_data['system_message'][:200] + '...' if len(agent_data.get('system_message', '')) > 200 else agent_data.get('system_message', '')
            normalized['metadata']['systemMessage'] = agent_data['system_message']
            
        if 'llm_config' in agent_data:
            llm_config = agent_data['llm_config']
            if isinstance(llm_config, dict):
                if 'model' in llm_config:
                    normalized['metadata']['model'] = llm_config['model']
                    normalized['capabilities'].append(f"model:{llm_config['model']}")
                if 'temperature' in llm_config:
                    normalized['metadata']['temperature'] = llm_config['temperature']
                if 'functions' in llm_config:
                    normalized['capabilities'].append('function_calling:enabled')
                    function_count = len(llm_config['functions'])
                    normalized['metadata']['functionCount'] = function_count
                    normalized['capabilities'].append(f'functions:{function_count}')
                    
        if 'code_execution_config' in agent_data:
            if agent_data['code_execution_config']:
                normalized['capabilities'].append('code_execution:enabled')
                normalized['metadata']['codeExecution'] = True
                
        if 'code_execution' in agent_data:
            if agent_data['code_execution']:
                normalized['capabilities'].append('code_execution:enabled')
                normalized['metadata']['codeExecution'] = True
                
        if 'human_input_mode' in agent_data:
            normalized['metadata']['humanInputMode'] = agent_data['human_input_mode']
            if agent_data['human_input_mode'] != 'NEVER':
                normalized['capabilities'].append('human_input:enabled')
                
        if 'max_consecutive_auto_reply' in agent_data:
            normalized['metadata']['maxConsecutiveAutoReply'] = agent_data['max_consecutive_auto_reply']
            
        # Check for agent type
        if 'agent_type' in agent_data:
            normalized['metadata']['autogenAgentType'] = agent_data['agent_type']
        elif 'is_assistant' in agent_data and agent_data['is_assistant']:
            normalized['metadata']['autogenAgentType'] = 'AssistantAgent'
        elif 'is_user_proxy' in agent_data and agent_data['is_user_proxy']:
            normalized['metadata']['autogenAgentType'] = 'UserProxyAgent'
            
        # Group chat configuration
        if 'group_chat_config' in agent_data:
            normalized['capabilities'].append('group_chat:enabled')
            group_config = agent_data['group_chat_config']
            if 'agents' in group_config:
                agent_count = len(group_config['agents'])
                normalized['metadata']['groupAgentCount'] = agent_count
                normalized['capabilities'].append(f'agents:{agent_count}')
                
        # Direct agents list
        if 'agents' in agent_data:
            agents = agent_data['agents']
            if isinstance(agents, list):
                agent_count = len(agents)
                normalized['metadata']['agentCount'] = agent_count
                normalized['capabilities'].append(f'agents:{agent_count}')
                normalized['capabilities'].append('groupchat:enabled')
                
        # GroupChat specific fields
        if 'max_round' in agent_data:
            normalized['metadata']['maxRounds'] = agent_data['max_round']
        if 'speaker_selection_method' in agent_data:
            normalized['metadata']['speakerSelectionMethod'] = agent_data['speaker_selection_method']
            
        # Conversable agent support
        if 'conversable' in agent_data and agent_data['conversable']:
            normalized['capabilities'].append('conversable:enabled')
        if 'function_map' in agent_data:
            function_map = agent_data['function_map']
            if isinstance(function_map, dict):
                function_count = len(function_map)
                normalized['metadata']['functionCount'] = function_count
                normalized['capabilities'].append(f'functions:{function_count}')
                
    # Ensure capabilities are unique
    normalized['capabilities'] = list(set(normalized['capabilities']))
    
    # Set defaults for missing required fields
    if 'name' not in normalized:
        normalized['name'] = 'Unnamed AutoGen Agent'
    if 'description' not in normalized:
        normalized['description'] = 'Microsoft AutoGen agent for autonomous task completion'
    if 'owner' not in normalized:
        normalized['owner'] = 'Unknown'
    if 'version' not in normalized:
        normalized['version'] = '1.0'
    
    # Calculate trust score with AutoGen-specific bonuses
    trust_score = calculate_trust_score(normalized)
    
    # AutoGen-specific trust score bonuses
    if normalized['capabilities']:
        trust_score += min(5, len(normalized['capabilities']))
    if 'function_calling:enabled' in normalized['capabilities']:
        trust_score += 5
    if 'code_execution:enabled' in normalized['capabilities']:
        trust_score += 5
    if 'group_chat:enabled' in normalized['capabilities']:
        trust_score += 5
    if normalized['metadata'].get('groupAgentCount', 0) > 2:
        trust_score += 3  # Bonus for complex multi-agent systems
        
    normalized['trustScore'] = min(trust_score, 100)  # Production scoring
    
    return normalized


def register_autogen(agent: Any, email: str, owner: Optional[str] = None) -> Dict[str, Any]:
    """
    Register an AutoGen agent with AstraSync.
    
    Args:
        agent: AutoGen agent object or configuration
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
        logger.error(f"Failed to register AutoGen agent: {e}")
        raise


def create_registration_decorator(email: str, owner: Optional[str] = None):
    """
    Create a decorator for automatic AutoGen agent registration.
    
    Usage:
        @register_with_astrasync(email="dev@example.com")
        class MyAutoGenAgent(AssistantAgent):
            ...
    """
    def decorator(cls):
        original_init = cls.__init__
        
        def new_init(self, *args, **kwargs):
            original_init(self, *args, **kwargs)
            try:
                result = register_autogen(self, email=email, owner=owner)
                self.astrasync_id = result.get('agentId')
                self.astrasync_trust_score = result.get('trustScore')
                logger.info(f"Auto-registered AutoGen agent: {self.astrasync_id}")
            except Exception as e:
                logger.warning(f"Failed to auto-register agent: {e}")
                self.astrasync_id = None
                self.astrasync_trust_score = None
                
        cls.__init__ = new_init
        return cls
        
    return decorator


# Convenience function alias
register_with_astrasync = create_registration_decorator