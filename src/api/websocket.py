"""
WebSocket server for Theatre.

Bridges Theatre backend to web clients via WebSocket.
Embeddable anywhere - web pages, iframes, widgets.
"""

import asyncio
import json
import logging
import uuid
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any

from pathlib import Path

from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles

from ..theatre.orchestrator import (
    TheatreOrchestrator,
    TheatreState,
    ConversationTurn,
    get_orchestrator,
)

logger = logging.getLogger(__name__)


# =============================================================================
# CONNECTION MANAGEMENT
# =============================================================================


@dataclass
class Connection:
    """A connected WebSocket client."""

    connection_id: str
    websocket: WebSocket
    session_id: str | None = None
    human_id: str | None = None
    connected_at: datetime = field(default_factory=datetime.utcnow)


class ConnectionManager:
    """Manages WebSocket connections and sessions."""

    def __init__(self):
        self._connections: dict[str, Connection] = {}
        self._sessions: dict[str, TheatreOrchestrator] = {}
        self._session_connections: dict[str, set[str]] = {}  # session_id -> connection_ids

    async def connect(self, websocket: WebSocket) -> Connection:
        """Accept a new WebSocket connection."""
        await websocket.accept()
        connection_id = f"conn_{uuid.uuid4().hex[:12]}"
        connection = Connection(
            connection_id=connection_id,
            websocket=websocket,
        )
        self._connections[connection_id] = connection
        logger.info(f"Client connected: {connection_id}")
        return connection

    def disconnect(self, connection_id: str) -> None:
        """Handle client disconnect."""
        if connection_id in self._connections:
            conn = self._connections[connection_id]
            # Remove from session if in one
            if conn.session_id and conn.session_id in self._session_connections:
                self._session_connections[conn.session_id].discard(connection_id)
            del self._connections[connection_id]
            logger.info(f"Client disconnected: {connection_id}")

    def join_session(
        self,
        connection_id: str,
        session_id: str,
        orchestrator: TheatreOrchestrator,
    ) -> None:
        """Add a connection to a session."""
        if connection_id in self._connections:
            self._connections[connection_id].session_id = session_id

        if session_id not in self._session_connections:
            self._session_connections[session_id] = set()
        self._session_connections[session_id].add(connection_id)

        self._sessions[session_id] = orchestrator

    def get_orchestrator(self, session_id: str) -> TheatreOrchestrator | None:
        """Get orchestrator for a session."""
        return self._sessions.get(session_id)

    async def send_to_connection(
        self,
        connection_id: str,
        message: dict,
    ) -> None:
        """Send message to a specific connection."""
        if connection_id in self._connections:
            try:
                await self._connections[connection_id].websocket.send_json(message)
            except Exception as e:
                logger.error(f"Error sending to {connection_id}: {e}")

    async def broadcast_to_session(
        self,
        session_id: str,
        message: dict,
    ) -> None:
        """Broadcast message to all connections in a session."""
        if session_id in self._session_connections:
            for conn_id in self._session_connections[session_id]:
                await self.send_to_connection(conn_id, message)


# Global connection manager
manager = ConnectionManager()


# =============================================================================
# FASTAPI APP
# =============================================================================


app = FastAPI(
    title="Soul Kiln Theatre",
    description="WebSocket API for theatrical agent conversations",
    version="1.0.0",
)

# CORS for embedding anywhere
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allow all for embeddability
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Static files for embeddable client
STATIC_DIR = Path(__file__).parent / "static"
if STATIC_DIR.exists():
    app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")


# =============================================================================
# WEBSOCKET HANDLERS
# =============================================================================


@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """Main WebSocket endpoint for theatre connections."""
    connection = await manager.connect(websocket)

    try:
        # Send welcome message
        await manager.send_to_connection(
            connection.connection_id,
            {
                "type": "connected",
                "connection_id": connection.connection_id,
                "timestamp": datetime.utcnow().isoformat(),
            },
        )

        # Listen for messages
        while True:
            data = await websocket.receive_json()
            await handle_message(connection, data)

    except WebSocketDisconnect:
        manager.disconnect(connection.connection_id)
    except Exception as e:
        logger.error(f"WebSocket error: {e}")
        manager.disconnect(connection.connection_id)


async def handle_message(connection: Connection, data: dict) -> None:
    """Route incoming WebSocket messages."""
    msg_type = data.get("type", "")

    handlers = {
        "start_session": handle_start_session,
        "join_session": handle_join_session,
        "user_input": handle_user_input,
        "end_session": handle_end_session,
        "ping": handle_ping,
    }

    handler = handlers.get(msg_type)
    if handler:
        await handler(connection, data)
    else:
        await manager.send_to_connection(
            connection.connection_id,
            {"type": "error", "error": f"Unknown message type: {msg_type}"},
        )


