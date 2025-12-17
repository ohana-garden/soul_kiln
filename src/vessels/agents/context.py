"""
Agent Context Management.

Provides session state management for agents with:
- Global context registry
- Task lifecycle tracking
- Pause/resume capabilities
- Stuck detection
"""

import logging
import threading
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from typing import Any, Callable

logger = logging.getLogger(__name__)


class ContextState(str, Enum):
    """State of an agent context."""

    IDLE = "idle"
    RUNNING = "running"
    PAUSED = "paused"
    WAITING = "waiting"
    COMPLETED = "completed"
    FAILED = "failed"


@dataclass
class ContextTask:
    """A simple task scheduled for deferred execution within a context."""

    id: str
    func: Callable
    args: tuple = field(default_factory=tuple)
    kwargs: dict = field(default_factory=dict)
    scheduled_at: datetime = field(default_factory=datetime.utcnow)
    execute_after: datetime | None = None
    completed: bool = False
    result: Any = None
    error: Exception | None = None


@dataclass
class AgentContext:
    """
    Context for an agent session.

    Manages:
    - Session state and configuration
    - Task lifecycle with deferred execution
    - Pause/resume with auto-unpause
    - Intervention message queue
    - Notification handling
    """

    id: str = field(default_factory=lambda: f"ctx_{uuid.uuid4().hex[:12]}")
    agent_id: str | None = None
    state: ContextState = ContextState.IDLE
    config: dict = field(default_factory=dict)
    created_at: datetime = field(default_factory=datetime.utcnow)
    last_activity: datetime = field(default_factory=datetime.utcnow)
    pause_until: datetime | None = None
    intervention_queue: list[str] = field(default_factory=list)
    deferred_tasks: list[ContextTask] = field(default_factory=list)
    metadata: dict = field(default_factory=dict)

    # Performance tracking
    total_operations: int = 0
    successful_operations: int = 0
    failed_operations: int = 0

    def __post_init__(self):
        self._lock = threading.RLock()
        self._callbacks: dict[str, list[Callable]] = {
            "on_state_change": [],
            "on_pause": [],
            "on_resume": [],
            "on_intervention": [],
        }

    def update_activity(self) -> None:
        """Update last activity timestamp."""
        with self._lock:
            self.last_activity = datetime.utcnow()

    def set_state(self, state: ContextState) -> None:
        """Set context state with callbacks."""
        with self._lock:
            old_state = self.state
            self.state = state
            self.update_activity()

            # Fire callbacks
            for callback in self._callbacks["on_state_change"]:
                try:
                    callback(self, old_state, state)
                except Exception as e:
                    logger.error(f"State change callback error: {e}")

    def pause(self, duration_seconds: int | None = None) -> None:
        """
        Pause the context.

        Args:
            duration_seconds: Optional auto-resume after this duration
        """
        with self._lock:
            self.set_state(ContextState.PAUSED)
            if duration_seconds:
                self.pause_until = datetime.utcnow() + timedelta(seconds=duration_seconds)
            else:
                self.pause_until = None

            for callback in self._callbacks["on_pause"]:
                try:
                    callback(self)
                except Exception as e:
                    logger.error(f"Pause callback error: {e}")

            logger.debug(f"Context {self.id} paused")

    def resume(self) -> None:
        """Resume a paused context."""
        with self._lock:
            if self.state == ContextState.PAUSED:
                self.set_state(ContextState.RUNNING)
                self.pause_until = None

                for callback in self._callbacks["on_resume"]:
                    try:
                        callback(self)
                    except Exception as e:
                        logger.error(f"Resume callback error: {e}")

                logger.debug(f"Context {self.id} resumed")

    def should_auto_resume(self) -> bool:
        """Check if context should auto-resume based on pause_until."""
        if self.state != ContextState.PAUSED:
            return False
        if self.pause_until is None:
            return False
        return datetime.utcnow() >= self.pause_until

    def check_auto_resume(self) -> bool:
        """Auto-resume if pause_until has passed."""
        if self.should_auto_resume():
            self.resume()
            return True
        return False

    def is_active(self) -> bool:
        """Check if context is in an active state."""
        return self.state in (ContextState.RUNNING, ContextState.WAITING)

    def is_stuck(self, threshold_seconds: int = 300) -> bool:
        """
        Check if context appears stuck.

        Args:
            threshold_seconds: Seconds of inactivity to consider stuck

        Returns:
            True if context appears stuck
        """
        if not self.is_active():
            return False

        idle_time = (datetime.utcnow() - self.last_activity).total_seconds()
        return idle_time > threshold_seconds

    def add_intervention(self, message: str) -> None:
        """Add an intervention message to the queue."""
        with self._lock:
            self.intervention_queue.append(message)
            self.update_activity()

            for callback in self._callbacks["on_intervention"]:
                try:
                    callback(self, message)
                except Exception as e:
                    logger.error(f"Intervention callback error: {e}")

    def pop_intervention(self) -> str | None:
        """Pop and return the next intervention message."""
        with self._lock:
            if self.intervention_queue:
                return self.intervention_queue.pop(0)
            return None

    def has_interventions(self) -> bool:
        """Check if there are pending interventions."""
        return len(self.intervention_queue) > 0

    def add_deferred_task(
        self,
        func: Callable,
        *args,
        delay_seconds: int = 0,
        **kwargs,
    ) -> str:
        """
        Add a task for deferred execution.

        Args:
            func: Function to execute
            *args: Positional arguments
            delay_seconds: Delay before execution
            **kwargs: Keyword arguments

        Returns:
            Task ID
        """
        with self._lock:
            task = ContextTask(
                id=f"task_{uuid.uuid4().hex[:8]}",
                func=func,
                args=args,
                kwargs=kwargs,
                execute_after=datetime.utcnow() + timedelta(seconds=delay_seconds)
                if delay_seconds > 0
                else None,
            )
            self.deferred_tasks.append(task)
            return task.id

    def execute_ready_tasks(self) -> list[DeferredTask]:
        """Execute and return tasks that are ready."""
        with self._lock:
            ready = []
            remaining = []

            now = datetime.utcnow()
            for task in self.deferred_tasks:
                if task.completed:
                    continue

                if task.execute_after is None or now >= task.execute_after:
                    ready.append(task)
                else:
                    remaining.append(task)

            self.deferred_tasks = remaining

            # Execute ready tasks
            for task in ready:
                try:
                    task.result = task.func(*task.args, **task.kwargs)
                    task.completed = True
                except Exception as e:
                    task.error = e
                    task.completed = True
                    logger.error(f"Deferred task {task.id} failed: {e}")

            return ready

    def register_callback(self, event: str, callback: Callable) -> None:
        """Register a callback for an event."""
        if event in self._callbacks:
            self._callbacks[event].append(callback)

    def record_operation(self, success: bool) -> None:
        """Record an operation result."""
        with self._lock:
            self.total_operations += 1
            if success:
                self.successful_operations += 1
            else:
                self.failed_operations += 1
            self.update_activity()

    def get_stats(self) -> dict:
        """Get context statistics."""
        return {
            "id": self.id,
            "agent_id": self.agent_id,
            "state": self.state.value,
            "created_at": self.created_at.isoformat(),
            "last_activity": self.last_activity.isoformat(),
            "total_operations": self.total_operations,
            "successful_operations": self.successful_operations,
            "failed_operations": self.failed_operations,
            "success_rate": (
                self.successful_operations / self.total_operations
                if self.total_operations > 0
                else 0.0
            ),
            "pending_interventions": len(self.intervention_queue),
            "pending_tasks": len([t for t in self.deferred_tasks if not t.completed]),
        }


