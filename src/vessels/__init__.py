"""
Vessels Integration Module for Soul Kiln.

Provides advanced agent capabilities inspired by Vessels3:
- Semantic memory with vector search
- Agent intervention and session management
- Subordinate agent delegation
- Task scheduling
- Code execution
- Document querying
- Agent-to-agent communication
- LLM model wrappers with rate limiting
"""

from .memory import SemanticMemory, MemoryEntry
from .agents import AgentContext, InterventionManager, SubordinateManager
from .scheduler import TaskScheduler, ScheduledTask, TaskType
from .tools import CodeExecutor, DocumentQuery, A2AChat, BehaviorAdjuster
from .models import ModelWrapper, ChatGenerationResult, ModelConfig
from .runtime import DeferredTaskManager, SessionManager

__all__ = [
    # Memory
    "SemanticMemory",
    "MemoryEntry",
    # Agents
    "AgentContext",
    "InterventionManager",
    "SubordinateManager",
    # Scheduler
    "TaskScheduler",
    "ScheduledTask",
    "TaskType",
    # Tools
    "CodeExecutor",
    "DocumentQuery",
    "A2AChat",
    "BehaviorAdjuster",
    # Models
    "ModelWrapper",
    "ChatGenerationResult",
    "ModelConfig",
    # Runtime
    "DeferredTaskManager",
    "SessionManager",
]
