"""
Tests for Vessels integration module.
"""

import pytest
import time
from datetime import datetime, timedelta

from src.vessels.memory import SemanticMemory, MemoryEntry
from src.vessels.agents import AgentContext, ContextRegistry, InterventionManager, SubordinateManager
from src.vessels.agents.context import ContextState
from src.vessels.agents.intervention import InterventionType
from src.vessels.scheduler import TaskScheduler, ScheduledTask, TaskType, TaskState
from src.vessels.tools import CodeExecutor, Runtime, A2AChat, BehaviorAdjuster
from src.vessels.tools.behavior import BehaviorDimension
from src.vessels.models import ChatGenerationResult, ModelConfig, ModelWrapper
from src.vessels.runtime import DeferredTaskManager, SessionManager, Session


class TestSemanticMemory:
    """Tests for SemanticMemory."""

    def test_save_and_load(self):
        """Test saving and loading memories."""
        memory = SemanticMemory()

        # Save a memory
        mem_id = memory.save(
            content="Test lesson about trustworthiness",
            agent_id="agent_001",
            tags=["lesson", "V01"],
        )

        assert mem_id is not None
        assert mem_id.startswith("mem_")

        # Load by query
        results = memory.load(query="trustworthiness", limit=5)
        assert len(results) > 0
        assert results[0].content == "Test lesson about trustworthiness"

    def test_memory_filtering(self):
        """Test filtering memories."""
        memory = SemanticMemory()

        # Save multiple memories
        memory.save("Lesson 1", agent_id="agent_001", tags=["type_a"])
        memory.save("Lesson 2", agent_id="agent_002", tags=["type_b"])
        memory.save("Lesson 3", agent_id="agent_001", tags=["type_a"])

        # Filter by agent
        results = memory.get_all(agent_id="agent_001")
        assert len(results) == 2

        # Filter by tags
        results = memory.get_all(tags=["type_b"])
        assert len(results) == 1

    def test_memory_delete(self):
        """Test deleting memories."""
        memory = SemanticMemory()

        mem_id = memory.save("To be deleted", agent_id="agent_001")
        assert memory.get(mem_id) is not None

        deleted = memory.delete(mem_id)
        assert deleted == 1
        assert memory.get(mem_id) is None

    def test_memory_forget(self):
        """Test forgetting memories by query."""
        memory = SemanticMemory()

        memory.save("Important lesson to keep", agent_id="agent_001")
        memory.save("Duplicate lesson duplicate", agent_id="agent_001")
        memory.save("Another duplicate lesson", agent_id="agent_001")

        # Forget duplicates
        forgotten = memory.forget("duplicate", threshold=0.5)
        assert forgotten >= 1


class TestAgentContext:
    """Tests for AgentContext."""

    def test_context_lifecycle(self):
        """Test context state transitions."""
        context = AgentContext(agent_id="agent_001")

        assert context.state == ContextState.IDLE

        context.set_state(ContextState.RUNNING)
        assert context.state == ContextState.RUNNING

        context.pause(duration_seconds=60)
        assert context.state == ContextState.PAUSED
        assert context.pause_until is not None

    def test_context_auto_resume(self):
        """Test auto-resume functionality."""
        context = AgentContext(agent_id="agent_001")
        context.set_state(ContextState.RUNNING)

        # Pause with short duration
        context.pause(duration_seconds=0)

        # Should be ready to auto-resume immediately
        assert context.should_auto_resume()

        context.check_auto_resume()
        assert context.state == ContextState.RUNNING

    def test_intervention_queue(self):
        """Test intervention message queue."""
        context = AgentContext(agent_id="agent_001")

        context.add_intervention("Message 1")
        context.add_intervention("Message 2")

        assert context.has_interventions()
        assert context.pop_intervention() == "Message 1"
        assert context.pop_intervention() == "Message 2"
        assert not context.has_interventions()

    def test_deferred_tasks(self):
        """Test deferred task execution."""
        context = AgentContext(agent_id="agent_001")

        results = []
        task_id = context.add_deferred_task(
            lambda x: results.append(x), "executed"
        )

        assert task_id is not None

        # Execute ready tasks
        executed = context.execute_ready_tasks()
        assert len(executed) == 1
        assert results == ["executed"]


