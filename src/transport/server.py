"""
WebSocket Transport Server.

FastAPI-based WebSocket server for real-time communication.
"""

import asyncio
import json
import logging
import uuid
from typing import Callable, Any

from .events import Event, EventType, PresenceEvent, PresenceType
from .session import TransportSession, SessionEvent

logger = logging.getLogger(__name__)


class TransportServer:
    """
    WebSocket server for the conversational theatre.

    Manages:
    - WebSocket connections
    - Session routing
    - Event dispatching
    - Connection lifecycle
    """

    def __init__(self):
        self._sessions: dict[str, TransportSession] = {}
        self._connection_sessions: dict[str, str] = {}  # conn_id -> session_id

        # Event handlers: EventType -> list of async handlers
        self._handlers: dict[EventType, list[Callable]] = {
            event_type: [] for event_type in EventType
        }

        # Connection handlers
        self._on_connect: list[Callable] = []
        self._on_disconnect: list[Callable] = []

    def create_session(
        self,
        session_id: str | None = None,
        host_user_id: str | None = None,
    ) -> TransportSession:
        """Create a new session."""
        session = TransportSession(
            session_id=session_id,
            host_user_id=host_user_id,
        )
        self._sessions[session.id] = session
        logger.info(f"Created session {session.id}")
        return session

    def get_session(self, session_id: str) -> TransportSession | None:
        """Get a session by ID."""
        return self._sessions.get(session_id)

    async def close_session(self, session_id: str) -> None:
        """Close and remove a session."""
        session = self._sessions.pop(session_id, None)
        if session:
            await session.close()
            logger.info(f"Closed session {session_id}")

    async def handle_connection(
        self,
        websocket: Any,
        session_id: str,
        user_id: str,
        proxy_id: str | None = None,
    ) -> None:
        """
        Handle a new WebSocket connection.

        Args:
            websocket: The WebSocket connection (framework-agnostic)
            session_id: Session to join
            user_id: User identifier
            proxy_id: Optional proxy to use
        """
        connection_id = f"conn_{uuid.uuid4().hex[:12]}"

        # Get or create session
        session = self._sessions.get(session_id)
        if not session:
            session = self.create_session(session_id)

        # Create send function
        async def send(message: str):
            await websocket.send_text(message)

        # Add participant
        await session.add_participant(
            user_id=user_id,
            proxy_id=proxy_id,
            connection_id=connection_id,
            send_fn=send,
        )

        self._connection_sessions[connection_id] = session_id

        # Notify connect handlers
        for handler in self._on_connect:
            try:
                await handler(session, user_id, connection_id)
            except Exception as e:
                logger.error(f"Connect handler error: {e}")

        try:
            # Message loop
            async for message in websocket.iter_text():
                await self._handle_message(
                    message, session, user_id, connection_id
                )

        except Exception as e:
            logger.error(f"Connection error: {e}")

        finally:
            # Clean up
            await session.remove_participant(user_id)
            self._connection_sessions.pop(connection_id, None)

            # Notify disconnect handlers
            for handler in self._on_disconnect:
                try:
                    await handler(session, user_id, connection_id)
                except Exception as e:
                    logger.error(f"Disconnect handler error: {e}")

    async def _handle_message(
        self,
        message: str,
        session: TransportSession,
        user_id: str,
        connection_id: str,
    ) -> None:
        """Handle an incoming WebSocket message."""
        try:
            data = json.loads(message)
            event = Event.from_dict(data)
            event.session_id = session.id
            event.user_id = user_id

            # Update participant activity
            participant = session.get_participant(user_id)
            if participant:
                from datetime import datetime
                participant.last_activity = datetime.utcnow()

            # Handle presence events
            if isinstance(event, PresenceEvent):
                await self._handle_presence(event, session, user_id)
                return

            # Dispatch to handlers
            handlers = self._handlers.get(event.type, [])
            for handler in handlers:
                try:
                    await handler(event, session, user_id)
                except Exception as e:
                    logger.error(
                        f"Handler error for {event.type}: {e}"
                    )

        except json.JSONDecodeError as e:
            logger.error(f"Invalid JSON: {e}")
        except Exception as e:
            logger.error(f"Message handling error: {e}")

    async def _handle_presence(
        self,
        event: PresenceEvent,
        session: TransportSession,
        user_id: str,
    ) -> None:
        """Handle presence events."""
        if event.presence_type == PresenceType.OBSERVE:
            await session.set_participant_status(user_id, "observing")

        elif event.presence_type == PresenceType.ENGAGE:
            await session.set_participant_status(user_id, "active")

        elif event.presence_type == PresenceType.AWAY:
            await session.set_participant_status(user_id, "away")
            # Pause session if all participants away
            all_away = all(
                p.status == "away"
                for p in session._participants.values()
            )
            if all_away:
                await session.pause()

        elif event.presence_type == PresenceType.LEAVE:
            await session.remove_participant(user_id)

    def on_event(self, event_type: EventType, handler: Callable) -> None:
        """Register a handler for an event type."""
        self._handlers[event_type].append(handler)

    def on_connect(self, handler: Callable) -> None:
        """Register a handler for new connections."""
        self._on_connect.append(handler)

    def on_disconnect(self, handler: Callable) -> None:
        """Register a handler for disconnections."""
        self._on_disconnect.append(handler)

    @property
    def session_count(self) -> int:
        """Get number of active sessions."""
        return len(self._sessions)

    @property
    def connection_count(self) -> int:
        """Get number of active connections."""
        return len(self._connection_sessions)


