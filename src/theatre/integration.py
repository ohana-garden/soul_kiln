"""
Theatre Integration.

Wires all theatre components together into a unified system.

Architecture:
1. User speaks (audio + text) →
2. Hume.ai extracts emotional state →
3. ConceptExtractor maps to graph nodes →
4. TopicDetector tracks topic via activation →
5. User Proxy echoes/interprets →
6. Builder and Agent respond →
7. ViewManager decides what to show →
8. CaptionRenderer displays conversation

Two views available:
- Workspace: Primary utilitarian view with contextual artifacts
- Graph: The actual semantic graph (truth layer), always available

"Yes, and..." - everything flows smoothly.
"""

import logging
from dataclasses import dataclass
from typing import Any, Callable

from .concept_extractor import ConceptExtractor, get_concept_extractor
from .topic_detector import TopicDetector, TopicState, TopicShift, get_topic_detector
from .scene_generator import SceneGenerator, Scene, get_scene_generator
from .orchestrator import (
    TheatreOrchestrator,
    TheatreState,
    ConversationTurn,
    AgentRole,
    get_orchestrator,
)
from .captions import CaptionRenderer, Caption, get_caption_renderer
from .hume_integration import HumeIntegration, EmotionalState, get_hume_integration
from .artifacts import ArtifactCurator, Artifact, ArtifactRequest, get_artifact_curator
from .graph_view import GraphViewRenderer, get_graph_view_renderer
from .views import ViewManager, ViewType, ViewState, get_view_manager

logger = logging.getLogger(__name__)


@dataclass
class TheatreConfig:
    """Configuration for the theatre system."""

    # Component enable/disable
    enable_emotions: bool = True
    enable_scene_generation: bool = True
    enable_captions: bool = True
    enable_artifacts: bool = True

    # Timing
    scene_blend_duration: float = 2.0
    caption_default_duration: float = 4.0
    topic_shift_threshold: float = 0.4

    # Display
    max_visible_captions: int = 3
    caption_overlap: bool = True
    default_view: ViewType = ViewType.WORKSPACE

    # Integration
    hume_api_key: str | None = None
    llm_fn: Callable[[str, str], str] | None = None
    image_generator_fn: Callable[[str], str] | None = None


