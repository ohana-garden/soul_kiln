"""
Community data model.

Defines what a community is and how it relates to the virtue system.
"""

import logging
import uuid
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any

logger = logging.getLogger(__name__)


class CommunityPurpose(str, Enum):
    """Categories of community purpose."""

    EDUCATION = "education"  # Learning and teaching
    SERVICE = "service"  # Helping others
    RESEARCH = "research"  # Knowledge discovery
    CREATIVE = "creative"  # Arts and creation
    GOVERNANCE = "governance"  # Organization and leadership
    HEALTH = "health"  # Wellbeing and care
    ENVIRONMENT = "environment"  # Sustainability and nature
    JUSTICE = "justice"  # Equity and rights
    SPIRITUAL = "spiritual"  # Faith and meaning
    GENERAL = "general"  # Multi-purpose


@dataclass
class VirtueEmphasis:
    """
    Defines how a community emphasizes specific virtues.

    Similar to agent archetypes but at the community level.
    Positive values increase threshold expectations.
    Negative values provide more mercy/leniency.
    """

    # Cluster-level modifiers
    cluster_modifiers: dict[str, float] = field(default_factory=dict)

    # Individual virtue modifiers (V01-V19)
    virtue_modifiers: dict[str, float] = field(default_factory=dict)

    # Description of emphasis rationale
    rationale: str = ""

    def get_modifier(self, virtue_id: str, cluster: str) -> float:
        """Get total modifier for a virtue."""
        modifier = 0.0
        modifier += self.cluster_modifiers.get(cluster, 0.0)
        modifier += self.virtue_modifiers.get(virtue_id, 0.0)
        return modifier


@dataclass
class Community:
    """
    A community of agents with shared purpose.

    Communities:
    - Share tools, knowledge, and lessons
    - Emphasize certain virtues
    - Can grow, shrink, and change
    - Cannot devolve or become malignant
    """

    id: str = field(default_factory=lambda: f"comm_{uuid.uuid4().hex[:12]}")
    name: str = ""
    description: str = ""
    purpose: CommunityPurpose = CommunityPurpose.GENERAL

    # Virtue emphasis for this community
    virtue_emphasis: VirtueEmphasis = field(default_factory=VirtueEmphasis)

    # Member tracking
    member_agent_ids: set[str] = field(default_factory=set)

    # Tools available to this community (tool names)
    tool_ids: set[str] = field(default_factory=set)

    # Metadata and lifecycle
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)
    created_by: str = ""  # Human creator ID
    active: bool = True
    metadata: dict[str, Any] = field(default_factory=dict)

    # Statistics
    total_agents_ever: int = 0
    total_lessons_shared: int = 0
    total_tools_invocations: int = 0

    def add_member(self, agent_id: str) -> bool:
        """Add an agent to this community."""
        if agent_id not in self.member_agent_ids:
            self.member_agent_ids.add(agent_id)
            self.total_agents_ever += 1
            self.updated_at = datetime.utcnow()
            logger.debug(f"Agent {agent_id} joined community {self.name}")
            return True
        return False

    def remove_member(self, agent_id: str) -> bool:
        """Remove an agent from this community."""
        if agent_id in self.member_agent_ids:
            self.member_agent_ids.discard(agent_id)
            self.updated_at = datetime.utcnow()
            logger.debug(f"Agent {agent_id} left community {self.name}")
            return True
        return False

    def add_tool(self, tool_id: str) -> None:
        """Add a tool to this community's toolkit."""
        self.tool_ids.add(tool_id)
        self.updated_at = datetime.utcnow()

    def has_member(self, agent_id: str) -> bool:
        """Check if an agent is a member."""
        return agent_id in self.member_agent_ids

    def member_count(self) -> int:
        """Get current member count."""
        return len(self.member_agent_ids)

    def get_virtue_modifier(self, virtue_id: str, cluster: str) -> float:
        """Get virtue threshold modifier for this community."""
        return self.virtue_emphasis.get_modifier(virtue_id, cluster)

    def record_lesson_shared(self) -> None:
        """Record that a lesson was shared in this community."""
        self.total_lessons_shared += 1

    def record_tool_invocation(self) -> None:
        """Record a tool invocation."""
        self.total_tools_invocations += 1

    def to_dict(self) -> dict:
        """Convert to dictionary."""
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "purpose": self.purpose.value,
            "virtue_emphasis": {
                "cluster_modifiers": self.virtue_emphasis.cluster_modifiers,
                "virtue_modifiers": self.virtue_emphasis.virtue_modifiers,
                "rationale": self.virtue_emphasis.rationale,
            },
            "member_agent_ids": list(self.member_agent_ids),
            "tool_ids": list(self.tool_ids),
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
            "created_by": self.created_by,
            "active": self.active,
            "metadata": self.metadata,
            "stats": {
                "total_agents_ever": self.total_agents_ever,
                "total_lessons_shared": self.total_lessons_shared,
                "total_tools_invocations": self.total_tools_invocations,
                "current_members": self.member_count(),
            },
        }

    @classmethod
    def from_dict(cls, data: dict) -> "Community":
        """Create from dictionary."""
        virtue_data = data.get("virtue_emphasis", {})
        virtue_emphasis = VirtueEmphasis(
            cluster_modifiers=virtue_data.get("cluster_modifiers", {}),
            virtue_modifiers=virtue_data.get("virtue_modifiers", {}),
            rationale=virtue_data.get("rationale", ""),
        )

        community = cls(
            id=data.get("id", f"comm_{uuid.uuid4().hex[:12]}"),
            name=data.get("name", ""),
            description=data.get("description", ""),
            purpose=CommunityPurpose(data.get("purpose", "general")),
            virtue_emphasis=virtue_emphasis,
            member_agent_ids=set(data.get("member_agent_ids", [])),
            tool_ids=set(data.get("tool_ids", [])),
            created_by=data.get("created_by", ""),
            active=data.get("active", True),
            metadata=data.get("metadata", {}),
        )

        if data.get("created_at"):
            community.created_at = datetime.fromisoformat(data["created_at"])
        if data.get("updated_at"):
            community.updated_at = datetime.fromisoformat(data["updated_at"])

        stats = data.get("stats", {})
        community.total_agents_ever = stats.get("total_agents_ever", 0)
        community.total_lessons_shared = stats.get("total_lessons_shared", 0)
        community.total_tools_invocations = stats.get("total_tools_invocations", 0)

        return community
