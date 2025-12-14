"""
Membership Manager.

Handles agent membership in communities with rules enforcement.
"""

import logging
from datetime import datetime
from typing import Any

from .model import Community
from .registry import CommunityRegistry, get_registry

logger = logging.getLogger(__name__)


class MembershipManager:
    """
    Manages agent membership in communities.

    Enforces rules:
    - Every agent must belong to at least one community
    - Agents can belong to multiple communities
    - Membership changes are tracked
    """

    def __init__(self, registry: CommunityRegistry | None = None):
        """
        Initialize the membership manager.

        Args:
            registry: Community registry to use (defaults to singleton)
        """
        self._registry = registry or get_registry()
        self._membership_history: list[dict] = []
        self._max_history = 10000

    def join(
        self,
        agent_id: str,
        community_id: str,
        reason: str = "",
    ) -> bool:
        """
        Add an agent to a community.

        Args:
            agent_id: Agent ID
            community_id: Community to join
            reason: Reason for joining

        Returns:
            True if successfully joined
        """
        if self._registry.add_member(community_id, agent_id):
            self._record_change(
                agent_id=agent_id,
                community_id=community_id,
                action="join",
                reason=reason,
            )
            return True
        return False

    def leave(
        self,
        agent_id: str,
        community_id: str,
        reason: str = "",
    ) -> bool:
        """
        Remove an agent from a community.

        Args:
            agent_id: Agent ID
            community_id: Community to leave
            reason: Reason for leaving

        Returns:
            True if successfully left

        Raises:
            ValueError: If this would leave the agent with no community
        """
        # Check if agent would have no communities
        communities = self._registry.get_for_agent(agent_id)
        if len(communities) <= 1:
            community = self._registry.get(community_id)
            if community and community.has_member(agent_id):
                raise ValueError(
                    f"Agent {agent_id} cannot leave {community_id}: "
                    "agents must belong to at least one community"
                )

        if self._registry.remove_member(community_id, agent_id):
            self._record_change(
                agent_id=agent_id,
                community_id=community_id,
                action="leave",
                reason=reason,
            )
            return True
        return False

    def transfer(
        self,
        agent_id: str,
        from_community_id: str,
        to_community_id: str,
        reason: str = "",
    ) -> bool:
        """
        Transfer an agent between communities atomically.

        Ensures agent always has at least one community.

        Args:
            agent_id: Agent ID
            from_community_id: Community to leave
            to_community_id: Community to join
            reason: Reason for transfer

        Returns:
            True if successfully transferred
        """
        # First join the new community
        if not self._registry.add_member(to_community_id, agent_id):
            return False

        # Then leave the old one
        self._registry.remove_member(from_community_id, agent_id)

        self._record_change(
            agent_id=agent_id,
            community_id=from_community_id,
            action="transfer_from",
            reason=reason,
            metadata={"to": to_community_id},
        )
        self._record_change(
            agent_id=agent_id,
            community_id=to_community_id,
            action="transfer_to",
            reason=reason,
            metadata={"from": from_community_id},
        )

        return True

    def get_communities(self, agent_id: str) -> list[Community]:
        """Get all communities an agent belongs to."""
        return self._registry.get_for_agent(agent_id)

    def get_primary_community(self, agent_id: str) -> Community | None:
        """
        Get the agent's primary community.

        The primary community is the first one joined (oldest membership).
        """
        communities = self._registry.get_for_agent(agent_id)
        if not communities:
            return None

        # Find oldest membership from history
        agent_history = [
            h for h in self._membership_history
            if h["agent_id"] == agent_id and h["action"] == "join"
        ]

        if agent_history:
            oldest_community_id = agent_history[0]["community_id"]
            for c in communities:
                if c.id == oldest_community_id:
                    return c

        # Fallback to first in list
        return communities[0] if communities else None

    def is_member(self, agent_id: str, community_id: str) -> bool:
        """Check if an agent is a member of a community."""
        community = self._registry.get(community_id)
        return community.has_member(agent_id) if community else False

    def get_peers(self, agent_id: str) -> set[str]:
        """Get all agents that share at least one community with this agent."""
        peers = set()
        for community in self._registry.get_for_agent(agent_id):
            peers.update(community.member_agent_ids)
        peers.discard(agent_id)  # Remove self
        return peers

    def get_history(
        self,
        agent_id: str | None = None,
        community_id: str | None = None,
        limit: int = 100,
    ) -> list[dict]:
        """Get membership change history."""
        history = self._membership_history

        if agent_id:
            history = [h for h in history if h["agent_id"] == agent_id]
        if community_id:
            history = [h for h in history if h["community_id"] == community_id]

        return history[-limit:]

    def _record_change(
        self,
        agent_id: str,
        community_id: str,
        action: str,
        reason: str = "",
        metadata: dict[str, Any] | None = None,
    ) -> None:
        """Record a membership change."""
        self._membership_history.append({
            "timestamp": datetime.utcnow().isoformat(),
            "agent_id": agent_id,
            "community_id": community_id,
            "action": action,
            "reason": reason,
            "metadata": metadata or {},
        })

        # Prune if over limit
        if len(self._membership_history) > self._max_history:
            self._membership_history = self._membership_history[-self._max_history // 2:]

    def ensure_membership(self, agent_id: str, default_community_id: str) -> bool:
        """
        Ensure an agent belongs to at least one community.

        If the agent has no communities, adds them to the default.

        Args:
            agent_id: Agent ID
            default_community_id: Fallback community

        Returns:
            True if agent now has at least one community
        """
        communities = self._registry.get_for_agent(agent_id)
        if communities:
            return True

        return self.join(
            agent_id=agent_id,
            community_id=default_community_id,
            reason="automatic_default_membership",
        )

    def get_stats(self) -> dict:
        """Get membership statistics."""
        return {
            "total_history_entries": len(self._membership_history),
            "joins": len([h for h in self._membership_history if h["action"] == "join"]),
            "leaves": len([h for h in self._membership_history if h["action"] == "leave"]),
            "transfers": len([h for h in self._membership_history if "transfer" in h["action"]]),
        }
