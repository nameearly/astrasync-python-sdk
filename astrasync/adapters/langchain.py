"""
LangChain adapter for AstraSync agent registration.
Supports LangChain agents, chains, and tools.
"""

import logging
from typing import Dict, Any, List, Optional, Union
from ..utils.trust_score import calculate_trust_score
from ..core import AstraSync

logger = logging.getLogger(__name__)


def normalize_agent_data(agent_data: Any) -> Dict[str, Any]:
    """
    Normalize LangChain agent data to AstraSync standard format.
    
    Supports:
    - LangChain agents (AgentExecutor, BaseAgent)
    - LangChain chains (LLMChain, SequentialChain, etc.)
    - LangChain tools
    """
    # Start with empty normalized structure - we'll fill it based on the data
    normalized = {
        'agentType': 'langchain',
        'version': '1.0',
        'capabilities': [],
        'metadata': {}
    }
    
    # Handle different LangChain object types
    if hasattr(agent_data, '__class__') and not isinstance(agent_data, dict):
        class_name = agent_data.__class__.__name__
        module_name = agent_data.__class__.__module__
        
        # Default name based on class if not set
        normalized['name'] = getattr(agent_data, 'name', f'{class_name} Instance')
        
        # Extract agent type from class
        if 'agent' in class_name.lower():
            normalized['metadata']['agentClass'] = class_name
            normalized['description'] = f'LangChain {class_name} agent'
            
            # Extract agent-specific properties
            if hasattr(agent_data, 'agent'):
                # AgentExecutor case
                if hasattr(agent_data.agent, 'llm_chain'):
                    _extract_llm_info(agent_data.agent.llm_chain, normalized)
                if hasattr(agent_data.agent, 'allowed_tools'):
                    tools = agent_data.agent.allowed_tools
                    normalized['capabilities'].extend([f'tool:{tool}' for tool in tools])
            
            # Extract tools if available
            if hasattr(agent_data, 'tools'):
                _extract_tools_info(agent_data.tools, normalized)
                
        elif 'chain' in class_name.lower():
            normalized['metadata']['chainClass'] = class_name
            normalized['description'] = f'LangChain {class_name}'
            
            # Extract chain-specific properties
            if hasattr(agent_data, 'llm'):
                _extract_llm_info(agent_data, normalized)
            
            # Sequential chain handling
            if hasattr(agent_data, 'chains'):
                chain_names = []
                for chain in agent_data.chains:
                    if hasattr(chain, '__class__'):
                        chain_names.append(chain.__class__.__name__)
                normalized['capabilities'].append(f'sequential_chain:{len(chain_names)}')
                normalized['metadata']['chainSequence'] = chain_names
                
        # Extract general properties
        if hasattr(agent_data, 'verbose'):
            normalized['metadata']['verbose'] = agent_data.verbose
            
        if hasattr(agent_data, 'memory'):
            if agent_data.memory is not None:
                normalized['capabilities'].append('memory:enabled')
                memory_type = agent_data.memory.__class__.__name__
                normalized['metadata']['memoryType'] = memory_type
                
        if hasattr(agent_data, 'callbacks'):
            if agent_data.callbacks:
                normalized['capabilities'].append('callbacks:enabled')
                
        if hasattr(agent_data, 'tags'):
            if agent_data.tags:
                normalized['metadata']['tags'] = list(agent_data.tags)
                
    # Handle dictionary-based agent definitions
    elif isinstance(agent_data, dict):
        # Direct field mappings first
        for field in ['name', 'description', 'owner', 'version']:
            if field in agent_data:
                normalized[field] = agent_data[field]
        
        # Check for LangChain-specific keys
        if 'agent_type' in agent_data:
            normalized['metadata']['agentType'] = agent_data['agent_type']
            if 'name' not in agent_data:
                normalized['name'] = f"LangChain {agent_data['agent_type']} Agent"
            
        if 'llm' in agent_data:
            normalized['metadata']['llm'] = agent_data['llm']
            normalized['capabilities'].append(f"llm:{agent_data['llm']}")
            
        if 'tools' in agent_data:
            tools = agent_data['tools']
            if isinstance(tools, list):
                for tool in tools:
                    if isinstance(tool, str):
                        normalized['capabilities'].append(f'tool:{tool}')
                    elif isinstance(tool, dict) and 'name' in tool:
                        normalized['capabilities'].append(f"tool:{tool['name']}")
                        
        if 'memory' in agent_data:
            normalized['capabilities'].append('memory:enabled')
            normalized['metadata']['memory'] = agent_data['memory']
            
        if 'prompt' in agent_data:
            normalized['metadata']['hasPrompt'] = True
            # Extract description from prompt if possible
            prompt_str = str(agent_data['prompt'])
            if len(prompt_str) > 50:
                normalized['description'] = prompt_str[:100] + '...'
                
        if 'capabilities' in agent_data:
            if isinstance(agent_data['capabilities'], list):
                normalized['capabilities'].extend(agent_data['capabilities'])
                
    # Ensure capabilities are unique
    normalized['capabilities'] = list(set(normalized['capabilities']))
    
    # Set defaults for any missing required fields
    if 'name' not in normalized:
        normalized['name'] = 'Unnamed LangChain Agent'
    if 'description' not in normalized:
        normalized['description'] = 'A LangChain-based AI agent'
    if 'owner' not in normalized:
        normalized['owner'] = 'Unknown'
    if 'version' not in normalized:
        normalized['version'] = '1.0'
    
    # Calculate trust score with LangChain-specific bonuses
    trust_score = calculate_trust_score(normalized)
    
    # LangChain-specific trust score bonuses
    if normalized['capabilities']:
        trust_score += min(5, len(normalized['capabilities']))
    if 'memory:enabled' in normalized['capabilities']:
        trust_score += 5
    if normalized['metadata'].get('agentClass', '').endswith('Agent'):
        trust_score += 5
        
    normalized['trustScore'] = min(trust_score, 100)  # Production scoring
    
    return normalized


