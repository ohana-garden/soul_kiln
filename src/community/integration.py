"""
Community Integration Module for Soul Kiln.

"I am, because we are" - Ubuntu philosophy.

Connects the community framework with existing soul_kiln systems:
- Virtue system integration for community-based threshold modifiers
- Knowledge pool integration for shared learning
- Agent membership management
- Tool invocation tracking
"""

import logging
from datetime import datetime
from typing import Any, Callable

from .model import Community, CommunityPurpose, VirtueEmphasis
from .registry import CommunityRegistry, get_registry
from .membership import MembershipManager
from .tools import ToolRegistry, ToolResult, get_tool_registry
from .definitions import create_grant_getter_community

logger = logging.getLogger(__name__)


class CommunityIntegration:
    """
    Integrates community framework with soul_kiln.

    Provides a unified interface for:
    - Community management
    - Agent membership
    - Tool invocation with tracking
    - Virtue modifier calculation
    - Knowledge sharing across communities
    """

    def __init__(
        self,
        community_storage_dir: str = "data/communities",
        auto_create_default: bool = True,
    ):
        """
        Initialize community integration.

        Args:
            community_storage_dir: Directory for community storage
            auto_create_default: Whether to create Grant-Getter by default
        """
        self._registry = CommunityRegistry(storage_dir=community_storage_dir)
        self._membership = MembershipManager(registry=self._registry)
        self._tool_registry = get_tool_registry()
        self._initialized = False
        self._auto_create_default = auto_create_default

        # Callbacks for integration events
        self._lesson_callbacks: list[Callable[[str, str, dict], None]] = []

    def initialize(self) -> None:
        """Initialize all community systems."""
        if self._initialized:
            return

        # Load persisted communities
        self._registry.load()

        # Create default communities if enabled
        if self._auto_create_default:
            self._create_default_communities()

        self._initialized = True
        logger.info("Community integration initialized")

    def shutdown(self) -> None:
        """Shutdown and persist state."""
        self._registry.save()
        self._initialized = False
        logger.info("Community integration shutdown")

    def _create_default_communities(self) -> None:
        """Create default communities."""
        # Create Grant-Getter as the first community
        create_grant_getter_community(
            registry=self._registry,
            created_by="system",
            register_tools=True,
        )
        logger.info("Created default Grant-Getter community")

    # Community Management

    def create_community(
        self,
        name: str,
        description: str = "",
        purpose: CommunityPurpose = CommunityPurpose.GENERAL,
        virtue_emphasis: VirtueEmphasis | None = None,
        created_by: str = "",
        tool_ids: list[str] | None = None,
    ) -> Community:
        """Create a new community."""
        return self._registry.create(
            name=name,
            description=description,
            purpose=purpose,
            virtue_emphasis=virtue_emphasis,
            created_by=created_by,
            tool_ids=tool_ids,
        )

    def get_community(self, community_id: str) -> Community | None:
        """Get a community by ID."""
        return self._registry.get(community_id)

    def get_community_by_name(self, name: str) -> Community | None:
        """Get a community by name."""
        return self._registry.get_by_name(name)

    def list_communities(self, active_only: bool = True) -> list[Community]:
        """List all communities."""
        return self._registry.list_all(active_only=active_only)

    # Agent Membership

    def join_community(
        self,
        agent_id: str,
        community_id: str,
        reason: str = "",
    ) -> bool:
        """Add an agent to a community."""
        return self._membership.join(agent_id, community_id, reason)

    def leave_community(
        self,
        agent_id: str,
        community_id: str,
        reason: str = "",
    ) -> bool:
        """Remove an agent from a community."""
        return self._membership.leave(agent_id, community_id, reason)

    def get_agent_communities(self, agent_id: str) -> list[Community]:
        """Get all communities an agent belongs to."""
        return self._membership.get_communities(agent_id)

    def ensure_agent_membership(
        self,
        agent_id: str,
        default_community_name: str = "Grant-Getter",
    ) -> bool:
        """Ensure an agent belongs to at least one community."""
        community = self._registry.get_by_name(default_community_name)
        if community:
            return self._membership.ensure_membership(agent_id, community.id)
        return False

    # Virtue Integration

    def get_virtue_modifier(
        self,
        agent_id: str,
        virtue_id: str,
        cluster: str,
    ) -> float:
        """
        Get combined virtue modifier for an agent from all their communities.

        This modifier is added to the base virtue threshold to create
        community-influenced expectations.

        Args:
            agent_id: Agent ID
            virtue_id: Virtue ID (e.g., "V19")
            cluster: Virtue cluster (e.g., "transcendent")

        Returns:
            Combined modifier from all agent's communities
        """
        return self._registry.get_combined_virtue_modifier(
            agent_id=agent_id,
            virtue_id=virtue_id,
            cluster=cluster,
        )

    # Tool Invocation

    def invoke_tool(
        self,
        tool_id: str,
        agent_id: str,
        community_id: str | None = None,
        **kwargs,
    ) -> ToolResult:
        """
        Invoke a tool on behalf of an agent.

        Tracks invocation and updates community statistics.

        Args:
            tool_id: Tool ID to invoke
            agent_id: Invoking agent
            community_id: Community context (uses primary if not specified)
            **kwargs: Tool arguments

        Returns:
            ToolResult from the tool
        """
        # Determine community context
        if not community_id:
            primary = self._membership.get_primary_community(agent_id)
            community_id = primary.id if primary else None

        # Check if agent has access to tool through communities
        available_tools = self._registry.get_all_tools_for_agent(agent_id)
        if tool_id not in available_tools:
            return ToolResult(
                success=False,
                error=f"Agent {agent_id} does not have access to tool {tool_id}",
            )

        # Invoke the tool
        result = self._tool_registry.invoke(
            tool_id=tool_id,
            agent_id=agent_id,
            community_id=community_id,
            **kwargs,
        )

        # Update community statistics
        if community_id:
            community = self._registry.get(community_id)
            if community:
                community.record_tool_invocation()

        return result

    def get_available_tools(self, agent_id: str) -> list[str]:
        """Get all tools available to an agent through their communities."""
        return list(self._registry.get_all_tools_for_agent(agent_id))

    # Knowledge Sharing

    def share_lesson(
        self,
        agent_id: str,
        lesson_type: str,
        content: dict,
        community_id: str | None = None,
    ) -> None:
        """
        Share a lesson with the community.

        Lessons are shared across all communities - knowledge flows freely.

        Args:
            agent_id: Agent sharing the lesson
            lesson_type: Type of lesson (success, failure, warning)
            content: Lesson content
            community_id: Origin community
        """
        # Update community statistics
        for community in self._membership.get_communities(agent_id):
            community.record_lesson_shared()

        # Notify callbacks
        for callback in self._lesson_callbacks:
            try:
                callback(agent_id, lesson_type, content)
            except Exception as e:
                logger.error(f"Lesson callback error: {e}")

    def on_lesson_shared(
        self,
        callback: Callable[[str, str, dict], None],
    ) -> None:
        """Register a callback for when lessons are shared."""
        self._lesson_callbacks.append(callback)

    # Statistics

    def get_status(self) -> dict:
        """Get integration status."""
        return {
            "initialized": self._initialized,
            "registry": self._registry.get_stats(),
            "membership": self._membership.get_stats(),
            "tools": self._tool_registry.get_stats(),
        }


# Singleton instance
_integration: CommunityIntegration | None = None


def get_community_integration() -> CommunityIntegration:
    """Get the singleton community integration instance."""
    global _integration
    if _integration is None:
        _integration = CommunityIntegration()
    return _integration


def initialize_communities() -> CommunityIntegration:
    """Initialize and return the community integration."""
    integration = get_community_integration()
    integration.initialize()
    return integration
