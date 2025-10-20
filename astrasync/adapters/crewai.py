"""
CrewAI adapter for AstraSync agent registration.
Supports CrewAI agents, crews, and tasks.
"""

import logging
from typing import Dict, Any, List, Optional, Union
from ..utils.trust_score import calculate_trust_score
from ..core import AstraSync

logger = logging.getLogger(__name__)


def normalize_agent_data(agent_data: Any) -> Dict[str, Any]:
    """
    Normalize CrewAI agent data to AstraSync standard format.
    
    Supports:
    - CrewAI agents
    - CrewAI crews
    - CrewAI tasks
    """
    # Start with empty normalized structure - we'll fill it based on the data
    normalized = {
        'agentType': 'crewai',
        'version': '1.0',
        'capabilities': [],
        'metadata': {}
    }
    
    # Handle different CrewAI object types
    if hasattr(agent_data, '__class__') and not isinstance(agent_data, dict):
        class_name = agent_data.__class__.__name__
        module_name = agent_data.__class__.__module__
        
        # Default name based on class if not set
        normalized['name'] = getattr(agent_data, 'name', f'{class_name} Instance')
        
        # Extract based on CrewAI class type
        if 'agent' in class_name.lower():
            normalized['metadata']['agentClass'] = class_name
            normalized['description'] = getattr(agent_data, 'backstory', f'CrewAI {class_name} agent')
            
            # Extract agent properties
            if hasattr(agent_data, 'role'):
                normalized['metadata']['role'] = agent_data.role
                normalized['capabilities'].append(f'role:{agent_data.role}')
                
            if hasattr(agent_data, 'goal'):
                normalized['metadata']['goal'] = agent_data.goal
                
            if hasattr(agent_data, 'backstory'):
                normalized['metadata']['backstory'] = agent_data.backstory
                
            if hasattr(agent_data, 'tools'):
                _extract_tools_info(agent_data.tools, normalized)
                
            if hasattr(agent_data, 'llm'):
                normalized['metadata']['llm'] = str(agent_data.llm)
                normalized['capabilities'].append(f'llm:{str(agent_data.llm)}')
                
            if hasattr(agent_data, 'max_iter'):
                normalized['metadata']['maxIterations'] = agent_data.max_iter
                
            if hasattr(agent_data, 'memory'):
                if agent_data.memory:
                    normalized['capabilities'].append('memory:enabled')
                    
        elif 'crew' in class_name.lower():
            normalized['metadata']['crewClass'] = class_name
            normalized['description'] = f'CrewAI {class_name} - Multi-agent collaboration'
            
            # Extract crew properties
            if hasattr(agent_data, 'agents'):
                agent_count = len(agent_data.agents) if hasattr(agent_data.agents, '__len__') else 0
                normalized['capabilities'].append(f'agents:{agent_count}')
                normalized['metadata']['agentCount'] = agent_count
                
                # Extract agent roles
                agent_roles = []
                for agent in agent_data.agents:
                    if hasattr(agent, 'role'):
                        agent_roles.append(agent.role)
                if agent_roles:
                    normalized['metadata']['agentRoles'] = agent_roles
                    
            if hasattr(agent_data, 'tasks'):
                task_count = len(agent_data.tasks) if hasattr(agent_data.tasks, '__len__') else 0
                normalized['capabilities'].append(f'tasks:{task_count}')
                normalized['metadata']['taskCount'] = task_count
                
            if hasattr(agent_data, 'process'):
                normalized['metadata']['process'] = str(agent_data.process)
                normalized['capabilities'].append(f'process:{str(agent_data.process)}')
                
        elif 'task' in class_name.lower():
            normalized['metadata']['taskClass'] = class_name
            normalized['description'] = getattr(agent_data, 'description', f'CrewAI {class_name}')
            
            # Extract task properties
            if hasattr(agent_data, 'description'):
                normalized['metadata']['taskDescription'] = agent_data.description
                
            if hasattr(agent_data, 'agent'):
                if hasattr(agent_data.agent, 'role'):
                    normalized['metadata']['assignedAgent'] = agent_data.agent.role
                    
            if hasattr(agent_data, 'expected_output'):
                normalized['metadata']['expectedOutput'] = agent_data.expected_output
                
    # Handle dictionary-based agent definitions
    elif isinstance(agent_data, dict):
        # Direct field mappings first
        for field in ['name', 'description', 'owner', 'version']:
            if field in agent_data:
                normalized[field] = agent_data[field]
        
        # Check for CrewAI-specific keys
        if 'role' in agent_data:
            normalized['metadata']['role'] = agent_data['role']
            normalized['capabilities'].append(f"role:{agent_data['role']}")
            if 'name' not in agent_data:
                normalized['name'] = f"CrewAI {agent_data['role']} Agent"
                
        if 'goal' in agent_data:
            normalized['metadata']['goal'] = agent_data['goal']
            
        if 'backstory' in agent_data:
            normalized['metadata']['backstory'] = agent_data['backstory']
            if 'description' not in agent_data:
                normalized['description'] = agent_data['backstory'][:200] + '...' if len(agent_data['backstory']) > 200 else agent_data['backstory']
                
        if 'tools' in agent_data:
            tools = agent_data['tools']
            if isinstance(tools, list):
                for tool in tools:
                    if isinstance(tool, str):
                        normalized['capabilities'].append(f'tool:{tool}')
                    elif isinstance(tool, dict) and 'name' in tool:
                        normalized['capabilities'].append(f"tool:{tool['name']}")
                        
        if 'llm' in agent_data:
            normalized['metadata']['llm'] = agent_data['llm']
            normalized['capabilities'].append(f"llm:{agent_data['llm']}")
            
        if 'memory' in agent_data:
            normalized['capabilities'].append('memory:enabled')
            normalized['metadata']['memory'] = agent_data['memory']
            
        if 'max_iter' in agent_data:
            normalized['metadata']['maxIterations'] = agent_data['max_iter']
            
        # Crew-specific fields
        if 'agents' in agent_data:
            if isinstance(agent_data['agents'], list):
                normalized['metadata']['agentCount'] = len(agent_data['agents'])
                normalized['capabilities'].append(f"agents:{len(agent_data['agents'])}")
                
        if 'tasks' in agent_data:
            if isinstance(agent_data['tasks'], list):
                normalized['metadata']['taskCount'] = len(agent_data['tasks'])
                normalized['capabilities'].append(f"tasks:{len(agent_data['tasks'])}")
                
        if 'process' in agent_data:
            normalized['metadata']['process'] = agent_data['process']
            normalized['capabilities'].append(f"process:{agent_data['process']}")
            
        if 'capabilities' in agent_data:
            if isinstance(agent_data['capabilities'], list):
                normalized['capabilities'].extend(agent_data['capabilities'])
                
    # Ensure capabilities are unique
    normalized['capabilities'] = list(set(normalized['capabilities']))
    
    # Set defaults for any missing required fields
    if 'name' not in normalized:
        normalized['name'] = 'Unnamed CrewAI Agent'
    if 'description' not in normalized:
        normalized['description'] = 'A CrewAI-based autonomous agent'
    if 'owner' not in normalized:
        normalized['owner'] = 'Unknown'
    if 'version' not in normalized:
        normalized['version'] = '1.0'
    
    # Calculate trust score with CrewAI-specific bonuses
    trust_score = calculate_trust_score(normalized)
    
    # CrewAI-specific trust score bonuses
    if normalized['capabilities']:
        trust_score += min(5, len(normalized['capabilities']))
    if 'memory:enabled' in normalized['capabilities']:
        trust_score += 5
    if normalized['metadata'].get('agentCount', 0) > 1:
        trust_score += 5  # Bonus for multi-agent crews
    if normalized['metadata'].get('role'):
        trust_score += 3  # Bonus for defined role
        
    normalized['trustScore'] = min(trust_score, 100)  # Production scoring
    
    return normalized


