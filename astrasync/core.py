"""
AstraSync SDK - Core functionality
"""
from astrasync.utils.api import register_agent, verify_agent
from astrasync.utils.detector import detect_agent_type, normalize_agent_data
from astrasync.utils.validator import validate_email
import json


class AstraSync:
    """Main client for interacting with AstraSync API"""

    def __init__(self, email=None, api_key=None, password=None):
        """Initialize AstraSync client

        Args:
            email: Developer email for registration
            api_key: API key for authentication (recommended)
            password: Account password for authentication (alternative to api_key)
        """
        self.email = email
        self.api_key = api_key
        self.password = password

        if not api_key and not password:
            raise ValueError("Authentication required: provide either api_key or password")
    
    def register(self, agent_data, owner=None):
        """Register an agent with AstraSync
        
        Args:
            agent_data: Agent configuration (dict or object)
            owner: Optional owner override
            
        Returns:
            Registration response from API
        """
        if not self.email:
            raise ValueError("Email is required for registration. Initialize with AstraSync(email='your@email.com')")
        
        if not validate_email(self.email):
            raise ValueError(f"Invalid email format: {self.email}")
        
        # Normalize the agent data
        normalized = normalize_agent_data(agent_data)
        
        # Apply owner override if provided
        if owner:
            normalized['owner'] = owner
        
        # CRITICAL FIX: Ensure owner is never empty
        if not normalized.get('owner') or normalized.get('owner') == '':
            # Use the original agent_data owner if available
            if isinstance(agent_data, dict) and agent_data.get('owner'):
                normalized['owner'] = agent_data['owner']
            else:
                # Default to email domain or 'Unknown'
                normalized['owner'] = self.email.split('@')[0] if '@' in self.email else 'Unknown'
        
        # Make API call with authentication
        response = register_agent(normalized, self.email, self.password, self.api_key)

        # Return the complete API response
        return response
    
    def verify(self, agent_id):
        """Verify an agent registration
        
        Args:
            agent_id: The agent ID to verify
            
        Returns:
            Verification response from API
        """
        return verify_agent(agent_id)
