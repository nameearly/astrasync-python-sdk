"""
AgentStack adapter for AstraSync agent registration.
Supports AgentStack agents, swarms, and YAML configurations.
"""

import logging
import yaml
from typing import Dict, Any, List, Optional, Union
from ..utils.trust_score import calculate_trust_score
from ..core import AstraSync

logger = logging.getLogger(__name__)


def normalize_agent_data(agent_data: Any) -> Dict[str, Any]:
    """
    Normalize AgentStack agent data to AstraSync standard format.
    
    Supports:
    - AgentStack YAML agent definitions
    - AgentStack swarm configurations
    - AgentOps monitoring metadata
    """
    # Start with empty normalized structure
    normalized = {
        'agentType': 'agentstack',
        'version': '1.0',
        'capabilities': [],
        'metadata': {}
    }
    
    # Handle different input types
    if isinstance(agent_data, str):
        # If it's a YAML string, parse it
        try:
            agent_data = yaml.safe_load(agent_data)
        except yaml.YAMLError:
            # Not valid YAML, treat as description
            normalized['description'] = agent_data
            agent_data = {}
    
    if isinstance(agent_data, dict):
        # Check for AgentStack-specific structure
        if 'agents' in agent_data and isinstance(agent_data['agents'], list):
            # Multi-agent configuration
            agents = agent_data['agents']
            
            if len(agents) == 1:
                # Single agent in list format
                agent = agents[0]
                _extract_single_agent(agent, normalized)
            else:
                # Multiple agents (swarm)
                normalized['name'] = agent_data.get('swarm_name', 'AgentStack Swarm')
                normalized['description'] = agent_data.get('description', f'AgentStack swarm with {len(agents)} agents')
                normalized['metadata']['agentCount'] = len(agents)
                normalized['capabilities'].append(f'agents:{len(agents)}')
                
                # Extract agent names/roles
                agent_names = []
                for agent in agents:
                    agent_name = agent.get('agent_name', agent.get('name', 'Unknown'))
                    agent_names.append(agent_name)
                    if 'system_prompt' in agent:
                        normalized['capabilities'].append(f'agent:{agent_name}')
                        
                normalized['metadata']['agentNames'] = agent_names
                
        elif 'agent_name' in agent_data or 'name' in agent_data:
            # Single agent configuration
            _extract_single_agent(agent_data, normalized)
            
        elif 'swarm_architecture' in agent_data:
            # Swarm architecture configuration
            swarm = agent_data['swarm_architecture']
            normalized['name'] = swarm.get('name', 'AgentStack Swarm')
            normalized['description'] = swarm.get('description', 'AgentStack swarm architecture')
            normalized['metadata']['swarmType'] = swarm.get('swarm_type', 'ConcurrentWorkflow')
            normalized['capabilities'].append(f'swarm_type:{swarm.get("swarm_type", "unknown")}')
            
            if 'task' in swarm:
                normalized['metadata']['task'] = swarm['task']
            if 'max_loops' in swarm:
                normalized['metadata']['maxLoops'] = swarm['max_loops']
                
        # Direct field mappings
        for field in ['name', 'description', 'owner', 'version']:
            if field in agent_data and field not in normalized:
                normalized[field] = agent_data[field]
                
    # Handle object instances
    elif hasattr(agent_data, '__class__'):
        class_name = agent_data.__class__.__name__
        module_name = getattr(agent_data.__class__, '__module__', '')
        
        # Check if it's an AgentStack/AgentOps agent
        if 'agentstack' in module_name.lower() or 'agentops' in module_name.lower():
            normalized['name'] = getattr(agent_data, 'agent_name', getattr(agent_data, 'name', f'{class_name} Instance'))
            normalized['description'] = getattr(agent_data, 'system_prompt', 'AgentStack agent')[:200] + '...' if hasattr(agent_data, 'system_prompt') else 'AgentStack agent'
            
            # Extract AgentStack-specific attributes
            if hasattr(agent_data, 'max_loops'):
                normalized['metadata']['maxLoops'] = agent_data.max_loops
            if hasattr(agent_data, 'autosave'):
                normalized['metadata']['autosave'] = agent_data.autosave
            if hasattr(agent_data, 'context_length'):
                normalized['metadata']['contextLength'] = agent_data.context_length
                
    # Ensure capabilities are unique
    normalized['capabilities'] = list(set(normalized['capabilities']))
    
    # Set defaults for any missing required fields
    if 'name' not in normalized:
        normalized['name'] = 'Unnamed AgentStack Agent'
    if 'description' not in normalized:
        normalized['description'] = 'AgentStack AI agent'
    if 'owner' not in normalized:
        normalized['owner'] = 'Unknown'
    if 'version' not in normalized:
        normalized['version'] = '1.0'
    
    # Calculate trust score with AgentStack-specific bonuses
    trust_score = calculate_trust_score(normalized)
    
    # AgentStack-specific trust score bonuses
    if normalized['capabilities']:
        trust_score += min(5, len(normalized['capabilities']))
    if normalized['metadata'].get('autosave'):
        trust_score += 3  # Bonus for persistence
    if normalized['metadata'].get('agentCount', 0) > 1:
        trust_score += 5  # Bonus for swarms
    if normalized['metadata'].get('contextLength', 0) > 50000:
        trust_score += 3  # Bonus for large context
    if normalized['metadata'].get('dynamicTemperature'):
        trust_score += 2  # Bonus for advanced features
        
    normalized['trustScore'] = min(trust_score, 100)  # Production scoring
    
    return normalized