def _extract_tools_info(tools: List[Any], normalized: Dict[str, Any]) -> None:
    """Extract tools information from CrewAI tools list."""
    tool_names = []
    for tool in tools:
        if hasattr(tool, 'name'):
            tool_names.append(tool.name)
            normalized['capabilities'].append(f'tool:{tool.name}')
        elif hasattr(tool, '__class__'):
            tool_name = tool.__class__.__name__
            tool_names.append(tool_name)
            normalized['capabilities'].append(f'tool:{tool_name}')
        elif isinstance(tool, dict) and 'name' in tool:
            tool_names.append(tool['name'])
            normalized['capabilities'].append(f"tool:{tool['name']}")
        elif isinstance(tool, str):
            tool_names.append(tool)
            normalized['capabilities'].append(f'tool:{tool}')
            
    if tool_names:
        normalized['metadata']['tools'] = tool_names


def register_crewai(agent: Any, email: str, owner: Optional[str] = None) -> Dict[str, Any]:
    """
    Register a CrewAI agent with AstraSync.
    
    Args:
        agent: CrewAI agent, crew, or task object
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
        logger.error(f"Failed to register CrewAI agent: {e}")
        raise


def create_registration_decorator(email: str, owner: Optional[str] = None):
    """
    Create a decorator for automatic CrewAI agent registration.
    
    Usage:
        @register_with_astrasync(email="dev@example.com")
        class MyAgent(Agent):
            ...
    """
    def decorator(cls):
        original_init = cls.__init__
        
        def new_init(self, *args, **kwargs):
            original_init(self, *args, **kwargs)
            try:
                result = register_crewai(self, email=email, owner=owner)
                self.astrasync_id = result.get('agentId')
                self.astrasync_trust_score = result.get('trustScore')
                logger.info(f"Auto-registered CrewAI agent: {self.astrasync_id}")
            except Exception as e:
                logger.warning(f"Failed to auto-register agent: {e}")
                self.astrasync_id = None
                self.astrasync_trust_score = None
                
        cls.__init__ = new_init
        return cls
        
    return decorator


# Convenience function alias
register_with_astrasync = create_registration_decorator