class ContextRegistry:
    """
    Global registry of active agent contexts.

    Provides:
    - Context lookup by ID or agent
    - Stuck detection across all contexts
    - Bulk operations
    """

    _instance = None
    _lock = threading.Lock()

    def __new__(cls):
        with cls._lock:
            if cls._instance is None:
                cls._instance = super().__new__(cls)
                cls._instance._contexts = {}
                cls._instance._agent_contexts = {}
            return cls._instance

    def register(self, context: AgentContext) -> None:
        """Register a context."""
        self._contexts[context.id] = context
        if context.agent_id:
            if context.agent_id not in self._agent_contexts:
                self._agent_contexts[context.agent_id] = []
            self._agent_contexts[context.agent_id].append(context.id)

    def unregister(self, context_id: str) -> None:
        """Unregister a context."""
        if context_id in self._contexts:
            context = self._contexts[context_id]
            if context.agent_id and context.agent_id in self._agent_contexts:
                self._agent_contexts[context.agent_id] = [
                    cid
                    for cid in self._agent_contexts[context.agent_id]
                    if cid != context_id
                ]
            del self._contexts[context_id]

    def get(self, context_id: str) -> AgentContext | None:
        """Get a context by ID."""
        return self._contexts.get(context_id)

    def get_for_agent(self, agent_id: str) -> list[AgentContext]:
        """Get all contexts for an agent."""
        context_ids = self._agent_contexts.get(agent_id, [])
        return [self._contexts[cid] for cid in context_ids if cid in self._contexts]

    def get_active(self) -> list[AgentContext]:
        """Get all active contexts."""
        return [ctx for ctx in self._contexts.values() if ctx.is_active()]

    def get_stuck(self, threshold_seconds: int = 300) -> list[AgentContext]:
        """Get all stuck contexts."""
        return [ctx for ctx in self._contexts.values() if ctx.is_stuck(threshold_seconds)]

    def process_auto_resumes(self) -> list[AgentContext]:
        """Process auto-resumes for all paused contexts."""
        resumed = []
        for context in self._contexts.values():
            if context.check_auto_resume():
                resumed.append(context)
        return resumed

    def execute_all_ready_tasks(self) -> int:
        """Execute ready deferred tasks across all contexts."""
        total = 0
        for context in self._contexts.values():
            tasks = context.execute_ready_tasks()
            total += len(tasks)
        return total

    def get_stats(self) -> dict:
        """Get registry statistics."""
        states = {}
        for context in self._contexts.values():
            state = context.state.value
            states[state] = states.get(state, 0) + 1

        return {
            "total_contexts": len(self._contexts),
            "total_agents": len(self._agent_contexts),
            "states": states,
            "stuck_count": len(self.get_stuck()),
        }

    def clear(self) -> None:
        """Clear all contexts."""
        self._contexts.clear()
        self._agent_contexts.clear()