# FastAPI integration


def create_fastapi_app(server: TransportServer):
    """
    Create a FastAPI app with WebSocket routes.

    Usage:
        server = TransportServer()
        app = create_fastapi_app(server)
        uvicorn.run(app, host="0.0.0.0", port=8000)
    """
    try:
        from fastapi import FastAPI, WebSocket, WebSocketDisconnect, Query
        from fastapi.middleware.cors import CORSMiddleware
    except ImportError:
        raise ImportError(
            "FastAPI required. Install with: pip install fastapi uvicorn"
        )

    app = FastAPI(
        title="Soul Kiln Theatre",
        description="Conversational theatre WebSocket server",
        version="1.0.0",
    )

    # CORS for mobile apps
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    @app.websocket("/ws/{session_id}")
    async def websocket_endpoint(
        websocket: WebSocket,
        session_id: str,
        user_id: str = Query(...),
        proxy_id: str | None = Query(None),
    ):
        await websocket.accept()
        await server.handle_connection(
            websocket=websocket,
            session_id=session_id,
            user_id=user_id,
            proxy_id=proxy_id,
        )

    @app.get("/sessions")
    async def list_sessions():
        return {
            "sessions": [
                {
                    "id": s.id,
                    "status": s.status.value,
                    "participants": s.participant_count,
                }
                for s in server._sessions.values()
            ]
        }

    @app.get("/sessions/{session_id}")
    async def get_session(session_id: str):
        session = server.get_session(session_id)
        if not session:
            from fastapi import HTTPException
            raise HTTPException(status_code=404, detail="Session not found")
        return session.get_state().to_dict()

    @app.post("/sessions")
    async def create_session(host_user_id: str | None = None):
        session = server.create_session(host_user_id=host_user_id)
        return {"session_id": session.id}

    @app.delete("/sessions/{session_id}")
    async def delete_session(session_id: str):
        await server.close_session(session_id)
        return {"status": "closed"}

    @app.get("/health")
    async def health():
        return {
            "status": "healthy",
            "sessions": server.session_count,
            "connections": server.connection_count,
        }

    return app


def create_server() -> TransportServer:
    """Create a new transport server instance."""
    return TransportServer()
