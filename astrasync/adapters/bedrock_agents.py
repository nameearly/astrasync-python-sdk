"""
Amazon Bedrock Agents adapter for AstraSync agent registration.
Supports AWS Bedrock managed AI agents with action groups and knowledge bases.
"""

import logging
from typing import Dict, Any, List, Optional, Union
from ..utils.trust_score import calculate_trust_score
from ..core import AstraSync

logger = logging.getLogger(__name__)


def normalize_agent_data(agent_data: Any) -> Dict[str, Any]:
    """
    Normalize Bedrock Agents data to AstraSync standard format.
    
    Supports:
    - Amazon Bedrock managed agents
    - Action groups for API integrations
    - Knowledge bases for RAG capabilities
    - Guardrails for content filtering
    """
    # Start with empty normalized structure
    normalized = {
        'agentType': 'bedrock_agents',
        'version': '1.0',
        'capabilities': [],
        'metadata': {}
    }
    
    # Handle Bedrock agent objects (not plain dicts)
    if hasattr(agent_data, '__class__') and not isinstance(agent_data, dict):
        class_name = agent_data.__class__.__name__
        module_name = getattr(agent_data.__class__, '__module__', '')
        
        if 'bedrock' in module_name.lower() or 'boto3' in module_name.lower() or 'aws' in module_name.lower():
            normalized['name'] = getattr(agent_data, 'agent_name', getattr(agent_data, 'name', f'{class_name} Instance'))
            normalized['metadata']['agentClass'] = class_name
            
            # Check for BedrockAgent
            if 'BedrockAgent' in class_name or 'Agent' in class_name:
                normalized['description'] = getattr(agent_data, 'description', 'Amazon Bedrock managed AI agent')
                normalized['capabilities'].append('managed:enabled')
                
                # Extract agent configuration
                if hasattr(agent_data, 'agent_id'):
                    normalized['metadata']['agentId'] = agent_data.agent_id
                if hasattr(agent_data, 'agent_arn'):
                    normalized['metadata']['agentArn'] = agent_data.agent_arn
                if hasattr(agent_data, 'agent_version'):
                    normalized['metadata']['agentVersion'] = agent_data.agent_version
                    
                # Extract instruction
                if hasattr(agent_data, 'instruction'):
                    instruction = agent_data.instruction
                    normalized['metadata']['instruction'] = instruction
                    normalized['description'] = instruction[:200] + '...' if len(instruction) > 200 else instruction
                    
                # Extract foundation model
                if hasattr(agent_data, 'foundation_model'):
                    normalized['metadata']['foundationModel'] = agent_data.foundation_model
                    normalized['capabilities'].append(f'model:{agent_data.foundation_model}')
                    
                # Check for action groups
                if hasattr(agent_data, 'action_groups'):
                    action_groups = agent_data.action_groups
                    if action_groups:
                        _extract_action_groups(action_groups, normalized)
                        
                # Check for knowledge bases
                if hasattr(agent_data, 'knowledge_bases'):
                    kb_list = agent_data.knowledge_bases
                    if kb_list:
                        _extract_knowledge_bases(kb_list, normalized)
                        
                # Check for guardrails
                if hasattr(agent_data, 'guardrails'):
                    if agent_data.guardrails:
                        normalized['capabilities'].append('guardrails:enabled')
                        
    # Handle dictionary-based definitions
    elif isinstance(agent_data, dict):
        # Direct field mappings
        for field in ['name', 'description', 'owner', 'version']:
            if field in agent_data:
                normalized[field] = agent_data[field]
                
        # Agent name variations
        if 'agent_name' in agent_data:
            normalized['name'] = agent_data['agent_name']
            
        # Bedrock-specific fields
        if 'instruction' in agent_data:
            instruction = agent_data['instruction']
            normalized['metadata']['instruction'] = instruction
            if 'description' not in normalized or not normalized['description']:
                normalized['description'] = instruction[:200] + '...' if len(instruction) > 200 else instruction
                
        if 'foundation_model' in agent_data:
            normalized['metadata']['foundationModel'] = agent_data['foundation_model']
            normalized['capabilities'].append(f"model:{agent_data['foundation_model']}")
            
        # Agent resource configuration
        if 'agent_resource_role_arn' in agent_data:
            normalized['metadata']['agentResourceRoleArn'] = agent_data['agent_resource_role_arn']
            normalized['capabilities'].append('iam:configured')
            
        # Action groups configuration
        if 'action_groups' in agent_data:
            _extract_action_groups(agent_data['action_groups'], normalized)
            
        # Knowledge bases configuration
        if 'knowledge_bases' in agent_data:
            _extract_knowledge_bases(agent_data['knowledge_bases'], normalized)
            
        # Guardrails configuration
        if 'guardrails' in agent_data:
            guardrails = agent_data['guardrails']
            if guardrails:
                normalized['capabilities'].append('guardrails:enabled')
                if isinstance(guardrails, dict):
                    if 'guardrail_id' in guardrails:
                        normalized['metadata']['guardrailId'] = guardrails['guardrail_id']
                    if 'version' in guardrails:
                        normalized['metadata']['guardrailVersion'] = guardrails['version']
                        
        # Prompt override configuration
        if 'prompt_override_configuration' in agent_data:
            normalized['capabilities'].append('prompt_override:enabled')
            normalized['metadata']['promptOverride'] = True
            
        # Session configuration
        if 'idle_session_ttl' in agent_data:
            normalized['metadata']['idleSessionTtl'] = agent_data['idle_session_ttl']
            
        # Customer encryption key
        if 'customer_encryption_key_arn' in agent_data:
            normalized['metadata']['customerEncryptionKeyArn'] = agent_data['customer_encryption_key_arn']
            normalized['capabilities'].append('encryption:custom')
            
        # Tags
        if 'tags' in agent_data:
            tags = agent_data['tags']
            if isinstance(tags, dict):
                normalized['metadata']['tags'] = tags
                
    # Ensure capabilities are unique
    normalized['capabilities'] = list(set(normalized['capabilities']))
    
    # Set defaults for missing required fields
    if 'name' not in normalized:
        normalized['name'] = 'Unnamed Bedrock Agent'
    if 'description' not in normalized:
        normalized['description'] = 'AWS Bedrock managed AI agent'
    if 'owner' not in normalized:
        normalized['owner'] = 'Unknown'
    if 'version' not in normalized:
        normalized['version'] = '1.0'
    
    # Calculate trust score with Bedrock-specific bonuses
    trust_score = calculate_trust_score(normalized)
    
    # Bedrock-specific trust score bonuses
    if normalized['capabilities']:
        trust_score += min(5, len(normalized['capabilities']))
    if 'action_groups:enabled' in normalized['capabilities']:
        trust_score += 5  # Bonus for API integrations
    if 'knowledge_bases:enabled' in normalized['capabilities']:
        trust_score += 5  # Bonus for RAG
    if 'guardrails:enabled' in normalized['capabilities']:
        trust_score += 5  # Bonus for content filtering
    if normalized['metadata'].get('actionGroupCount', 0) > 2:
        trust_score += 3
    if normalized['metadata'].get('knowledgeBaseCount', 0) > 0:
        trust_score += 3
    if 'iam:configured' in normalized['capabilities']:
        trust_score += 2  # Bonus for proper IAM setup
        
    normalized['trustScore'] = min(trust_score, 100)  # Production scoring
    
    return normalized


