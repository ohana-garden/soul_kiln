"""
Agent-to-Agent Chat System.

Provides structured communication between agents.
"""

import logging
import threading
import uuid
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Callable

logger = logging.getLogger(__name__)


class MessageType(str, Enum):
    """Types of chat messages."""

    TEXT = "text"
    REQUEST = "request"
    RESPONSE = "response"
    BROADCAST = "broadcast"
    SYSTEM = "system"


class MessagePriority(str, Enum):
    """Message priority levels."""

    LOW = "low"
    NORMAL = "normal"
    HIGH = "high"
    URGENT = "urgent"


@dataclass
class ChatMessage:
    """A message in agent-to-agent communication."""

    id: str = field(default_factory=lambda: f"msg_{uuid.uuid4().hex[:12]}")
    sender_id: str = ""
    recipient_id: str | None = None  # None for broadcast
    room_id: str | None = None
    content: str = ""
    message_type: MessageType = MessageType.TEXT
    priority: MessagePriority = MessagePriority.NORMAL
    reply_to: str | None = None
    metadata: dict = field(default_factory=dict)
    created_at: datetime = field(default_factory=datetime.utcnow)
    read_at: datetime | None = None
    read_by: list[str] = field(default_factory=list)

    def to_dict(self) -> dict:
        """Convert to dictionary."""
        return {
            "id": self.id,
            "sender_id": self.sender_id,
            "recipient_id": self.recipient_id,
            "room_id": self.room_id,
            "content": self.content,
            "message_type": self.message_type.value,
            "priority": self.priority.value,
            "reply_to": self.reply_to,
            "metadata": self.metadata,
            "created_at": self.created_at.isoformat(),
            "read_at": self.read_at.isoformat() if self.read_at else None,
            "read_by": self.read_by,
        }


@dataclass
class ChatRoom:
    """A chat room for agent communication."""

    id: str = field(default_factory=lambda: f"room_{uuid.uuid4().hex[:8]}")
    name: str = ""
    description: str = ""
    members: list[str] = field(default_factory=list)
    created_by: str = ""
    created_at: datetime = field(default_factory=datetime.utcnow)
    is_private: bool = False
    metadata: dict = field(default_factory=dict)

    def to_dict(self) -> dict:
        """Convert to dictionary."""
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "members": self.members,
            "created_by": self.created_by,
            "created_at": self.created_at.isoformat(),
            "is_private": self.is_private,
        }