class TheatreSystem:
    """
    Unified theatre system integrating all components.

    Provides a simple interface for:
    - Starting/ending sessions
    - Processing user input
    - Retrieving display state (scene + captions)
    - Handling callbacks for UI updates

    Usage:
        theatre = TheatreSystem.create()
        theatre.start_session(human_id="user123", community="grant-getter")

        # Process user input
        result = theatre.process("I need help finding grants")

        # Get current display state
        display = theatre.get_display_state()

        theatre.end_session()
    """

    def __init__(
        self,
        config: TheatreConfig,
        orchestrator: TheatreOrchestrator,
        topic_detector: TopicDetector,
        scene_generator: SceneGenerator,
        caption_renderer: CaptionRenderer,
        hume: HumeIntegration | None,
        concept_extractor: ConceptExtractor,
        view_manager: ViewManager,
        artifact_curator: ArtifactCurator,
    ):
        """
        Initialize the theatre system.

        Use TheatreSystem.create() for standard initialization.
        """
        self.config = config
        self.orchestrator = orchestrator
        self.topic_detector = topic_detector
        self.scene_generator = scene_generator
        self.caption_renderer = caption_renderer
        self.hume = hume
        self.extractor = concept_extractor
        self.view_manager = view_manager
        self.artifact_curator = artifact_curator

        # Wire up callbacks
        self._setup_callbacks()

        # External callbacks
        self._display_callbacks: list[Callable[[dict], None]] = []
        self._turn_callbacks: list[Callable[[ConversationTurn], None]] = []

    @classmethod
    def create(
        cls,
        config: TheatreConfig | None = None,
        substrate=None,
        activation_spreader=None,
        embedding_fn=None,
    ) -> "TheatreSystem":
        """
        Create a fully configured TheatreSystem.

        Args:
            config: Optional configuration
            substrate: Graph substrate for concept extraction
            activation_spreader: For topic detection
            embedding_fn: Function for generating embeddings

        Returns:
            Configured TheatreSystem
        """
        config = config or TheatreConfig()

        # Create components
        extractor = ConceptExtractor(
            substrate=substrate,
            embedding_fn=embedding_fn,
        )
        if substrate:
            extractor.initialize()

        topic_detector = TopicDetector(
            activation_spreader=activation_spreader,
            concept_extractor=extractor,
            shift_threshold=config.topic_shift_threshold,
        )

        scene_generator = SceneGenerator(
            blend_duration=config.scene_blend_duration,
        )

        caption_renderer = CaptionRenderer(
            default_duration=config.caption_default_duration,
            overlap_enabled=config.caption_overlap,
            max_visible=config.max_visible_captions,
        )

        hume = None
        if config.enable_emotions:
            hume = HumeIntegration(api_key=config.hume_api_key)

        # Create artifact curator
        artifact_curator = ArtifactCurator()
        if substrate:
            artifact_curator.set_substrate(substrate)
        if config.image_generator_fn:
            artifact_curator.set_image_generator(config.image_generator_fn)

        # Create graph view renderer
        graph_renderer = GraphViewRenderer(substrate=substrate)

        # Create view manager
        view_manager = ViewManager(
            artifact_curator=artifact_curator,
            graph_renderer=graph_renderer,
        )

        orchestrator = TheatreOrchestrator(
            topic_detector=topic_detector,
            scene_generator=scene_generator,
            concept_extractor=extractor,
            hume_integration=hume,
            llm_fn=config.llm_fn,
        )

        return cls(
            config=config,
            orchestrator=orchestrator,
            topic_detector=topic_detector,
            scene_generator=scene_generator,
            caption_renderer=caption_renderer,
            hume=hume,
            concept_extractor=extractor,
            view_manager=view_manager,
            artifact_curator=artifact_curator,
        )

    def _setup_callbacks(self) -> None:
        """Set up internal callbacks between components."""
        # Topic shifts trigger updates
        self.topic_detector.on_shift(self._on_topic_shift)

        # New turns create captions
        self.orchestrator.on_turn(self._on_turn)

        # Caption updates notify display
        self.caption_renderer.on_update(self._on_caption_update)

        # Artifact surfaces notify display
        self.artifact_curator.on_surface(self._on_artifact_surface)

    def _on_topic_shift(self, shift: TopicShift) -> None:
        """Handle topic shift events."""
        logger.info(f"Topic shift: {shift.from_region} → {shift.to_region}")

        # Update view manager with new topic state
        topic_state = self.topic_detector.current_state
        if topic_state:
            self.view_manager.update_topic(topic_state)

            # Auto-surface relevant artifacts
            if self.config.enable_artifacts:
                self.artifact_curator.surface_from_topic(topic_state)

    def _on_artifact_surface(self, artifact: Artifact) -> None:
        """Handle artifact surface events."""
        logger.debug(f"Artifact surfaced: {artifact.title}")
        # View manager already has the artifact through curator
        # Just trigger display update
        self._notify_display_update()

    def _on_turn(self, turn: ConversationTurn) -> None:
        """Handle new conversation turns."""
        # Create caption for the turn
        if self.config.enable_captions:
            self.caption_renderer.add_turn(turn)

        # Notify external callbacks
        for callback in self._turn_callbacks:
            try:
                callback(turn)
            except Exception as e:
                logger.error(f"Turn callback error: {e}")

    def _on_caption_update(self, captions: list[Caption]) -> None:
        """Handle caption updates."""
        # Update view manager with captions
        self.view_manager.update_captions(
            [c.to_render_dict() for c in captions]
        )
        # Notify display callbacks
        self._notify_display_update()

    def _notify_display_update(self) -> None:
        """Notify all display callbacks of update."""
        display_state = self.get_display_state()
        for callback in self._display_callbacks:
            try:
                callback(display_state)
            except Exception as e:
                logger.error(f"Display callback error: {e}")

    def start_session(
        self,
        human_id: str | None = None,
        community: str | None = None,
        organization_context: dict | None = None,
    ) -> dict:
        """
        Start a new theatre session.

        Args:
            human_id: Optional human identifier
            community: Starting community (e.g., "grant-getter")
            organization_context: Context from intake

        Returns:
            Session information
        """
        # Start caption renderer
        if self.config.enable_captions:
            self.caption_renderer.start()

        # Set community in view manager
        self.view_manager.set_community(community)

        # Start orchestrator session
        context = self.orchestrator.start_session(
            human_id=human_id,
            community=community,
            organization_context=organization_context,
        )

        logger.info(f"Theatre session started: {context.session_id}")

        return {
            "session_id": context.session_id,
            "state": self.orchestrator.state.value,
            "community": community,
            "view": self.view_manager.current_view.value,
        }

    def process(
        self,
        text_input: str,
        audio_data: bytes | None = None,
    ) -> dict:
        """
        Process user input through the theatre.

        Args:
            text_input: What the user said (text)
            audio_data: Optional audio for emotional analysis

        Returns:
            Processing result with turns and updated state
        """
        # Analyze emotions if audio provided
        emotional_state = None
        if audio_data and self.hume and self.config.enable_emotions:
            emotional_state = self.hume.analyze_audio(audio_data)

        # Also analyze text for emotions as fallback
        if not emotional_state and self.hume and self.config.enable_emotions:
            emotional_state = self.hume.analyze_text(text_input)

        # Process through orchestrator
        turns = self.orchestrator.process_user_input(text_input, audio_data)

        # Get current state
        topic_state = self.topic_detector.current_state
        scene = self.scene_generator.current_scene

        return {
            "turns": [t.to_dict() for t in turns],
            "topic_state": topic_state.to_dict() if topic_state else None,
            "scene": scene.to_dict() if scene else None,
            "emotional_state": emotional_state.to_dict() if emotional_state else None,
            "theatre_state": self.orchestrator.state.value,
        }

    def get_display_state(self) -> dict:
        """
        Get current display state for rendering.

        Returns:
            Complete display state based on current view
        """
        # Get base state from view manager
        view_data = self.view_manager.get_render_data()

        # Add theatre state
        view_data["theatre_state"] = self.orchestrator.state.value

        return view_data

    def switch_view(self, view_type: ViewType | str) -> dict:
        """
        Switch between workspace and graph view.

        Args:
            view_type: Target view type (or string "workspace"/"graph")

        Returns:
            New view state
        """
        if isinstance(view_type, str):
            view_type = ViewType(view_type)

        state = self.view_manager.switch_to(view_type)
        return state.to_dict()

    def toggle_view(self) -> dict:
        """
        Toggle between workspace and graph view.

        Returns:
            New view state
        """
        state = self.view_manager.toggle_view()
        return state.to_dict()

    @property
    def current_view(self) -> ViewType:
        """Get current view type."""
        return self.view_manager.current_view

    def switch_community(self, community: str) -> dict:
        """
        Switch to a different community/domain agent.

        Args:
            community: Target community name

        Returns:
            Switch result
        """
        # Update view manager
        self.view_manager.set_community(community)

        # Switch orchestrator agent
        persona = self.orchestrator.switch_agent(community)
        return {
            "community": community,
            "agent_name": persona.name,
            "agent_role": persona.role.value,
        }

    def surface_artifact(
        self,
        context: str,
        artifact_type: str | None = None,
    ) -> dict | None:
        """
        Request an artifact to be surfaced in workspace.

        Args:
            context: What we're trying to show/explain
            artifact_type: Optional preferred type

        Returns:
            Artifact info if surfaced, None otherwise
        """
        from .artifacts import ArtifactType, ArtifactRequest

        type_hint = None
        if artifact_type:
            type_hint = ArtifactType(artifact_type)

        request = ArtifactRequest(
            context=context,
            type_hint=type_hint,
            topic_state=self.topic_detector.current_state,
            concepts=self.topic_detector.current_state.active_concepts[:5]
            if self.topic_detector.current_state
            else [],
        )

        artifact = self.artifact_curator.request_artifact(request)
        if artifact:
            return artifact.to_dict()
        return None

    def dismiss_artifact(self, artifact_id: str) -> bool:
        """Dismiss an artifact from workspace."""
        return self.artifact_curator.dismiss(artifact_id)

    def end_session(self) -> dict:
        """
        End the theatre session.

        Returns:
            Session summary
        """
        # Stop caption renderer
        if self.config.enable_captions:
            self.caption_renderer.stop()

        # End orchestrator session
        summary = self.orchestrator.end_session()

        logger.info(f"Theatre session ended: {summary.get('session_id')}")

        return summary

    def on_display_update(self, callback: Callable[[dict], None]) -> None:
        """Register callback for display updates."""
        self._display_callbacks.append(callback)

    def on_turn(self, callback: Callable[[ConversationTurn], None]) -> None:
        """Register callback for new turns."""
        self._turn_callbacks.append(callback)

    def get_topic_summary(self) -> dict:
        """Get summary of topic detection."""
        return self.topic_detector.get_topic_summary()

    def get_stats(self) -> dict:
        """Get system statistics."""
        return {
            "captions": self.caption_renderer.get_stats(),
            "topic": self.topic_detector.get_topic_summary(),
            "emotional_trend": self.hume.get_trend() if self.hume else None,
            "current_view": self.view_manager.current_view.value,
            "active_artifacts": len(self.artifact_curator.get_active_artifacts()),
        }


# Factory function for easy creation
def create_theatre(
    community: str | None = None,
    substrate=None,
    activation_spreader=None,
    embedding_fn=None,
    llm_fn=None,
) -> TheatreSystem:
    """
    Create a theatre system with sensible defaults.

    Args:
        community: Starting community
        substrate: Graph substrate
        activation_spreader: For topic detection
        embedding_fn: For semantic similarity
        llm_fn: For agent responses

    Returns:
        Configured TheatreSystem
    """
    config = TheatreConfig(llm_fn=llm_fn)

    return TheatreSystem.create(
        config=config,
        substrate=substrate,
        activation_spreader=activation_spreader,
        embedding_fn=embedding_fn,
    )
