"""
Subordinate Agent Management.

Enables hierarchical agent delegation where agents can
spawn and manage subordinate agents for complex tasks.
"""

import logging
import threading
import uuid
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Callable

from .context import AgentContext, ContextRegistry, ContextState

logger = logging.getLogger(__name__)


class SubordinateState(str, Enum):
    """State of a subordinate agent call."""

    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


@dataclass
class SubordinateCall:
    """
    A call to a subordinate agent.

    Represents delegation of a task from a superior agent
    to a subordinate agent.
    """

    id: str = field(default_factory=lambda: f"sub_{uuid.uuid4().hex[:12]}")
    superior_context_id: str = ""
    subordinate_context_id: str | None = None
    task: str = ""
    system_prompt: str | None = None
    state: SubordinateState = SubordinateState.PENDING
    result: Any = None
    error: str | None = None
    created_at: datetime = field(default_factory=datetime.utcnow)
    started_at: datetime | None = None
    completed_at: datetime | None = None
    timeout_seconds: int = 300
    metadata: dict = field(default_factory=dict)

    def to_dict(self) -> dict:
        """Convert to dictionary."""
        return {
            "id": self.id,
            "superior_context_id": self.superior_context_id,
            "subordinate_context_id": self.subordinate_context_id,
            "task": self.task,
            "state": self.state.value,
            "result": self.result,
            "error": self.error,
            "created_at": self.created_at.isoformat(),
            "started_at": self.started_at.isoformat() if self.started_at else None,
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
            "timeout_seconds": self.timeout_seconds,
        }

    @property
    def is_complete(self) -> bool:
        """Check if the call is complete."""
        return self.state in (
            SubordinateState.COMPLETED,
            SubordinateState.FAILED,
            SubordinateState.CANCELLED,
        )

    @property
    def duration_seconds(self) -> float | None:
        """Get duration if completed."""
        if self.started_at and self.completed_at:
            return (self.completed_at - self.started_at).total_seconds()
        return None


