"""
OpenAI Swarm adapter for AstraSync agent registration.
Supports Swarm agents, routines, and handoffs.
"""

import logging
from typing import Dict, Any, List, Optional, Union
from ..utils.trust_score import calculate_trust_score
from ..core import AstraSync

logger = logging.getLogger(__name__)


def normalize_agent_data(agent_data: Any) -> Dict[str, Any]:
    """
    Normalize OpenAI Swarm agent data to AstraSync standard format.
    
    Supports:
    - Swarm agents with instructions and functions
    - Agent handoffs and routines
    - Multi-agent orchestration
    """
    # Start with empty normalized structure
    normalized = {
        'agentType': 'swarm',
        'version': '1.0',
        'capabilities': [],
        'metadata': {}
    }
    
    # Handle Swarm agent objects (not plain dicts)
    if hasattr(agent_data, '__class__') and not isinstance(agent_data, dict):
        class_name = agent_data.__class__.__name__
        module_name = getattr(agent_data.__class__, '__module__', '')
        
        if 'swarm' in module_name.lower() or 'openai' in module_name.lower():
            # Check for Agent class
            if class_name == 'Agent' or 'Agent' in class_name:
                normalized['name'] = getattr(agent_data, 'name', 'Unnamed Swarm Agent')
                normalized['metadata']['agentClass'] = 'SwarmAgent'
                
                # Extract instructions
                if hasattr(agent_data, 'instructions'):
                    instructions = agent_data.instructions
                    if callable(instructions):
                        normalized['description'] = 'Swarm agent with dynamic instructions'
                        normalized['capabilities'].append('dynamic_instructions:enabled')
                    else:
                        normalized['description'] = str(instructions)[:200] + '...' if len(str(instructions)) > 200 else str(instructions)
                        normalized['metadata']['instructions'] = str(instructions)
                        
                # Extract functions
                if hasattr(agent_data, 'functions'):
                    functions = agent_data.functions
                    if functions:
                        function_count = len(functions) if hasattr(functions, '__len__') else 0
                        normalized['capabilities'].append(f'functions:{function_count}')
                        normalized['metadata']['functionCount'] = function_count
                        
                        # Extract function names if possible
                        function_names = []
                        for func in functions:
                            if hasattr(func, '__name__'):
                                function_names.append(func.__name__)
                                normalized['capabilities'].append(f'function:{func.__name__}')
                        if function_names:
                            normalized['metadata']['functions'] = function_names
                            
                # Check for model
                if hasattr(agent_data, 'model'):
                    normalized['metadata']['model'] = agent_data.model
                    normalized['capabilities'].append(f'model:{agent_data.model}')
                    
    # Handle dictionary-based definitions
    elif isinstance(agent_data, dict):
        # Direct field mappings
        for field in ['name', 'description', 'owner', 'version']:
            if field in agent_data:
                normalized[field] = agent_data[field]
                
        # Swarm-specific fields
        if 'instructions' in agent_data:
            instructions = agent_data['instructions']
            normalized['metadata']['instructions'] = instructions
            normalized['description'] = instructions[:200] + '...' if len(instructions) > 200 else instructions
            
        if 'functions' in agent_data:
            functions = agent_data['functions']
            if isinstance(functions, list):
                normalized['metadata']['functionCount'] = len(functions)
                normalized['capabilities'].append(f'functions:{len(functions)}')
                
                for func in functions:
                    if isinstance(func, str):
                        normalized['capabilities'].append(f'function:{func}')
                    elif isinstance(func, dict) and 'name' in func:
                        normalized['capabilities'].append(f'function:{func["name"]}')
                        
        if 'model' in agent_data:
            normalized['metadata']['model'] = agent_data['model']
            normalized['capabilities'].append(f'model:{agent_data["model"]}')
            
        # Multi-agent configuration
        if 'agents' in agent_data:
            agents = agent_data['agents']
            if isinstance(agents, list):
                agent_count = len(agents)
                normalized['metadata']['agentCount'] = agent_count
                normalized['capabilities'].append(f'agents:{agent_count}')
                
                # Extract agent names
                agent_names = []
                for agent in agents:
                    if isinstance(agent, dict) and 'name' in agent:
                        agent_names.append(agent['name'])
                    elif isinstance(agent, str):
                        agent_names.append(agent)
                if agent_names:
                    normalized['metadata']['agentNames'] = agent_names
                    
        # Handoff configuration
        if 'handoffs' in agent_data or 'can_handoff_to' in agent_data:
            normalized['capabilities'].append('handoffs:enabled')
            handoffs = agent_data.get('handoffs', agent_data.get('can_handoff_to', []))
            if isinstance(handoffs, list) and handoffs:
                normalized['metadata']['handoffTargets'] = handoffs
                
        # Routine configuration
        if 'routines' in agent_data:
            normalized['capabilities'].append('routines:enabled')
            routines = agent_data['routines']
            if isinstance(routines, list):
                normalized['metadata']['routineCount'] = len(routines)
                
    # Ensure capabilities are unique
    normalized['capabilities'] = list(set(normalized['capabilities']))
    
    # Set defaults for missing required fields
    if 'name' not in normalized:
        normalized['name'] = 'Unnamed Swarm Agent'
    if 'description' not in normalized:
        normalized['description'] = 'OpenAI Swarm agent for lightweight orchestration'
    if 'owner' not in normalized:
        normalized['owner'] = 'Unknown'
    if 'version' not in normalized:
        normalized['version'] = '1.0'
    
    # Calculate trust score with Swarm-specific bonuses
    trust_score = calculate_trust_score(normalized)
    
    # Swarm-specific trust score bonuses
    if normalized['capabilities']:
        trust_score += min(5, len(normalized['capabilities']))
    if 'handoffs:enabled' in normalized['capabilities']:
        trust_score += 5  # Bonus for handoff capability
    if 'dynamic_instructions:enabled' in normalized['capabilities']:
        trust_score += 3  # Bonus for dynamic behavior
    if normalized['metadata'].get('functionCount', 0) > 3:
        trust_score += 3
    if normalized['metadata'].get('agentCount', 0) > 1:
        trust_score += 5  # Bonus for multi-agent swarm
        
    normalized['trustScore'] = min(trust_score, 100)  # Production scoring
    
    return normalized


def register_swarm(agent: Any, email: str, owner: Optional[str] = None) -> Dict[str, Any]:
    """
    Register an OpenAI Swarm agent with AstraSync.
    
    Args:
        agent: Swarm agent object or configuration
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
        logger.error(f"Failed to register Swarm agent: {e}")
        raise


def create_registration_decorator(email: str, owner: Optional[str] = None):
    """
    Create a decorator for automatic Swarm agent registration.
    
    Usage:
        @register_with_astrasync(email="dev@example.com")
        class MySwarmAgent:
            ...
    """
    def decorator(cls):
        original_init = cls.__init__
        
        def new_init(self, *args, **kwargs):
            original_init(self, *args, **kwargs)
            try:
                result = register_swarm(self, email=email, owner=owner)
                self.astrasync_id = result.get('agentId')
                self.astrasync_trust_score = result.get('trustScore')
                logger.info(f"Auto-registered Swarm agent: {self.astrasync_id}")
            except Exception as e:
                logger.warning(f"Failed to auto-register agent: {e}")
                self.astrasync_id = None
                self.astrasync_trust_score = None
                
        cls.__init__ = new_init
        return cls
        
    return decorator


# Convenience function alias
register_with_astrasync = create_registration_decorator