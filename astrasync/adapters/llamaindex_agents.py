"""
LlamaIndex agents adapter for AstraSync agent registration.
Supports llama-agents framework for multi-agent microservices.
"""

import logging
from typing import Dict, Any, List, Optional, Union
from ..utils.trust_score import calculate_trust_score
from ..core import AstraSync

logger = logging.getLogger(__name__)


def normalize_agent_data(agent_data: Any) -> Dict[str, Any]:
    """
    Normalize LlamaIndex agents data to AstraSync standard format.
    
    Supports:
    - LlamaIndex agent services and workers
    - Multi-agent orchestration
    - Tool services and query pipelines
    """
    # Start with empty normalized structure
    normalized = {
        'agentType': 'llamaindex_agents',
        'version': '1.0',
        'capabilities': [],
        'metadata': {}
    }
    
    # Handle LlamaIndex agent objects (not plain dicts)
    if hasattr(agent_data, '__class__') and not isinstance(agent_data, dict):
        class_name = agent_data.__class__.__name__
        module_name = getattr(agent_data.__class__, '__module__', '')
        
        if 'llamaindex' in module_name.lower() or 'llama_index' in module_name.lower():
            normalized['name'] = getattr(agent_data, 'name', f'{class_name} Instance')
            normalized['metadata']['agentClass'] = class_name
            
            # Check for AgentService
            if 'AgentService' in class_name or 'Service' in class_name:
                normalized['description'] = getattr(agent_data, 'description', 'LlamaIndex agent microservice')
                normalized['capabilities'].append('microservice:enabled')
                
                # Extract service configuration
                if hasattr(agent_data, 'service_name'):
                    normalized['metadata']['serviceName'] = agent_data.service_name
                if hasattr(agent_data, 'host'):
                    normalized['metadata']['host'] = agent_data.host
                if hasattr(agent_data, 'port'):
                    normalized['metadata']['port'] = agent_data.port
                    
            # Check for Agent/Worker
            elif 'Agent' in class_name or 'Worker' in class_name:
                normalized['description'] = getattr(agent_data, 'description', 'LlamaIndex agent worker')
                normalized['capabilities'].append('agent:enabled')
                
                # Extract tools
                if hasattr(agent_data, 'tools'):
                    tools = agent_data.tools
                    if tools:
                        tool_count = len(tools) if hasattr(tools, '__len__') else 0
                        normalized['capabilities'].append(f'tools:{tool_count}')
                        normalized['metadata']['toolCount'] = tool_count
                        
            # Check for Orchestrator
            elif 'Orchestrator' in class_name:
                normalized['description'] = 'LlamaIndex multi-agent orchestrator'
                normalized['capabilities'].append('orchestrator:enabled')
                
    # Handle dictionary-based definitions
    elif isinstance(agent_data, dict):
        # Direct field mappings
        for field in ['name', 'description', 'owner', 'version']:
            if field in agent_data:
                normalized[field] = agent_data[field]
                
        # Agent service configuration
        if 'agent_service' in agent_data or 'service' in agent_data:
            service_config = agent_data.get('agent_service', agent_data.get('service', {}))
            
            if 'service_name' in service_config:
                normalized['metadata']['serviceName'] = service_config['service_name']
            if 'description' in service_config:
                normalized['description'] = service_config['description']
            if 'host' in service_config:
                normalized['metadata']['host'] = service_config['host']
            if 'port' in service_config:
                normalized['metadata']['port'] = service_config['port']
                
            normalized['capabilities'].append('microservice:enabled')
            
        # Agent configuration
        if 'agent' in agent_data:
            agent_config = agent_data['agent']
            if 'system_prompt' in agent_config:
                normalized['metadata']['systemPrompt'] = agent_config['system_prompt']
            if 'tools' in agent_config:
                _extract_tools(agent_config['tools'], normalized)
                
        # Tools configuration
        if 'tools' in agent_data:
            _extract_tools(agent_data['tools'], normalized)
            
        # Orchestration configuration
        if 'orchestrator' in agent_data:
            normalized['capabilities'].append('orchestrator:enabled')
            orch_config = agent_data['orchestrator']
            if isinstance(orch_config, dict):
                if 'agents' in orch_config:
                    agents = orch_config['agents']
                    if isinstance(agents, list):
                        normalized['metadata']['agentCount'] = len(agents)
                        normalized['capabilities'].append(f'agents:{len(agents)}')
                        
        # Message queue configuration
        if 'message_queue' in agent_data:
            normalized['capabilities'].append('message_queue:enabled')
            mq_config = agent_data['message_queue']
            if isinstance(mq_config, dict):
                if 'type' in mq_config:
                    normalized['metadata']['messageQueueType'] = mq_config['type']
                    
        # Control plane configuration
        if 'control_plane' in agent_data:
            normalized['capabilities'].append('control_plane:enabled')
            
        # Human in the loop
        if 'human_in_loop' in agent_data or 'human_approval' in agent_data:
            if agent_data.get('human_in_loop', agent_data.get('human_approval')):
                normalized['capabilities'].append('human_in_loop:enabled')
                
    # Ensure capabilities are unique
    normalized['capabilities'] = list(set(normalized['capabilities']))
    
    # Set defaults for missing required fields
    if 'name' not in normalized:
        normalized['name'] = 'Unnamed LlamaIndex Agent'
    if 'description' not in normalized:
        normalized['description'] = 'LlamaIndex multi-agent microservice'
    if 'owner' not in normalized:
        normalized['owner'] = 'Unknown'
    if 'version' not in normalized:
        normalized['version'] = '1.0'
    
    # Calculate trust score with LlamaIndex-specific bonuses
    trust_score = calculate_trust_score(normalized)
    
    # LlamaIndex agents-specific trust score bonuses
    if normalized['capabilities']:
        trust_score += min(5, len(normalized['capabilities']))
    if 'microservice:enabled' in normalized['capabilities']:
        trust_score += 5  # Bonus for microservice architecture
    if 'orchestrator:enabled' in normalized['capabilities']:
        trust_score += 5  # Bonus for orchestration
    if 'message_queue:enabled' in normalized['capabilities']:
        trust_score += 3  # Bonus for async messaging
    if 'control_plane:enabled' in normalized['capabilities']:
        trust_score += 3  # Bonus for control plane
    if normalized['metadata'].get('agentCount', 0) > 2:
        trust_score += 5  # Bonus for multi-agent system
        
    normalized['trustScore'] = min(trust_score, 100)  # Production scoring
    
    return normalized


