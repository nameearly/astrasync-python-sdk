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
            # FIXME(逻辑): CLI 与 decorators 目前只传了 email（未传 api_key/password），这里会导致
            # `astrasync register ...` 与 `@register(auto_register=True)` 直接崩溃。
            # 建议：
            # 1) CLI/装饰器增加传入 api_key/password 的机制；或
            # 2) 将鉴权要求延后到具体 API 调用处，并提供更明确的错误提示。
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
        # NOTE(逻辑): CLI 当前传入的是 agent_file 路径字符串（不是 dict/object 配置），会在
        # normalize_agent_data() 中被当成 unknown，进而生成 Unnamed/Unknown 的默认值。
        # 建议：CLI 先读取并解析文件内容（JSON/YAML 等），再传入 dict。
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
        # FIXME(逻辑): utils.api.register_agent() 当前 payload 的 owner 固定使用 email，
        # 这里对 normalized['owner'] 的修复/override 实际不会影响发往服务端的 owner。
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
