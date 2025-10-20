"""
n8n adapter for AstraSync agent registration.
Supports n8n AI Agent nodes and workflows.
"""

import logging
from typing import Dict, Any, List, Optional, Union
from ..utils.trust_score import calculate_trust_score
from ..core import AstraSync

logger = logging.getLogger(__name__)


def normalize_agent_data(agent_data: Any) -> Dict[str, Any]:
    """
    Normalize n8n agent/workflow data to AstraSync standard format.
    
    Supports:
    - n8n AI Agent nodes
    - n8n workflows with AI agents
    - LangChain integrations in n8n
    """
    # Start with empty normalized structure
    normalized = {
        'agentType': 'n8n',
        'version': '1.0',
        'capabilities': [],
        'metadata': {}
    }
    
    # Handle n8n workflow structure
    if isinstance(agent_data, dict):
        # Check if it's a workflow definition
        if 'workflow' in agent_data or 'nodes' in agent_data:
            workflow = agent_data.get('workflow', agent_data)
            normalized['name'] = workflow.get('name', 'Unnamed n8n Workflow')
            normalized['description'] = workflow.get('description', 'n8n AI workflow automation')
            
            # Extract nodes
            nodes = workflow.get('nodes', [])
            ai_agent_nodes = []
            tool_nodes = []
            
            for node in nodes:
                node_type = node.get('type', '')
                node_name = node.get('name', '')
                
                # Check for AI Agent nodes
                if 'agent' in node_type.lower() or 'langchain' in node_type.lower():
                    ai_agent_nodes.append(node)
                    normalized['capabilities'].append(f'agent:{node_name}')
                    
                    # Extract agent parameters
                    params = node.get('parameters', {})
                    if 'systemPrompt' in params:
                        normalized['metadata']['systemPrompt'] = params['systemPrompt']
                    if 'model' in params:
                        normalized['metadata']['model'] = params['model']
                        normalized['capabilities'].append(f'model:{params["model"]}')
                        
                # Check for tool nodes
                elif any(tool in node_type.lower() for tool in ['tool', 'http', 'code', 'function']):
                    tool_nodes.append(node)
                    normalized['capabilities'].append(f'tool:{node_name}')
                    
            normalized['metadata']['agentNodeCount'] = len(ai_agent_nodes)
            normalized['metadata']['toolNodeCount'] = len(tool_nodes)
            normalized['metadata']['totalNodeCount'] = len(nodes)
            
            # Check for memory configurations
            for node in ai_agent_nodes:
                params = node.get('parameters', {})
                if 'memory' in params:
                    normalized['capabilities'].append('memory:enabled')
                    memory_type = params['memory'].get('type', 'unknown')
                    normalized['metadata']['memoryType'] = memory_type
                    
        # Check if it's a single AI Agent node configuration
        elif 'type' in agent_data and ('agent' in agent_data['type'].lower() or 'langchain' in agent_data['type'].lower()):
            normalized['name'] = agent_data.get('name', 'n8n AI Agent')
            params = agent_data.get('parameters', {})
            
            # Extract from parameters
            if 'systemPrompt' in params:
                normalized['description'] = params['systemPrompt'][:200] + '...' if len(params.get('systemPrompt', '')) > 200 else params.get('systemPrompt', 'n8n AI Agent')
                normalized['metadata']['systemPrompt'] = params['systemPrompt']
                
            if 'model' in params:
                normalized['metadata']['model'] = params['model']
                normalized['capabilities'].append(f'model:{params["model"]}')
                
            if 'tools' in params:
                tools = params['tools']
                if isinstance(tools, list):
                    for tool in tools:
                        if isinstance(tool, str):
                            normalized['capabilities'].append(f'tool:{tool}')
                        elif isinstance(tool, dict):
                            tool_name = tool.get('name', tool.get('type', 'unknown'))
                            normalized['capabilities'].append(f'tool:{tool_name}')
                            
            if 'memory' in params:
                normalized['capabilities'].append('memory:enabled')
                if isinstance(params['memory'], dict):
                    normalized['metadata']['memoryType'] = params['memory'].get('type', 'buffer')
                    
            # n8n specific fields
            if 'agentType' in params:
                normalized['metadata']['n8nAgentType'] = params['agentType']
            if 'outputParsing' in params:
                normalized['capabilities'].append('output_parsing:enabled')
                
        # Direct field mappings
        for field in ['name', 'description', 'owner', 'version']:
            if field in agent_data:
                normalized[field] = agent_data[field]
                
        # Handle n8n-specific metadata
        if 'settings' in agent_data:
            normalized['metadata']['settings'] = agent_data['settings']
            
        if 'staticData' in agent_data:
            normalized['metadata']['hasStaticData'] = True
            
        if 'connections' in agent_data:
            # Extract connection information
            connections = agent_data['connections']
            normalized['metadata']['connectionCount'] = len(connections)
            
    # Handle object instances (less common for n8n)
    elif hasattr(agent_data, '__class__'):
        class_name = agent_data.__class__.__name__
        normalized['name'] = getattr(agent_data, 'name', f'n8n {class_name}')
        normalized['description'] = getattr(agent_data, 'description', 'n8n workflow automation')
        
        # Extract workflow data if available
        if hasattr(agent_data, 'workflow'):
            workflow_data = agent_data.workflow
            if hasattr(workflow_data, 'nodes'):
                normalized['metadata']['nodeCount'] = len(workflow_data.nodes)
                
    # Ensure capabilities are unique
    normalized['capabilities'] = list(set(normalized['capabilities']))
    
    # Set defaults for any missing required fields
    if 'name' not in normalized:
        normalized['name'] = 'Unnamed n8n Agent'
    if 'description' not in normalized:
        normalized['description'] = 'n8n workflow automation with AI agents'
    if 'owner' not in normalized:
        normalized['owner'] = 'Unknown'
    if 'version' not in normalized:
        normalized['version'] = '1.0'
    
    # Calculate trust score with n8n-specific bonuses
    trust_score = calculate_trust_score(normalized)
    
    # n8n-specific trust score bonuses
    if normalized['capabilities']:
        trust_score += min(5, len(normalized['capabilities']))
    if 'memory:enabled' in normalized['capabilities']:
        trust_score += 5
    if normalized['metadata'].get('agentNodeCount', 0) > 1:
        trust_score += 5  # Bonus for multi-agent workflows
    if 'output_parsing:enabled' in normalized['capabilities']:
        trust_score += 3  # Bonus for structured outputs
        
    normalized['trustScore'] = min(trust_score, 100)  # Production scoring
    
    return normalized


def register_n8n(agent: Any, email: str, owner: Optional[str] = None) -> Dict[str, Any]:
    """
    Register an n8n agent/workflow with AstraSync.
    
    Args:
        agent: n8n agent node or workflow configuration
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
        logger.error(f"Failed to register n8n agent: {e}")
        raise


def create_registration_decorator(email: str, owner: Optional[str] = None):
    """
    Create a decorator for automatic n8n workflow registration.
    
    Usage:
        @register_with_astrasync(email="dev@example.com")
        class MyN8nWorkflow:
            ...
    """
    def decorator(cls):
        original_init = cls.__init__
        
        def new_init(self, *args, **kwargs):
            original_init(self, *args, **kwargs)
            try:
                result = register_n8n(self, email=email, owner=owner)
                self.astrasync_id = result.get('agentId')
                self.astrasync_trust_score = result.get('trustScore')
                logger.info(f"Auto-registered n8n workflow: {self.astrasync_id}")
            except Exception as e:
                logger.warning(f"Failed to auto-register workflow: {e}")
                self.astrasync_id = None
                self.astrasync_trust_score = None
                
        cls.__init__ = new_init
        return cls
        
    return decorator


# Convenience function alias
register_with_astrasync = create_registration_decorator