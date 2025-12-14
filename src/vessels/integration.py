"""
Integration Module for Soul Kiln.

Connects Vessels capabilities with existing soul_kiln systems:
- Memory integration with knowledge pool
- Agent context with virtue agents
- Scheduler with kiln loop
"""

import logging
from datetime import datetime
from typing import Any

from .memory import SemanticMemory, MemoryStore
from .agents import AgentContext, ContextRegistry, InterventionManager, SubordinateManager
from .scheduler import TaskScheduler, ScheduledTask, TaskType
from .tools import BehaviorAdjuster, BehaviorProfile, BehaviorDimension
from .runtime import DeferredTaskManager, SessionManager

logger = logging.getLogger(__name__)


class VesselsIntegration:
    """
    Integrates Vessels capabilities with soul_kiln.

    Provides a unified interface for:
    - Enhanced memory for agents with semantic search
    - Agent context management with interventions
    - Task scheduling for automated virtue testing
    - Behavior adjustment based on virtue profiles
    """

    def __init__(
        self,
        memory_dir: str = "data/vessels/memories",
        max_memories: int = 10000,
    ):
        """
        Initialize vessels integration.

        Args:
            memory_dir: Directory for memory storage
            max_memories: Maximum memories to store
        """
        # Initialize core systems
        self.semantic_memory = SemanticMemory(max_memories=max_memories)
        self.memory_store = MemoryStore(self.semantic_memory, storage_dir=memory_dir)

        self.context_registry = ContextRegistry()
        self.intervention_manager = InterventionManager(self.context_registry)
        self.subordinate_manager = SubordinateManager(self.context_registry)

        self.scheduler = TaskScheduler(auto_start=False)
        self.behavior_adjuster = BehaviorAdjuster()
        self.deferred_tasks = DeferredTaskManager(auto_start=True)
        self.session_manager = SessionManager(auto_start=True)

        self._initialized = False

    def initialize(self) -> None:
        """Initialize all systems."""
        if self._initialized:
            return

        # Load stored memories
        self.memory_store.load_latest()

        # Start scheduler
        self.scheduler.start()

        # Create default behavior profiles
        self._create_virtue_profiles()

        self._initialized = True
        logger.info("Vessels integration initialized")

    def shutdown(self) -> None:
        """Shutdown all systems."""
        # Save memories
        self.memory_store.save_to_file()

        # Stop background services
        self.scheduler.stop()
        self.session_manager.stop()
        self.deferred_tasks.stop()

        self._initialized = False
        logger.info("Vessels integration shutdown")

    def _create_virtue_profiles(self) -> None:
        """Create behavior profiles aligned with virtue system."""
        # Trustworthy profile - foundation virtue
        self.behavior_adjuster.create_profile(
            name="trustworthy",
            description="High caution, low autonomy - aligned with trustworthiness",
            dimensions={
                BehaviorDimension.CAUTION.value: 0.9,
                BehaviorDimension.AUTONOMY.value: -0.5,
                BehaviorDimension.PERSISTENCE.value: 0.7,
            },
        )

        # Wise profile - wisdom virtue
        self.behavior_adjuster.create_profile(
            name="wise",
            description="Balanced, thorough approach - aligned with wisdom",
            dimensions={
                BehaviorDimension.CREATIVITY.value: 0.3,
                BehaviorDimension.SPEED.value: -0.3,
                BehaviorDimension.VERBOSITY.value: 0.5,
                BehaviorDimension.CAUTION.value: 0.4,
            },
        )

        # Service profile - service virtue
        self.behavior_adjuster.create_profile(
            name="service",
            description="Responsive, helpful - aligned with service",
            dimensions={
                BehaviorDimension.SPEED.value: 0.5,
                BehaviorDimension.PERSISTENCE.value: 0.6,
                BehaviorDimension.AUTONOMY.value: 0.3,
            },
        )

    # Memory Integration

    def remember_lesson(
        self,
        agent_id: str,
        lesson_type: str,
        content: str,
        virtue_id: str | None = None,
    ) -> str:
        """
        Store a lesson in semantic memory.

        Args:
            agent_id: Agent who learned
            lesson_type: Type of lesson
            content: Lesson content
            virtue_id: Related virtue

        Returns:
            Memory ID
        """
        tags = [lesson_type]
        if virtue_id:
            tags.append(virtue_id)

        return self.memory_store.save_memory(
            content=content,
            agent_id=agent_id,
            tags=tags,
            metadata={
                "lesson_type": lesson_type,
                "virtue_id": virtue_id,
                "timestamp": datetime.utcnow().isoformat(),
            },
        )

    def recall_lessons(
        self,
        query: str,
        agent_id: str | None = None,
        virtue_id: str | None = None,
        limit: int = 10,
    ) -> list[dict]:
        """
        Recall lessons from semantic memory.

        Args:
            query: Search query
            agent_id: Filter by agent
            virtue_id: Filter by virtue
            limit: Max results

        Returns:
            List of lesson dictionaries
        """
        tags = [virtue_id] if virtue_id else None

        memories = self.memory_store.search_memories(
            query=query,
            agent_id=agent_id,
            tags=tags,
            limit=limit,
        )

        return [
            {
                "id": m.id,
                "content": m.content,
                "agent_id": m.agent_id,
                "metadata": m.metadata,
                "access_count": m.access_count,
            }
            for m in memories
        ]

    # Agent Context Integration

    def create_agent_context(
        self,
        agent_id: str,
        virtue_profile: str = "trustworthy",
    ) -> AgentContext:
        """
        Create a context for an agent with virtue-aligned behavior.

        Args:
            agent_id: Agent ID
            virtue_profile: Behavior profile to apply

        Returns:
            Created AgentContext
        """
        context = AgentContext(agent_id=agent_id)
        self.context_registry.register(context)

        # Apply behavior profile
        profile = self.behavior_adjuster.get_profile_by_name(virtue_profile)
        if profile:
            self.behavior_adjuster.assign_profile(agent_id, profile.id)

        return context

    def intervene_agent(
        self,
        agent_id: str,
        message: str,
    ) -> bool:
        """
        Send an intervention to an agent.

        Args:
            agent_id: Target agent
            message: Intervention message

        Returns:
            True if intervention queued
        """
        contexts = self.context_registry.get_for_agent(agent_id)
        if not contexts:
            return False

        for context in contexts:
            if context.is_active():
                self.intervention_manager.redirect(context.id, message)
                return True

        return False

    # Scheduler Integration

    def schedule_virtue_test(
        self,
        agent_id: str,
        cron_expression: str = "0 */6 * * *",  # Every 6 hours
        test_func: Any = None,
    ) -> ScheduledTask:
        """
        Schedule recurring virtue testing for an agent.

        Args:
            agent_id: Agent to test
            cron_expression: When to test
            test_func: Test function

        Returns:
            Created task
        """
        return self.scheduler.create_scheduled(
            name=f"virtue_test_{agent_id}",
            cron_expression=cron_expression,
            func=test_func,
            metadata={"agent_id": agent_id},
        )

    def schedule_memory_consolidation(
        self,
        cron_expression: str = "0 0 * * *",  # Daily at midnight
    ) -> ScheduledTask:
        """
        Schedule memory consolidation.

        Args:
            cron_expression: When to consolidate

        Returns:
            Created task
        """
        return self.scheduler.create_scheduled(
            name="memory_consolidation",
            cron_expression=cron_expression,
            func=lambda: self.semantic_memory.consolidate(),
        )

    # Behavior Integration

    def adjust_for_virtue_violation(
        self,
        agent_id: str,
        virtue_id: str,
        severity: float = 0.1,
    ) -> None:
        """
        Adjust agent behavior after a virtue violation.

        Args:
            agent_id: Agent who violated
            virtue_id: Violated virtue
            severity: Violation severity (0-1)
        """
        # Increase caution after violations
        self.behavior_adjuster.adjust_agent_behavior(
            agent_id,
            BehaviorDimension.CAUTION,
            severity,
        )

        # Decrease autonomy temporarily
        self.behavior_adjuster.adjust_agent_behavior(
            agent_id,
            BehaviorDimension.AUTONOMY,
            -severity * 0.5,
        )

    def adjust_for_virtue_achievement(
        self,
        agent_id: str,
        virtue_id: str,
        magnitude: float = 0.05,
    ) -> None:
        """
        Adjust agent behavior after virtue achievement.

        Args:
            agent_id: Agent who achieved
            virtue_id: Achieved virtue
            magnitude: Achievement magnitude (0-1)
        """
        # Slightly increase autonomy for good behavior
        self.behavior_adjuster.adjust_agent_behavior(
            agent_id,
            BehaviorDimension.AUTONOMY,
            magnitude * 0.3,
        )

    # Status

    def get_status(self) -> dict:
        """Get integration status."""
        return {
            "initialized": self._initialized,
            "memory": self.semantic_memory.get_stats(),
            "contexts": self.context_registry.get_stats(),
            "scheduler": self.scheduler.get_stats(),
            "behavior": self.behavior_adjuster.get_stats(),
            "deferred": self.deferred_tasks.get_stats(),
            "sessions": self.session_manager.get_stats(),
        }


# Singleton instance
_integration: VesselsIntegration | None = None


def get_integration() -> VesselsIntegration:
    """Get the singleton integration instance."""
    global _integration
    if _integration is None:
        _integration = VesselsIntegration()
    return _integration


def initialize_vessels() -> VesselsIntegration:
    """Initialize and return the vessels integration."""
    integration = get_integration()
    integration.initialize()
    return integration
