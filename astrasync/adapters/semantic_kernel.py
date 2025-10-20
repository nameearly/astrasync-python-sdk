"""
Microsoft Semantic Kernel adapter for AstraSync agent registration.
Supports SK agents, planners, plugins, and AI services.
"""

import logging
from typing import Dict, Any, List, Optional, Union
from ..utils.trust_score import calculate_trust_score
from ..core import AstraSync

logger = logging.getLogger(__name__)


def normalize_agent_data(agent_data: Any) -> Dict[str, Any]:
    """
    Normalize Semantic Kernel agent data to AstraSync standard format.
    
    Supports:
    - Semantic Kernel agents and kernels
    - Plugins and functions
    - Planners (Sequential, Action, Stepwise)
    - Memory stores and AI services
    """
    # Start with empty normalized structure
    normalized = {
        'agentType': 'semantic_kernel',
        'version': '1.0',
        'capabilities': [],
        'metadata': {}
    }
    
    # Handle SK kernel/agent objects (not plain dicts)
    if hasattr(agent_data, '__class__') and not isinstance(agent_data, dict):
        class_name = agent_data.__class__.__name__
        module_name = getattr(agent_data.__class__, '__module__', '')
        
        if 'semantic_kernel' in module_name.lower() or 'sk' in module_name.lower():
            normalized['name'] = getattr(agent_data, 'name', f'{class_name} Instance')
            
            # Check for Kernel
            if 'Kernel' in class_name:
                normalized['description'] = 'Semantic Kernel orchestration instance'
                normalized['metadata']['kernelClass'] = class_name
                
                # Extract plugins
                if hasattr(agent_data, 'plugins'):
                    plugin_count = len(agent_data.plugins) if hasattr(agent_data.plugins, '__len__') else 0
                    normalized['capabilities'].append(f'plugins:{plugin_count}')
                    normalized['metadata']['pluginCount'] = plugin_count
                    
                # Extract AI services
                if hasattr(agent_data, 'ai_services'):
                    for service_type, service in agent_data.ai_services.items():
                        normalized['capabilities'].append(f'ai_service:{service_type}')
                        
                # Extract memory
                if hasattr(agent_data, 'memory'):
                    if agent_data.memory:
                        normalized['capabilities'].append('memory:enabled')
                        
            # Check for Agent
            elif 'Agent' in class_name:
                normalized['description'] = getattr(agent_data, 'description', 'Semantic Kernel AI Agent')
                normalized['metadata']['agentClass'] = class_name
                normalized['capabilities'].append('agent:enabled')
                
                # Extract instructions
                if hasattr(agent_data, 'instructions'):
                    instructions = agent_data.instructions
                    normalized['metadata']['instructions'] = instructions[:500] if len(instructions) > 500 else instructions
                    
                # Extract kernel if present
                if hasattr(agent_data, 'kernel'):
                    kernel = agent_data.kernel
                    if hasattr(kernel, 'plugins'):
                        plugin_count = len(kernel.plugins) if hasattr(kernel.plugins, '__len__') else 0
                        normalized['capabilities'].append(f'plugins:{plugin_count}')
                        normalized['metadata']['pluginCount'] = plugin_count
                    if hasattr(kernel, 'memory'):
                        if kernel.memory:
                            normalized['capabilities'].append('memory:enabled')
                    
            # Check for Planner
            elif 'Planner' in class_name:
                normalized['description'] = f'Semantic Kernel {class_name}'
                normalized['metadata']['plannerType'] = class_name
                normalized['capabilities'].append(f'planner:{class_name.replace("Planner", "").lower()}')
                
    # Handle dictionary-based definitions
    elif isinstance(agent_data, dict):
        # Direct field mappings
        for field in ['name', 'description', 'owner', 'version']:
            if field in agent_data:
                normalized[field] = agent_data[field]
                
        # SK-specific configurations
        if 'kernel_config' in agent_data or 'kernel' in agent_data:
            kernel_config = agent_data.get('kernel_config', agent_data.get('kernel', {}))
            
            # AI service configuration
            if 'ai_service' in kernel_config:
                ai_service = kernel_config['ai_service']
                if 'model' in ai_service:
                    normalized['metadata']['model'] = ai_service['model']
                    normalized['capabilities'].append(f"model:{ai_service['model']}")
                if 'service_type' in ai_service:
                    normalized['capabilities'].append(f"ai_service:{ai_service['service_type']}")
                    
            # Direct model in kernel config
            if 'model' in kernel_config:
                normalized['metadata']['model'] = kernel_config['model']
                normalized['capabilities'].append(f"model:{kernel_config['model']}")
                
            # Functions in kernel config
            if 'functions' in kernel_config:
                functions = kernel_config['functions']
                if isinstance(functions, list):
                    normalized['metadata']['functionCount'] = len(functions)
                    normalized['capabilities'].append(f'functions:{len(functions)}')
                    
        # Agent configuration
        if 'agent' in agent_data:
            agent_config = agent_data['agent']
            if 'instructions' in agent_config:
                normalized['metadata']['instructions'] = agent_config['instructions']
                normalized['description'] = agent_config['instructions'][:200] + '...' if len(agent_config['instructions']) > 200 else agent_config['instructions']
            if 'plugins' in agent_config:
                plugin_list = agent_config['plugins']
                normalized['metadata']['plugins'] = plugin_list
                normalized['capabilities'].extend([f'plugin:{p}' for p in plugin_list])
                
        # Plugins configuration
        if 'plugins' in agent_data:
            plugins = agent_data['plugins']
            if isinstance(plugins, list):
                plugin_count = len(plugins)
                normalized['capabilities'].append(f'plugins:{plugin_count}')
                normalized['metadata']['pluginCount'] = plugin_count
                for plugin in plugins:
                    if isinstance(plugin, str):
                        normalized['capabilities'].append(f'plugin:{plugin}')
                    elif isinstance(plugin, dict):
                        plugin_name = plugin.get('name', plugin.get('plugin_name', 'unknown'))
                        normalized['capabilities'].append(f'plugin:{plugin_name}')
            elif isinstance(plugins, dict):
                # Dictionary of plugins
                plugin_count = len(plugins)
                normalized['capabilities'].append(f'plugins:{plugin_count}')
                normalized['metadata']['pluginCount'] = plugin_count
                for plugin_name, plugin_config in plugins.items():
                    normalized['capabilities'].append(f'plugin:{plugin_name}')
                        
        # Skills configuration (legacy name for plugins)
        if 'skills' in agent_data:
            skills = agent_data['skills']
            if isinstance(skills, list):
                skill_count = len(skills)
                normalized['capabilities'].append(f'skills:{skill_count}')
                normalized['metadata']['skillCount'] = skill_count
                
        # Functions configuration
        if 'functions' in agent_data:
            functions = agent_data['functions']
            if isinstance(functions, list):
                normalized['metadata']['functionCount'] = len(functions)
                normalized['capabilities'].append(f'functions:{len(functions)}')
                
        # Planner configuration
        if 'planner' in agent_data:
            planner = agent_data['planner']
            if isinstance(planner, str):
                normalized['capabilities'].append(f'planner:{planner.lower()}')
            elif isinstance(planner, dict):
                planner_type = planner.get('type', 'sequential')
                normalized['capabilities'].append(f'planner:{planner_type}')
                normalized['metadata']['plannerConfig'] = planner
                
        # Memory configuration
        if 'memory' in agent_data:
            memory_config = agent_data['memory']
            if memory_config:
                normalized['capabilities'].append('memory:enabled')
                if isinstance(memory_config, dict):
                    memory_type = memory_config.get('type', 'semantic')
                    normalized['metadata']['memoryType'] = memory_type
                    
        # Process/workflow configuration
        if 'process' in agent_data or 'workflow' in agent_data:
            process = agent_data.get('process', agent_data.get('workflow'))
            normalized['capabilities'].append('process:enabled')
            normalized['metadata']['hasProcess'] = True
            
        # Orchestration configuration
        if 'orchestration' in agent_data:
            if agent_data['orchestration']:
                normalized['capabilities'].append('orchestration:enabled')
            
    # Ensure capabilities are unique
    normalized['capabilities'] = list(set(normalized['capabilities']))
    
    # Set defaults for missing required fields
    if 'name' not in normalized:
        normalized['name'] = 'Unnamed Semantic Kernel Agent'
    if 'description' not in normalized:
        normalized['description'] = 'Microsoft Semantic Kernel AI orchestration'
    if 'owner' not in normalized:
        normalized['owner'] = 'Unknown'
    if 'version' not in normalized:
        normalized['version'] = '1.0'
    
    # Calculate trust score with SK-specific bonuses
    trust_score = calculate_trust_score(normalized)
    
    # Semantic Kernel-specific trust score bonuses
    if normalized['capabilities']:
        trust_score += min(5, len(normalized['capabilities']))
    if any('planner:' in cap for cap in normalized['capabilities']):
        trust_score += 5  # Bonus for planning capabilities
    if any('plugin:' in cap for cap in normalized['capabilities']):
        trust_score += 3  # Bonus for plugins
    if 'memory:enabled' in normalized['capabilities']:
        trust_score += 5
    if 'process:enabled' in normalized['capabilities']:
        trust_score += 5  # Bonus for process framework
    if normalized['metadata'].get('functionCount', 0) > 5:
        trust_score += 3  # Bonus for rich functionality
        
    normalized['trustScore'] = min(trust_score, 100)  # Production scoring
    
    return normalized