async def handle_start_session(connection: Connection, data: dict) -> None:
    """Handle start_session request."""
    human_id = data.get("human_id")
    community = data.get("community")
    organization_context = data.get("organization_context", {})

    # Create orchestrator with async turn callback
    orchestrator = TheatreOrchestrator()

    # Wire up callbacks
    def on_turn(turn: ConversationTurn):
        asyncio.create_task(
            broadcast_turn(orchestrator, turn)
        )

    def on_state(state: TheatreState):
        asyncio.create_task(
            broadcast_state(orchestrator, state)
        )

    orchestrator.on_turn(on_turn)
    orchestrator.on_state_change(on_state)

    # Store orchestrator reference for broadcasts
    orchestrator._connection_session_id = None  # Will be set below

    # Start session
    context = orchestrator.start_session(
        human_id=human_id,
        community=community,
        organization_context=organization_context,
    )

    orchestrator._connection_session_id = context.session_id

    # Join connection to session
    connection.human_id = human_id
    manager.join_session(connection.connection_id, context.session_id, orchestrator)

    # Send session started confirmation
    await manager.send_to_connection(
        connection.connection_id,
        {
            "type": "session_started",
            "session_id": context.session_id,
            "human_id": human_id,
            "community": community,
            "timestamp": datetime.utcnow().isoformat(),
        },
    )


async def handle_join_session(connection: Connection, data: dict) -> None:
    """Handle join_session request (join existing session)."""
    session_id = data.get("session_id")
    human_id = data.get("human_id")

    orchestrator = manager.get_orchestrator(session_id)
    if not orchestrator:
        await manager.send_to_connection(
            connection.connection_id,
            {"type": "error", "error": f"Session not found: {session_id}"},
        )
        return

    connection.human_id = human_id
    manager.join_session(connection.connection_id, session_id, orchestrator)

    # Send current state
    await manager.send_to_connection(
        connection.connection_id,
        {
            "type": "session_joined",
            "session_id": session_id,
            "state": orchestrator.state.value,
            "context": orchestrator.context.to_dict() if orchestrator.context else None,
            "timestamp": datetime.utcnow().isoformat(),
        },
    )


async def handle_user_input(connection: Connection, data: dict) -> None:
    """Handle user_input message."""
    if not connection.session_id:
        await manager.send_to_connection(
            connection.connection_id,
            {"type": "error", "error": "Not in a session"},
        )
        return

    orchestrator = manager.get_orchestrator(connection.session_id)
    if not orchestrator:
        await manager.send_to_connection(
            connection.connection_id,
            {"type": "error", "error": "Session not found"},
        )
        return

    user_input = data.get("content", "")
    audio_data = data.get("audio")  # Base64 encoded if present

    # Process input (turns will be broadcast via callbacks)
    turns = orchestrator.process_user_input(
        user_input=user_input,
        audio_data=audio_data.encode() if audio_data else None,
    )

    # Also send confirmation
    await manager.send_to_connection(
        connection.connection_id,
        {
            "type": "input_received",
            "turn_count": len(turns),
            "timestamp": datetime.utcnow().isoformat(),
        },
    )


async def handle_end_session(connection: Connection, data: dict) -> None:
    """Handle end_session request."""
    if not connection.session_id:
        return

    orchestrator = manager.get_orchestrator(connection.session_id)
    if orchestrator:
        summary = orchestrator.end_session()

        await manager.broadcast_to_session(
            connection.session_id,
            {
                "type": "session_ended",
                "session_id": connection.session_id,
                "summary": summary,
                "timestamp": datetime.utcnow().isoformat(),
            },
        )


async def handle_ping(connection: Connection, data: dict) -> None:
    """Handle ping/keepalive."""
    await manager.send_to_connection(
        connection.connection_id,
        {
            "type": "pong",
            "timestamp": datetime.utcnow().isoformat(),
        },
    )


# =============================================================================
# BROADCAST HELPERS
# =============================================================================


async def broadcast_turn(orchestrator: TheatreOrchestrator, turn: ConversationTurn) -> None:
    """Broadcast a conversation turn to all session clients."""
    session_id = getattr(orchestrator, '_connection_session_id', None)
    if session_id:
        await manager.broadcast_to_session(
            session_id,
            {
                "type": "turn",
                "turn": turn.to_dict(),
                "timestamp": datetime.utcnow().isoformat(),
            },
        )


async def broadcast_state(orchestrator: TheatreOrchestrator, state: TheatreState) -> None:
    """Broadcast state change to all session clients."""
    session_id = getattr(orchestrator, '_connection_session_id', None)
    if session_id:
        await manager.broadcast_to_session(
            session_id,
            {
                "type": "state_change",
                "state": state.value,
                "timestamp": datetime.utcnow().isoformat(),
            },
        )


# =============================================================================
# HTTP ENDPOINTS (for health checks, etc.)
# =============================================================================


@app.get("/health")
async def health():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "connections": len(manager._connections),
        "sessions": len(manager._sessions),
    }


@app.get("/")
async def root():
    """Root endpoint - serves demo page."""
    index_path = STATIC_DIR / "index.html"
    if index_path.exists():
        return HTMLResponse(content=index_path.read_text())
    return {
        "service": "Soul Kiln Theatre",
        "websocket": "/ws",
        "docs": "/docs",
    }


# =============================================================================
# RUN SERVER
# =============================================================================


def run_server(host: str = "0.0.0.0", port: int = 8000):
    """Run the WebSocket server."""
    import uvicorn
    uvicorn.run(app, host=host, port=port)


if __name__ == "__main__":
    run_server()
