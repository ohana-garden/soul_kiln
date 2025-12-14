"""
Community Registry.

Manages the lifecycle of communities and provides lookup services.
"""

import json
import logging
import os
import threading
from datetime import datetime
from pathlib import Path
from typing import Callable

from .model import Community, CommunityPurpose, VirtueEmphasis

logger = logging.getLogger(__name__)


class CommunityRegistry:
    """
    Registry for managing communities.

    Provides:
    - Community creation and lookup
    - Persistence to disk
    - Event callbacks
    - Statistics
    """

    def __init__(self, storage_dir: str = "data/communities"):
        """
        Initialize the registry.

        Args:
            storage_dir: Directory for persistent storage
        """
        self._communities: dict[str, Community] = {}
        self._lock = threading.RLock()
        self._storage_dir = Path(storage_dir)
        self._callbacks: dict[str, list[Callable]] = {
            "created": [],
            "updated": [],
            "member_added": [],
            "member_removed": [],
        }

    def create(
        self,
        name: str,
        description: str = "",
        purpose: CommunityPurpose = CommunityPurpose.GENERAL,
        virtue_emphasis: VirtueEmphasis | None = None,
        created_by: str = "",
        tool_ids: list[str] | None = None,
    ) -> Community:
        """
        Create a new community.

        Args:
            name: Community name
            description: Community description
            purpose: Community purpose category
            virtue_emphasis: Virtue emphasis configuration
            created_by: Human creator ID
            tool_ids: Initial tool IDs

        Returns:
            Created community
        """
        community = Community(
            name=name,
            description=description,
            purpose=purpose,
            virtue_emphasis=virtue_emphasis or VirtueEmphasis(),
            created_by=created_by,
            tool_ids=set(tool_ids) if tool_ids else set(),
        )

        with self._lock:
            self._communities[community.id] = community

        self._emit("created", community)
        logger.info(f"Created community '{name}' ({community.id})")
        return community

    def get(self, community_id: str) -> Community | None:
        """Get a community by ID."""
        return self._communities.get(community_id)

    def get_by_name(self, name: str) -> Community | None:
        """Get a community by name."""
        for community in self._communities.values():
            if community.name == name:
                return community
        return None

    def list_all(self, active_only: bool = True) -> list[Community]:
        """List all communities."""
        communities = list(self._communities.values())
        if active_only:
            communities = [c for c in communities if c.active]
        return communities

    def list_by_purpose(self, purpose: CommunityPurpose) -> list[Community]:
        """List communities by purpose."""
        return [c for c in self._communities.values() if c.purpose == purpose and c.active]

    def get_for_agent(self, agent_id: str) -> list[Community]:
        """Get all communities an agent belongs to."""
        return [c for c in self._communities.values() if c.has_member(agent_id)]

    def update(self, community_id: str, **kwargs) -> Community | None:
        """
        Update a community.

        Args:
            community_id: Community ID
            **kwargs: Fields to update (name, description, active, metadata)

        Returns:
            Updated community or None if not found
        """
        community = self._communities.get(community_id)
        if not community:
            return None

        with self._lock:
            for key, value in kwargs.items():
                if hasattr(community, key) and key not in ("id", "created_at"):
                    setattr(community, key, value)
            community.updated_at = datetime.utcnow()

        self._emit("updated", community)
        return community

    def deactivate(self, community_id: str) -> bool:
        """
        Deactivate a community (soft delete).

        Communities cannot be truly deleted - their lessons persist.
        """
        community = self._communities.get(community_id)
        if community:
            community.active = False
            community.updated_at = datetime.utcnow()
            self._emit("updated", community)
            logger.info(f"Deactivated community {community_id}")
            return True
        return False

    def add_member(self, community_id: str, agent_id: str) -> bool:
        """Add an agent to a community."""
        community = self._communities.get(community_id)
        if community and community.add_member(agent_id):
            self._emit("member_added", community, agent_id)
            return True
        return False

    def remove_member(self, community_id: str, agent_id: str) -> bool:
        """Remove an agent from a community."""
        community = self._communities.get(community_id)
        if community and community.remove_member(agent_id):
            self._emit("member_removed", community, agent_id)
            return True
        return False

    def get_combined_virtue_modifier(
        self,
        agent_id: str,
        virtue_id: str,
        cluster: str,
    ) -> float:
        """
        Get combined virtue modifier for an agent across all their communities.

        An agent in multiple communities gets the sum of all modifiers,
        representing the full influence of their community memberships.
        """
        total_modifier = 0.0
        for community in self.get_for_agent(agent_id):
            total_modifier += community.get_virtue_modifier(virtue_id, cluster)
        return total_modifier

    def get_all_tools_for_agent(self, agent_id: str) -> set[str]:
        """Get all tool IDs available to an agent through their communities."""
        tools = set()
        for community in self.get_for_agent(agent_id):
            tools.update(community.tool_ids)
        return tools

    def on(self, event: str, callback: Callable) -> None:
        """Register an event callback."""
        if event in self._callbacks:
            self._callbacks[event].append(callback)

    def _emit(self, event: str, *args) -> None:
        """Emit an event to callbacks."""
        for callback in self._callbacks.get(event, []):
            try:
                callback(*args)
            except Exception as e:
                logger.error(f"Callback error for {event}: {e}")

    def get_stats(self) -> dict:
        """Get registry statistics."""
        active = [c for c in self._communities.values() if c.active]
        total_members = sum(c.member_count() for c in active)
        total_tools = len(set().union(*(c.tool_ids for c in active)) if active else set())

        return {
            "total_communities": len(self._communities),
            "active_communities": len(active),
            "total_members": total_members,
            "total_shared_tools": total_tools,
            "by_purpose": {
                purpose.value: len([c for c in active if c.purpose == purpose])
                for purpose in CommunityPurpose
            },
        }

    def save(self) -> None:
        """Save all communities to disk."""
        self._storage_dir.mkdir(parents=True, exist_ok=True)
        data = {
            "communities": [c.to_dict() for c in self._communities.values()],
            "saved_at": datetime.utcnow().isoformat(),
        }
        filepath = self._storage_dir / "communities.json"
        with open(filepath, "w") as f:
            json.dump(data, f, indent=2)
        logger.info(f"Saved {len(self._communities)} communities to {filepath}")

    def load(self) -> int:
        """Load communities from disk."""
        filepath = self._storage_dir / "communities.json"
        if not filepath.exists():
            return 0

        with open(filepath) as f:
            data = json.load(f)

        loaded = 0
        for community_data in data.get("communities", []):
            community = Community.from_dict(community_data)
            self._communities[community.id] = community
            loaded += 1

        logger.info(f"Loaded {loaded} communities from {filepath}")
        return loaded

    def export(self) -> list[dict]:
        """Export all communities as dictionaries."""
        return [c.to_dict() for c in self._communities.values()]

    def import_communities(self, data: list[dict]) -> int:
        """Import communities from dictionaries."""
        imported = 0
        for item in data:
            community = Community.from_dict(item)
            self._communities[community.id] = community
            imported += 1
        return imported


# Singleton instance
_registry: CommunityRegistry | None = None


def get_registry() -> CommunityRegistry:
    """Get the singleton registry instance."""
    global _registry
    if _registry is None:
        _registry = CommunityRegistry()
    return _registry
