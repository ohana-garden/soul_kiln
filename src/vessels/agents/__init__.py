"""
Agent Management Module.

Provides advanced agent capabilities:
- AgentContext for session state management
- InterventionManager for mid-task redirection
- SubordinateManager for hierarchical delegation
"""

from .context import AgentContext, ContextRegistry
from .intervention import InterventionManager, Intervention, InterventionType
from .subordinate import SubordinateManager, SubordinateCall

__all__ = [
    "AgentContext",
    "ContextRegistry",
    "InterventionManager",
    "Intervention",
    "InterventionType",
    "SubordinateManager",
    "SubordinateCall",
]
