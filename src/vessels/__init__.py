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

from .memory import SemanticMemory, MemoryEntry, MemoryStore
from .agents import AgentContext, ContextRegistry, InterventionManager, SubordinateManager
from .scheduler import TaskScheduler, ScheduledTask, TaskType
from .tools import CodeExecutor, DocumentQuery, A2AChat, BehaviorAdjuster, BehaviorProfile, BehaviorDimension
from .models import ModelWrapper, ChatGenerationResult, ModelConfig
from .runtime import DeferredTaskManager, SessionManager
from .integration import VesselsIntegration, get_integration, initialize_vessels

__all__ = [
    # Memory
    "SemanticMemory",
    "MemoryEntry",
    "MemoryStore",
    # Agents
    "AgentContext",
    "ContextRegistry",
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
    "BehaviorProfile",
    "BehaviorDimension",
    # Models
    "ModelWrapper",
    "ChatGenerationResult",
    "ModelConfig",
    # Runtime
    "DeferredTaskManager",
    "SessionManager",
    # Integration
    "VesselsIntegration",
    "get_integration",
    "initialize_vessels",
]
