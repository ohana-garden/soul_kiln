"""
Deferred Task Execution System.

Provides non-blocking initialization and task execution
for heavy components.
"""

import logging
import queue
import threading
import uuid
from concurrent.futures import Future, ThreadPoolExecutor
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Callable

logger = logging.getLogger(__name__)


class TaskPriority(int, Enum):
    """Priority levels for deferred tasks."""

    LOW = 0
    NORMAL = 1
    HIGH = 2
    CRITICAL = 3


class TaskStatus(str, Enum):
    """Status of a deferred task."""

    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


@dataclass
class DeferredTask:
    """A task for deferred execution."""

    id: str = field(default_factory=lambda: f"def_{uuid.uuid4().hex[:12]}")
    name: str = ""
    func: Callable | None = None
    args: tuple = field(default_factory=tuple)
    kwargs: dict = field(default_factory=dict)
    priority: TaskPriority = TaskPriority.NORMAL
    status: TaskStatus = TaskStatus.PENDING
    result: Any = None
    error: str | None = None
    created_at: datetime = field(default_factory=datetime.utcnow)
    started_at: datetime | None = None
    completed_at: datetime | None = None
    dependencies: list[str] = field(default_factory=list)  # Task IDs to wait for
    future: Future | None = field(default=None, repr=False)

    def __lt__(self, other: "DeferredTask") -> bool:
        """Compare by priority (higher priority = earlier)."""
        return self.priority.value > other.priority.value

    @property
    def is_complete(self) -> bool:
        """Check if task is complete."""
        return self.status in (
            TaskStatus.COMPLETED,
            TaskStatus.FAILED,
            TaskStatus.CANCELLED,
        )

    @property
    def duration_seconds(self) -> float | None:
        """Get execution duration."""
        if self.started_at and self.completed_at:
            return (self.completed_at - self.started_at).total_seconds()
        return None

    def to_dict(self) -> dict:
        """Convert to dictionary."""
        return {
            "id": self.id,
            "name": self.name,
            "priority": self.priority.name,
            "status": self.status.value,
            "result": str(self.result) if self.result else None,
            "error": self.error,
            "created_at": self.created_at.isoformat(),
            "started_at": self.started_at.isoformat() if self.started_at else None,
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
            "duration": self.duration_seconds,
            "dependencies": self.dependencies,
        }


