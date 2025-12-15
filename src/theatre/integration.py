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
7. SceneGenerator produces visual →
8. CaptionRenderer displays conversation

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

logger = logging.getLogger(__name__)


@dataclass
class TheatreConfig:
    """Configuration for the theatre system."""

    # Component enable/disable
    enable_emotions: bool = True
    enable_scene_generation: bool = True
    enable_captions: bool = True

    # Timing
    scene_blend_duration: float = 2.0
    caption_default_duration: float = 4.0
    topic_shift_threshold: float = 0.4

    # Display
    max_visible_captions: int = 3
    caption_overlap: bool = True

    # Integration
    hume_api_key: str | None = None
    llm_fn: Callable[[str, str], str] | None = None


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
        )

    def _setup_callbacks(self) -> None:
        """Set up internal callbacks between components."""
        # Topic shifts trigger scene updates
        self.topic_detector.on_shift(self._on_topic_shift)

        # New turns create captions
        self.orchestrator.on_turn(self._on_turn)

        # Caption updates notify display
        self.caption_renderer.on_update(self._on_caption_update)

    def _on_topic_shift(self, shift: TopicShift) -> None:
        """Handle topic shift events."""
        logger.info(f"Topic shift: {shift.from_region} → {shift.to_region}")

        if self.config.enable_scene_generation:
            # Scene generator handles this through orchestrator
            pass

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
        # Notify display callbacks
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
            Complete display state including scene and captions
        """
        scene = self.scene_generator.current_scene
        captions = self.caption_renderer.get_render_data()
        topic_state = self.topic_detector.current_state

        return {
            "scene": scene.to_dict() if scene else None,
            "captions": captions,
            "topic": {
                "region": topic_state.primary_region.value if topic_state else "unknown",
                "confidence": topic_state.confidence if topic_state else 0.0,
            },
            "theatre_state": self.orchestrator.state.value,
        }

    def switch_community(self, community: str) -> dict:
        """
        Switch to a different community/domain agent.

        Args:
            community: Target community name

        Returns:
            Switch result
        """
        persona = self.orchestrator.switch_agent(community)
        return {
            "community": community,
            "agent_name": persona.name,
            "agent_role": persona.role.value,
        }

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