class SubordinateManager:
    """
    Manages subordinate agent calls.

    Features:
    - Create and track subordinate calls
    - Execute subordinate tasks
    - Handle results and errors
    - Support for async execution
    """

    def __init__(
        self,
        registry: ContextRegistry | None = None,
        executor: Callable[[SubordinateCall], Any] | None = None,
    ):
        """
        Initialize subordinate manager.

        Args:
            registry: Context registry
            executor: Function to execute subordinate tasks
        """
        self.registry = registry or ContextRegistry()
        self._executor = executor or self._default_executor
        self._calls: dict[str, SubordinateCall] = {}
        self._by_superior: dict[str, list[str]] = {}
        self._lock = threading.RLock()
        self._callbacks: dict[str, list[Callable]] = {
            "on_start": [],
            "on_complete": [],
            "on_error": [],
        }

    def _default_executor(self, call: SubordinateCall) -> Any:
        """Default executor - raises NotImplemented."""
        raise NotImplementedError(
            "Subordinate executor not configured. "
            "Provide an executor function to SubordinateManager."
        )

    def create_call(
        self,
        superior_context_id: str,
        task: str,
        system_prompt: str | None = None,
        timeout_seconds: int = 300,
        metadata: dict | None = None,
    ) -> SubordinateCall:
        """
        Create a subordinate call.

        Args:
            superior_context_id: ID of the calling context
            task: Task description for the subordinate
            system_prompt: Optional custom system prompt
            timeout_seconds: Timeout for the call
            metadata: Additional metadata

        Returns:
            Created SubordinateCall
        """
        call = SubordinateCall(
            superior_context_id=superior_context_id,
            task=task,
            system_prompt=system_prompt,
            timeout_seconds=timeout_seconds,
            metadata=metadata or {},
        )

        with self._lock:
            self._calls[call.id] = call
            if superior_context_id not in self._by_superior:
                self._by_superior[superior_context_id] = []
            self._by_superior[superior_context_id].append(call.id)

        logger.debug(f"Created subordinate call {call.id} for context {superior_context_id}")
        return call

    def execute(self, call_id: str) -> Any:
        """
        Execute a subordinate call.

        Args:
            call_id: ID of the call to execute

        Returns:
            Result from the subordinate
        """
        call = self._calls.get(call_id)
        if not call:
            raise ValueError(f"Call not found: {call_id}")

        if call.state != SubordinateState.PENDING:
            raise ValueError(f"Call {call_id} is not pending: {call.state}")

        # Update state
        call.state = SubordinateState.RUNNING
        call.started_at = datetime.utcnow()

        # Fire start callbacks
        for callback in self._callbacks["on_start"]:
            try:
                callback(call)
            except Exception as e:
                logger.error(f"Start callback error: {e}")

        try:
            # Execute via configured executor
            result = self._executor(call)

            call.result = result
            call.state = SubordinateState.COMPLETED
            call.completed_at = datetime.utcnow()

            # Fire complete callbacks
            for callback in self._callbacks["on_complete"]:
                try:
                    callback(call)
                except Exception as e:
                    logger.error(f"Complete callback error: {e}")

            logger.debug(f"Subordinate call {call_id} completed successfully")
            return result

        except Exception as e:
            call.error = str(e)
            call.state = SubordinateState.FAILED
            call.completed_at = datetime.utcnow()

            # Fire error callbacks
            for callback in self._callbacks["on_error"]:
                try:
                    callback(call, e)
                except Exception as cb_err:
                    logger.error(f"Error callback error: {cb_err}")

            logger.error(f"Subordinate call {call_id} failed: {e}")
            raise

    def call_subordinate(
        self,
        superior_context_id: str,
        task: str,
        system_prompt: str | None = None,
        timeout_seconds: int = 300,
        wait: bool = True,
    ) -> SubordinateCall:
        """
        Create and execute a subordinate call.

        Convenience method that creates and optionally executes a call.

        Args:
            superior_context_id: Calling context ID
            task: Task for subordinate
            system_prompt: Optional system prompt
            timeout_seconds: Timeout
            wait: If True, execute synchronously

        Returns:
            The SubordinateCall with results if wait=True
        """
        call = self.create_call(
            superior_context_id=superior_context_id,
            task=task,
            system_prompt=system_prompt,
            timeout_seconds=timeout_seconds,
        )

        if wait:
            try:
                self.execute(call.id)
            except Exception:
                pass  # Error captured in call object

        return call

    def cancel(self, call_id: str, reason: str = "") -> bool:
        """
        Cancel a pending or running call.

        Args:
            call_id: Call to cancel
            reason: Cancellation reason

        Returns:
            True if cancelled
        """
        call = self._calls.get(call_id)
        if not call:
            return False

        if call.is_complete:
            return False

        call.state = SubordinateState.CANCELLED
        call.error = reason or "Cancelled by superior"
        call.completed_at = datetime.utcnow()

        logger.debug(f"Cancelled subordinate call {call_id}")
        return True

    def get_call(self, call_id: str) -> SubordinateCall | None:
        """Get a call by ID."""
        return self._calls.get(call_id)

    def get_calls_for_superior(self, superior_context_id: str) -> list[SubordinateCall]:
        """Get all calls made by a superior context."""
        call_ids = self._by_superior.get(superior_context_id, [])
        return [self._calls[cid] for cid in call_ids if cid in self._calls]

    def get_pending_calls(self) -> list[SubordinateCall]:
        """Get all pending calls."""
        return [c for c in self._calls.values() if c.state == SubordinateState.PENDING]

    def get_running_calls(self) -> list[SubordinateCall]:
        """Get all running calls."""
        return [c for c in self._calls.values() if c.state == SubordinateState.RUNNING]

    def wait_for_call(
        self,
        call_id: str,
        timeout_seconds: float | None = None,
        poll_interval: float = 0.1,
    ) -> SubordinateCall:
        """
        Wait for a call to complete.

        Args:
            call_id: Call to wait for
            timeout_seconds: Maximum wait time
            poll_interval: Polling interval

        Returns:
            The completed call
        """
        import time

        call = self._calls.get(call_id)
        if not call:
            raise ValueError(f"Call not found: {call_id}")

        start = time.time()
        timeout = timeout_seconds or call.timeout_seconds

        while not call.is_complete:
            if time.time() - start > timeout:
                call.state = SubordinateState.FAILED
                call.error = "Timeout waiting for completion"
                call.completed_at = datetime.utcnow()
                break
            time.sleep(poll_interval)

        return call

    def register_callback(
        self,
        event: str,
        callback: Callable,
    ) -> None:
        """Register a callback for subordinate events."""
        if event in self._callbacks:
            self._callbacks[event].append(callback)

    def set_executor(self, executor: Callable[[SubordinateCall], Any]) -> None:
        """Set the executor function for subordinate tasks."""
        self._executor = executor

    def cleanup_completed(self, max_age_seconds: int = 3600) -> int:
        """
        Clean up old completed calls.

        Args:
            max_age_seconds: Maximum age to keep

        Returns:
            Number of calls cleaned up
        """
        now = datetime.utcnow()
        cleaned = 0

        with self._lock:
            to_remove = []
            for call_id, call in self._calls.items():
                if call.is_complete and call.completed_at:
                    age = (now - call.completed_at).total_seconds()
                    if age > max_age_seconds:
                        to_remove.append(call_id)

            for call_id in to_remove:
                call = self._calls.pop(call_id)
                if call.superior_context_id in self._by_superior:
                    self._by_superior[call.superior_context_id] = [
                        cid
                        for cid in self._by_superior[call.superior_context_id]
                        if cid != call_id
                    ]
                cleaned += 1

        return cleaned

    def get_stats(self) -> dict:
        """Get subordinate call statistics."""
        with self._lock:
            states = {}
            total_duration = 0
            completed_count = 0

            for call in self._calls.values():
                state = call.state.value
                states[state] = states.get(state, 0) + 1
                if call.duration_seconds:
                    total_duration += call.duration_seconds
                    completed_count += 1

            return {
                "total_calls": len(self._calls),
                "by_state": states,
                "avg_duration": total_duration / completed_count if completed_count else 0,
                "unique_superiors": len(self._by_superior),
            }