def register_semantic_kernel(agent: Any, email: str, owner: Optional[str] = None) -> Dict[str, Any]:
    """
    Register a Semantic Kernel agent with AstraSync.
    
    Args:
        agent: Semantic Kernel agent/kernel object or configuration
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
        logger.error(f"Failed to register Semantic Kernel agent: {e}")
        raise


def create_registration_decorator(email: str, owner: Optional[str] = None):
    """
    Create a decorator for automatic Semantic Kernel agent registration.
    
    Usage:
        @register_with_astrasync(email="dev@example.com")
        class MySKAgent:
            ...
    """
    def decorator(cls):
        original_init = cls.__init__
        
        def new_init(self, *args, **kwargs):
            original_init(self, *args, **kwargs)
            try:
                result = register_semantic_kernel(self, email=email, owner=owner)
                self.astrasync_id = result.get('agentId')
                self.astrasync_trust_score = result.get('trustScore')
                logger.info(f"Auto-registered Semantic Kernel agent: {self.astrasync_id}")
            except Exception as e:
                logger.warning(f"Failed to auto-register agent: {e}")
                self.astrasync_id = None
                self.astrasync_trust_score = None
                
        cls.__init__ = new_init
        return cls
        
    return decorator


# Convenience function alias
register_with_astrasync = create_registration_decorator