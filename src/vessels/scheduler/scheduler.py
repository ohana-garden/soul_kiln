"""
Task Scheduler implementation.

Provides cron-based, datetime-based, and ad-hoc task scheduling.
"""

import logging
import re
import threading
import time
from datetime import datetime, timedelta
from typing import Any, Callable

from .tasks import ScheduledTask, TaskType, TaskState

logger = logging.getLogger(__name__)


class CronParser:
    """
    Simple cron expression parser.

    Supports 5-field cron expressions:
    minute hour day_of_month month day_of_week

    Special characters: * , - /
    """

    @staticmethod
    def parse_field(field: str, min_val: int, max_val: int) -> set[int]:
        """Parse a single cron field into a set of values."""
        values = set()

        for part in field.split(","):
            # Handle */n (every n)
            if part.startswith("*/"):
                step = int(part[2:])
                values.update(range(min_val, max_val + 1, step))

            # Handle n-m (range)
            elif "-" in part and not part.startswith("-"):
                start, end = part.split("-")
                values.update(range(int(start), int(end) + 1))

            # Handle n/m (start at n, every m)
            elif "/" in part:
                base, step = part.split("/")
                start = min_val if base == "*" else int(base)
                values.update(range(start, max_val + 1, int(step)))

            # Handle * (all)
            elif part == "*":
                values.update(range(min_val, max_val + 1))

            # Handle single value
            else:
                values.add(int(part))

        return values

    @classmethod
    def parse(cls, expression: str) -> dict[str, set[int]]:
        """
        Parse a cron expression into field values.

        Args:
            expression: Cron expression (5 fields)

        Returns:
            Dict with minute, hour, day, month, weekday sets
        """
        parts = expression.strip().split()
        if len(parts) != 5:
            raise ValueError(f"Invalid cron expression: {expression} (need 5 fields)")

        return {
            "minute": cls.parse_field(parts[0], 0, 59),
            "hour": cls.parse_field(parts[1], 0, 23),
            "day": cls.parse_field(parts[2], 1, 31),
            "month": cls.parse_field(parts[3], 1, 12),
            "weekday": cls.parse_field(parts[4], 0, 6),  # 0=Sunday
        }

    @classmethod
    def get_next_run(cls, expression: str, after: datetime | None = None) -> datetime:
        """
        Calculate the next run time for a cron expression.

        Args:
            expression: Cron expression
            after: Start time (default: now)

        Returns:
            Next datetime matching the expression
        """
        parsed = cls.parse(expression)
        current = (after or datetime.utcnow()) + timedelta(minutes=1)
        current = current.replace(second=0, microsecond=0)

        # Search for next matching time (limit iterations)
        for _ in range(525600):  # Max 1 year of minutes
            if (
                current.minute in parsed["minute"]
                and current.hour in parsed["hour"]
                and current.day in parsed["day"]
                and current.month in parsed["month"]
                and current.weekday() in parsed["weekday"]
            ):
                return current
            current += timedelta(minutes=1)

        raise ValueError(f"Could not find next run time for: {expression}")


