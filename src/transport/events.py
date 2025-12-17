"""
WebSocket Event Types.

Defines all events that flow between client and server.
"""

import json
import uuid
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any


class EventType(str, Enum):
    """Types of events in the transport layer."""

    # Client -> Server
    VOICE_CHUNK = "voice_chunk"
    TEXT_INPUT = "text_input"
    GESTURE = "gesture"
    PRESENCE = "presence"
    ARTIFACT_REQUEST = "artifact_request"
    PROXY_SWITCH = "proxy_switch"

    # Server -> Client
    CAPTION = "caption"
    STAGE_UPDATE = "stage_update"
    AGENT_STATE = "agent_state"
    SESSION_STATE = "session_state"
    VOICE_OUTPUT = "voice_output"
    ERROR = "error"

    # Bidirectional
    PING = "ping"
    PONG = "pong"


@dataclass
class Event:
    """Base event class."""

    type: EventType
    id: str = field(default_factory=lambda: uuid.uuid4().hex[:12])
    timestamp: datetime = field(default_factory=datetime.utcnow)
    session_id: str | None = None
    user_id: str | None = None

    def to_dict(self) -> dict:
        return {
            "type": self.type.value,
            "id": self.id,
            "timestamp": self.timestamp.isoformat(),
            "session_id": self.session_id,
            "user_id": self.user_id,
        }

    def to_json(self) -> str:
        return json.dumps(self.to_dict())

    @classmethod
    def from_dict(cls, data: dict) -> "Event":
        event_type = EventType(data.get("type"))
        # Route to specific event class
        event_classes = {
            EventType.VOICE_CHUNK: VoiceChunk,
            EventType.TEXT_INPUT: TextInput,
            EventType.CAPTION: Caption,
            EventType.STAGE_UPDATE: StageUpdate,
            EventType.AGENT_STATE: AgentState,
            EventType.SESSION_STATE: SessionState,
            EventType.PRESENCE: PresenceEvent,
            EventType.VOICE_OUTPUT: VoiceOutput,
            EventType.ARTIFACT_REQUEST: ArtifactRequest,
            EventType.PROXY_SWITCH: ProxySwitch,
        }
        event_class = event_classes.get(event_type, Event)
        return event_class._from_dict(data)

    @classmethod
    def _from_dict(cls, data: dict) -> "Event":
        return cls(
            type=EventType(data.get("type")),
            id=data.get("id", uuid.uuid4().hex[:12]),
            timestamp=datetime.fromisoformat(data["timestamp"])
            if "timestamp" in data
            else datetime.utcnow(),
            session_id=data.get("session_id"),
            user_id=data.get("user_id"),
        )


# Client -> Server Events


@dataclass
class VoiceChunk(Event):
    """Audio data from client microphone."""

    type: EventType = field(default=EventType.VOICE_CHUNK)
    audio_data: bytes = field(default=b"")
    sample_rate: int = 16000
    encoding: str = "pcm"
    is_final: bool = False

    def to_dict(self) -> dict:
        base = super().to_dict()
        base.update(
            {
                "audio_data": self.audio_data.hex() if self.audio_data else "",
                "sample_rate": self.sample_rate,
                "encoding": self.encoding,
                "is_final": self.is_final,
            }
        )
        return base

    @classmethod
    def _from_dict(cls, data: dict) -> "VoiceChunk":
        return cls(
            id=data.get("id", uuid.uuid4().hex[:12]),
            timestamp=datetime.fromisoformat(data["timestamp"])
            if "timestamp" in data
            else datetime.utcnow(),
            session_id=data.get("session_id"),
            user_id=data.get("user_id"),
            audio_data=bytes.fromhex(data.get("audio_data", "")),
            sample_rate=data.get("sample_rate", 16000),
            encoding=data.get("encoding", "pcm"),
            is_final=data.get("is_final", False),
        )


@dataclass
class TextInput(Event):
    """Text message from client (fallback input)."""

    type: EventType = field(default=EventType.TEXT_INPUT)
    text: str = ""
    is_asl: bool = False  # True if interpreted from ASL

    def to_dict(self) -> dict:
        base = super().to_dict()
        base.update({"text": self.text, "is_asl": self.is_asl})
        return base

    @classmethod
    def _from_dict(cls, data: dict) -> "TextInput":
        return cls(
            id=data.get("id", uuid.uuid4().hex[:12]),
            timestamp=datetime.fromisoformat(data["timestamp"])
            if "timestamp" in data
            else datetime.utcnow(),
            session_id=data.get("session_id"),
            user_id=data.get("user_id"),
            text=data.get("text", ""),
            is_asl=data.get("is_asl", False),
        )


class PresenceType(str, Enum):
    """Types of presence events."""

    JOIN = "join"
    LEAVE = "leave"
    OBSERVE = "observe"  # Step back
    ENGAGE = "engage"  # Return from observe
    AWAY = "away"  # Disengagement detected


