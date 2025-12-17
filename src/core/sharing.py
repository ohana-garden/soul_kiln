"""
Community Sharing.

Communities share EVERYTHING:
- Lessons learned from conversations
- Successful pathways through virtue basins
- Patterns and insights
- Tools and capabilities

When one proxy learns, the whole community benefits.
"""

import logging
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any
from enum import Enum

from .graph_store import get_core_store

logger = logging.getLogger(__name__)


class SharedItemType(str, Enum):
    """Types of things that can be shared."""

    LESSON = "lesson"  # Something learned
    PATHWAY = "pathway"  # A successful route to virtue
    PATTERN = "pattern"  # A behavioral pattern
    INSIGHT = "insight"  # A realization
    TOOL_USE = "tool_use"  # How to use a tool effectively


@dataclass
class SharedItem:
    """An item shared with the community."""

    id: str
    item_type: SharedItemType
    content: dict[str, Any]
    shared_by: str  # Proxy ID
    community_id: str
    shared_at: datetime = field(default_factory=datetime.utcnow)

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "item_type": self.item_type.value,
            "content": self.content,
            "shared_by": self.shared_by,
            "community_id": self.community_id,
            "shared_at": self.shared_at.isoformat(),
        }


class CommunitySharing:
    """
    Manages sharing between community members.

    Principles:
    1. Sharing is automatic - proxies don't decide what to share
    2. All learning is collective - no private knowledge
    3. Community benefits compound - more members = faster learning
    """

    def __init__(self, store=None):
        """
        Initialize sharing manager.

        Args:
            store: Graph store (defaults to singleton)
        """
        self.store = store or get_core_store()

    def share_lesson(
        self,
        proxy_id: str,
        lesson_type: str,
        description: str,
        virtue_id: str | None = None,
        context: dict | None = None,
    ) -> list[str]:
        """
        Share a lesson with all communities the proxy belongs to.

        Args:
            proxy_id: Who learned this
            lesson_type: Type of lesson (success, failure, insight)
            description: What was learned
            virtue_id: Related virtue if any
            context: Additional context

        Returns:
            List of community IDs that received the lesson
        """
        proxy = self.store.get_proxy(proxy_id)
        if not proxy:
            logger.warning(f"Proxy {proxy_id} not found for sharing")
            return []

        # Create lesson in graph
        from ..knowledge.pool import add_lesson
        try:
            lesson_id = add_lesson(
                lesson_type=lesson_type,
                description=description,
                virtue_id=virtue_id,
                agent_id=proxy.agent_id,
            )
        except Exception as e:
            logger.error(f"Failed to create lesson: {e}")
            return []

        # Share to all communities
        shared_to = []
        for community_id in proxy.community_ids:
            try:
                self.store.share_lesson_to_community(
                    lesson_id=lesson_id,
                    community_id=community_id,
                    proxy_id=proxy_id,
                )
                shared_to.append(community_id)

                # Update community stats
                community = self.store.get_community(community_id)
                if community:
                    community.share_lesson(lesson_id)
                    self.store.save_community(community)

            except Exception as e:
                logger.error(f"Failed to share to community {community_id}: {e}")

        logger.info(f"Lesson shared to {len(shared_to)} communities")
        return shared_to

    def share_pathway(
        self,
        proxy_id: str,
        start_concept: str,
        virtue_id: str,
        path: list[str],
        capture_time: float,
    ) -> list[str]:
        """
        Share a successful pathway to a virtue.

        Args:
            proxy_id: Who found this path
            start_concept: Starting point
            virtue_id: Destination virtue
            path: The path taken
            capture_time: How long it took

        Returns:
            List of community IDs that received the pathway
        """
        proxy = self.store.get_proxy(proxy_id)
        if not proxy:
            return []

        # Create pathway in graph
        from ..knowledge.pathways import record_pathway
        try:
            pathway_id = record_pathway(
                start_node=start_concept,
                virtue_id=virtue_id,
                path=path,
                capture_time=capture_time,
                agent_id=proxy.agent_id,
            )
        except Exception as e:
            logger.error(f"Failed to create pathway: {e}")
            return []

        # Share to communities
        shared_to = []
        for community_id in proxy.community_ids:
            community = self.store.get_community(community_id)
            if community:
                community.share_pathway(pathway_id)
                self.store.save_community(community)
                shared_to.append(community_id)

        return shared_to

    def share_pattern(
        self,
        proxy_id: str,
        pattern_key: str,
        pattern_value: Any,
    ) -> list[str]:
        """
        Share a learned pattern with communities.

        Patterns are behavioral insights that help other proxies.

        Args:
            proxy_id: Who learned this
            pattern_key: What kind of pattern
            pattern_value: The pattern itself

        Returns:
            List of community IDs
        """
        proxy = self.store.get_proxy(proxy_id)
        if not proxy:
            return []

        # Store in proxy's learned patterns
        proxy.learn(pattern_key, pattern_value)
        self.store.save_proxy(proxy)

        # Patterns are automatically available to community via proxy
        return proxy.community_ids.copy()

    def get_community_lessons(
        self,
        community_id: str,
        limit: int = 50,
        lesson_type: str | None = None,
    ) -> list[dict]:
        """
        Get lessons shared in a community.

        Args:
            community_id: Which community
            limit: Max lessons to return
            lesson_type: Optional filter by type

        Returns:
            List of lesson dictionaries
        """
        return self.store.get_community_lessons(community_id, limit)

    def get_community_wisdom(self, community_id: str) -> dict:
        """
        Get the collective wisdom of a community.

        Returns aggregated learnings:
        - Common patterns
        - Successful pathways
        - Key lessons
        """
        community = self.store.get_community(community_id)
        if not community:
            return {}

        # Get member patterns
        patterns = {}
        for proxy_id in community.member_ids:
            proxy = self.store.get_proxy(proxy_id)
            if proxy:
                for key, value in proxy.learned_patterns.items():
                    if key not in patterns:
                        patterns[key] = []
                    patterns[key].append(value)

        # Get lessons
        lessons = self.store.get_community_lessons(community_id, limit=100)

        # Get pathways (simplified)
        pathways = list(community.shared_pathway_ids)[:20]

        return {
            "community_id": community_id,
            "community_name": community.name,
            "member_count": community.member_count,
            "total_lessons": community.total_lessons_shared,
            "patterns": patterns,
            "recent_lessons": lessons[:10],
            "pathways": pathways,
        }

    def propagate_to_new_member(
        self,
        proxy_id: str,
        community_id: str,
    ) -> dict:
        """
        Give a new community member access to collective wisdom.

        Called when a proxy joins a community.

        Args:
            proxy_id: The new member
            community_id: The community joined

        Returns:
            Summary of what was shared
        """
        proxy = self.store.get_proxy(proxy_id)
        community = self.store.get_community(community_id)

        if not proxy or not community:
            return {"error": "Proxy or community not found"}

        # Get community wisdom
        wisdom = self.get_community_wisdom(community_id)

        # The proxy now has access to all shared lessons/pathways
        # through the community relationship

        logger.info(
            f"Proxy {proxy_id} now has access to community {community_id} wisdom"
        )

        return {
            "proxy_id": proxy_id,
            "community_id": community_id,
            "lessons_available": wisdom.get("total_lessons", 0),
            "patterns_available": len(wisdom.get("patterns", {})),
            "pathways_available": len(wisdom.get("pathways", [])),
        }