class A2AChat:
    """
    Agent-to-Agent Chat System.

    Features:
    - Direct messaging between agents
    - Chat rooms for group communication
    - Message prioritization
    - Request/response patterns
    - Message history and search
    """

    def __init__(
        self,
        max_history: int = 10000,
        message_callback: Callable[[ChatMessage], None] | None = None,
    ):
        """
        Initialize A2A chat system.

        Args:
            max_history: Maximum message history to keep
            message_callback: Optional callback for new messages
        """
        self._messages: dict[str, ChatMessage] = {}
        self._rooms: dict[str, ChatRoom] = {}
        self._agent_messages: dict[str, list[str]] = {}  # agent_id -> message_ids
        self._room_messages: dict[str, list[str]] = {}  # room_id -> message_ids
        self._max_history = max_history
        self._callback = message_callback
        self._lock = threading.RLock()
        self._subscribers: dict[str, list[Callable]] = {}  # agent_id -> callbacks

    def send_message(
        self,
        sender_id: str,
        content: str,
        recipient_id: str | None = None,
        room_id: str | None = None,
        message_type: MessageType = MessageType.TEXT,
        priority: MessagePriority = MessagePriority.NORMAL,
        reply_to: str | None = None,
        metadata: dict | None = None,
    ) -> ChatMessage:
        """
        Send a message.

        Args:
            sender_id: Sending agent ID
            content: Message content
            recipient_id: Optional direct recipient
            room_id: Optional room ID
            message_type: Type of message
            priority: Message priority
            reply_to: Optional message ID to reply to
            metadata: Additional metadata

        Returns:
            Created ChatMessage
        """
        message = ChatMessage(
            sender_id=sender_id,
            recipient_id=recipient_id,
            room_id=room_id,
            content=content,
            message_type=message_type,
            priority=priority,
            reply_to=reply_to,
            metadata=metadata or {},
        )

        with self._lock:
            self._messages[message.id] = message

            # Track by sender
            if sender_id not in self._agent_messages:
                self._agent_messages[sender_id] = []
            self._agent_messages[sender_id].append(message.id)

            # Track by room
            if room_id:
                if room_id not in self._room_messages:
                    self._room_messages[room_id] = []
                self._room_messages[room_id].append(message.id)

            # Notify subscribers
            self._notify_subscribers(message)

        # Callback
        if self._callback:
            try:
                self._callback(message)
            except Exception as e:
                logger.error(f"Message callback error: {e}")

        logger.debug(f"Message {message.id} sent from {sender_id}")
        return message

    def send_request(
        self,
        sender_id: str,
        recipient_id: str,
        request: str,
        timeout_seconds: float = 30.0,
        metadata: dict | None = None,
    ) -> ChatMessage | None:
        """
        Send a request and wait for response.

        Args:
            sender_id: Requesting agent
            recipient_id: Target agent
            request: Request content
            timeout_seconds: Wait timeout
            metadata: Additional metadata

        Returns:
            Response message or None if timeout
        """
        request_msg = self.send_message(
            sender_id=sender_id,
            recipient_id=recipient_id,
            content=request,
            message_type=MessageType.REQUEST,
            priority=MessagePriority.HIGH,
            metadata=metadata,
        )

        # Wait for response
        import time

        start = time.time()
        while time.time() - start < timeout_seconds:
            response = self._find_response(request_msg.id, recipient_id)
            if response:
                return response
            time.sleep(0.1)

        logger.warning(f"Request {request_msg.id} timed out")
        return None

    def send_response(
        self,
        sender_id: str,
        request_id: str,
        response: str,
        metadata: dict | None = None,
    ) -> ChatMessage:
        """
        Send a response to a request.

        Args:
            sender_id: Responding agent
            request_id: Original request message ID
            response: Response content
            metadata: Additional metadata

        Returns:
            Response message
        """
        request_msg = self._messages.get(request_id)
        if not request_msg:
            raise ValueError(f"Request not found: {request_id}")

        return self.send_message(
            sender_id=sender_id,
            recipient_id=request_msg.sender_id,
            content=response,
            message_type=MessageType.RESPONSE,
            reply_to=request_id,
            metadata=metadata,
        )

    def broadcast(
        self,
        sender_id: str,
        room_id: str,
        content: str,
        priority: MessagePriority = MessagePriority.NORMAL,
        metadata: dict | None = None,
    ) -> ChatMessage:
        """
        Broadcast a message to a room.

        Args:
            sender_id: Sending agent
            room_id: Target room
            content: Message content
            priority: Message priority
            metadata: Additional metadata

        Returns:
            Broadcast message
        """
        room = self._rooms.get(room_id)
        if not room:
            raise ValueError(f"Room not found: {room_id}")

        if sender_id not in room.members:
            raise ValueError(f"Agent {sender_id} is not a member of room {room_id}")

        return self.send_message(
            sender_id=sender_id,
            room_id=room_id,
            content=content,
            message_type=MessageType.BROADCAST,
            priority=priority,
            metadata=metadata,
        )

    def _find_response(self, request_id: str, from_agent: str) -> ChatMessage | None:
        """Find response to a request."""
        with self._lock:
            for msg in self._messages.values():
                if (
                    msg.reply_to == request_id
                    and msg.sender_id == from_agent
                    and msg.message_type == MessageType.RESPONSE
                ):
                    return msg
        return None

    def _notify_subscribers(self, message: ChatMessage) -> None:
        """Notify subscribers of a new message."""
        targets = []

        if message.recipient_id:
            targets.append(message.recipient_id)

        if message.room_id:
            room = self._rooms.get(message.room_id)
            if room:
                targets.extend(room.members)

        for agent_id in set(targets):
            if agent_id in self._subscribers:
                for callback in self._subscribers[agent_id]:
                    try:
                        callback(message)
                    except Exception as e:
                        logger.error(f"Subscriber callback error: {e}")

    def subscribe(self, agent_id: str, callback: Callable[[ChatMessage], None]) -> None:
        """Subscribe an agent to message notifications."""
        if agent_id not in self._subscribers:
            self._subscribers[agent_id] = []
        self._subscribers[agent_id].append(callback)

    def unsubscribe(self, agent_id: str, callback: Callable[[ChatMessage], None]) -> None:
        """Unsubscribe from notifications."""
        if agent_id in self._subscribers:
            self._subscribers[agent_id] = [
                cb for cb in self._subscribers[agent_id] if cb != callback
            ]

    def create_room(
        self,
        name: str,
        creator_id: str,
        members: list[str] | None = None,
        description: str = "",
        is_private: bool = False,
    ) -> ChatRoom:
        """Create a chat room."""
        room = ChatRoom(
            name=name,
            description=description,
            members=members or [creator_id],
            created_by=creator_id,
            is_private=is_private,
        )

        if creator_id not in room.members:
            room.members.append(creator_id)

        with self._lock:
            self._rooms[room.id] = room

        logger.info(f"Created room {room.id}: {name}")
        return room

    def join_room(self, room_id: str, agent_id: str) -> bool:
        """Join a chat room."""
        room = self._rooms.get(room_id)
        if not room:
            return False

        if room.is_private:
            logger.warning(f"Agent {agent_id} cannot join private room {room_id}")
            return False

        if agent_id not in room.members:
            room.members.append(agent_id)

        return True

    def leave_room(self, room_id: str, agent_id: str) -> bool:
        """Leave a chat room."""
        room = self._rooms.get(room_id)
        if not room:
            return False

        if agent_id in room.members:
            room.members.remove(agent_id)

        return True

    def get_room(self, room_id: str) -> ChatRoom | None:
        """Get a room by ID."""
        return self._rooms.get(room_id)

    def list_rooms(self, agent_id: str | None = None) -> list[ChatRoom]:
        """List rooms, optionally filtered by membership."""
        rooms = list(self._rooms.values())
        if agent_id:
            rooms = [r for r in rooms if agent_id in r.members or not r.is_private]
        return rooms

    def get_messages(
        self,
        agent_id: str | None = None,
        room_id: str | None = None,
        since: datetime | None = None,
        limit: int = 100,
    ) -> list[ChatMessage]:
        """Get messages with optional filters."""
        with self._lock:
            messages = list(self._messages.values())

            if agent_id:
                messages = [
                    m
                    for m in messages
                    if m.sender_id == agent_id or m.recipient_id == agent_id
                ]

            if room_id:
                messages = [m for m in messages if m.room_id == room_id]

            if since:
                messages = [m for m in messages if m.created_at >= since]

            messages.sort(key=lambda m: m.created_at, reverse=True)
            return messages[:limit]

    def get_unread(self, agent_id: str) -> list[ChatMessage]:
        """Get unread messages for an agent."""
        with self._lock:
            messages = []
            for msg in self._messages.values():
                if msg.sender_id == agent_id:
                    continue
                if msg.recipient_id == agent_id and agent_id not in msg.read_by:
                    messages.append(msg)
                elif msg.room_id:
                    room = self._rooms.get(msg.room_id)
                    if room and agent_id in room.members and agent_id not in msg.read_by:
                        messages.append(msg)

            messages.sort(key=lambda m: m.created_at)
            return messages

    def mark_read(self, message_id: str, agent_id: str) -> bool:
        """Mark a message as read."""
        msg = self._messages.get(message_id)
        if not msg:
            return False

        if agent_id not in msg.read_by:
            msg.read_by.append(agent_id)
            if msg.read_at is None:
                msg.read_at = datetime.utcnow()

        return True

    def search_messages(
        self,
        query: str,
        agent_id: str | None = None,
        room_id: str | None = None,
        limit: int = 50,
    ) -> list[ChatMessage]:
        """Search messages by content."""
        with self._lock:
            results = []
            query_lower = query.lower()

            for msg in self._messages.values():
                if query_lower not in msg.content.lower():
                    continue
                if agent_id and msg.sender_id != agent_id and msg.recipient_id != agent_id:
                    continue
                if room_id and msg.room_id != room_id:
                    continue
                results.append(msg)

            results.sort(key=lambda m: m.created_at, reverse=True)
            return results[:limit]

    def get_stats(self) -> dict:
        """Get chat statistics."""
        with self._lock:
            type_counts = {}
            for msg in self._messages.values():
                t = msg.message_type.value
                type_counts[t] = type_counts.get(t, 0) + 1

            return {
                "total_messages": len(self._messages),
                "total_rooms": len(self._rooms),
                "by_type": type_counts,
                "active_subscribers": len(self._subscribers),
            }

    def cleanup(self, max_age_seconds: int = 86400) -> int:
        """Clean up old messages."""
        now = datetime.utcnow()
        cleaned = 0

        with self._lock:
            to_remove = []
            for msg_id, msg in self._messages.items():
                age = (now - msg.created_at).total_seconds()
                if age > max_age_seconds:
                    to_remove.append(msg_id)

            for msg_id in to_remove:
                del self._messages[msg_id]
                cleaned += 1

        return cleaned
