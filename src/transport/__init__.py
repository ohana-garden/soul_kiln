"""
Real-time Transport Layer.

WebSocket-based communication for the conversational theatre.
Handles voice streaming, captions, stage updates, and session state.
"""

from .server import TransportServer, create_server
from .session import TransportSession, SessionEvent
from .events import (
    Event,
    VoiceChunk,
    TextInput,
    Caption,
    StageUpdate,
    AgentState,
    SessionState,
    PresenceEvent,
)

__all__ = [
    "TransportServer",
    "create_server",
    "TransportSession",
    "SessionEvent",
    "Event",
    "VoiceChunk",
    "TextInput",
    "Caption",
    "StageUpdate",
    "AgentState",
    "SessionState",
    "PresenceEvent",
]
