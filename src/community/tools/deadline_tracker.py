"""
Deadline Tracker Tool.

Manages grant deadlines and sends reminders.
Adapted from Grant-Getter for soul_kiln community framework.
"""

import json
import logging
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from pathlib import Path
from typing import Any, Callable

from .registry import Tool, ToolResult, ToolCategory

logger = logging.getLogger(__name__)


class DeadlineStatus(str, Enum):
    """Status of a deadline."""

    UPCOMING = "upcoming"
    DUE_SOON = "due_soon"  # Within 7 days
    URGENT = "urgent"  # Within 3 days
    OVERDUE = "overdue"
    COMPLETED = "completed"
    CANCELLED = "cancelled"


class ReminderFrequency(str, Enum):
    """Frequency of reminders."""

    DAILY = "daily"
    WEEKLY = "weekly"
    CUSTOM = "custom"


@dataclass
class Deadline:
    """A tracked deadline."""

    id: str = field(default_factory=lambda: f"deadline_{uuid.uuid4().hex[:8]}")
    title: str = ""
    description: str = ""
    due_date: datetime = field(default_factory=datetime.utcnow)
    grant_id: str = ""
    funder: str = ""
    status: DeadlineStatus = DeadlineStatus.UPCOMING
    priority: int = 1  # 1-5, higher is more important
    reminder_frequency: ReminderFrequency = ReminderFrequency.WEEKLY
    last_reminder: datetime | None = None
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)
    completed_at: datetime | None = None
    notes: list[str] = field(default_factory=list)
    metadata: dict = field(default_factory=dict)

    def days_until(self) -> int:
        """Get days until deadline."""
        delta = self.due_date - datetime.utcnow()
        return delta.days

    def update_status(self) -> DeadlineStatus:
        """Update and return status based on current date."""
        if self.status in (DeadlineStatus.COMPLETED, DeadlineStatus.CANCELLED):
            return self.status

        days = self.days_until()
        if days < 0:
            self.status = DeadlineStatus.OVERDUE
        elif days <= 3:
            self.status = DeadlineStatus.URGENT
        elif days <= 7:
            self.status = DeadlineStatus.DUE_SOON
        else:
            self.status = DeadlineStatus.UPCOMING

        return self.status

    def add_note(self, note: str) -> None:
        """Add a note to this deadline."""
        timestamp = datetime.utcnow().isoformat()
        self.notes.append(f"[{timestamp}] {note}")
        self.updated_at = datetime.utcnow()

    def to_dict(self) -> dict:
        """Convert to dictionary."""
        return {
            "id": self.id,
            "title": self.title,
            "description": self.description,
            "due_date": self.due_date.isoformat(),
            "grant_id": self.grant_id,
            "funder": self.funder,
            "status": self.status.value,
            "priority": self.priority,
            "reminder_frequency": self.reminder_frequency.value,
            "last_reminder": self.last_reminder.isoformat() if self.last_reminder else None,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
            "days_until": self.days_until(),
            "notes": self.notes,
            "metadata": self.metadata,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "Deadline":
        """Create from dictionary."""
        deadline = cls(
            id=data.get("id", f"deadline_{uuid.uuid4().hex[:8]}"),
            title=data.get("title", ""),
            description=data.get("description", ""),
            grant_id=data.get("grant_id", ""),
            funder=data.get("funder", ""),
            priority=data.get("priority", 1),
            notes=data.get("notes", []),
            metadata=data.get("metadata", {}),
        )

        if data.get("due_date"):
            deadline.due_date = datetime.fromisoformat(data["due_date"])
        if data.get("status"):
            deadline.status = DeadlineStatus(data["status"])
        if data.get("reminder_frequency"):
            deadline.reminder_frequency = ReminderFrequency(data["reminder_frequency"])
        if data.get("last_reminder"):
            deadline.last_reminder = datetime.fromisoformat(data["last_reminder"])
        if data.get("created_at"):
            deadline.created_at = datetime.fromisoformat(data["created_at"])
        if data.get("updated_at"):
            deadline.updated_at = datetime.fromisoformat(data["updated_at"])
        if data.get("completed_at"):
            deadline.completed_at = datetime.fromisoformat(data["completed_at"])

        return deadline


class DeadlineTracker(Tool):
    """
    Tool for tracking grant deadlines and sending reminders.

    Features:
    - Add, update, and remove deadlines
    - Automatic status updates based on dates
    - Reminder scheduling
    - Priority management
    - Persistent storage
    """

    def __init__(self, storage_dir: str = "data/deadlines"):
        """Initialize the deadline tracker tool."""
        super().__init__()
        self.id = "tool_deadline_tracker"
        self.name = "Deadline Tracker"
        self.description = "Track grant deadlines and reminders"
        self.category = ToolCategory.SCHEDULING
        self.version = "1.0.0"

        self._deadlines: dict[str, Deadline] = {}
        self._storage_path = Path(storage_dir) / "deadlines.json"
        self._reminder_callbacks: list[Callable[[Deadline], None]] = []

        # Load existing deadlines
        self._load()

    def execute(
        self,
        action: str = "list",
        deadline_id: str | None = None,
        title: str | None = None,
        description: str | None = None,
        due_date: str | None = None,
        grant_id: str | None = None,
        funder: str | None = None,
        priority: int | None = None,
        note: str | None = None,
        status_filter: str | None = None,
        days_ahead: int | None = None,
        **kwargs,
    ) -> ToolResult:
        """
        Execute deadline tracking action.

        Args:
            action: "add", "update", "remove", "complete", "list", "check_reminders"
            deadline_id: ID for update/remove/complete actions
            title: Deadline title (for add/update)
            description: Deadline description
            due_date: Due date as ISO string
            grant_id: Associated grant ID
            funder: Funder name
            priority: Priority level 1-5
            note: Note to add
            status_filter: Filter by status for list
            days_ahead: Only show deadlines within this many days

        Returns:
            ToolResult with deadline data
        """
        try:
            if action == "add":
                return self._add_deadline(
                    title=title or "",
                    description=description or "",
                    due_date=due_date,
                    grant_id=grant_id or "",
                    funder=funder or "",
                    priority=priority or 1,
                )
            elif action == "update":
                return self._update_deadline(
                    deadline_id=deadline_id or "",
                    title=title,
                    description=description,
                    due_date=due_date,
                    priority=priority,
                    note=note,
                )
            elif action == "remove":
                return self._remove_deadline(deadline_id or "")
            elif action == "complete":
                return self._complete_deadline(deadline_id or "")
            elif action == "list":
                return self._list_deadlines(
                    status_filter=status_filter,
                    days_ahead=days_ahead,
                )
            elif action == "check_reminders":
                return self._check_reminders()
            elif action == "get":
                return self._get_deadline(deadline_id or "")
            else:
                return ToolResult(
                    success=False,
                    error=f"Invalid action: {action}",
                )

        except Exception as e:
            logger.error(f"Deadline tracker error: {e}")
            return ToolResult(
                success=False,
                error=str(e),
            )

    def _add_deadline(
        self,
        title: str,
        description: str,
        due_date: str | None,
        grant_id: str,
        funder: str,
        priority: int,
    ) -> ToolResult:
        """Add a new deadline."""
        if not title:
            return ToolResult(success=False, error="Title required")

        deadline = Deadline(
            title=title,
            description=description,
            grant_id=grant_id,
            funder=funder,
            priority=min(5, max(1, priority)),
        )

        if due_date:
            try:
                deadline.due_date = datetime.fromisoformat(due_date)
            except ValueError:
                return ToolResult(
                    success=False,
                    error=f"Invalid date format: {due_date}. Use ISO format.",
                )

        deadline.update_status()
        self._deadlines[deadline.id] = deadline
        self._save()

        return ToolResult(
            success=True,
            data=deadline.to_dict(),
            metadata={"action": "added"},
        )

    def _update_deadline(
        self,
        deadline_id: str,
        title: str | None,
        description: str | None,
        due_date: str | None,
        priority: int | None,
        note: str | None,
    ) -> ToolResult:
        """Update an existing deadline."""
        deadline = self._deadlines.get(deadline_id)
        if not deadline:
            return ToolResult(
                success=False,
                error=f"Deadline not found: {deadline_id}",
            )

        if title is not None:
            deadline.title = title
        if description is not None:
            deadline.description = description
        if due_date is not None:
            try:
                deadline.due_date = datetime.fromisoformat(due_date)
            except ValueError:
                return ToolResult(
                    success=False,
                    error=f"Invalid date format: {due_date}",
                )
        if priority is not None:
            deadline.priority = min(5, max(1, priority))
        if note is not None:
            deadline.add_note(note)

        deadline.updated_at = datetime.utcnow()
        deadline.update_status()
        self._save()

        return ToolResult(
            success=True,
            data=deadline.to_dict(),
            metadata={"action": "updated"},
        )

    def _remove_deadline(self, deadline_id: str) -> ToolResult:
        """Remove a deadline."""
        if deadline_id not in self._deadlines:
            return ToolResult(
                success=False,
                error=f"Deadline not found: {deadline_id}",
            )

        del self._deadlines[deadline_id]
        self._save()

        return ToolResult(
            success=True,
            data={"id": deadline_id},
            metadata={"action": "removed"},
        )

    def _complete_deadline(self, deadline_id: str) -> ToolResult:
        """Mark a deadline as completed."""
        deadline = self._deadlines.get(deadline_id)
        if not deadline:
            return ToolResult(
                success=False,
                error=f"Deadline not found: {deadline_id}",
            )

        deadline.status = DeadlineStatus.COMPLETED
        deadline.completed_at = datetime.utcnow()
        deadline.updated_at = datetime.utcnow()
        self._save()

        return ToolResult(
            success=True,
            data=deadline.to_dict(),
            metadata={"action": "completed"},
        )

    def _get_deadline(self, deadline_id: str) -> ToolResult:
        """Get a specific deadline."""
        deadline = self._deadlines.get(deadline_id)
        if not deadline:
            return ToolResult(
                success=False,
                error=f"Deadline not found: {deadline_id}",
            )

        deadline.update_status()
        return ToolResult(
            success=True,
            data=deadline.to_dict(),
        )

    def _list_deadlines(
        self,
        status_filter: str | None,
        days_ahead: int | None,
    ) -> ToolResult:
        """List deadlines with optional filters."""
        deadlines = list(self._deadlines.values())

        # Update all statuses
        for d in deadlines:
            d.update_status()

        # Apply status filter
        if status_filter:
            try:
                filter_status = DeadlineStatus(status_filter)
                deadlines = [d for d in deadlines if d.status == filter_status]
            except ValueError:
                pass  # Invalid status, ignore filter

        # Apply days ahead filter
        if days_ahead is not None:
            cutoff = datetime.utcnow() + timedelta(days=days_ahead)
            deadlines = [d for d in deadlines if d.due_date <= cutoff]

        # Sort by due date, then priority
        deadlines.sort(key=lambda d: (d.due_date, -d.priority))

        return ToolResult(
            success=True,
            data={
                "deadlines": [d.to_dict() for d in deadlines],
                "total": len(deadlines),
                "by_status": {
                    status.value: len([d for d in deadlines if d.status == status])
                    for status in DeadlineStatus
                },
            },
        )

    def _check_reminders(self) -> ToolResult:
        """Check which deadlines need reminders."""
        now = datetime.utcnow()
        reminders_due = []

        for deadline in self._deadlines.values():
            deadline.update_status()

            # Skip completed or cancelled
            if deadline.status in (DeadlineStatus.COMPLETED, DeadlineStatus.CANCELLED):
                continue

            # Check if reminder is due
            needs_reminder = False
            if deadline.last_reminder is None:
                needs_reminder = True
            else:
                if deadline.reminder_frequency == ReminderFrequency.DAILY:
                    needs_reminder = (now - deadline.last_reminder).days >= 1
                elif deadline.reminder_frequency == ReminderFrequency.WEEKLY:
                    needs_reminder = (now - deadline.last_reminder).days >= 7

            # Urgent deadlines always get reminders
            if deadline.status == DeadlineStatus.URGENT:
                needs_reminder = True

            if needs_reminder:
                reminders_due.append(deadline)
                deadline.last_reminder = now

                # Trigger callbacks
                for callback in self._reminder_callbacks:
                    try:
                        callback(deadline)
                    except Exception as e:
                        logger.error(f"Reminder callback error: {e}")

        self._save()

        return ToolResult(
            success=True,
            data={
                "reminders_sent": len(reminders_due),
                "deadlines": [d.to_dict() for d in reminders_due],
            },
        )

    def on_reminder(self, callback: Callable[[Deadline], None]) -> None:
        """Register a callback for reminders."""
        self._reminder_callbacks.append(callback)

    def _save(self) -> None:
        """Save deadlines to disk."""
        self._storage_path.parent.mkdir(parents=True, exist_ok=True)
        data = {
            "deadlines": [d.to_dict() for d in self._deadlines.values()],
            "saved_at": datetime.utcnow().isoformat(),
        }
        with open(self._storage_path, "w") as f:
            json.dump(data, f, indent=2)

    def _load(self) -> None:
        """Load deadlines from disk."""
        if not self._storage_path.exists():
            return

        try:
            with open(self._storage_path) as f:
                data = json.load(f)

            for deadline_data in data.get("deadlines", []):
                deadline = Deadline.from_dict(deadline_data)
                self._deadlines[deadline.id] = deadline

            logger.info(f"Loaded {len(self._deadlines)} deadlines")
        except Exception as e:
            logger.error(f"Error loading deadlines: {e}")

    def get_schema(self) -> dict:
        """Get the tool's input schema."""
        return {
            "type": "object",
            "required": ["action"],
            "properties": {
                "action": {
                    "type": "string",
                    "enum": ["add", "update", "remove", "complete", "list", "get", "check_reminders"],
                    "description": "Action to perform",
                },
                "deadline_id": {
                    "type": "string",
                    "description": "Deadline ID (for update/remove/complete/get)",
                },
                "title": {
                    "type": "string",
                    "description": "Deadline title",
                },
                "description": {
                    "type": "string",
                    "description": "Deadline description",
                },
                "due_date": {
                    "type": "string",
                    "description": "Due date in ISO format",
                },
                "grant_id": {
                    "type": "string",
                    "description": "Associated grant ID",
                },
                "funder": {
                    "type": "string",
                    "description": "Funder name",
                },
                "priority": {
                    "type": "integer",
                    "minimum": 1,
                    "maximum": 5,
                    "description": "Priority level",
                },
                "note": {
                    "type": "string",
                    "description": "Note to add",
                },
                "status_filter": {
                    "type": "string",
                    "enum": [s.value for s in DeadlineStatus],
                    "description": "Filter by status",
                },
                "days_ahead": {
                    "type": "integer",
                    "description": "Only show deadlines within this many days",
                },
            },
        }
