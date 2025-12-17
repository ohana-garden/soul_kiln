"""
Theatre Bridge.

Connects the Streamlit UI to the theatre backend.
Translates between UI events and theatre system calls.
"""

import logging
from typing import Any, Callable

logger = logging.getLogger(__name__)


class TheatreBridge:
    """
    Bridges the UI layer to the theatre backend.

    Handles:
    - Processing user input through the theatre system
    - Retrieving topic state for UI generation
    - Resolving artifacts for display
    - Managing conversation state
    """

    def __init__(self):
        self._theatre = None
        self._topic_detector = None
        self._artifact_curator = None
        self._concept_extractor = None
        self._graph_client = None
        self._llm_fn: Callable[[str, str], str] | None = None

        # State
        self._conversation: list[dict] = []
        self._current_topic_state: dict | None = None

    def initialize(
        self,
        graph_client=None,
        llm_fn: Callable[[str, str], str] | None = None,
    ) -> bool:
        """
        Initialize the bridge with backend components.

        Args:
            graph_client: Graph database client
            llm_fn: LLM function for generating responses

        Returns:
            True if initialized successfully
        """
        self._graph_client = graph_client
        self._llm_fn = llm_fn

        try:
            # Initialize theatre components
            from src.theatre.topic_detector import TopicDetector
            from src.theatre.artifacts import ArtifactCurator
            from src.theatre.concept_extractor import ConceptExtractor

            self._topic_detector = TopicDetector()
            self._artifact_curator = ArtifactCurator()
            self._concept_extractor = ConceptExtractor()

            if graph_client:
                self._artifact_curator.set_client(graph_client)

            logger.info("Theatre bridge initialized")
            return True

        except Exception as e:
            logger.error(f"Failed to initialize theatre bridge: {e}")
            return False

    def process_input(self, user_input: str) -> dict:
        """
        Process user input through the theatre system.

        Args:
            user_input: The user's message

        Returns:
            Dict with response, topic_state, artifacts
        """
        # Add to conversation
        self._conversation.append({
            "role": "user",
            "content": user_input
        })

        # Process through topic detector
        topic_state = None
        if self._topic_detector:
            try:
                state = self._topic_detector.process_utterance(user_input)
                topic_state = state.to_dict() if state else None
                self._current_topic_state = topic_state
            except Exception as e:
                logger.debug(f"Topic detection failed: {e}")

        # Get relevant artifacts
        artifacts = []
        if self._artifact_curator and topic_state:
            try:
                from src.theatre.topic_detector import TopicState
                # Reconstruct TopicState for curator
                state_obj = TopicState(
                    primary_region=topic_state.get("primary_region", "unknown"),
                    confidence=topic_state.get("confidence", 0),
                    active_concepts=topic_state.get("active_concepts", []),
                    active_virtues=topic_state.get("active_virtues", []),
                )
                artifact_objs = self._artifact_curator.surface_for_topic(state_obj)
                artifacts = [a.to_dict() for a in artifact_objs]
            except Exception as e:
                logger.debug(f"Artifact retrieval failed: {e}")

        # Generate response via LLM
        response = self._generate_response(user_input, topic_state, artifacts)

        # Add response to conversation
        self._conversation.append({
            "role": "assistant",
            "content": response
        })

        return {
            "response": response,
            "topic_state": topic_state,
            "artifacts": artifacts,
            "conversation": self._conversation.copy()
        }

    def _generate_response(
        self,
        user_input: str,
        topic_state: dict | None,
        artifacts: list[dict]
    ) -> str:
        """Generate a response using the LLM."""
        if not self._llm_fn:
            return self._fallback_response(user_input, topic_state)

        # Build context for LLM
        system_prompt = self._build_system_prompt(topic_state, artifacts)
        user_prompt = user_input

        try:
            return self._llm_fn(system_prompt, user_prompt)
        except Exception as e:
            logger.error(f"LLM response generation failed: {e}")
            return self._fallback_response(user_input, topic_state)

    def _build_system_prompt(
        self,
        topic_state: dict | None,
        artifacts: list[dict]
    ) -> str:
        """Build system prompt with context."""
        parts = [
            "You are a helpful assistant in Soul Kiln, a virtue-based AI system.",
            "Respond thoughtfully and helpfully to the user.",
        ]

        if topic_state:
            region = topic_state.get("primary_region", "unknown")
            concepts = topic_state.get("active_concepts", [])
            parts.append(f"\nCurrent topic region: {region}")
            if concepts:
                parts.append(f"Active concepts: {', '.join(concepts[:5])}")

        if artifacts:
            parts.append(f"\nAvailable artifacts: {len(artifacts)} items")
            for a in artifacts[:3]:
                parts.append(f"- {a.get('type')}: {a.get('title')}")

        return "\n".join(parts)

    def _fallback_response(self, user_input: str, topic_state: dict | None) -> str:
        """Generate a fallback response without LLM."""
        if topic_state:
            region = topic_state.get("primary_region", "general")
            return f"I understand you're asking about something in the {region} domain. How can I help you explore this further?"
        return "I'm here to help. Could you tell me more about what you're looking for?"

    def get_topic_state(self) -> dict | None:
        """Get the current topic state."""
        return self._current_topic_state

    def get_artifacts(self) -> list[dict]:
        """Get currently active artifacts."""
        if self._artifact_curator:
            return self._artifact_curator.get_artifacts_for_render()
        return []

    def get_conversation(self) -> list[dict]:
        """Get conversation history."""
        return self._conversation.copy()

    def resolve_artifact(self, artifact_id: str) -> dict | None:
        """Resolve an artifact ID to its full data."""
        if not self._artifact_curator:
            return None

        for artifact in self._artifact_curator.get_active_artifacts():
            if artifact.id == artifact_id:
                return artifact.to_dict()
        return None

    def clear_conversation(self) -> None:
        """Clear conversation history."""
        self._conversation = []
        self._current_topic_state = None
        if self._artifact_curator:
            self._artifact_curator.dismiss_all()


# Singleton
_bridge: TheatreBridge | None = None


def get_theatre_bridge() -> TheatreBridge:
    """Get the singleton theatre bridge."""
    global _bridge
    if _bridge is None:
        _bridge = TheatreBridge()
    return _bridge
