"""
Session Management with Pause/Resume.

Provides session lifecycle management with pause, resume,
and automatic timeout handling.
"""

import logging
import threading
import time
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from typing import Any, Callable

logger = logging.getLogger(__name__)


class SessionState(str, Enum):
    """State of a session."""

    CREATED = "created"
    ACTIVE = "active"
    PAUSED = "paused"
    SUSPENDED = "suspended"
    COMPLETED = "completed"
    FAILED = "failed"
    EXPIRED = "expired"


@dataclass
class Session:
    """A managed session with pause/resume support."""

    id: str = field(default_factory=lambda: f"sess_{uuid.uuid4().hex[:12]}")
    name: str = ""
    state: SessionState = SessionState.CREATED
    owner_id: str | None = None
    created_at: datetime = field(default_factory=datetime.utcnow)
    last_activity: datetime = field(default_factory=datetime.utcnow)
    paused_at: datetime | None = None
    resume_at: datetime | None = None  # Auto-resume time
    expires_at: datetime | None = None
    data: dict = field(default_factory=dict)
    metadata: dict = field(default_factory=dict)
    pause_count: int = 0
    resume_count: int = 0

    def __post_init__(self):
        self._lock = threading.RLock()
        self._callbacks: dict[str, list[Callable]] = {
            "on_pause": [],
            "on_resume": [],
            "on_expire": [],
            "on_state_change": [],
        }

    def activate(self) -> None:
        """Activate the session."""
        with self._lock:
            if self.state == SessionState.CREATED:
                self._set_state(SessionState.ACTIVE)

    def pause(self, duration_seconds: int | None = None, reason: str = "") -> None:
        """
        Pause the session.

        Args:
            duration_seconds: Optional auto-resume duration
            reason: Reason for pause
        """
        with self._lock:
            if self.state != SessionState.ACTIVE:
                return

            self._set_state(SessionState.PAUSED)
            self.paused_at = datetime.utcnow()
            self.pause_count += 1

            if duration_seconds:
                self.resume_at = datetime.utcnow() + timedelta(seconds=duration_seconds)

            if reason:
                self.metadata["pause_reason"] = reason

            for callback in self._callbacks["on_pause"]:
                try:
                    callback(self, reason)
                except Exception as e:
                    logger.error(f"Pause callback error: {e}")

            logger.debug(f"Session {self.id} paused")

    def resume(self) -> None:
        """Resume a paused session."""
        with self._lock:
            if self.state != SessionState.PAUSED:
                return

            self._set_state(SessionState.ACTIVE)
            self.paused_at = None
            self.resume_at = None
            self.resume_count += 1
            self.update_activity()

            for callback in self._callbacks["on_resume"]:
                try:
                    callback(self)
                except Exception as e:
                    logger.error(f"Resume callback error: {e}")

            logger.debug(f"Session {self.id} resumed")

    def suspend(self) -> None:
        """Suspend the session (longer-term pause)."""
        with self._lock:
            if self.state in (SessionState.COMPLETED, SessionState.FAILED):
                return
            self._set_state(SessionState.SUSPENDED)
            self.paused_at = datetime.utcnow()

    def complete(self, result: Any = None) -> None:
        """Mark session as completed."""
        with self._lock:
            self._set_state(SessionState.COMPLETED)
            if result is not None:
                self.data["result"] = result

    def fail(self, error: str) -> None:
        """Mark session as failed."""
        with self._lock:
            self._set_state(SessionState.FAILED)
            self.data["error"] = error

    def expire(self) -> None:
        """Mark session as expired."""
        with self._lock:
            self._set_state(SessionState.EXPIRED)

            for callback in self._callbacks["on_expire"]:
                try:
                    callback(self)
                except Exception as e:
                    logger.error(f"Expire callback error: {e}")

    def _set_state(self, new_state: SessionState) -> None:
        """Set state with callbacks."""
        old_state = self.state
        self.state = new_state
        self.update_activity()

        for callback in self._callbacks["on_state_change"]:
            try:
                callback(self, old_state, new_state)
            except Exception as e:
                logger.error(f"State change callback error: {e}")

    def update_activity(self) -> None:
        """Update last activity timestamp."""
        self.last_activity = datetime.utcnow()

    def should_auto_resume(self) -> bool:
        """Check if session should auto-resume."""
        if self.state != SessionState.PAUSED:
            return False
        if self.resume_at is None:
            return False
        return datetime.utcnow() >= self.resume_at

    def is_expired(self) -> bool:
        """Check if session has expired."""
        if self.expires_at is None:
            return False
        return datetime.utcnow() >= self.expires_at

    def is_active(self) -> bool:
        """Check if session is active."""
        return self.state == SessionState.ACTIVE

    def is_paused(self) -> bool:
        """Check if session is paused."""
        return self.state in (SessionState.PAUSED, SessionState.SUSPENDED)

    def is_terminal(self) -> bool:
        """Check if session is in terminal state."""
        return self.state in (
            SessionState.COMPLETED,
            SessionState.FAILED,
            SessionState.EXPIRED,
        )

    @property
    def pause_duration_seconds(self) -> float | None:
        """Get how long session has been paused."""
        if self.paused_at and self.state == SessionState.PAUSED:
            return (datetime.utcnow() - self.paused_at).total_seconds()
        return None

    @property
    def age_seconds(self) -> float:
        """Get session age in seconds."""
        return (datetime.utcnow() - self.created_at).total_seconds()

    @property
    def idle_seconds(self) -> float:
        """Get time since last activity."""
        return (datetime.utcnow() - self.last_activity).total_seconds()

    def register_callback(self, event: str, callback: Callable) -> None:
        """Register a callback for session events."""
        if event in self._callbacks:
            self._callbacks[event].append(callback)

    def to_dict(self) -> dict:
        """Convert to dictionary."""
        return {
            "id": self.id,
            "name": self.name,
            "state": self.state.value,
            "owner_id": self.owner_id,
            "created_at": self.created_at.isoformat(),
            "last_activity": self.last_activity.isoformat(),
            "paused_at": self.paused_at.isoformat() if self.paused_at else None,
            "resume_at": self.resume_at.isoformat() if self.resume_at else None,
            "expires_at": self.expires_at.isoformat() if self.expires_at else None,
            "pause_count": self.pause_count,
            "resume_count": self.resume_count,
            "age_seconds": self.age_seconds,
            "idle_seconds": self.idle_seconds,
        }


