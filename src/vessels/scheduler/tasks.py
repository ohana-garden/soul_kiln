"""
Task definitions for the scheduler.

Defines task types, states, and the ScheduledTask model.
"""

import uuid
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Callable


class TaskType(str, Enum):
    """Types of scheduled tasks."""

    SCHEDULED = "scheduled"  # Cron-based recurring
    PLANNED = "planned"  # Run at specific datetime
    ADHOC = "adhoc"  # Manual execution


class TaskState(str, Enum):
    """State of a task."""

    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"
    PAUSED = "paused"


@dataclass
class ScheduledTask:
    """
    A scheduled task.

    Supports cron-based scheduling, planned datetime execution,
    and ad-hoc manual triggers.
    """

    id: str = field(default_factory=lambda: f"task_{uuid.uuid4().hex[:12]}")
    name: str = ""
    description: str = ""
    task_type: TaskType = TaskType.ADHOC

    # Execution configuration
    func: Callable | None = None
    func_name: str = ""  # For serialization
    args: tuple = field(default_factory=tuple)
    kwargs: dict = field(default_factory=dict)
    system_prompt: str | None = None
    user_prompt: str | None = None

    # Scheduling
    cron_expression: str | None = None  # For SCHEDULED type (5 fields)
    planned_datetime: datetime | None = None  # For PLANNED type
    timezone: str = "UTC"

    # State
    state: TaskState = TaskState.PENDING
    last_run: datetime | None = None
    next_run: datetime | None = None
    run_count: int = 0
    error_count: int = 0
    last_error: str | None = None
    last_result: Any = None

    # Lifecycle
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)
    max_runs: int | None = None  # None = unlimited
    timeout_seconds: int = 300

    # Context
    context_id: str | None = None  # Run in existing context
    agent_id: str | None = None
    isolated: bool = True  # Run in isolated context
    attachments: list[str] = field(default_factory=list)  # File paths or URLs
    metadata: dict = field(default_factory=dict)

    def to_dict(self) -> dict:
        """Convert to dictionary."""
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "task_type": self.task_type.value,
            "func_name": self.func_name,
            "cron_expression": self.cron_expression,
            "planned_datetime": (
                self.planned_datetime.isoformat() if self.planned_datetime else None
            ),
            "timezone": self.timezone,
            "state": self.state.value,
            "last_run": self.last_run.isoformat() if self.last_run else None,
            "next_run": self.next_run.isoformat() if self.next_run else None,
            "run_count": self.run_count,
            "error_count": self.error_count,
            "last_error": self.last_error,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
            "max_runs": self.max_runs,
            "timeout_seconds": self.timeout_seconds,
            "context_id": self.context_id,
            "agent_id": self.agent_id,
            "isolated": self.isolated,
            "attachments": self.attachments,
            "metadata": self.metadata,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "ScheduledTask":
        """Create from dictionary."""
        task = cls(
            id=data.get("id", f"task_{uuid.uuid4().hex[:12]}"),
            name=data.get("name", ""),
            description=data.get("description", ""),
            task_type=TaskType(data.get("task_type", "adhoc")),
            func_name=data.get("func_name", ""),
            cron_expression=data.get("cron_expression"),
            timezone=data.get("timezone", "UTC"),
            state=TaskState(data.get("state", "pending")),
            run_count=data.get("run_count", 0),
            error_count=data.get("error_count", 0),
            last_error=data.get("last_error"),
            max_runs=data.get("max_runs"),
            timeout_seconds=data.get("timeout_seconds", 300),
            context_id=data.get("context_id"),
            agent_id=data.get("agent_id"),
            isolated=data.get("isolated", True),
            attachments=data.get("attachments", []),
            metadata=data.get("metadata", {}),
        )

        # Parse datetime fields
        if data.get("planned_datetime"):
            task.planned_datetime = datetime.fromisoformat(data["planned_datetime"])
        if data.get("last_run"):
            task.last_run = datetime.fromisoformat(data["last_run"])
        if data.get("next_run"):
            task.next_run = datetime.fromisoformat(data["next_run"])
        if data.get("created_at"):
            task.created_at = datetime.fromisoformat(data["created_at"])
        if data.get("updated_at"):
            task.updated_at = datetime.fromisoformat(data["updated_at"])

        return task

    @property
    def is_active(self) -> bool:
        """Check if task is active (can be scheduled)."""
        return self.state in (TaskState.PENDING, TaskState.COMPLETED)

    @property
    def is_recurring(self) -> bool:
        """Check if task is recurring."""
        return self.task_type == TaskType.SCHEDULED and self.cron_expression is not None

    @property
    def reached_max_runs(self) -> bool:
        """Check if max runs reached."""
        if self.max_runs is None:
            return False
        return self.run_count >= self.max_runs

    def mark_started(self) -> None:
        """Mark task as started."""
        self.state = TaskState.RUNNING
        self.updated_at = datetime.utcnow()

    def mark_completed(self, result: Any = None) -> None:
        """Mark task as completed."""
        self.state = TaskState.COMPLETED
        self.last_run = datetime.utcnow()
        self.updated_at = datetime.utcnow()
        self.run_count += 1
        self.last_result = result
        self.last_error = None

    def mark_failed(self, error: str) -> None:
        """Mark task as failed."""
        self.state = TaskState.FAILED
        self.last_run = datetime.utcnow()
        self.updated_at = datetime.utcnow()
        self.run_count += 1
        self.error_count += 1
        self.last_error = error

    def mark_cancelled(self) -> None:
        """Mark task as cancelled."""
        self.state = TaskState.CANCELLED
        self.updated_at = datetime.utcnow()

    def reset(self) -> None:
        """Reset task to pending state."""
        self.state = TaskState.PENDING
        self.updated_at = datetime.utcnow()
