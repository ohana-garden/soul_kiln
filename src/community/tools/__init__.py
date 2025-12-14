"""
Community Tools Framework.

Provides shared tools that communities can use.
Tools are registered globally and shared across all communities.
"""

from .registry import ToolRegistry, Tool, ToolResult, get_tool_registry
from .grant_discovery import GrantDiscovery, GrantOpportunity
from .proposal_writer import ProposalWriter, ProposalSection
from .compliance_checker import ComplianceChecker, ComplianceResult
from .deadline_tracker import DeadlineTracker, Deadline

__all__ = [
    # Registry
    "ToolRegistry",
    "Tool",
    "ToolResult",
    "get_tool_registry",
    # Grant tools
    "GrantDiscovery",
    "GrantOpportunity",
    "ProposalWriter",
    "ProposalSection",
    "ComplianceChecker",
    "ComplianceResult",
    "DeadlineTracker",
    "Deadline",
]