class TestContextRegistry:
    """Tests for ContextRegistry."""

    def test_registry_singleton(self):
        """Test registry is singleton."""
        reg1 = ContextRegistry()
        reg2 = ContextRegistry()
        assert reg1 is reg2

    def test_register_and_get(self):
        """Test registering and retrieving contexts."""
        registry = ContextRegistry()
        registry.clear()

        context = AgentContext(agent_id="agent_001")
        registry.register(context)

        assert registry.get(context.id) is context
        assert len(registry.get_for_agent("agent_001")) == 1

    def test_get_stuck_contexts(self):
        """Test stuck detection."""
        registry = ContextRegistry()
        registry.clear()

        context = AgentContext(agent_id="agent_001")
        context.set_state(ContextState.RUNNING)
        # Make it look old
        context.last_activity = datetime.utcnow() - timedelta(hours=1)
        registry.register(context)

        stuck = registry.get_stuck(threshold_seconds=60)
        assert len(stuck) == 1


class TestInterventionManager:
    """Tests for InterventionManager."""

    def test_create_intervention(self):
        """Test creating interventions."""
        registry = ContextRegistry()
        registry.clear()

        context = AgentContext(agent_id="agent_001")
        context.set_state(ContextState.RUNNING)
        registry.register(context)

        manager = InterventionManager(registry)

        intervention = manager.redirect(context.id, "Change direction")
        assert intervention.type == InterventionType.REDIRECT

        pending = manager.get_pending(context.id)
        assert len(pending) == 1

    def test_process_pause_intervention(self):
        """Test processing pause intervention."""
        registry = ContextRegistry()
        registry.clear()

        context = AgentContext(agent_id="agent_001")
        context.set_state(ContextState.RUNNING)
        registry.register(context)

        manager = InterventionManager(registry)
        intervention = manager.pause(context.id, "Testing", duration_seconds=60)

        manager.process_intervention(intervention, context)
        assert context.state == ContextState.PAUSED


class TestTaskScheduler:
    """Tests for TaskScheduler."""

    def test_create_adhoc_task(self):
        """Test creating ad-hoc task."""
        scheduler = TaskScheduler(auto_start=False)

        results = []
        task = scheduler.create_adhoc(
            name="test_task",
            func=lambda: results.append("executed"),
        )

        assert task.task_type == TaskType.ADHOC
        assert task.state == TaskState.PENDING

        scheduler.run_task(task.id)
        assert results == ["executed"]
        assert task.state == TaskState.COMPLETED

    def test_cron_parsing(self):
        """Test cron expression parsing."""
        from src.vessels.scheduler.scheduler import CronParser

        # Every minute
        parsed = CronParser.parse("* * * * *")
        assert len(parsed["minute"]) == 60
        assert len(parsed["hour"]) == 24

        # Every 5 minutes
        parsed = CronParser.parse("*/5 * * * *")
        assert 0 in parsed["minute"]
        assert 5 in parsed["minute"]
        assert 1 not in parsed["minute"]

    def test_scheduled_task(self):
        """Test scheduled recurring task."""
        scheduler = TaskScheduler(auto_start=False)

        results = []
        task = scheduler.create_scheduled(
            name="recurring",
            cron_expression="*/5 * * * *",
            func=lambda: results.append("tick"),
        )

        assert task.task_type == TaskType.SCHEDULED
        assert task.next_run is not None


class TestCodeExecutor:
    """Tests for CodeExecutor."""

    def test_execute_python(self):
        """Test Python code execution."""
        executor = CodeExecutor()

        result = executor.execute(
            code="print('Hello from Python')",
            runtime=Runtime.PYTHON,
        )

        assert result.success
        assert "Hello from Python" in result.stdout

    def test_execute_terminal(self):
        """Test terminal command execution."""
        executor = CodeExecutor()

        result = executor.execute(
            code="echo 'Hello from terminal'",
            runtime=Runtime.TERMINAL,
        )

        assert result.success
        assert "Hello from terminal" in result.stdout

    def test_session_reset(self):
        """Test session reset."""
        executor = CodeExecutor()

        result = executor.execute(
            code="",
            runtime=Runtime.RESET,
            session_id=0,
        )

        assert result.success


class TestA2AChat:
    """Tests for A2AChat."""

    def test_send_message(self):
        """Test sending messages."""
        chat = A2AChat()

        msg = chat.send_message(
            sender_id="agent_001",
            recipient_id="agent_002",
            content="Hello agent 002",
        )

        assert msg.sender_id == "agent_001"
        assert msg.recipient_id == "agent_002"

    def test_room_chat(self):
        """Test room-based chat."""
        chat = A2AChat()

        room = chat.create_room(
            name="test_room",
            creator_id="agent_001",
            members=["agent_001", "agent_002"],
        )

        msg = chat.broadcast(
            sender_id="agent_001",
            room_id=room.id,
            content="Hello room",
        )

        messages = chat.get_messages(room_id=room.id)
        assert len(messages) == 1

    def test_unread_messages(self):
        """Test unread message tracking."""
        chat = A2AChat()

        chat.send_message(
            sender_id="agent_001",
            recipient_id="agent_002",
            content="Message 1",
        )

        unread = chat.get_unread("agent_002")
        assert len(unread) == 1

        chat.mark_read(unread[0].id, "agent_002")
        unread = chat.get_unread("agent_002")
        assert len(unread) == 0


