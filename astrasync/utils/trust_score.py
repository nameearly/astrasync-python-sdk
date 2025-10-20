from typing import Dict, Any

def calculate_trust_score(agent_data: Dict[str, Any]) -> int:
    """Calculate trust score based on agent metadata completeness"""
    score = 70  # Base score
    
    # Name quality
    if agent_data.get('name') and agent_data['name'] != 'Unnamed Agent':
        score += 5
    
    # Description quality
    desc = agent_data.get('description', '')
    if len(desc) > 50:
        score += 5
    if len(desc) > 100:
        score += 5
    
    # Capabilities
    capabilities = agent_data.get('capabilities', [])
    if len(capabilities) > 0:
        score += 5
    if len(capabilities) > 3:
        score += 5
    
    # Version info
    if agent_data.get('version'):
        score += 5
    
    # Google ADK specific bonuses
    if agent_data.get('framework') == 'google-adk' or agent_data.get('agentType') == 'google-adk':
        # Structured output capability adds trust
        if agent_data.get('structured_output'):
            score += 5  # Deterministic outputs are more trustworthy
        
        # Multi-agent orchestration indicates sophistication
        if agent_data.get('orchestration_capable'):
            score += 3
        
        # Session management indicates stateful compliance tracking
        if 'session_service' in str(agent_data):
            score += 2
    
    return min(score, 100)  # Production scoring