def _extract_single_agent(agent: Dict[str, Any], normalized: Dict[str, Any]) -> None:
    """Extract data from a single AgentStack agent configuration."""
    # Name and description
    normalized['name'] = agent.get('agent_name', agent.get('name', 'AgentStack Agent'))
    
    if 'system_prompt' in agent:
        prompt = agent['system_prompt']
        normalized['description'] = prompt[:200] + '...' if len(prompt) > 200 else prompt
        normalized['metadata']['systemPrompt'] = prompt
        
    # Model configuration
    if 'model' in agent:
        normalized['metadata']['model'] = agent['model']
        normalized['capabilities'].append(f'model:{agent["model"]}')
    elif 'llm' in agent:
        normalized['metadata']['model'] = agent['llm']
        normalized['capabilities'].append(f'model:{agent["llm"]}')
        
    # AgentStack-specific fields
    agentstack_fields = {
        'max_loops': 'maxLoops',
        'autosave': 'autosave',
        'dashboard': 'dashboard',
        'verbose': 'verbose',
        'dynamic_temperature_enabled': 'dynamicTemperature',
        'saved_state_path': 'savedStatePath',
        'user_name': 'userName',
        'retry_attempts': 'retryAttempts',
        'context_length': 'contextLength',
        'return_step_meta': 'returnStepMeta',
        'output_type': 'outputType'
    }
    
    for field, meta_field in agentstack_fields.items():
        if field in agent:
            normalized['metadata'][meta_field] = agent[field]
            
    # Tools
    if 'tools' in agent:
        tools = agent['tools']
        if isinstance(tools, list):
            for tool in tools:
                if isinstance(tool, str):
                    normalized['capabilities'].append(f'tool:{tool}')
                elif isinstance(tool, dict):
                    tool_name = tool.get('name', 'unknown')
                    normalized['capabilities'].append(f'tool:{tool_name}')
                    
    # Memory
    if 'memory' in agent or agent.get('autosave'):
        normalized['capabilities'].append('memory:enabled')
        
    # Advanced capabilities
    if agent.get('dynamic_temperature_enabled'):
        normalized['capabilities'].append('dynamic_temperature:enabled')
    if agent.get('return_step_meta'):
        normalized['capabilities'].append('step_metadata:enabled')


def register_agentstack(agent: Any, email: str, owner: Optional[str] = None) -> Dict[str, Any]:
    """
    Register an AgentStack agent with AstraSync.
    
    Args:
        agent: AgentStack agent configuration (dict, YAML string, or object)
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
        logger.error(f"Failed to register AgentStack agent: {e}")
        raise


def create_registration_decorator(email: str, owner: Optional[str] = None):
    """
    Create a decorator for automatic AgentStack agent registration.
    
    Usage:
        @register_with_astrasync(email="dev@example.com")
        class MyAgentStackAgent:
            ...
    """
    def decorator(cls):
        original_init = cls.__init__
        
        def new_init(self, *args, **kwargs):
            original_init(self, *args, **kwargs)
            try:
                result = register_agentstack(self, email=email, owner=owner)
                self.astrasync_id = result.get('agentId')
                self.astrasync_trust_score = result.get('trustScore')
                logger.info(f"Auto-registered AgentStack agent: {self.astrasync_id}")
            except Exception as e:
                logger.warning(f"Failed to auto-register agent: {e}")
                self.astrasync_id = None
                self.astrasync_trust_score = None
                
        cls.__init__ = new_init
        return cls
        
    return decorator


# Convenience function alias
register_with_astrasync = create_registration_decorator