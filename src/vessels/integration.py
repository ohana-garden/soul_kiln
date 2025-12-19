"""
Integration Module for Soul Kiln.

Connects Vessels capabilities with existing soul_kiln systems:
- Memory integration with knowledge pool (Graphiti + FalkorDB)
- Agent context with virtue agents
- Scheduler with kiln loop
"""

import asyncio
import logging
import os
from datetime import datetime
from typing import Any

from .memory import SemanticMemory, MemoryStore, GraphitiMemory
from .agents import AgentContext, ContextRegistry, InterventionManager, SubordinateManager
from .scheduler import TaskScheduler, ScheduledTask, TaskType
from .tools import BehaviorAdjuster, BehaviorProfile, BehaviorDimension
from .runtime import DeferredTaskManager, SessionManager

logger = logging.getLogger(__name__)


class VesselsIntegration:
    """
    Integrates Vessels capabilities with soul_kiln.

    Provides a unified interface for:
    - Enhanced memory for agents with semantic search (Graphiti + FalkorDB)
    - Agent context management with interventions
    - Task scheduling for automated virtue testing
    - Behavior adjustment based on virtue profiles
    """

    def __init__(
        self,
        memory_dir: str = "data/vessels/memories",
        max_memories: int = 10000,
        use_graphiti: bool | None = None,
        graphiti_host: str | None = None,
        graphiti_port: int | None = None,
    ):
        """
        Initialize vessels integration.

        Args:
            memory_dir: Directory for memory storage (fallback)
            max_memories: Maximum memories to store
            use_graphiti: Force Graphiti on/off (default: auto-detect)
            graphiti_host: FalkorDB host for Graphiti
            graphiti_port: FalkorDB port for Graphiti
        """
        # Determine whether to use Graphiti
        if use_graphiti is None:
            # Auto-detect: use Graphiti if FALKORDB_HOST is set
            use_graphiti = bool(os.getenv("FALKORDB_HOST"))

        self._use_graphiti = use_graphiti
        self._graphiti_initialized = False

        # Initialize Graphiti if enabled
        if use_graphiti:
            self.graphiti_memory = GraphitiMemory(
                host=graphiti_host,
                port=graphiti_port,
            )
            self.semantic_memory = None
            self.memory_store = None
            logger.info("Using Graphiti for memory (FalkorDB backend)")
        else:
            # Fallback to local semantic memory
            self.graphiti_memory = None
            self.semantic_memory = SemanticMemory(max_memories=max_memories)
            self.memory_store = MemoryStore(self.semantic_memory, storage_dir=memory_dir)
            logger.info("Using local SemanticMemory (fallback mode)")

        self.context_registry = ContextRegistry()
        self.intervention_manager = InterventionManager(self.context_registry)
        self.subordinate_manager = SubordinateManager(self.context_registry)

        self.scheduler = TaskScheduler(auto_start=False)
        self.behavior_adjuster = BehaviorAdjuster()
        self.deferred_tasks = DeferredTaskManager(auto_start=True)
        self.session_manager = SessionManager(auto_start=True)

        self._initialized = False
        self._loop = None

    def _get_loop(self) -> asyncio.AbstractEventLoop:
        """Get or create event loop for async operations."""
        if self._loop is None or self._loop.is_closed():
            try:
                self._loop = asyncio.get_running_loop()
            except RuntimeError:
                self._loop = asyncio.new_event_loop()
                asyncio.set_event_loop(self._loop)
        return self._loop

    def _run_async(self, coro):
        """Run async coroutine synchronously."""
        loop = self._get_loop()
        if loop.is_running():
            # Create a new thread for the coroutine
            import concurrent.futures
            with concurrent.futures.ThreadPoolExecutor() as executor:
                future = executor.submit(asyncio.run, coro)
                return future.result()
        else:
            return loop.run_until_complete(coro)

    def initialize(self) -> None:
        """Initialize all systems."""
        if self._initialized:
            return

        # Initialize Graphiti if enabled
        if self._use_graphiti and self.graphiti_memory:
            try:
                self._run_async(self.graphiti_memory.initialize())
                self._graphiti_initialized = True
                logger.info("Graphiti memory initialized")
            except Exception as e:
                logger.error(f"Failed to initialize Graphiti: {e}")
                logger.warning("Falling back to local semantic memory")
                self._use_graphiti = False
                self.graphiti_memory = None
                self.semantic_memory = SemanticMemory(max_memories=10000)
                self.memory_store = MemoryStore(self.semantic_memory)

        # Load stored memories (fallback mode only)
        if self.memory_store:
            self.memory_store.load_latest()

        # Start scheduler
        self.scheduler.start()

        # Create default behavior profiles
        self._create_virtue_profiles()

        self._initialized = True
        logger.info("Vessels integration initialized")

    def shutdown(self) -> None:
        """Shutdown all systems."""
        # Save memories or close Graphiti
        if self.memory_store:
            self.memory_store.save_to_file()
        if self.graphiti_memory and self._graphiti_initialized:
            try:
                self._run_async(self.graphiti_memory.close())
            except Exception as e:
                logger.warning(f"Error closing Graphiti: {e}")

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
        Store a lesson in memory (Graphiti or fallback).

        Args:
            agent_id: Agent who learned
            lesson_type: Type of lesson
            content: Lesson content
            virtue_id: Related virtue

        Returns:
            Memory ID
        """
        if self._use_graphiti and self.graphiti_memory:
            # Use Graphiti temporal knowledge graph
            return self._run_async(
                self.graphiti_memory.remember_lesson(
                    agent_id=agent_id,
                    lesson_type=lesson_type,
                    content=content,
                    virtue_id=virtue_id,
                )
            )
        else:
            # Fallback to local memory store
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
        Recall lessons from memory (Graphiti or fallback).

        Args:
            query: Search query
            agent_id: Filter by agent
            virtue_id: Filter by virtue
            limit: Max results

        Returns:
            List of lesson dictionaries
        """
        if self._use_graphiti and self.graphiti_memory:
            # Use Graphiti search
            return self._run_async(
                self.graphiti_memory.recall_lessons(
                    query=query,
                    agent_id=agent_id,
                    virtue_id=virtue_id,
                    limit=limit,
                )
            )
        else:
            # Fallback to local memory store
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

    def record_pathway(
        self,
        agent_id: str,
        virtue_id: str,
        path: list[str],
        capture_time: int,
        success: bool = True,
    ) -> str | None:
        """
        Record a successful pathway to a virtue.

        Args:
            agent_id: Agent who discovered the pathway
            virtue_id: Target virtue
            path: Sequence of nodes traversed
            capture_time: Steps to capture
            success: Whether pathway was successful

        Returns:
            Pathway ID if using Graphiti, None otherwise
        """
        if self._use_graphiti and self.graphiti_memory:
            return self._run_async(
                self.graphiti_memory.record_pathway(
                    agent_id=agent_id,
                    virtue_id=virtue_id,
                    path=path,
                    capture_time=capture_time,
                    success=success,
                )
            )
        return None

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
    ) -> ScheduledTask | None:
        """
        Schedule memory consolidation.

        Args:
            cron_expression: When to consolidate

        Returns:
            Created task (only for fallback mode)
        """
        # Graphiti handles its own consolidation
        if self._use_graphiti:
            return None

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
        # Get memory stats based on mode
        if self._use_graphiti and self.graphiti_memory:
            memory_stats = self._run_async(self.graphiti_memory.get_stats())
            memory_stats["mode"] = "graphiti"
        elif self.semantic_memory:
            memory_stats = self.semantic_memory.get_stats()
            memory_stats["mode"] = "semantic_fallback"
        else:
            memory_stats = {"mode": "none"}

        return {
            "initialized": self._initialized,
            "use_graphiti": self._use_graphiti,
            "graphiti_initialized": self._graphiti_initialized,
            "memory": memory_stats,
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