class TestBehaviorAdjuster:
    """Tests for BehaviorAdjuster."""

    def test_create_profile(self):
        """Test creating behavior profile."""
        adjuster = BehaviorAdjuster()

        profile = adjuster.create_profile(
            name="test_profile",
            dimensions={
                BehaviorDimension.CAUTION.value: 0.5,
            },
        )

        assert profile.get(BehaviorDimension.CAUTION) == 0.5

    def test_apply_preset(self):
        """Test applying preset profile."""
        adjuster = BehaviorAdjuster()

        result = adjuster.apply_preset("agent_001", "careful")
        assert result

        profile = adjuster.get_agent_profile("agent_001")
        assert profile is not None
        assert profile.get(BehaviorDimension.CAUTION) > 0.5

    def test_adjust_behavior(self):
        """Test adjusting behavior dimension."""
        adjuster = BehaviorAdjuster()
        adjuster.apply_preset("agent_001", "careful")

        initial = adjuster.get_behavior_value("agent_001", BehaviorDimension.CAUTION)
        new_value = adjuster.adjust_agent_behavior(
            "agent_001",
            BehaviorDimension.CAUTION,
            -0.2,
        )

        assert new_value < initial


class TestChatGenerationResult:
    """Tests for ChatGenerationResult."""

    def test_basic_response(self):
        """Test basic response accumulation."""
        result = ChatGenerationResult()

        result.add_chunk("Hello ")
        result.add_chunk("world!")
        result.complete()

        assert result.response == "Hello world!"

    def test_thinking_extraction(self):
        """Test thinking tag extraction."""
        result = ChatGenerationResult()

        result.add_chunk("<thinking>Let me think...")
        result.add_chunk("</thinking>")
        result.add_chunk("The answer is 42.")
        result.complete()

        assert "Let me think" in result.reasoning
        assert "42" in result.response
        assert "thinking" not in result.response.lower()

    def test_nested_thinking(self):
        """Test handling of multiple thinking sections."""
        result = ChatGenerationResult()

        result.add_chunk("<thinking>First thought</thinking>")
        result.add_chunk("Middle content ")
        result.add_chunk("<reasoning>Second thought</reasoning>")
        result.add_chunk("Final answer.")
        result.complete()

        assert "First thought" in result.reasoning
        assert "Second thought" in result.reasoning
        assert len(result.thinking_pairs) == 2


class TestDeferredTaskManager:
    """Tests for DeferredTaskManager."""

    def test_submit_task(self):
        """Test submitting deferred task."""
        manager = DeferredTaskManager()

        results = []
        task = manager.submit(
            lambda x: results.append(x),
            "test",
            name="test_task",
        )

        manager.wait_for(task.id)

        assert results == ["test"]
        assert task.status.value == "completed"

        manager.stop()

    def test_task_dependencies(self):
        """Test task dependencies."""
        manager = DeferredTaskManager()

        results = []

        task1 = manager.submit(
            lambda: results.append(1),
            name="first",
        )

        task2 = manager.submit(
            lambda: results.append(2),
            name="second",
            dependencies=[task1.id],
        )

        manager.wait_all(timeout=5)

        assert results == [1, 2]
        manager.stop()


class TestSessionManager:
    """Tests for SessionManager."""

    def test_create_session(self):
        """Test creating session."""
        manager = SessionManager(auto_start=False)

        session = manager.create_session(
            name="test_session",
            owner_id="agent_001",
        )

        assert session.is_active()
        assert session.owner_id == "agent_001"

    def test_pause_resume(self):
        """Test pause and resume."""
        manager = SessionManager(auto_start=False)

        session = manager.create_session(name="test")

        manager.pause_session(session.id, reason="testing")
        assert session.is_paused()

        manager.resume_session(session.id)
        assert session.is_active()

    def test_auto_resume(self):
        """Test auto-resume after duration."""
        manager = SessionManager(auto_start=False)

        session = manager.create_session(name="test")
        session.pause(duration_seconds=0)  # Immediate resume

        assert session.should_auto_resume()

        # Manually trigger maintenance
        manager._process_auto_resumes()
        assert session.is_active()