@dataclass
class PresenceEvent(Event):
    """User presence change."""

    type: EventType = field(default=EventType.PRESENCE)
    presence_type: PresenceType = PresenceType.JOIN
    proxy_id: str | None = None

    def to_dict(self) -> dict:
        base = super().to_dict()
        base.update(
            {
                "presence_type": self.presence_type.value,
                "proxy_id": self.proxy_id,
            }
        )
        return base

    @classmethod
    def _from_dict(cls, data: dict) -> "PresenceEvent":
        return cls(
            id=data.get("id", uuid.uuid4().hex[:12]),
            timestamp=datetime.fromisoformat(data["timestamp"])
            if "timestamp" in data
            else datetime.utcnow(),
            session_id=data.get("session_id"),
            user_id=data.get("user_id"),
            presence_type=PresenceType(data.get("presence_type", "join")),
            proxy_id=data.get("proxy_id"),
        )


@dataclass
class ArtifactRequest(Event):
    """Request to surface a specific artifact."""

    type: EventType = field(default=EventType.ARTIFACT_REQUEST)
    query: str = ""  # "Show me the timeline"
    artifact_type: str | None = None

    def to_dict(self) -> dict:
        base = super().to_dict()
        base.update({"query": self.query, "artifact_type": self.artifact_type})
        return base

    @classmethod
    def _from_dict(cls, data: dict) -> "ArtifactRequest":
        return cls(
            id=data.get("id", uuid.uuid4().hex[:12]),
            timestamp=datetime.fromisoformat(data["timestamp"])
            if "timestamp" in data
            else datetime.utcnow(),
            session_id=data.get("session_id"),
            user_id=data.get("user_id"),
            query=data.get("query", ""),
            artifact_type=data.get("artifact_type"),
        )


@dataclass
class ProxySwitch(Event):
    """Request to switch active proxy."""

    type: EventType = field(default=EventType.PROXY_SWITCH)
    target_proxy_id: str = ""

    def to_dict(self) -> dict:
        base = super().to_dict()
        base.update({"target_proxy_id": self.target_proxy_id})
        return base

    @classmethod
    def _from_dict(cls, data: dict) -> "ProxySwitch":
        return cls(
            id=data.get("id", uuid.uuid4().hex[:12]),
            timestamp=datetime.fromisoformat(data["timestamp"])
            if "timestamp" in data
            else datetime.utcnow(),
            session_id=data.get("session_id"),
            user_id=data.get("user_id"),
            target_proxy_id=data.get("target_proxy_id", ""),
        )


# Server -> Client Events


@dataclass
class Caption(Event):
    """Caption to display on stage."""

    type: EventType = field(default=EventType.CAPTION)
    speaker_id: str = ""
    speaker_name: str = ""
    speaker_role: str = ""  # proxy, agent, system
    text: str = ""
    color: str = "#FFFFFF"
    duration_ms: int = 4000
    animation: str = "fade"  # fade, slide_up, typewriter

    def to_dict(self) -> dict:
        base = super().to_dict()
        base.update(
            {
                "speaker_id": self.speaker_id,
                "speaker_name": self.speaker_name,
                "speaker_role": self.speaker_role,
                "text": self.text,
                "color": self.color,
                "duration_ms": self.duration_ms,
                "animation": self.animation,
            }
        )
        return base

    @classmethod
    def _from_dict(cls, data: dict) -> "Caption":
        return cls(
            id=data.get("id", uuid.uuid4().hex[:12]),
            timestamp=datetime.fromisoformat(data["timestamp"])
            if "timestamp" in data
            else datetime.utcnow(),
            session_id=data.get("session_id"),
            user_id=data.get("user_id"),
            speaker_id=data.get("speaker_id", ""),
            speaker_name=data.get("speaker_name", ""),
            speaker_role=data.get("speaker_role", ""),
            text=data.get("text", ""),
            color=data.get("color", "#FFFFFF"),
            duration_ms=data.get("duration_ms", 4000),
            animation=data.get("animation", "fade"),
        )


class TransitionType(str, Enum):
    """Types of stage transitions."""

    NONE = "none"
    CROSSFADE = "crossfade"
    CUT = "cut"
    MORPH = "morph"


