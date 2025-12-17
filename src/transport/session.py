"""
Transport Session Management.

Manages WebSocket connections and session state.
"""

import asyncio
import logging
import uuid
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Callable

from .events import (
    Event,
    EventType,
    SessionState,
    SessionStatus,
    PresenceEvent,
    PresenceType,
    Caption,
    StageUpdate,
    AgentState,
)

logger = logging.getLogger(__name__)


class SessionEvent(str, Enum):
    """Session lifecycle events."""

    CREATED = "created"
    PARTICIPANT_JOINED = "participant_joined"
    PARTICIPANT_LEFT = "participant_left"
    PARTICIPANT_OBSERVING = "participant_observing"
    PARTICIPANT_ENGAGED = "participant_engaged"
    PAUSED = "paused"
    RESUMED = "resumed"
    CLOSED = "closed"


@dataclass
class Participant:
    """A participant in a session."""

    user_id: str
    proxy_id: str | None = None
    connection_id: str | None = None
    status: str = "active"  # active, observing, away
    joined_at: datetime = field(default_factory=datetime.utcnow)
    last_activity: datetime = field(default_factory=datetime.utcnow)

    def to_dict(self) -> dict:
        return {
            "user_id": self.user_id,
            "proxy_id": self.proxy_id,
            "status": self.status,
            "joined_at": self.joined_at.isoformat(),
        }


@dataclass
class AgentInstance:
    """An agent instance in a session."""

    agent_id: str
    agent_type: str  # proxy, context, host
    name: str
    state: str = "idle"
    owner_id: str | None = None  # For proxies

    def to_dict(self) -> dict:
        return {
            "agent_id": self.agent_id,
            "agent_type": self.agent_type,
            "name": self.name,
            "state": self.state,
            "owner_id": self.owner_id,
        }


