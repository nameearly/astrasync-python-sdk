"""
AstraSync API client utilities
"""
import requests
import json
from typing import Dict, Any, Optional


API_BASE_URL = "https://astrasync.ai/api"


def _get_auth_token(email: str, password: Optional[str] = None, api_key: Optional[str] = None) -> str:
    """Get authentication token

    Args:
        email: Developer email
        password: Account password (optional if api_key provided)
        api_key: API key (optional if password provided)

    Returns:
        Authentication token
    """
    if api_key:
        return api_key

    if password:
        endpoint = f"{API_BASE_URL}/auth/login"
        payload = {"email": email, "password": password}
        headers = {
            "Content-Type": "application/json",
            "User-Agent": "AstraSync-Python-SDK/1.0.0"
        }

        try:
            response = requests.post(endpoint, json=payload, headers=headers)
            response.raise_for_status()
            data = response.json()
            return data["data"]["token"]
        except requests.exceptions.RequestException as e:
            # NOTE(可维护性): 这里直接 raise Exception，项目里虽然定义了 AstraSyncError/APIError，
            # 但 API 层没有使用它们，导致上层（例如 CLI 捕获 AstraSyncError）可能捕获不到。
            raise Exception(f"Authentication failed: {str(e)}")

    raise Exception("Authentication required: provide either api_key or password")


def register_agent(agent_data: Dict[str, Any], email: str, password: Optional[str] = None, api_key: Optional[str] = None) -> Dict[str, Any]:
    """Register an agent with AstraSync API

    Args:
        agent_data: Normalized agent data
        email: Developer email
        password: Account password (optional if api_key provided)
        api_key: API key (optional if password provided)

    Returns:
        API response dict
    """
    token = _get_auth_token(email, password, api_key)
    endpoint = f"{API_BASE_URL}/agents"

    payload = {
        "name": agent_data.get("name"),
        "description": agent_data.get("description"),
        # FIXME(逻辑): 这里 owner 固定用 email，会忽略 agent_data 里 normalize/override 后的 owner。
        # 建议："owner": agent_data.get("owner") or email
        "owner": email
    }

    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {token}",
        "User-Agent": "AstraSync-Python-SDK/1.0.0"
    }

    try:
        response = requests.post(endpoint, json=payload, headers=headers)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        # NOTE(可维护性): 同上，这里直接抛 Exception 而不是 SDK 自定义异常（如 APIError）。
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
        # NOTE(可维护性): 同上，建议抛 SDK 自定义异常并附带 status_code/response_body。
        raise Exception(f"Failed to verify agent: {str(e)}")
