"""
Community - A group that shares everything.

Communities are the social fabric of Soul Kiln. Every proxy belongs
to at least one community. Community members share:
- Knowledge and lessons
- Patterns and pathways
- Tools and capabilities
- Collective wisdom

Communities have virtue emphases that shape behavior.
"""

import uuid
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any


class CommunityPurpose(str, Enum):
    """What the community exists for."""

    EDUCATION = "education"  # Learning and teaching
    SERVICE = "service"  # Helping others
    RESEARCH = "research"  # Knowledge discovery
    CREATIVE = "creative"  # Arts and creation
    GOVERNANCE = "governance"  # Organization and leadership
    HEALTH = "health"  # Wellbeing and care
    ENVIRONMENT = "environment"  # Sustainability
    JUSTICE = "justice"  # Equity and rights
    SPIRITUAL = "spiritual"  # Faith and meaning
    FAMILY = "family"  # Personal connections
    GENERAL = "general"  # Multi-purpose


@dataclass
class VirtueEmphasis:
    """
    How a community emphasizes specific virtues.

    Modifiers adjust virtue thresholds:
    - Positive: higher expectations
    - Negative: more mercy/leniency
    """

    # Cluster-level modifiers (e.g., "wisdom": +0.05)
    cluster_modifiers: dict[str, float] = field(default_factory=dict)

    # Individual virtue modifiers (e.g., "V03": +0.1 for compassion)
    virtue_modifiers: dict[str, float] = field(default_factory=dict)

    # Why these emphases?
    rationale: str = ""

    def get_modifier(self, virtue_id: str, cluster: str = "") -> float:
        """Get total modifier for a virtue."""
        modifier = 0.0
        if cluster:
            modifier += self.cluster_modifiers.get(cluster, 0.0)
        modifier += self.virtue_modifiers.get(virtue_id, 0.0)
        return modifier

    def to_dict(self) -> dict:
        return {
            "cluster_modifiers": self.cluster_modifiers,
            "virtue_modifiers": self.virtue_modifiers,
            "rationale": self.rationale,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "VirtueEmphasis":
        return cls(
            cluster_modifiers=data.get("cluster_modifiers", {}),
            virtue_modifiers=data.get("virtue_modifiers", {}),
            rationale=data.get("rationale", ""),
        )


@dataclass
class Community:
    """
    A community of proxies that share everything.

    Graph relationships:
    - (Community)-[:HAS_MEMBER]->(Proxy)
    - (Community)-[:SHARES]->(Lesson)
    - (Community)-[:EMPHASIZES]->(VirtueAnchor)
    """

    id: str = field(default_factory=lambda: f"comm_{uuid.uuid4().hex[:12]}")
    name: str = ""
    description: str = ""
    purpose: CommunityPurpose = CommunityPurpose.GENERAL

    # Virtue emphasis
    virtue_emphasis: VirtueEmphasis = field(default_factory=VirtueEmphasis)

    # Member proxy IDs
    member_ids: set[str] = field(default_factory=set)

    # Shared resources
    shared_lesson_ids: set[str] = field(default_factory=set)
    shared_pathway_ids: set[str] = field(default_factory=set)
    tool_ids: set[str] = field(default_factory=set)

    # Who created this community
    creator_id: str = ""

    # Lifecycle
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)
    active: bool = True

    # Stats
    total_members_ever: int = 0
    total_lessons_shared: int = 0
    total_conversations: int = 0

    # Metadata
    metadata: dict[str, Any] = field(default_factory=dict)

    def add_member(self, proxy_id: str) -> bool:
        """Add a proxy to this community."""
        if proxy_id not in self.member_ids:
            self.member_ids.add(proxy_id)
            self.total_members_ever += 1
            self.updated_at = datetime.utcnow()
            return True
        return False

    def remove_member(self, proxy_id: str) -> bool:
        """Remove a proxy from this community."""
        if proxy_id in self.member_ids:
            self.member_ids.discard(proxy_id)
            self.updated_at = datetime.utcnow()
            return True
        return False

    def share_lesson(self, lesson_id: str) -> None:
        """Share a lesson with the community."""
        self.shared_lesson_ids.add(lesson_id)
        self.total_lessons_shared += 1
        self.updated_at = datetime.utcnow()

    def share_pathway(self, pathway_id: str) -> None:
        """Share a successful pathway."""
        self.shared_pathway_ids.add(pathway_id)
        self.updated_at = datetime.utcnow()

    def add_tool(self, tool_id: str) -> None:
        """Add a tool to the community."""
        self.tool_ids.add(tool_id)
        self.updated_at = datetime.utcnow()

    def record_conversation(self) -> None:
        """Record a conversation happened."""
        self.total_conversations += 1
        self.updated_at = datetime.utcnow()

    def has_member(self, proxy_id: str) -> bool:
        """Check if proxy is a member."""
        return proxy_id in self.member_ids

    @property
    def member_count(self) -> int:
        """Current member count."""
        return len(self.member_ids)

    def get_virtue_modifier(self, virtue_id: str, cluster: str = "") -> float:
        """Get virtue threshold modifier."""
        return self.virtue_emphasis.get_modifier(virtue_id, cluster)

    def to_dict(self) -> dict:
        """Convert to dictionary for storage."""
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "purpose": self.purpose.value,
            "virtue_emphasis": self.virtue_emphasis.to_dict(),
            "member_ids": list(self.member_ids),
            "shared_lesson_ids": list(self.shared_lesson_ids),
            "shared_pathway_ids": list(self.shared_pathway_ids),
            "tool_ids": list(self.tool_ids),
            "creator_id": self.creator_id,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
            "active": self.active,
            "stats": {
                "total_members_ever": self.total_members_ever,
                "total_lessons_shared": self.total_lessons_shared,
                "total_conversations": self.total_conversations,
                "current_members": self.member_count,
            },
            "metadata": self.metadata,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "Community":
        """Create from dictionary."""
        virtue_data = data.get("virtue_emphasis", {})
        community = cls(
            id=data.get("id", f"comm_{uuid.uuid4().hex[:12]}"),
            name=data.get("name", ""),
            description=data.get("description", ""),
            purpose=CommunityPurpose(data.get("purpose", "general")),
            virtue_emphasis=VirtueEmphasis.from_dict(virtue_data),
            member_ids=set(data.get("member_ids", [])),
            shared_lesson_ids=set(data.get("shared_lesson_ids", [])),
            shared_pathway_ids=set(data.get("shared_pathway_ids", [])),
            tool_ids=set(data.get("tool_ids", [])),
            creator_id=data.get("creator_id", ""),
            active=data.get("active", True),
            metadata=data.get("metadata", {}),
        )

        if data.get("created_at"):
            community.created_at = datetime.fromisoformat(data["created_at"])
        if data.get("updated_at"):
            community.updated_at = datetime.fromisoformat(data["updated_at"])

        stats = data.get("stats", {})
        community.total_members_ever = stats.get("total_members_ever", 0)
        community.total_lessons_shared = stats.get("total_lessons_shared", 0)
        community.total_conversations = stats.get("total_conversations", 0)

        return community

    def __str__(self) -> str:
        return f"Community({self.name}, purpose={self.purpose.value}, members={self.member_count})"
