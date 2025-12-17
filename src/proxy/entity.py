"""
Proxy Entity.

Core proxy data model and configuration.
"""

import uuid
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any


class ProxyStatus(str, Enum):
    """Proxy status values."""

    ACTIVE = "active"
    IDLE = "idle"
    SPEAKING = "speaking"
    LISTENING = "listening"
    THINKING = "thinking"


@dataclass
class ProxyConfig:
    """Configuration for proxy behavior."""

    # Voice settings
    voice_id: str = "default"
    voice_speed: float = 1.0
    voice_pitch: float = 1.0

    # Behavior
    autonomy_level: float = 0.5  # 0 = silent, 1 = fully autonomous
    clarify_threshold: float = 0.3  # When to ask for clarification
    defer_on_major: bool = True  # Defer major decisions to user

    # Style
    formality: float = 0.5  # 0 = casual, 1 = formal
    verbosity: float = 0.5  # 0 = terse, 1 = elaborate

    def to_dict(self) -> dict:
        return {
            "voice_id": self.voice_id,
            "voice_speed": self.voice_speed,
            "voice_pitch": self.voice_pitch,
            "autonomy_level": self.autonomy_level,
            "clarify_threshold": self.clarify_threshold,
            "defer_on_major": self.defer_on_major,
            "formality": self.formality,
            "verbosity": self.verbosity,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "ProxyConfig":
        return cls(
            voice_id=data.get("voice_id", "default"),
            voice_speed=data.get("voice_speed", 1.0),
            voice_pitch=data.get("voice_pitch", 1.0),
            autonomy_level=data.get("autonomy_level", 0.5),
            clarify_threshold=data.get("clarify_threshold", 0.3),
            defer_on_major=data.get("defer_on_major", True),
            formality=data.get("formality", 0.5),
            verbosity=data.get("verbosity", 0.5),
        )


@dataclass
class Position:
    """A recorded position on a topic."""

    topic: str
    stance: str
    confidence: float = 0.5
    source: str = "inferred"  # user_stated, inferred, assumed
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)

    def to_dict(self) -> dict:
        return {
            "topic": self.topic,
            "stance": self.stance,
            "confidence": self.confidence,
            "source": self.source,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
        }


@dataclass
class Proxy:
    """
    A user's proxy agent in conversations.

    Proxies:
    - Speak for users with their voice when active
    - Continue advocating when user is silent
    - Maintain positions and preferences
    - Learn from interaction patterns
    """

    id: str = field(default_factory=lambda: f"proxy_{uuid.uuid4().hex[:12]}")
    owner_id: str = ""
    name: str = ""
    role: str = ""  # "Nonprofit Director", "Grant Writer", etc.

    # Community membership
    communities: list[str] = field(default_factory=list)

    # Configuration
    config: ProxyConfig = field(default_factory=ProxyConfig)

    # State
    status: ProxyStatus = ProxyStatus.IDLE
    current_session_id: str | None = None

    # Timestamps
    created_at: datetime = field(default_factory=datetime.utcnow)
    last_active: datetime = field(default_factory=datetime.utcnow)

    # Learned patterns
    positions: dict[str, Position] = field(default_factory=dict)
    vocabulary: dict[str, float] = field(default_factory=dict)  # term -> preference
    topics_discussed: list[str] = field(default_factory=list)

    # Metadata
    metadata: dict = field(default_factory=dict)

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "owner_id": self.owner_id,
            "name": self.name,
            "role": self.role,
            "communities": self.communities,
            "config": self.config.to_dict(),
            "status": self.status.value,
            "current_session_id": self.current_session_id,
            "created_at": self.created_at.isoformat(),
            "last_active": self.last_active.isoformat(),
            "positions": {k: v.to_dict() for k, v in self.positions.items()},
            "vocabulary": self.vocabulary,
            "topics_discussed": self.topics_discussed,
            "metadata": self.metadata,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "Proxy":
        positions = {}
        for k, v in data.get("positions", {}).items():
            positions[k] = Position(
                topic=v["topic"],
                stance=v["stance"],
                confidence=v.get("confidence", 0.5),
                source=v.get("source", "inferred"),
            )

        return cls(
            id=data.get("id", f"proxy_{uuid.uuid4().hex[:12]}"),
            owner_id=data.get("owner_id", ""),
            name=data.get("name", ""),
            role=data.get("role", ""),
            communities=data.get("communities", []),
            config=ProxyConfig.from_dict(data.get("config", {})),
            status=ProxyStatus(data.get("status", "idle")),
            current_session_id=data.get("current_session_id"),
            created_at=datetime.fromisoformat(data["created_at"])
            if "created_at" in data
            else datetime.utcnow(),
            last_active=datetime.fromisoformat(data["last_active"])
            if "last_active" in data
            else datetime.utcnow(),
            positions=positions,
            vocabulary=data.get("vocabulary", {}),
            topics_discussed=data.get("topics_discussed", []),
            metadata=data.get("metadata", {}),
        )

    def record_position(
        self,
        topic: str,
        stance: str,
        confidence: float = 0.5,
        source: str = "inferred",
    ) -> None:
        """Record or update a position on a topic."""
        now = datetime.utcnow()
        if topic in self.positions:
            pos = self.positions[topic]
            pos.stance = stance
            pos.confidence = confidence
            pos.source = source
            pos.updated_at = now
        else:
            self.positions[topic] = Position(
                topic=topic,
                stance=stance,
                confidence=confidence,
                source=source,
                created_at=now,
                updated_at=now,
            )

    def get_position(self, topic: str) -> Position | None:
        """Get position on a topic."""
        return self.positions.get(topic)

    def record_vocabulary(self, term: str, preference: float = 0.5) -> None:
        """Record vocabulary preference."""
        self.vocabulary[term] = preference

    def record_topic(self, topic: str) -> None:
        """Record a topic discussed."""
        if topic not in self.topics_discussed:
            self.topics_discussed.append(topic)
            # Keep last 100
            if len(self.topics_discussed) > 100:
                self.topics_discussed = self.topics_discussed[-100:]

    def activate(self, session_id: str) -> None:
        """Activate proxy for a session."""
        self.status = ProxyStatus.ACTIVE
        self.current_session_id = session_id
        self.last_active = datetime.utcnow()

    def deactivate(self) -> None:
        """Deactivate proxy."""
        self.status = ProxyStatus.IDLE
        self.current_session_id = None

    def set_speaking(self) -> None:
        """Set proxy to speaking state."""
        self.status = ProxyStatus.SPEAKING
        self.last_active = datetime.utcnow()

    def set_listening(self) -> None:
        """Set proxy to listening state."""
        self.status = ProxyStatus.LISTENING
        self.last_active = datetime.utcnow()

    def set_thinking(self) -> None:
        """Set proxy to thinking state."""
        self.status = ProxyStatus.THINKING
        self.last_active = datetime.utcnow()

    @property
    def is_active(self) -> bool:
        """Check if proxy is active."""
        return self.status != ProxyStatus.IDLE

    def __str__(self) -> str:
        return f"Proxy({self.name}, role={self.role})"
