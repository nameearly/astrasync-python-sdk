"""
AstraSync API client utilities
"""
import requests
import json
from typing import Dict, Any


API_BASE_URL = "https://astrasync.ai/api/v1"


def register_agent(agent_data: Dict[str, Any], email: str) -> Dict[str, Any]:
    """Register an agent with AstraSync API
    
    Args:
        agent_data: Normalized agent data
        email: Developer email
        
    Returns:
        API response dict
    """
    endpoint = f"{API_BASE_URL}/register"
    
    payload = {
        "email": email,
        "agent": agent_data
    }
    
    headers = {
        "Content-Type": "application/json",
        "User-Agent": "AstraSync-Python-SDK/1.0.0"
    }
    
    try:
        response = requests.post(endpoint, json=payload, headers=headers)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        raise Exception(f"Failed to register agent: {str(e)}")


def verify_agent(agent_id: str) -> Dict[str, Any]:
    """Verify an agent registration
    
    Args:
        agent_id: The agent ID to verify
        
    Returns:
        API response dict
    """
    endpoint = f"{API_BASE_URL}/verify/{agent_id}"
    
    headers = {
        "User-Agent": "AstraSync-Python-SDK/1.0.0"
    }
    
    try:
        response = requests.get(endpoint, headers=headers)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        raise Exception(f"Failed to verify agent: {str(e)}")