class DeferredTaskManager:
    """
    Manages deferred task execution.

    Features:
    - Non-blocking task submission
    - Priority-based execution
    - Task dependencies
    - Progress tracking
    - Concurrent execution with thread pool
    """

    def __init__(
        self,
        max_workers: int = 4,
        auto_start: bool = True,
    ):
        """
        Initialize deferred task manager.

        Args:
            max_workers: Maximum concurrent workers
            auto_start: Start processing automatically
        """
        self._tasks: dict[str, DeferredTask] = {}
        self._queue: queue.PriorityQueue = queue.PriorityQueue()
        self._executor: ThreadPoolExecutor | None = None
        self._max_workers = max_workers
        self._running = False
        self._lock = threading.RLock()
        self._callbacks: dict[str, list[Callable]] = {
            "on_complete": [],
            "on_error": [],
            "on_all_complete": [],
        }

        if auto_start:
            self.start()

    def start(self) -> None:
        """Start the task manager."""
        if self._running:
            return

        self._running = True
        self._executor = ThreadPoolExecutor(max_workers=self._max_workers)
        logger.info(f"DeferredTaskManager started with {self._max_workers} workers")

    def stop(self, wait: bool = True) -> None:
        """Stop the task manager."""
        self._running = False
        if self._executor:
            self._executor.shutdown(wait=wait)
            self._executor = None
        logger.info("DeferredTaskManager stopped")

    def submit(
        self,
        func: Callable,
        *args,
        name: str = "",
        priority: TaskPriority = TaskPriority.NORMAL,
        dependencies: list[str] | None = None,
        **kwargs,
    ) -> DeferredTask:
        """
        Submit a task for deferred execution.

        Args:
            func: Function to execute
            *args: Positional arguments
            name: Task name
            priority: Execution priority
            dependencies: Task IDs to wait for
            **kwargs: Keyword arguments

        Returns:
            Created DeferredTask
        """
        task = DeferredTask(
            name=name or func.__name__,
            func=func,
            args=args,
            kwargs=kwargs,
            priority=priority,
            dependencies=dependencies or [],
        )

        with self._lock:
            self._tasks[task.id] = task

        # Check dependencies
        if self._can_execute(task):
            self._schedule_task(task)
        else:
            logger.debug(f"Task {task.id} waiting for dependencies")

        return task

    def _can_execute(self, task: DeferredTask) -> bool:
        """Check if task can execute (all dependencies complete)."""
        for dep_id in task.dependencies:
            dep_task = self._tasks.get(dep_id)
            if not dep_task or not dep_task.is_complete:
                return False
            if dep_task.status == TaskStatus.FAILED:
                # Dependency failed - cancel this task
                task.status = TaskStatus.CANCELLED
                task.error = f"Dependency {dep_id} failed"
                return False
        return True

    def _schedule_task(self, task: DeferredTask) -> None:
        """Schedule a task for execution."""
        if not self._executor or not self._running:
            logger.warning("Task manager not running")
            return

        if task.status != TaskStatus.PENDING:
            return

        task.future = self._executor.submit(self._execute_task, task)

    def _execute_task(self, task: DeferredTask) -> Any:
        """Execute a single task."""
        task.status = TaskStatus.RUNNING
        task.started_at = datetime.utcnow()

        try:
            result = task.func(*task.args, **task.kwargs)
            task.result = result
            task.status = TaskStatus.COMPLETED
            task.completed_at = datetime.utcnow()

            logger.debug(f"Task {task.id} ({task.name}) completed")

            # Fire callbacks
            for callback in self._callbacks["on_complete"]:
                try:
                    callback(task)
                except Exception as e:
                    logger.error(f"Callback error: {e}")

            # Check for dependent tasks
            self._check_dependents(task.id)

            return result

        except Exception as e:
            task.status = TaskStatus.FAILED
            task.error = str(e)
            task.completed_at = datetime.utcnow()

            logger.error(f"Task {task.id} ({task.name}) failed: {e}")

            for callback in self._callbacks["on_error"]:
                try:
                    callback(task, e)
                except Exception as cb_err:
                    logger.error(f"Error callback error: {cb_err}")

            raise

    def _check_dependents(self, completed_task_id: str) -> None:
        """Check and schedule tasks dependent on completed task."""
        with self._lock:
            for task in self._tasks.values():
                if (
                    task.status == TaskStatus.PENDING
                    and completed_task_id in task.dependencies
                ):
                    if self._can_execute(task):
                        self._schedule_task(task)

        # Check if all tasks complete
        if self._all_complete():
            for callback in self._callbacks["on_all_complete"]:
                try:
                    callback()
                except Exception as e:
                    logger.error(f"All complete callback error: {e}")

    def _all_complete(self) -> bool:
        """Check if all tasks are complete."""
        with self._lock:
            return all(task.is_complete for task in self._tasks.values())

    def cancel(self, task_id: str) -> bool:
        """Cancel a pending task."""
        task = self._tasks.get(task_id)
        if not task:
            return False

        if task.status == TaskStatus.PENDING:
            task.status = TaskStatus.CANCELLED
            task.completed_at = datetime.utcnow()
            return True

        if task.future and not task.future.done():
            task.future.cancel()
            task.status = TaskStatus.CANCELLED
            task.completed_at = datetime.utcnow()
            return True

        return False

    def get_task(self, task_id: str) -> DeferredTask | None:
        """Get a task by ID."""
        return self._tasks.get(task_id)

    def wait_for(self, task_id: str, timeout: float | None = None) -> DeferredTask:
        """
        Wait for a task to complete.

        Args:
            task_id: Task to wait for
            timeout: Maximum wait time

        Returns:
            Completed task
        """
        task = self._tasks.get(task_id)
        if not task:
            raise ValueError(f"Task not found: {task_id}")

        if task.future:
            try:
                task.future.result(timeout=timeout)
            except Exception:
                pass  # Error captured in task

        return task

    def wait_all(self, timeout: float | None = None) -> bool:
        """
        Wait for all tasks to complete.

        Args:
            timeout: Maximum wait time

        Returns:
            True if all completed successfully
        """
        import time

        start = time.time()

        while not self._all_complete():
            if timeout and time.time() - start > timeout:
                return False
            time.sleep(0.1)

        return all(
            task.status == TaskStatus.COMPLETED for task in self._tasks.values()
        )

    def get_pending(self) -> list[DeferredTask]:
        """Get all pending tasks."""
        return [t for t in self._tasks.values() if t.status == TaskStatus.PENDING]

    def get_running(self) -> list[DeferredTask]:
        """Get all running tasks."""
        return [t for t in self._tasks.values() if t.status == TaskStatus.RUNNING]

    def get_completed(self) -> list[DeferredTask]:
        """Get all completed tasks."""
        return [t for t in self._tasks.values() if t.status == TaskStatus.COMPLETED]

    def get_failed(self) -> list[DeferredTask]:
        """Get all failed tasks."""
        return [t for t in self._tasks.values() if t.status == TaskStatus.FAILED]

    def register_callback(
        self,
        event: str,
        callback: Callable,
    ) -> None:
        """Register a callback for task events."""
        if event in self._callbacks:
            self._callbacks[event].append(callback)

    def clear_completed(self) -> int:
        """Clear completed tasks from history."""
        with self._lock:
            to_remove = [
                task_id
                for task_id, task in self._tasks.items()
                if task.is_complete
            ]
            for task_id in to_remove:
                del self._tasks[task_id]
            return len(to_remove)

    def get_stats(self) -> dict:
        """Get task manager statistics."""
        with self._lock:
            status_counts = {}
            for task in self._tasks.values():
                s = task.status.value
                status_counts[s] = status_counts.get(s, 0) + 1

            total_duration = sum(
                t.duration_seconds or 0
                for t in self._tasks.values()
                if t.is_complete
            )
            completed = len(self.get_completed())

            return {
                "total_tasks": len(self._tasks),
                "by_status": status_counts,
                "running": self._running,
                "workers": self._max_workers,
                "avg_duration": total_duration / completed if completed else 0,
            }
