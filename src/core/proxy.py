"""
Proxy - The personified agent that speaks for an entity.

A proxy is born through conversation. It:
- Represents an entity (human, org, concept, object)
- Belongs to one or more communities
- Behaves ethically via virtue basins
- Shares everything with its communities
"""

import uuid
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any


class ProxyType(str, Enum):
    """How the proxy operates."""

    VOICE = "voice"  # Speaks for the entity
    GUARDIAN = "guardian"  # Protects the entity's interests
    AMBASSADOR = "ambassador"  # Represents to others
    MIRROR = "mirror"  # Reflects back to the creator


class ProxyStatus(str, Enum):
    """Current state of the proxy."""

    NASCENT = "nascent"  # Being created
    ACTIVE = "active"  # Ready to engage
    SPEAKING = "speaking"  # Currently in conversation
    RESTING = "resting"  # Inactive but available
    DISSOLVED = "dissolved"  # No longer active


@dataclass
class ProxyConfig:
    """How the proxy behaves."""

    # Autonomy: how much does it act on its own?
    autonomy: float = 0.5  # 0=silent, 1=fully autonomous

    # When facing major decisions, defer to human?
    defer_on_major: bool = True

    # Voice characteristics
    formality: float = 0.5  # 0=casual, 1=formal
    verbosity: float = 0.5  # 0=terse, 1=elaborate
    warmth: float = 0.5  # 0=distant, 1=warm

    def to_dict(self) -> dict:
        return {
            "autonomy": self.autonomy,
            "defer_on_major": self.defer_on_major,
            "formality": self.formality,
            "verbosity": self.verbosity,
            "warmth": self.warmth,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "ProxyConfig":
        return cls(
            autonomy=data.get("autonomy", 0.5),
            defer_on_major=data.get("defer_on_major", True),
            formality=data.get("formality", 0.5),
            verbosity=data.get("verbosity", 0.5),
            warmth=data.get("warmth", 0.5),
        )


@dataclass
class Proxy:
    """
    A proxy speaks for an entity within communities.

    The proxy-entity-community triangle:
    - Entity: What is represented
    - Proxy: How it's personified
    - Community: Where it belongs and shares
    """

    id: str = field(default_factory=lambda: f"proxy_{uuid.uuid4().hex[:12]}")

    # What this proxy represents
    entity_id: str = ""

    # Who created this proxy
    creator_id: str = ""

    # Display identity
    name: str = ""
    role: str = ""  # "Voice of...", "Guardian of...", etc.

    # Type and status
    type: ProxyType = ProxyType.VOICE
    status: ProxyStatus = ProxyStatus.NASCENT

    # Community memberships
    community_ids: list[str] = field(default_factory=list)

    # Link to virtue graph (the agent node that navigates basins)
    agent_id: str = ""

    # Configuration
    config: ProxyConfig = field(default_factory=ProxyConfig)

    # Lifecycle
    created_at: datetime = field(default_factory=datetime.utcnow)
    activated_at: datetime | None = None
    last_active: datetime = field(default_factory=datetime.utcnow)

    # Session tracking
    current_session_id: str | None = None

    # Learned patterns (shared with community)
    learned_patterns: dict[str, Any] = field(default_factory=dict)

    # Metadata
    metadata: dict[str, Any] = field(default_factory=dict)

    def activate(self) -> None:
        """Activate the proxy (birth complete)."""
        self.status = ProxyStatus.ACTIVE
        self.activated_at = datetime.utcnow()
        self.last_active = datetime.utcnow()

    def join_session(self, session_id: str) -> None:
        """Join a conversation session."""
        self.current_session_id = session_id
        self.status = ProxyStatus.SPEAKING
        self.last_active = datetime.utcnow()

    def leave_session(self) -> None:
        """Leave the current session."""
        self.current_session_id = None
        self.status = ProxyStatus.ACTIVE
        self.last_active = datetime.utcnow()

    def rest(self) -> None:
        """Put proxy to rest."""
        self.current_session_id = None
        self.status = ProxyStatus.RESTING

    def dissolve(self) -> None:
        """Dissolve the proxy (with mercy)."""
        self.status = ProxyStatus.DISSOLVED
        self.current_session_id = None

    def join_community(self, community_id: str) -> bool:
        """Join a community."""
        if community_id not in self.community_ids:
            self.community_ids.append(community_id)
            return True
        return False

    def leave_community(self, community_id: str) -> bool:
        """Leave a community."""
        if community_id in self.community_ids:
            self.community_ids.remove(community_id)
            return True
        return False

    def learn(self, pattern_key: str, pattern_value: Any) -> None:
        """Learn a pattern (will be shared with community)."""
        self.learned_patterns[pattern_key] = pattern_value
        self.last_active = datetime.utcnow()

    @property
    def is_active(self) -> bool:
        return self.status in (ProxyStatus.ACTIVE, ProxyStatus.SPEAKING)

    @property
    def is_in_session(self) -> bool:
        return self.current_session_id is not None

    def to_dict(self) -> dict:
        """Convert to dictionary for storage."""
        return {
            "id": self.id,
            "entity_id": self.entity_id,
            "creator_id": self.creator_id,
            "name": self.name,
            "role": self.role,
            "type": self.type.value,
            "status": self.status.value,
            "community_ids": self.community_ids,
            "agent_id": self.agent_id,
            "config": self.config.to_dict(),
            "created_at": self.created_at.isoformat(),
            "activated_at": self.activated_at.isoformat() if self.activated_at else None,
            "last_active": self.last_active.isoformat(),
            "current_session_id": self.current_session_id,
            "learned_patterns": self.learned_patterns,
            "metadata": self.metadata,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "Proxy":
        """Create from dictionary."""
        proxy = cls(
            id=data.get("id", f"proxy_{uuid.uuid4().hex[:12]}"),
            entity_id=data.get("entity_id", ""),
            creator_id=data.get("creator_id", ""),
            name=data.get("name", ""),
            role=data.get("role", ""),
            type=ProxyType(data.get("type", "voice")),
            status=ProxyStatus(data.get("status", "nascent")),
            community_ids=data.get("community_ids", []),
            agent_id=data.get("agent_id", ""),
            config=ProxyConfig.from_dict(data.get("config", {})),
            current_session_id=data.get("current_session_id"),
            learned_patterns=data.get("learned_patterns", {}),
            metadata=data.get("metadata", {}),
        )
        if data.get("created_at"):
            proxy.created_at = datetime.fromisoformat(data["created_at"])
        if data.get("activated_at"):
            proxy.activated_at = datetime.fromisoformat(data["activated_at"])
        if data.get("last_active"):
            proxy.last_active = datetime.fromisoformat(data["last_active"])
        return proxy

    def __str__(self) -> str:
        return f"Proxy({self.name}, type={self.type.value}, status={self.status.value})"