def _extract_tools(tools: Any, normalized: Dict[str, Any]) -> None:
    """Extract tool information from LlamaIndex tools configuration."""
    if isinstance(tools, list):
        tool_names = []
        for tool in tools:
            if isinstance(tool, str):
                tool_names.append(tool)
                normalized['capabilities'].append(f'tool:{tool}')
            elif isinstance(tool, dict):
                tool_name = tool.get('name', tool.get('tool_name', 'unknown'))
                tool_names.append(tool_name)
                normalized['capabilities'].append(f'tool:{tool_name}')
            elif hasattr(tool, 'name'):
                tool_names.append(tool.name)
                normalized['capabilities'].append(f'tool:{tool.name}')
                
        if tool_names:
            normalized['metadata']['tools'] = tool_names
            normalized['metadata']['toolCount'] = len(tool_names)
            normalized['capabilities'].append(f'tools:{len(tool_names)}')


def register_llamaindex_agents(agent: Any, email: str, owner: Optional[str] = None) -> Dict[str, Any]:
    """
    Register a LlamaIndex agent with AstraSync.
    
    Args:
        agent: LlamaIndex agent object or configuration
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
        logger.error(f"Failed to register LlamaIndex agent: {e}")
        raise


def create_registration_decorator(email: str, owner: Optional[str] = None):
    """
    Create a decorator for automatic LlamaIndex agent registration.
    
    Usage:
        @register_with_astrasync(email="dev@example.com")
        class MyLlamaIndexAgent:
            ...
    """
    def decorator(cls):
        original_init = cls.__init__
        
        def new_init(self, *args, **kwargs):
            original_init(self, *args, **kwargs)
            try:
                result = register_llamaindex_agents(self, email=email, owner=owner)
                self.astrasync_id = result.get('agentId')
                self.astrasync_trust_score = result.get('trustScore')
                logger.info(f"Auto-registered LlamaIndex agent: {self.astrasync_id}")
            except Exception as e:
                logger.warning(f"Failed to auto-register agent: {e}")
                self.astrasync_id = None
                self.astrasync_trust_score = None
                
        cls.__init__ = new_init
        return cls
        
    return decorator


# Convenience function alias
register_with_astrasync = create_registration_decorator