class SessionManager:
    """
    Manages multiple sessions with lifecycle control.

    Features:
    - Session creation and tracking
    - Pause/resume with auto-resume
    - Expiration handling
    - Background maintenance
    """

    def __init__(
        self,
        default_timeout: int = 3600,
        auto_resume_check_interval: int = 60,
        auto_start: bool = True,
    ):
        """
        Initialize session manager.

        Args:
            default_timeout: Default session timeout in seconds
            auto_resume_check_interval: Interval for auto-resume checks
            auto_start: Start background maintenance automatically
        """
        self._sessions: dict[str, Session] = {}
        self._owner_sessions: dict[str, list[str]] = {}
        self._default_timeout = default_timeout
        self._check_interval = auto_resume_check_interval
        self._running = False
        self._thread: threading.Thread | None = None
        self._lock = threading.RLock()
        self._global_callbacks: dict[str, list[Callable]] = {
            "on_session_create": [],
            "on_session_end": [],
        }

        if auto_start:
            self.start()

    def start(self) -> None:
        """Start background maintenance."""
        if self._running:
            return

        self._running = True
        self._thread = threading.Thread(target=self._maintenance_loop, daemon=True)
        self._thread.start()
        logger.info("SessionManager started")

    def stop(self) -> None:
        """Stop background maintenance."""
        self._running = False
        if self._thread:
            self._thread.join(timeout=5)
            self._thread = None
        logger.info("SessionManager stopped")

    def create_session(
        self,
        name: str = "",
        owner_id: str | None = None,
        timeout_seconds: int | None = None,
        data: dict | None = None,
        auto_activate: bool = True,
    ) -> Session:
        """
        Create a new session.

        Args:
            name: Session name
            owner_id: Owner identifier
            timeout_seconds: Session timeout
            data: Initial session data
            auto_activate: Automatically activate session

        Returns:
            Created Session
        """
        timeout = timeout_seconds or self._default_timeout

        session = Session(
            name=name,
            owner_id=owner_id,
            expires_at=datetime.utcnow() + timedelta(seconds=timeout),
            data=data or {},
        )

        with self._lock:
            self._sessions[session.id] = session
            if owner_id:
                if owner_id not in self._owner_sessions:
                    self._owner_sessions[owner_id] = []
                self._owner_sessions[owner_id].append(session.id)

        if auto_activate:
            session.activate()

        # Fire callbacks
        for callback in self._global_callbacks["on_session_create"]:
            try:
                callback(session)
            except Exception as e:
                logger.error(f"Create callback error: {e}")

        logger.debug(f"Created session {session.id}")
        return session

    def get_session(self, session_id: str) -> Session | None:
        """Get a session by ID."""
        return self._sessions.get(session_id)

    def get_sessions_for_owner(self, owner_id: str) -> list[Session]:
        """Get all sessions for an owner."""
        session_ids = self._owner_sessions.get(owner_id, [])
        return [self._sessions[sid] for sid in session_ids if sid in self._sessions]

    def pause_session(
        self,
        session_id: str,
        duration_seconds: int | None = None,
        reason: str = "",
    ) -> bool:
        """Pause a session."""
        session = self._sessions.get(session_id)
        if not session:
            return False

        session.pause(duration_seconds, reason)
        return True

    def resume_session(self, session_id: str) -> bool:
        """Resume a session."""
        session = self._sessions.get(session_id)
        if not session:
            return False

        session.resume()
        return True

    def end_session(self, session_id: str, result: Any = None) -> bool:
        """End a session."""
        session = self._sessions.get(session_id)
        if not session:
            return False

        session.complete(result)
        self._on_session_end(session)
        return True

    def fail_session(self, session_id: str, error: str) -> bool:
        """Fail a session."""
        session = self._sessions.get(session_id)
        if not session:
            return False

        session.fail(error)
        self._on_session_end(session)
        return True

    def _on_session_end(self, session: Session) -> None:
        """Handle session end."""
        for callback in self._global_callbacks["on_session_end"]:
            try:
                callback(session)
            except Exception as e:
                logger.error(f"End callback error: {e}")

    def extend_session(self, session_id: str, additional_seconds: int) -> bool:
        """Extend a session's expiration."""
        session = self._sessions.get(session_id)
        if not session:
            return False

        if session.expires_at:
            session.expires_at += timedelta(seconds=additional_seconds)
        else:
            session.expires_at = datetime.utcnow() + timedelta(seconds=additional_seconds)

        return True

    def touch_session(self, session_id: str) -> bool:
        """Update session activity timestamp."""
        session = self._sessions.get(session_id)
        if not session:
            return False

        session.update_activity()
        return True

    def _maintenance_loop(self) -> None:
        """Background maintenance loop."""
        while self._running:
            try:
                self._process_auto_resumes()
                self._process_expirations()
            except Exception as e:
                logger.error(f"Maintenance error: {e}")

            time.sleep(self._check_interval)

    def _process_auto_resumes(self) -> None:
        """Process auto-resume for paused sessions."""
        with self._lock:
            for session in self._sessions.values():
                if session.should_auto_resume():
                    session.resume()

    def _process_expirations(self) -> None:
        """Process expired sessions."""
        with self._lock:
            for session in self._sessions.values():
                if not session.is_terminal() and session.is_expired():
                    session.expire()
                    self._on_session_end(session)

    def get_active_sessions(self) -> list[Session]:
        """Get all active sessions."""
        return [s for s in self._sessions.values() if s.is_active()]

    def get_paused_sessions(self) -> list[Session]:
        """Get all paused sessions."""
        return [s for s in self._sessions.values() if s.is_paused()]

    def cleanup_ended(self, max_age_seconds: int = 3600) -> int:
        """Clean up ended sessions older than max_age."""
        now = datetime.utcnow()
        cleaned = 0

        with self._lock:
            to_remove = []
            for session_id, session in self._sessions.items():
                if session.is_terminal():
                    age = (now - session.last_activity).total_seconds()
                    if age > max_age_seconds:
                        to_remove.append(session_id)

            for session_id in to_remove:
                session = self._sessions.pop(session_id)
                if session.owner_id and session.owner_id in self._owner_sessions:
                    self._owner_sessions[session.owner_id] = [
                        sid
                        for sid in self._owner_sessions[session.owner_id]
                        if sid != session_id
                    ]
                cleaned += 1

        return cleaned

    def register_callback(self, event: str, callback: Callable) -> None:
        """Register a global callback."""
        if event in self._global_callbacks:
            self._global_callbacks[event].append(callback)

    def get_stats(self) -> dict:
        """Get session statistics."""
        with self._lock:
            states = {}
            for session in self._sessions.values():
                s = session.state.value
                states[s] = states.get(s, 0) + 1

            return {
                "total_sessions": len(self._sessions),
                "by_state": states,
                "unique_owners": len(self._owner_sessions),
                "running": self._running,
            }