@dataclass
class StageUpdate(Event):
    """Update to the visual stage."""

    type: EventType = field(default=EventType.STAGE_UPDATE)
    image_url: str | None = None
    image_data: str | None = None  # Base64 for generated
    artifact_id: str | None = None
    artifact_type: str | None = None
    artifact_data: dict | None = None
    transition: TransitionType = TransitionType.CROSSFADE
    transition_duration_ms: int = 500

    def to_dict(self) -> dict:
        base = super().to_dict()
        base.update(
            {
                "image_url": self.image_url,
                "image_data": self.image_data,
                "artifact_id": self.artifact_id,
                "artifact_type": self.artifact_type,
                "artifact_data": self.artifact_data,
                "transition": self.transition.value,
                "transition_duration_ms": self.transition_duration_ms,
            }
        )
        return base

    @classmethod
    def _from_dict(cls, data: dict) -> "StageUpdate":
        return cls(
            id=data.get("id", uuid.uuid4().hex[:12]),
            timestamp=datetime.fromisoformat(data["timestamp"])
            if "timestamp" in data
            else datetime.utcnow(),
            session_id=data.get("session_id"),
            user_id=data.get("user_id"),
            image_url=data.get("image_url"),
            image_data=data.get("image_data"),
            artifact_id=data.get("artifact_id"),
            artifact_type=data.get("artifact_type"),
            artifact_data=data.get("artifact_data"),
            transition=TransitionType(data.get("transition", "crossfade")),
            transition_duration_ms=data.get("transition_duration_ms", 500),
        )


@dataclass
class AgentState(Event):
    """Agent activity state update."""

    type: EventType = field(default=EventType.AGENT_STATE)
    agent_id: str = ""
    agent_name: str = ""
    state: str = "idle"  # idle, speaking, thinking, listening
    is_proxy: bool = False
    owner_id: str | None = None  # For proxies

    def to_dict(self) -> dict:
        base = super().to_dict()
        base.update(
            {
                "agent_id": self.agent_id,
                "agent_name": self.agent_name,
                "state": self.state,
                "is_proxy": self.is_proxy,
                "owner_id": self.owner_id,
            }
        )
        return base

    @classmethod
    def _from_dict(cls, data: dict) -> "AgentState":
        return cls(
            id=data.get("id", uuid.uuid4().hex[:12]),
            timestamp=datetime.fromisoformat(data["timestamp"])
            if "timestamp" in data
            else datetime.utcnow(),
            session_id=data.get("session_id"),
            user_id=data.get("user_id"),
            agent_id=data.get("agent_id", ""),
            agent_name=data.get("agent_name", ""),
            state=data.get("state", "idle"),
            is_proxy=data.get("is_proxy", False),
            owner_id=data.get("owner_id"),
        )


class SessionStatus(str, Enum):
    """Session status values."""

    CREATED = "created"
    ACTIVE = "active"
    PAUSED = "paused"
    SUSPENDED = "suspended"
    COMPLETED = "completed"


@dataclass
class SessionState(Event):
    """Full session state update."""

    type: EventType = field(default=EventType.SESSION_STATE)
    status: SessionStatus = SessionStatus.ACTIVE
    participants: list[dict] = field(default_factory=list)
    agents: list[dict] = field(default_factory=list)
    topic: str | None = None
    context: dict = field(default_factory=dict)

    def to_dict(self) -> dict:
        base = super().to_dict()
        base.update(
            {
                "status": self.status.value,
                "participants": self.participants,
                "agents": self.agents,
                "topic": self.topic,
                "context": self.context,
            }
        )
        return base

    @classmethod
    def _from_dict(cls, data: dict) -> "SessionState":
        return cls(
            id=data.get("id", uuid.uuid4().hex[:12]),
            timestamp=datetime.fromisoformat(data["timestamp"])
            if "timestamp" in data
            else datetime.utcnow(),
            session_id=data.get("session_id"),
            user_id=data.get("user_id"),
            status=SessionStatus(data.get("status", "active")),
            participants=data.get("participants", []),
            agents=data.get("agents", []),
            topic=data.get("topic"),
            context=data.get("context", {}),
        )


@dataclass
class VoiceOutput(Event):
    """TTS audio to play on client."""

    type: EventType = field(default=EventType.VOICE_OUTPUT)
    agent_id: str = ""
    audio_data: bytes = field(default=b"")
    sample_rate: int = 24000
    encoding: str = "mp3"
    text: str = ""  # For caption sync

    def to_dict(self) -> dict:
        base = super().to_dict()
        base.update(
            {
                "agent_id": self.agent_id,
                "audio_data": self.audio_data.hex() if self.audio_data else "",
                "sample_rate": self.sample_rate,
                "encoding": self.encoding,
                "text": self.text,
            }
        )
        return base

    @classmethod
    def _from_dict(cls, data: dict) -> "VoiceOutput":
        return cls(
            id=data.get("id", uuid.uuid4().hex[:12]),
            timestamp=datetime.fromisoformat(data["timestamp"])
            if "timestamp" in data
            else datetime.utcnow(),
            session_id=data.get("session_id"),
            user_id=data.get("user_id"),
            agent_id=data.get("agent_id", ""),
            audio_data=bytes.fromhex(data.get("audio_data", "")),
            sample_rate=data.get("sample_rate", 24000),
            encoding=data.get("encoding", "mp3"),
            text=data.get("text", ""),
        )
