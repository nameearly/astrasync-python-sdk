"""
BabyAGI adapter for AstraSync agent registration.
Supports BabyAGI autonomous task management agents.
"""

import logging
from typing import Dict, Any, List, Optional, Union
from ..utils.trust_score import calculate_trust_score
from ..core import AstraSync

logger = logging.getLogger(__name__)


def normalize_agent_data(agent_data: Any) -> Dict[str, Any]:
    """
    Normalize BabyAGI agent data to AstraSync standard format.
    
    Supports:
    - BabyAGI task management systems
    - Autonomous task creation and prioritization
    - Vector memory stores
    - Execution chains
    """
    # Start with empty normalized structure
    normalized = {
        'agentType': 'babyagi',
        'version': '1.0',
        'capabilities': [],
        'metadata': {}
    }
    
    # Handle BabyAGI agent objects (not plain dicts)
    if hasattr(agent_data, '__class__') and not isinstance(agent_data, dict):
        class_name = agent_data.__class__.__name__
        module_name = getattr(agent_data.__class__, '__module__', '')
        
        if 'babyagi' in module_name.lower() or 'baby_agi' in module_name.lower():
            normalized['name'] = getattr(agent_data, 'name', 'BabyAGI Instance')
            normalized['metadata']['agentClass'] = class_name
            
            # Extract objective
            if hasattr(agent_data, 'objective'):
                normalized['description'] = f"BabyAGI pursuing: {agent_data.objective}"
                normalized['metadata']['objective'] = agent_data.objective
                
            # Extract task list
            if hasattr(agent_data, 'task_list') or hasattr(agent_data, 'tasks'):
                tasks = getattr(agent_data, 'task_list', getattr(agent_data, 'tasks', []))
                if tasks:
                    task_count = len(tasks) if hasattr(tasks, '__len__') else 0
                    normalized['capabilities'].append(f'tasks:{task_count}')
                    normalized['metadata']['taskCount'] = task_count
                    
            # Check for memory/vectorstore
            if hasattr(agent_data, 'vectorstore') or hasattr(agent_data, 'memory'):
                normalized['capabilities'].append('memory:enabled')
                normalized['capabilities'].append('vectorstore:enabled')
                
            # Check for execution chain
            if hasattr(agent_data, 'execution_chain') or hasattr(agent_data, 'chain'):
                normalized['capabilities'].append('execution_chain:enabled')
                
            # Check for LLM configuration
            if hasattr(agent_data, 'llm'):
                normalized['metadata']['llm'] = str(agent_data.llm)
                
    # Handle dictionary-based definitions
    elif isinstance(agent_data, dict):
        # Direct field mappings
        for field in ['name', 'description', 'owner', 'version']:
            if field in agent_data:
                normalized[field] = agent_data[field]
                
        # BabyAGI-specific fields
        if 'objective' in agent_data:
            objective = agent_data['objective']
            normalized['metadata']['objective'] = objective
            normalized['description'] = f"BabyAGI pursuing: {objective}"
            normalized['capabilities'].append('autonomous:enabled')
            
        if 'initial_task' in agent_data or 'first_task' in agent_data:
            initial_task = agent_data.get('initial_task', agent_data.get('first_task'))
            normalized['metadata']['initialTask'] = initial_task
            
        if 'task_list' in agent_data or 'tasks' in agent_data:
            tasks = agent_data.get('task_list', agent_data.get('tasks', []))
            if isinstance(tasks, list):
                normalized['metadata']['taskCount'] = len(tasks)
                normalized['capabilities'].append(f'tasks:{len(tasks)}')
                
                # Extract task details
                if tasks and isinstance(tasks[0], dict):
                    normalized['metadata']['taskStructure'] = 'complex'
                    normalized['capabilities'].append('task_prioritization:enabled')
                    
        if 'vectorstore' in agent_data or 'memory_backend' in agent_data:
            normalized['capabilities'].append('memory:enabled')
            normalized['capabilities'].append('vectorstore:enabled')
            vectorstore = agent_data.get('vectorstore', agent_data.get('memory_backend'))
            if isinstance(vectorstore, dict):
                if 'type' in vectorstore:
                    normalized['metadata']['vectorstoreType'] = vectorstore['type']
                    
        if 'llm' in agent_data or 'model' in agent_data:
            model = agent_data.get('llm', agent_data.get('model'))
            if isinstance(model, str):
                normalized['metadata']['model'] = model
                normalized['capabilities'].append(f'model:{model}')
            elif isinstance(model, dict) and 'model_name' in model:
                normalized['metadata']['model'] = model['model_name']
                normalized['capabilities'].append(f'model:{model["model_name"]}')
                
        if 'execution_chain' in agent_data:
            normalized['capabilities'].append('execution_chain:enabled')
            if isinstance(agent_data['execution_chain'], dict):
                normalized['metadata']['executionChainType'] = agent_data['execution_chain'].get('type', 'default')
                
        if 'max_iterations' in agent_data:
            normalized['metadata']['maxIterations'] = agent_data['max_iterations']
            
        # Task creation and prioritization
        if 'task_creation_chain' in agent_data:
            normalized['capabilities'].append('task_creation:enabled')
        if 'task_prioritization_chain' in agent_data:
            normalized['capabilities'].append('task_prioritization:enabled')
            
    # Ensure capabilities are unique
    normalized['capabilities'] = list(set(normalized['capabilities']))
    
    # Set defaults for missing required fields
    if 'name' not in normalized:
        normalized['name'] = 'Unnamed BabyAGI Agent'
    if 'description' not in normalized:
        normalized['description'] = 'Autonomous task management AI system'
    if 'owner' not in normalized:
        normalized['owner'] = 'Unknown'
    if 'version' not in normalized:
        normalized['version'] = '1.0'
    
    # Calculate trust score with BabyAGI-specific bonuses
    trust_score = calculate_trust_score(normalized)
    
    # BabyAGI-specific trust score bonuses
    if normalized['capabilities']:
        trust_score += min(5, len(normalized['capabilities']))
    if 'autonomous:enabled' in normalized['capabilities']:
        trust_score += 5  # Bonus for autonomous operation
    if 'vectorstore:enabled' in normalized['capabilities']:
        trust_score += 5  # Bonus for memory
    if 'task_creation:enabled' in normalized['capabilities']:
        trust_score += 5  # Bonus for task generation
    if 'task_prioritization:enabled' in normalized['capabilities']:
        trust_score += 3  # Bonus for smart prioritization
    if normalized['metadata'].get('taskCount', 0) > 5:
        trust_score += 3  # Bonus for managing multiple tasks
        
    normalized['trustScore'] = min(trust_score, 100)  # Production scoring
    
    return normalized


def register_babyagi(agent: Any, email: str, owner: Optional[str] = None) -> Dict[str, Any]:
    """
    Register a BabyAGI agent with AstraSync.
    
    Args:
        agent: BabyAGI agent object or configuration
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
        logger.error(f"Failed to register BabyAGI agent: {e}")
        raise


def create_registration_decorator(email: str, owner: Optional[str] = None):
    """
    Create a decorator for automatic BabyAGI agent registration.
    
    Usage:
        @register_with_astrasync(email="dev@example.com")
        class MyBabyAGI:
            ...
    """
    def decorator(cls):
        original_init = cls.__init__
        
        def new_init(self, *args, **kwargs):
            original_init(self, *args, **kwargs)
            try:
                result = register_babyagi(self, email=email, owner=owner)
                self.astrasync_id = result.get('agentId')
                self.astrasync_trust_score = result.get('trustScore')
                logger.info(f"Auto-registered BabyAGI agent: {self.astrasync_id}")
            except Exception as e:
                logger.warning(f"Failed to auto-register agent: {e}")
                self.astrasync_id = None
                self.astrasync_trust_score = None
                
        cls.__init__ = new_init
        return cls
        
    return decorator


# Convenience function alias
register_with_astrasync = create_registration_decorator