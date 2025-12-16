"""
Theatre Module.

Theatrical UX for soul_kiln with graph-based topic detection,
three-agent conversation orchestration, and dual-view system.

Philosophy: "Yes, and..." - Everything is incorporated smoothly.
The conversation is always already happening when you arrive.

Architecture:
1. User speaks (audio + text)
2. Hume.ai extracts emotional state
3. ConceptExtractor maps to graph nodes
4. TopicDetector tracks topic via spreading activation
5. User Proxy echoes/interprets user input
6. Builder and Current Agent respond
7. ViewManager decides what to show (workspace or graph)
8. CaptionRenderer displays conversation

Two views available:
- Workspace: Primary utilitarian view with contextual artifacts
- Graph: The actual semantic graph (truth layer), always available

Key insight: Since User Proxy echoes all user input, ALL I/O
flows through agents. This means we can use the knowledge graph
for topic detection on everything.
"""

from .concept_extractor import ConceptExtractor, ExtractedConcepts
from .topic_detector import TopicDetector, TopicState, TopicShift, TopicRegion
from .scene_generator import SceneGenerator, Scene, SceneElement, SceneType
from .orchestrator import (
    TheatreOrchestrator,
    AgentRole,
    AgentPersona,
    ConversationTurn,
    TheatreState,
)
from .captions import CaptionRenderer, Caption, CaptionStyle, CaptionPosition
from .hume_integration import HumeIntegration, EmotionalState, EmotionCategory
from .artifacts import (
    ArtifactCurator,
    Artifact,
    ArtifactType,
    ArtifactRequest,
)
from .graph_view import GraphViewRenderer, GraphViewState, GraphNode, GraphEdge, GeometryOverlay
from .views import ViewManager, ViewType, ViewState, WorkspaceState
from .integration import TheatreSystem, TheatreConfig, create_theatre

__all__ = [
    # Concept extraction
    "ConceptExtractor",
    "ExtractedConcepts",
    # Topic detection
    "TopicDetector",
    "TopicState",
    "TopicShift",
    "TopicRegion",
    # Scene generation (legacy, kept for compatibility)
    "SceneGenerator",
    "Scene",
    "SceneElement",
    "SceneType",
    # Orchestration
    "TheatreOrchestrator",
    "AgentRole",
    "AgentPersona",
    "ConversationTurn",
    "TheatreState",
    # Captions
    "CaptionRenderer",
    "Caption",
    "CaptionStyle",
    "CaptionPosition",
    # Emotional intelligence
    "HumeIntegration",
    "EmotionalState",
    "EmotionCategory",
    # Artifacts
    "ArtifactCurator",
    "Artifact",
    "ArtifactType",
    "ArtifactRequest",
    # Graph view
    "GraphViewRenderer",
    "GraphViewState",
    "GraphNode",
    "GraphEdge",
    "GeometryOverlay",
    # View management
    "ViewManager",
    "ViewType",
    "ViewState",
    "WorkspaceState",
    # Integration
    "TheatreSystem",
    "TheatreConfig",
    "create_theatre",
]