class TaskScheduler:
    """
    Task scheduler with cron, planned, and ad-hoc support.

    Features:
    - Create scheduled, planned, and ad-hoc tasks
    - Automatic execution based on schedule
    - Task management (list, find, show, run, delete)
    - Wait for task completion
    """

    def __init__(
        self,
        executor: Callable[[ScheduledTask], Any] | None = None,
        auto_start: bool = False,
        poll_interval: float = 60.0,
    ):
        """
        Initialize scheduler.

        Args:
            executor: Function to execute tasks
            auto_start: Start scheduler loop automatically
            poll_interval: Seconds between schedule checks
        """
        self._tasks: dict[str, ScheduledTask] = {}
        self._executor = executor or self._default_executor
        self._poll_interval = poll_interval
        self._running = False
        self._thread: threading.Thread | None = None
        self._lock = threading.RLock()
        self._func_registry: dict[str, Callable] = {}

        if auto_start:
            self.start()

    def _default_executor(self, task: ScheduledTask) -> Any:
        """Default executor - calls registered function or raises error."""
        if task.func:
            return task.func(*task.args, **task.kwargs)
        elif task.func_name and task.func_name in self._func_registry:
            func = self._func_registry[task.func_name]
            return func(*task.args, **task.kwargs)
        else:
            raise NotImplementedError(
                f"No executor configured for task {task.id}. "
                "Provide a func, register a func_name, or set a global executor."
            )

    def register_function(self, name: str, func: Callable) -> None:
        """Register a function for use in tasks."""
        self._func_registry[name] = func

    def create_scheduled(
        self,
        name: str,
        cron_expression: str,
        func: Callable | None = None,
        func_name: str = "",
        system_prompt: str | None = None,
        user_prompt: str | None = None,
        **kwargs,
    ) -> ScheduledTask:
        """
        Create a cron-scheduled recurring task.

        Args:
            name: Task name
            cron_expression: 5-field cron expression
            func: Function to execute
            func_name: Or name of registered function
            system_prompt: System prompt for AI tasks
            user_prompt: User prompt for AI tasks
            **kwargs: Additional task kwargs

        Returns:
            Created task
        """
        # Validate cron expression
        CronParser.parse(cron_expression)
        next_run = CronParser.get_next_run(cron_expression)

        task = ScheduledTask(
            name=name,
            task_type=TaskType.SCHEDULED,
            func=func,
            func_name=func_name,
            cron_expression=cron_expression,
            next_run=next_run,
            system_prompt=system_prompt,
            user_prompt=user_prompt,
            **kwargs,
        )

        with self._lock:
            self._tasks[task.id] = task

        logger.info(f"Created scheduled task {task.id}: {name} ({cron_expression})")
        return task

    def create_planned(
        self,
        name: str,
        run_at: datetime,
        func: Callable | None = None,
        func_name: str = "",
        system_prompt: str | None = None,
        user_prompt: str | None = None,
        **kwargs,
    ) -> ScheduledTask:
        """
        Create a task planned for a specific datetime.

        Args:
            name: Task name
            run_at: When to run the task
            func: Function to execute
            func_name: Or name of registered function
            system_prompt: System prompt for AI tasks
            user_prompt: User prompt for AI tasks
            **kwargs: Additional task kwargs

        Returns:
            Created task
        """
        task = ScheduledTask(
            name=name,
            task_type=TaskType.PLANNED,
            func=func,
            func_name=func_name,
            planned_datetime=run_at,
            next_run=run_at,
            system_prompt=system_prompt,
            user_prompt=user_prompt,
            **kwargs,
        )

        with self._lock:
            self._tasks[task.id] = task

        logger.info(f"Created planned task {task.id}: {name} (at {run_at})")
        return task

    def create_adhoc(
        self,
        name: str,
        func: Callable | None = None,
        func_name: str = "",
        system_prompt: str | None = None,
        user_prompt: str | None = None,
        **kwargs,
    ) -> ScheduledTask:
        """
        Create an ad-hoc manually-triggered task.

        Args:
            name: Task name
            func: Function to execute
            func_name: Or name of registered function
            system_prompt: System prompt for AI tasks
            user_prompt: User prompt for AI tasks
            **kwargs: Additional task kwargs

        Returns:
            Created task
        """
        task = ScheduledTask(
            name=name,
            task_type=TaskType.ADHOC,
            func=func,
            func_name=func_name,
            system_prompt=system_prompt,
            user_prompt=user_prompt,
            **kwargs,
        )

        with self._lock:
            self._tasks[task.id] = task

        logger.info(f"Created ad-hoc task {task.id}: {name}")
        return task

    def run_task(self, task_id: str) -> Any:
        """
        Run a task immediately.

        Args:
            task_id: Task to run

        Returns:
            Task result
        """
        task = self._tasks.get(task_id)
        if not task:
            raise ValueError(f"Task not found: {task_id}")

        if task.state == TaskState.RUNNING:
            raise ValueError(f"Task {task_id} is already running")

        if task.reached_max_runs:
            raise ValueError(f"Task {task_id} has reached max runs")

        task.mark_started()

        try:
            result = self._executor(task)
            task.mark_completed(result)

            # Update next run for recurring tasks
            if task.is_recurring:
                task.next_run = CronParser.get_next_run(
                    task.cron_expression, task.last_run
                )
                task.state = TaskState.PENDING

            logger.debug(f"Task {task_id} completed successfully")
            return result

        except Exception as e:
            task.mark_failed(str(e))
            logger.error(f"Task {task_id} failed: {e}")
            raise

    def delete_task(self, task_id: str) -> bool:
        """Delete a task."""
        with self._lock:
            if task_id in self._tasks:
                del self._tasks[task_id]
                logger.info(f"Deleted task {task_id}")
                return True
            return False

    def get_task(self, task_id: str) -> ScheduledTask | None:
        """Get a task by ID."""
        return self._tasks.get(task_id)

    def find_task(self, name: str) -> ScheduledTask | None:
        """Find a task by name."""
        for task in self._tasks.values():
            if task.name == name:
                return task
        return None

    def list_tasks(
        self,
        task_type: TaskType | None = None,
        state: TaskState | None = None,
    ) -> list[ScheduledTask]:
        """List tasks with optional filters."""
        tasks = list(self._tasks.values())

        if task_type:
            tasks = [t for t in tasks if t.task_type == task_type]
        if state:
            tasks = [t for t in tasks if t.state == state]

        return tasks

    def get_due_tasks(self) -> list[ScheduledTask]:
        """Get tasks that are due for execution."""
        now = datetime.utcnow()
        due = []

        for task in self._tasks.values():
            if not task.is_active:
                continue
            if task.reached_max_runs:
                continue
            if task.next_run and task.next_run <= now:
                due.append(task)

        return due

    def wait_for_task(
        self,
        task_id: str,
        timeout_seconds: float | None = None,
        poll_interval: float = 1.0,
    ) -> ScheduledTask:
        """
        Wait for a task to complete.

        Args:
            task_id: Task to wait for
            timeout_seconds: Maximum wait time
            poll_interval: Polling interval

        Returns:
            The completed task
        """
        task = self._tasks.get(task_id)
        if not task:
            raise ValueError(f"Task not found: {task_id}")

        start = time.time()
        timeout = timeout_seconds or task.timeout_seconds

        while task.state == TaskState.RUNNING:
            if time.time() - start > timeout:
                task.mark_failed("Wait timeout")
                break
            time.sleep(poll_interval)

        return task

    def start(self) -> None:
        """Start the scheduler loop."""
        if self._running:
            return

        self._running = True
        self._thread = threading.Thread(target=self._scheduler_loop, daemon=True)
        self._thread.start()
        logger.info("Task scheduler started")

    def stop(self) -> None:
        """Stop the scheduler loop."""
        self._running = False
        if self._thread:
            self._thread.join(timeout=5.0)
            self._thread = None
        logger.info("Task scheduler stopped")

    def _scheduler_loop(self) -> None:
        """Main scheduler loop."""
        while self._running:
            try:
                # Check for due tasks
                due_tasks = self.get_due_tasks()
                for task in due_tasks:
                    try:
                        self.run_task(task.id)
                    except Exception as e:
                        logger.error(f"Error running task {task.id}: {e}")

            except Exception as e:
                logger.error(f"Scheduler loop error: {e}")

            time.sleep(self._poll_interval)

    def get_stats(self) -> dict:
        """Get scheduler statistics."""
        with self._lock:
            states = {}
            types = {}
            for task in self._tasks.values():
                state = task.state.value
                states[state] = states.get(state, 0) + 1
                t = task.task_type.value
                types[t] = types.get(t, 0) + 1

            return {
                "total_tasks": len(self._tasks),
                "running": self._running,
                "by_state": states,
                "by_type": types,
                "due_count": len(self.get_due_tasks()),
            }

    def export_tasks(self) -> list[dict]:
        """Export all tasks as dictionaries."""
        return [task.to_dict() for task in self._tasks.values()]

    def import_tasks(self, data: list[dict]) -> int:
        """Import tasks from dictionaries."""
        imported = 0
        for item in data:
            task = ScheduledTask.from_dict(item)
            # Re-register function if available
            if task.func_name and task.func_name in self._func_registry:
                task.func = self._func_registry[task.func_name]
            self._tasks[task.id] = task
            imported += 1
        return imported
