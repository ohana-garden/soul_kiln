"""
Community Framework for Soul Kiln.

"I am, because we are" - Ubuntu philosophy.

Communities are the organizing principle for agents. Each community:
- Has a shared purpose and identity
- Emphasizes certain virtues over others
- Shares tools, knowledge, and lessons
- Cannot devolve or become malignant (virtue system prevents this)

Agents always belong to at least one community and are answerable
to their human creators.
"""

from .model import Community, CommunityPurpose, VirtueEmphasis
from .registry import CommunityRegistry, get_registry
from .membership import MembershipManager
from .tools import ToolRegistry, Tool, ToolResult, get_tool_registry
from .integration import (
    CommunityIntegration,
    get_community_integration,
    initialize_communities,
)

__all__ = [
    # Core model
    "Community",
    "CommunityPurpose",
    "VirtueEmphasis",
    # Registry
    "CommunityRegistry",
    "get_registry",
    # Membership
    "MembershipManager",
    # Tools
    "ToolRegistry",
    "Tool",
    "ToolResult",
    "get_tool_registry",
    # Integration
    "CommunityIntegration",
    "get_community_integration",
    "initialize_communities",
]