# Singleton
_sharing: CommunitySharing | None = None


def get_sharing() -> CommunitySharing:
    """Get the singleton sharing manager."""
    global _sharing
    if _sharing is None:
        _sharing = CommunitySharing()
    return _sharing


def share_learning(
    proxy_id: str,
    learning_type: str,
    content: dict,
) -> list[str]:
    """
    Convenience function to share any learning.

    Args:
        proxy_id: Who learned
        learning_type: What type of learning
        content: The content to share

    Returns:
        Communities that received it
    """
    sharing = get_sharing()

    if learning_type == "lesson":
        return sharing.share_lesson(
            proxy_id=proxy_id,
            lesson_type=content.get("type", "insight"),
            description=content.get("description", ""),
            virtue_id=content.get("virtue_id"),
            context=content.get("context"),
        )
    elif learning_type == "pathway":
        return sharing.share_pathway(
            proxy_id=proxy_id,
            start_concept=content.get("start", ""),
            virtue_id=content.get("virtue_id", ""),
            path=content.get("path", []),
            capture_time=content.get("capture_time", 0),
        )
    elif learning_type == "pattern":
        return sharing.share_pattern(
            proxy_id=proxy_id,
            pattern_key=content.get("key", ""),
            pattern_value=content.get("value"),
        )

    return []
