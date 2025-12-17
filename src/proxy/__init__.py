"""
Proxy System.

User representation through proxy agents in conversations.
Proxies speak for users, maintain positions, and can act autonomously.
"""

from .entity import Proxy, ProxyConfig
from .manager import ProxyManager, get_proxy_manager
from .autonomy import ProxyAutonomy, AutonomyMode
from .ambassador import Ambassador, get_ambassador

__all__ = [
    "Proxy",
    "ProxyConfig",
    "ProxyManager",
    "get_proxy_manager",
    "ProxyAutonomy",
    "AutonomyMode",
    "Ambassador",
    "get_ambassador",
]
