"""
AstraSync SDK - AI Agent Registration on Blockchain
"""
from astrasync.core import AstraSync
from astrasync.utils.detector import detect_agent_type, normalize_agent_data

__version__ = "0.2.1"
# NOTE(发布一致性): 这里的 __version__ 与 setup.py 的 version 目前不一致（setup.py=1.0.0）。
# 同时 utils/api.py 的 User-Agent 也写死为 1.0.0。建议统一版本来源，避免 CLI/包版本/UA 不一致。
__all__ = ["AstraSync", "detect_agent_type", "normalize_agent_data"]
