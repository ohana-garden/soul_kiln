"""
Agent Intervention System.

Allows external redirection of agent execution mid-task.
Inspired by Vessels3 intervention handling.
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


class InterventionType(str, Enum):
    """Types of interventions."""

    REDIRECT = "redirect"  # Change the current task
    PAUSE = "pause"  # Pause execution
    RESUME = "resume"  # Resume execution
    CANCEL = "cancel"  # Cancel current operation
    INJECT = "inject"  # Inject additional context
    PRIORITY = "priority"  # Change task priority
    FEEDBACK = "feedback"  # Provide feedback on output


class InterventionPriority(str, Enum):
    """Priority levels for interventions."""

    LOW = "low"
    NORMAL = "normal"
    HIGH = "high"
    CRITICAL = "critical"


@dataclass
class Intervention:
    """
    An intervention in agent execution.

    Interventions allow users to redirect, pause, or modify
    agent behavior during execution.
    """

    id: str = field(default_factory=lambda: f"int_{uuid.uuid4().hex[:12]}")
    type: InterventionType = InterventionType.REDIRECT
    priority: InterventionPriority = InterventionPriority.NORMAL
    message: str = ""
    context_id: str | None = None
    agent_id: str | None = None
    payload: dict = field(default_factory=dict)
    created_at: datetime = field(default_factory=datetime.utcnow)
    processed_at: datetime | None = None
    success: bool = False
    response: str | None = None

    def to_dict(self) -> dict:
        """Convert to dictionary."""
        return {
            "id": self.id,
            "type": self.type.value,
            "priority": self.priority.value,
            "message": self.message,
            "context_id": self.context_id,
            "agent_id": self.agent_id,
            "payload": self.payload,
            "created_at": self.created_at.isoformat(),
            "processed_at": self.processed_at.isoformat() if self.processed_at else None,
            "success": self.success,
            "response": self.response,
        }


class InterventionManager:
    """
    Manages interventions for agent contexts.

    Features:
    - Queue interventions for specific contexts or agents
    - Priority-based processing
    - Intervention history tracking
    - Callback support for intervention handling
    """

    def __init__(self, registry: ContextRegistry | None = None):
        """
        Initialize intervention manager.

        Args:
            registry: Context registry, uses singleton if not provided
        """
        self.registry = registry or ContextRegistry()
        self._pending: dict[str, list[Intervention]] = {}  # context_id -> interventions
        self._history: list[Intervention] = []
        self._max_history = 1000
        self._lock = threading.RLock()
        self._handlers: dict[InterventionType, list[Callable]] = {
            t: [] for t in InterventionType
        }

    def create_intervention(
        self,
        intervention_type: InterventionType,
        message: str,
        context_id: str | None = None,
        agent_id: str | None = None,
        priority: InterventionPriority = InterventionPriority.NORMAL,
        payload: dict | None = None,
    ) -> Intervention:
        """
        Create a new intervention.

        Args:
            intervention_type: Type of intervention
            message: Intervention message
            context_id: Target context ID
            agent_id: Target agent ID (will find active context)
            priority: Intervention priority
            payload: Additional data

        Returns:
            Created Intervention object
        """
        intervention = Intervention(
            type=intervention_type,
            priority=priority,
            message=message,
            context_id=context_id,
            agent_id=agent_id,
            payload=payload or {},
        )

        # Queue the intervention
        with self._lock:
            target_id = context_id

            # If agent_id provided, find active context
            if not target_id and agent_id:
                contexts = self.registry.get_for_agent(agent_id)
                active = [c for c in contexts if c.is_active()]
                if active:
                    target_id = active[0].id

            if target_id:
                if target_id not in self._pending:
                    self._pending[target_id] = []
                self._pending[target_id].append(intervention)
                # Sort by priority
                self._pending[target_id].sort(
                    key=lambda x: list(InterventionPriority).index(x.priority),
                    reverse=True,
                )

                logger.debug(
                    f"Queued {intervention_type.value} intervention for context {target_id}"
                )
            else:
                logger.warning(
                    f"Could not find target context for intervention: {intervention.id}"
                )

        return intervention

    def redirect(
        self,
        context_id: str,
        new_instruction: str,
        priority: InterventionPriority = InterventionPriority.HIGH,
    ) -> Intervention:
        """
        Redirect a context to a new task.

        Args:
            context_id: Context to redirect
            new_instruction: New instruction/task
            priority: Intervention priority

        Returns:
            Created intervention
        """
        return self.create_intervention(
            intervention_type=InterventionType.REDIRECT,
            message=new_instruction,
            context_id=context_id,
            priority=priority,
        )

    def pause(
        self,
        context_id: str,
        reason: str = "",
        duration_seconds: int | None = None,
    ) -> Intervention:
        """
        Pause a context.

        Args:
            context_id: Context to pause
            reason: Reason for pause
            duration_seconds: Auto-resume duration

        Returns:
            Created intervention
        """
        return self.create_intervention(
            intervention_type=InterventionType.PAUSE,
            message=reason,
            context_id=context_id,
            priority=InterventionPriority.HIGH,
            payload={"duration_seconds": duration_seconds},
        )

    def resume(self, context_id: str) -> Intervention:
        """
        Resume a paused context.

        Args:
            context_id: Context to resume

        Returns:
            Created intervention
        """
        return self.create_intervention(
            intervention_type=InterventionType.RESUME,
            message="Resume execution",
            context_id=context_id,
            priority=InterventionPriority.HIGH,
        )

    def cancel(self, context_id: str, reason: str = "") -> Intervention:
        """
        Cancel current operation in a context.

        Args:
            context_id: Context to cancel
            reason: Cancellation reason

        Returns:
            Created intervention
        """
        return self.create_intervention(
            intervention_type=InterventionType.CANCEL,
            message=reason,
            context_id=context_id,
            priority=InterventionPriority.CRITICAL,
        )

    def inject_context(
        self,
        context_id: str,
        additional_info: str,
        payload: dict | None = None,
    ) -> Intervention:
        """
        Inject additional context into an agent.

        Args:
            context_id: Target context
            additional_info: Information to inject
            payload: Additional structured data

        Returns:
            Created intervention
        """
        return self.create_intervention(
            intervention_type=InterventionType.INJECT,
            message=additional_info,
            context_id=context_id,
            priority=InterventionPriority.NORMAL,
            payload=payload,
        )

    def provide_feedback(
        self,
        context_id: str,
        feedback: str,
        rating: int | None = None,
    ) -> Intervention:
        """
        Provide feedback on agent output.

        Args:
            context_id: Target context
            feedback: Feedback message
            rating: Optional numeric rating

        Returns:
            Created intervention
        """
        return self.create_intervention(
            intervention_type=InterventionType.FEEDBACK,
            message=feedback,
            context_id=context_id,
            priority=InterventionPriority.NORMAL,
            payload={"rating": rating} if rating is not None else {},
        )

    def get_pending(self, context_id: str) -> list[Intervention]:
        """Get pending interventions for a context."""
        with self._lock:
            return list(self._pending.get(context_id, []))

    def pop_next(self, context_id: str) -> Intervention | None:
        """Pop and return the next intervention for a context."""
        with self._lock:
            interventions = self._pending.get(context_id, [])
            if interventions:
                return interventions.pop(0)
            return None

    def process_intervention(
        self,
        intervention: Intervention,
        context: AgentContext,
    ) -> bool:
        """
        Process an intervention.

        Args:
            intervention: Intervention to process
            context: Target context

        Returns:
            True if successful
        """
        intervention.processed_at = datetime.utcnow()

        try:
            # Handle built-in intervention types
            if intervention.type == InterventionType.PAUSE:
                duration = intervention.payload.get("duration_seconds")
                context.pause(duration)
                intervention.success = True
                intervention.response = "Context paused"

            elif intervention.type == InterventionType.RESUME:
                context.resume()
                intervention.success = True
                intervention.response = "Context resumed"

            elif intervention.type == InterventionType.CANCEL:
                context.set_state(ContextState.FAILED)
                intervention.success = True
                intervention.response = "Operation cancelled"

            elif intervention.type == InterventionType.REDIRECT:
                # Add redirect message to intervention queue
                context.add_intervention(intervention.message)
                intervention.success = True
                intervention.response = "Redirect queued"

            elif intervention.type == InterventionType.INJECT:
                context.add_intervention(intervention.message)
                context.metadata.update(intervention.payload)
                intervention.success = True
                intervention.response = "Context injected"

            elif intervention.type == InterventionType.FEEDBACK:
                context.add_intervention(f"[FEEDBACK] {intervention.message}")
                intervention.success = True
                intervention.response = "Feedback delivered"

            # Call registered handlers
            for handler in self._handlers.get(intervention.type, []):
                try:
                    handler(intervention, context)
                except Exception as e:
                    logger.error(f"Intervention handler error: {e}")

        except Exception as e:
            intervention.success = False
            intervention.response = str(e)
            logger.error(f"Failed to process intervention {intervention.id}: {e}")

        # Add to history
        with self._lock:
            self._history.append(intervention)
            if len(self._history) > self._max_history:
                self._history = self._history[-self._max_history // 2 :]

        return intervention.success

    def process_all_pending(self) -> int:
        """
        Process all pending interventions across contexts.

        Returns:
            Number of interventions processed
        """
        processed = 0

        with self._lock:
            context_ids = list(self._pending.keys())

        for context_id in context_ids:
            context = self.registry.get(context_id)
            if not context:
                continue

            while True:
                intervention = self.pop_next(context_id)
                if intervention is None:
                    break
                self.process_intervention(intervention, context)
                processed += 1

        return processed

    def register_handler(
        self,
        intervention_type: InterventionType,
        handler: Callable[[Intervention, AgentContext], None],
    ) -> None:
        """Register a handler for an intervention type."""
        self._handlers[intervention_type].append(handler)

    def get_history(
        self,
        context_id: str | None = None,
        intervention_type: InterventionType | None = None,
        limit: int = 100,
    ) -> list[Intervention]:
        """Get intervention history."""
        with self._lock:
            history = self._history

            if context_id:
                history = [i for i in history if i.context_id == context_id]
            if intervention_type:
                history = [i for i in history if i.type == intervention_type]

            return history[-limit:]

    def get_stats(self) -> dict:
        """Get intervention statistics."""
        with self._lock:
            type_counts = {}
            success_count = 0
            for intervention in self._history:
                t = intervention.type.value
                type_counts[t] = type_counts.get(t, 0) + 1
                if intervention.success:
                    success_count += 1

            pending_count = sum(len(v) for v in self._pending.values())

            return {
                "total_processed": len(self._history),
                "pending_count": pending_count,
                "success_count": success_count,
                "success_rate": (
                    success_count / len(self._history) if self._history else 0.0
                ),
                "by_type": type_counts,
            }
