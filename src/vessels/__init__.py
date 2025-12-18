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
- Persona capsule compilation (KG-persona pattern)
- Diffusion-based definition generation
"""

from .memory import SemanticMemory, MemoryEntry, MemoryStore
from .agents import AgentContext, ContextRegistry, InterventionManager, SubordinateManager
from .scheduler import TaskScheduler, ScheduledTask, TaskType
from .tools import CodeExecutor, DocumentQuery, A2AChat, BehaviorAdjuster, BehaviorProfile, BehaviorDimension
from .models import ModelWrapper, ChatGenerationResult, ModelConfig
from .runtime import DeferredTaskManager, SessionManager
from .integration import VesselsIntegration, get_integration, initialize_vessels
from .persona import (
    PersonaCapsule,
    PersonaCompiler,
    Trait,
    StyleRule,
    Boundary,
    Preference,
    Role,
    Conflict,
    compile_persona,
    capsule_to_prompt,
)
from .diffusion import (
    DiffusionDefiner,
    DefinitionEmbedding,
    GeneratedDefinition,
    define_persona_with_diffusion,
    define_virtue_with_diffusion,
    batch_define_virtues,
)

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
    # Persona (KG-persona pattern)
    "PersonaCapsule",
    "PersonaCompiler",
    "Trait",
    "StyleRule",
    "Boundary",
    "Preference",
    "Role",
    "Conflict",
    "compile_persona",
    "capsule_to_prompt",
    # Diffusion-based definitions
    "DiffusionDefiner",
    "DefinitionEmbedding",
    "GeneratedDefinition",
    "define_persona_with_diffusion",
    "define_virtue_with_diffusion",
    "batch_define_virtues",
]