def _extract_action_groups(action_groups: Any, normalized: Dict[str, Any]) -> None:
    """Extract action group information from Bedrock configuration."""
    if isinstance(action_groups, list):
        action_group_names = []
        for ag in action_groups:
            if isinstance(ag, str):
                action_group_names.append(ag)
                normalized['capabilities'].append(f'action_group:{ag}')
            elif isinstance(ag, dict):
                ag_name = ag.get('action_group_name', ag.get('name', 'unknown'))
                action_group_names.append(ag_name)
                normalized['capabilities'].append(f'action_group:{ag_name}')
                
                # Check for API schema
                if 'api_schema' in ag or 'openapi_schema' in ag:
                    normalized['capabilities'].append('api_schema:defined')
                    
                # Check for Lambda function
                if 'action_group_executor' in ag:
                    executor = ag['action_group_executor']
                    if isinstance(executor, dict) and 'lambda' in executor:
                        normalized['capabilities'].append('lambda:enabled')
                        
        if action_group_names:
            normalized['metadata']['actionGroups'] = action_group_names
            normalized['metadata']['actionGroupCount'] = len(action_group_names)
            normalized['capabilities'].append('action_groups:enabled')


def _extract_knowledge_bases(knowledge_bases: Any, normalized: Dict[str, Any]) -> None:
    """Extract knowledge base information from Bedrock configuration."""
    if isinstance(knowledge_bases, list):
        kb_names = []
        for kb in knowledge_bases:
            if isinstance(kb, str):
                kb_names.append(kb)
                normalized['capabilities'].append(f'knowledge_base:{kb}')
            elif isinstance(kb, dict):
                kb_id = kb.get('knowledge_base_id', kb.get('id', 'unknown'))
                kb_names.append(kb_id)
                normalized['capabilities'].append(f'knowledge_base:{kb_id}')
                
                # Check for description
                if 'description' in kb:
                    if 'knowledgeBaseDescriptions' not in normalized['metadata']:
                        normalized['metadata']['knowledgeBaseDescriptions'] = {}
                    normalized['metadata']['knowledgeBaseDescriptions'][kb_id] = kb['description']
                    
        if kb_names:
            normalized['metadata']['knowledgeBases'] = kb_names
            normalized['metadata']['knowledgeBaseCount'] = len(kb_names)
            normalized['capabilities'].append('knowledge_bases:enabled')
            normalized['capabilities'].append('rag:enabled')


def register_bedrock_agents(agent: Any, email: str, owner: Optional[str] = None) -> Dict[str, Any]:
    """
    Register a Bedrock agent with AstraSync.
    
    Args:
        agent: Bedrock agent object or configuration
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
        logger.error(f"Failed to register Bedrock agent: {e}")
        raise


def create_registration_decorator(email: str, owner: Optional[str] = None):
    """
    Create a decorator for automatic Bedrock agent registration.
    
    Usage:
        @register_with_astrasync(email="dev@example.com")
        class MyBedrockAgent:
            ...
    """
    def decorator(cls):
        original_init = cls.__init__
        
        def new_init(self, *args, **kwargs):
            original_init(self, *args, **kwargs)
            try:
                result = register_bedrock_agents(self, email=email, owner=owner)
                self.astrasync_id = result.get('agentId')
                self.astrasync_trust_score = result.get('trustScore')
                logger.info(f"Auto-registered Bedrock agent: {self.astrasync_id}")
            except Exception as e:
                logger.warning(f"Failed to auto-register agent: {e}")
                self.astrasync_id = None
                self.astrasync_trust_score = None
                
        cls.__init__ = new_init
        return cls
        
    return decorator


# Convenience function alias
register_with_astrasync = create_registration_decorator