def _extract_llm_info(llm_object: Any, normalized: Dict[str, Any]) -> None:
    """Extract LLM information from a LangChain LLM object."""
    if hasattr(llm_object, 'model_name'):
        normalized['metadata']['model'] = llm_object.model_name
        normalized['capabilities'].append(f'model:{llm_object.model_name}')
    elif hasattr(llm_object, 'model'):
        normalized['metadata']['model'] = llm_object.model
        normalized['capabilities'].append(f'model:{llm_object.model}')
        
    if hasattr(llm_object, 'temperature'):
        normalized['metadata']['temperature'] = llm_object.temperature
        
    if hasattr(llm_object, 'llm') and hasattr(llm_object.llm, 'model_name'):
        # For chains with nested LLM
        normalized['metadata']['model'] = llm_object.llm.model_name
        normalized['capabilities'].append(f'model:{llm_object.llm.model_name}')


def _extract_tools_info(tools: List[Any], normalized: Dict[str, Any]) -> None:
    """Extract tools information from LangChain tools list."""
    tool_names = []
    for tool in tools:
        if hasattr(tool, 'name'):
            tool_names.append(tool.name)
            normalized['capabilities'].append(f'tool:{tool.name}')
        elif isinstance(tool, dict) and 'name' in tool:
            tool_names.append(tool['name'])
            normalized['capabilities'].append(f"tool:{tool['name']}")
        elif isinstance(tool, str):
            tool_names.append(tool)
            normalized['capabilities'].append(f'tool:{tool}')
            
    if tool_names:
        normalized['metadata']['tools'] = tool_names


def register_langchain(agent: Any, email: str, owner: Optional[str] = None) -> Dict[str, Any]:
    """
    Register a LangChain agent with AstraSync.
    
    Args:
        agent: LangChain agent, chain, or tool object
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
        logger.error(f"Failed to register LangChain agent: {e}")
        raise


def create_registration_decorator(email: str, owner: Optional[str] = None):
    """
    Create a decorator for automatic LangChain agent registration.
    
    Usage:
        @register_with_astrasync(email="dev@example.com")
        class MyAgent(AgentExecutor):
            ...
    """
    def decorator(cls):
        original_init = cls.__init__
        
        def new_init(self, *args, **kwargs):
            original_init(self, *args, **kwargs)
            try:
                result = register_langchain(self, email=email, owner=owner)
                self.astrasync_id = result.get('agentId')
                self.astrasync_trust_score = result.get('trustScore')
                logger.info(f"Auto-registered LangChain agent: {self.astrasync_id}")
            except Exception as e:
                logger.warning(f"Failed to auto-register agent: {e}")
                self.astrasync_id = None
                self.astrasync_trust_score = None
                
        cls.__init__ = new_init
        return cls
        
    return decorator


# Convenience function alias
register_with_astrasync = create_registration_decorator