class TransportSession:
    """
    Manages a single conversation session.

    Handles:
    - Multiple participants (multi-user)
    - Agent instances
    - Event routing
    - State synchronization
    """

    def __init__(
        self,
        session_id: str | None = None,
        host_user_id: str | None = None,
    ):
        self.id = session_id or f"session_{uuid.uuid4().hex[:12]}"
        self.host_user_id = host_user_id
        self.status = SessionStatus.CREATED
        self.created_at = datetime.utcnow()

        # Participants and agents
        self._participants: dict[str, Participant] = {}
        self._agents: dict[str, AgentInstance] = {}

        # Connection mapping: connection_id -> user_id
        self._connections: dict[str, str] = {}

        # Send functions: connection_id -> async send function
        self._senders: dict[str, Callable[[str], Any]] = {}

        # Event callbacks
        self._callbacks: dict[SessionEvent, list[Callable]] = {
            event: [] for event in SessionEvent
        }

        # Current context
        self.topic: str | None = None
        self.context: dict = {}

        # Lock for thread safety
        self._lock = asyncio.Lock()

    async def add_participant(
        self,
        user_id: str,
        proxy_id: str | None = None,
        connection_id: str | None = None,
        send_fn: Callable[[str], Any] | None = None,
    ) -> Participant:
        """Add a participant to the session."""
        async with self._lock:
            participant = Participant(
                user_id=user_id,
                proxy_id=proxy_id,
                connection_id=connection_id,
            )
            self._participants[user_id] = participant

            if connection_id:
                self._connections[connection_id] = user_id
                if send_fn:
                    self._senders[connection_id] = send_fn

            # Set host if first participant
            if not self.host_user_id:
                self.host_user_id = user_id

            # Activate session if first participant
            if self.status == SessionStatus.CREATED:
                self.status = SessionStatus.ACTIVE

            logger.info(f"Participant {user_id} joined session {self.id}")

            # Notify
            await self._emit(SessionEvent.PARTICIPANT_JOINED, participant)

            # Broadcast state update
            await self._broadcast_state()

            return participant

    async def remove_participant(self, user_id: str) -> None:
        """Remove a participant from the session."""
        async with self._lock:
            if user_id not in self._participants:
                return

            participant = self._participants.pop(user_id)

            # Clean up connection
            if participant.connection_id:
                self._connections.pop(participant.connection_id, None)
                self._senders.pop(participant.connection_id, None)

            logger.info(f"Participant {user_id} left session {self.id}")

            # Notify
            await self._emit(SessionEvent.PARTICIPANT_LEFT, participant)

            # Close session if no participants
            if not self._participants:
                await self.close()
            else:
                await self._broadcast_state()

    async def set_participant_status(
        self, user_id: str, status: str
    ) -> None:
        """Update participant status (active, observing, away)."""
        async with self._lock:
            if user_id not in self._participants:
                return

            participant = self._participants[user_id]
            old_status = participant.status
            participant.status = status
            participant.last_activity = datetime.utcnow()

            if old_status != status:
                if status == "observing":
                    await self._emit(
                        SessionEvent.PARTICIPANT_OBSERVING, participant
                    )
                elif status == "active" and old_status == "observing":
                    await self._emit(
                        SessionEvent.PARTICIPANT_ENGAGED, participant
                    )

                await self._broadcast_state()

    async def add_agent(
        self,
        agent_id: str,
        agent_type: str,
        name: str,
        owner_id: str | None = None,
    ) -> AgentInstance:
        """Add an agent to the session."""
        async with self._lock:
            agent = AgentInstance(
                agent_id=agent_id,
                agent_type=agent_type,
                name=name,
                owner_id=owner_id,
            )
            self._agents[agent_id] = agent

            await self._broadcast_state()
            return agent

    async def remove_agent(self, agent_id: str) -> None:
        """Remove an agent from the session."""
        async with self._lock:
            if agent_id in self._agents:
                del self._agents[agent_id]
                await self._broadcast_state()

    async def update_agent_state(
        self, agent_id: str, state: str
    ) -> None:
        """Update an agent's state."""
        async with self._lock:
            if agent_id not in self._agents:
                return

            self._agents[agent_id].state = state

            # Broadcast agent state change
            event = AgentState(
                session_id=self.id,
                agent_id=agent_id,
                agent_name=self._agents[agent_id].name,
                state=state,
                is_proxy=self._agents[agent_id].agent_type == "proxy",
                owner_id=self._agents[agent_id].owner_id,
            )
            await self.broadcast(event)

    async def pause(self) -> None:
        """Pause the session."""
        async with self._lock:
            if self.status == SessionStatus.ACTIVE:
                self.status = SessionStatus.PAUSED
                await self._emit(SessionEvent.PAUSED, None)
                await self._broadcast_state()

    async def resume(self) -> None:
        """Resume the session."""
        async with self._lock:
            if self.status == SessionStatus.PAUSED:
                self.status = SessionStatus.ACTIVE
                await self._emit(SessionEvent.RESUMED, None)
                await self._broadcast_state()

    async def close(self) -> None:
        """Close the session."""
        async with self._lock:
            self.status = SessionStatus.COMPLETED
            await self._emit(SessionEvent.CLOSED, None)
            await self._broadcast_state()

    async def broadcast(self, event: Event) -> None:
        """Broadcast an event to all connected participants."""
        event.session_id = self.id
        message = event.to_json()

        for connection_id, send_fn in list(self._senders.items()):
            try:
                await send_fn(message)
            except Exception as e:
                logger.error(
                    f"Failed to send to {connection_id}: {e}"
                )
                # Remove dead connection
                user_id = self._connections.get(connection_id)
                if user_id:
                    await self.remove_participant(user_id)

    async def send_to_user(self, user_id: str, event: Event) -> None:
        """Send an event to a specific user."""
        event.session_id = self.id
        event.user_id = user_id
        message = event.to_json()

        participant = self._participants.get(user_id)
        if participant and participant.connection_id:
            send_fn = self._senders.get(participant.connection_id)
            if send_fn:
                try:
                    await send_fn(message)
                except Exception as e:
                    logger.error(f"Failed to send to {user_id}: {e}")

    async def send_caption(
        self,
        speaker_id: str,
        speaker_name: str,
        text: str,
        speaker_role: str = "agent",
        color: str = "#FFFFFF",
    ) -> None:
        """Send a caption to all participants."""
        caption = Caption(
            session_id=self.id,
            speaker_id=speaker_id,
            speaker_name=speaker_name,
            speaker_role=speaker_role,
            text=text,
            color=color,
        )
        await self.broadcast(caption)

    async def send_stage_update(
        self,
        image_url: str | None = None,
        artifact_id: str | None = None,
        artifact_type: str | None = None,
        artifact_data: dict | None = None,
        transition: str = "crossfade",
    ) -> None:
        """Send a stage update to all participants."""
        from .events import TransitionType

        update = StageUpdate(
            session_id=self.id,
            image_url=image_url,
            artifact_id=artifact_id,
            artifact_type=artifact_type,
            artifact_data=artifact_data,
            transition=TransitionType(transition),
        )
        await self.broadcast(update)

    def get_state(self) -> SessionState:
        """Get current session state."""
        return SessionState(
            session_id=self.id,
            status=self.status,
            participants=[p.to_dict() for p in self._participants.values()],
            agents=[a.to_dict() for a in self._agents.values()],
            topic=self.topic,
            context=self.context,
        )

    async def _broadcast_state(self) -> None:
        """Broadcast current session state to all participants."""
        await self.broadcast(self.get_state())

    def on(self, event: SessionEvent, callback: Callable) -> None:
        """Register a callback for a session event."""
        self._callbacks[event].append(callback)

    async def _emit(self, event: SessionEvent, data: Any) -> None:
        """Emit a session event to callbacks."""
        for callback in self._callbacks[event]:
            try:
                if asyncio.iscoroutinefunction(callback):
                    await callback(self, data)
                else:
                    callback(self, data)
            except Exception as e:
                logger.error(f"Callback error for {event}: {e}")

    @property
    def participant_count(self) -> int:
        """Get number of participants."""
        return len(self._participants)

    @property
    def is_active(self) -> bool:
        """Check if session is active."""
        return self.status == SessionStatus.ACTIVE

    def get_participant(self, user_id: str) -> Participant | None:
        """Get a participant by user ID."""
        return self._participants.get(user_id)

    def get_agent(self, agent_id: str) -> AgentInstance | None:
        """Get an agent by ID."""
        return self._agents.get(agent_id)

    def get_user_proxy(self, user_id: str) -> AgentInstance | None:
        """Get the proxy agent for a user."""
        for agent in self._agents.values():
            if agent.agent_type == "proxy" and agent.owner_id == user_id:
                return agent
        return None
