"""
Topic Detector.

Uses spreading activation in the knowledge graph to detect
what the conversation is about and when topics shift.

Key insight: Since we map utterances to concepts and inject
activation, the "hot" region of the graph tells us the topic.
When activation moves to a different region, the topic has shifted.

This is inspired by ChatSense and dual-process cognitive models:
- Fast: Track which graph region has highest activation
- Slow: Analyze temporal patterns for significant shifts
"""

import logging
from collections import deque
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Callable

import numpy as np

from .concept_extractor import ConceptExtractor, ExtractedConcepts

logger = logging.getLogger(__name__)


class TopicRegion(str, Enum):
    """High-level topic regions in the graph."""

    # Virtue clusters (from soul_kiln virtue model)
    FOUNDATION = "foundation"  # Trustworthiness
    CORE = "core"  # Truthfulness, Sincerity, Righteousness
    RELATIONAL = "relational"  # Justice, Courtesy, Hospitality, Goodwill
    PERSONAL = "personal"  # Chastity, Forbearance, Fidelity, Cleanliness
    TRANSCENDENT = "transcendent"  # Godliness, Piety, Wisdom, Detachment, Unity, Service

    # Domain regions (based on concepts)
    TECHNICAL = "technical"
    EMOTIONAL = "emotional"
    PRACTICAL = "practical"
    ABSTRACT = "abstract"

    # Meta regions
    MIXED = "mixed"
    TRANSITIONAL = "transitional"
    UNKNOWN = "unknown"


# Virtue to region mapping
VIRTUE_REGIONS = {
    "V01": TopicRegion.FOUNDATION,  # Trustworthiness
    "V02": TopicRegion.CORE,  # Truthfulness
    "V03": TopicRegion.RELATIONAL,  # Justice
    "V04": TopicRegion.CORE,  # Righteousness
    "V05": TopicRegion.CORE,  # Sincerity
    "V06": TopicRegion.RELATIONAL,  # Courtesy
    "V07": TopicRegion.PERSONAL,  # Forbearance
    "V08": TopicRegion.PERSONAL,  # Fidelity
    "V09": TopicRegion.TRANSCENDENT,  # Wisdom
    "V10": TopicRegion.TRANSCENDENT,  # Piety
    "V11": TopicRegion.TRANSCENDENT,  # Godliness
    "V12": TopicRegion.PERSONAL,  # Chastity
    "V13": TopicRegion.RELATIONAL,  # Goodwill
    "V14": TopicRegion.RELATIONAL,  # Hospitality
    "V15": TopicRegion.TRANSCENDENT,  # Detachment
    "V16": TopicRegion.PERSONAL,  # Humility
    "V17": TopicRegion.PERSONAL,  # Cleanliness
    "V18": TopicRegion.TRANSCENDENT,  # Unity
    "V19": TopicRegion.TRANSCENDENT,  # Service
}


@dataclass
class TopicState:
    """Current state of topic detection."""

    primary_region: TopicRegion
    secondary_region: TopicRegion | None = None
    confidence: float = 0.0  # 0-1, how confident we are about the topic
    active_concepts: list[str] = field(default_factory=list)  # Top active concept IDs
    active_virtues: list[str] = field(default_factory=list)  # Top active virtue IDs
    activation_centroid: np.ndarray | None = None  # Semantic centroid of activation
    region_activations: dict[str, float] = field(default_factory=dict)  # Region -> total activation
    timestamp: datetime = field(default_factory=datetime.utcnow)

    def to_dict(self) -> dict:
        """Convert to dictionary."""
        return {
            "primary_region": self.primary_region.value,
            "secondary_region": self.secondary_region.value if self.secondary_region else None,
            "confidence": self.confidence,
            "active_concepts": self.active_concepts,
            "active_virtues": self.active_virtues,
            "region_activations": self.region_activations,
            "timestamp": self.timestamp.isoformat(),
        }


@dataclass
class TopicShift:
    """Detected topic shift event."""

    from_region: TopicRegion
    to_region: TopicRegion
    magnitude: float  # 0-1, how significant the shift is
    trigger_utterance: str
    shift_type: str  # "gradual", "abrupt", "return"
    timestamp: datetime = field(default_factory=datetime.utcnow)

    def to_dict(self) -> dict:
        """Convert to dictionary."""
        return {
            "from_region": self.from_region.value,
            "to_region": self.to_region.value,
            "magnitude": self.magnitude,
            "trigger_utterance": self.trigger_utterance,
            "shift_type": self.shift_type,
            "timestamp": self.timestamp.isoformat(),
        }


class TopicDetector:
    """
    Detects conversation topics using graph activation dynamics.

    The detector:
    1. Receives utterances (via concept extractor)
    2. Injects activation into relevant graph nodes
    3. Observes which regions become "hot"
    4. Tracks temporal patterns to detect shifts

    Dual-process approach:
    - System 1 (fast): Immediate activation readout
    - System 2 (slow): Temporal analysis for shift detection
    """

    def __init__(
        self,
        activation_spreader=None,
        concept_extractor: ConceptExtractor | None = None,
        history_length: int = 20,
        shift_threshold: float = 0.4,
        decay_factor: float = 0.85,
    ):
        """
        Initialize the topic detector.

        Args:
            activation_spreader: The ActivationSpreader for graph dynamics
            concept_extractor: ConceptExtractor for utterance -> concepts
            history_length: Number of states to keep in history
            shift_threshold: Magnitude threshold for declaring a shift
            decay_factor: How much activation decays between utterances
        """
        self.spreader = activation_spreader
        self.extractor = concept_extractor
        self._history_length = history_length
        self._shift_threshold = shift_threshold
        self._decay_factor = decay_factor

        # State tracking
        self._state_history: deque[TopicState] = deque(maxlen=history_length)
        self._shift_history: deque[TopicShift] = deque(maxlen=50)
        self._current_state: TopicState | None = None
        self._utterance_count = 0

        # Callbacks
        self._shift_callbacks: list[Callable[[TopicShift], None]] = []

    @property
    def current_topic(self) -> TopicRegion:
        """Get the current topic region."""
        if self._current_state:
            return self._current_state.primary_region
        return TopicRegion.UNKNOWN

    @property
    def current_state(self) -> TopicState | None:
        """Get the full current state."""
        return self._current_state

    def process_utterance(
        self,
        utterance: str,
        speaker: str = "unknown",
        emotional_context: dict | None = None,
    ) -> TopicState:
        """
        Process an utterance and update topic state.

        Args:
            utterance: The text to process
            speaker: Who said it (for context)
            emotional_context: Optional emotional signals (from Hume.ai)

        Returns:
            Updated TopicState
        """
        self._utterance_count += 1

        # Extract concepts from utterance
        if self.extractor:
            extracted = self.extractor.extract(utterance)
        else:
            extracted = ExtractedConcepts(
                utterance=utterance, concepts=[], virtues=[]
            )

        # Apply decay to existing activation (temporal dynamics)
        if self.spreader:
            self.spreader.decay_all_activations(self._decay_factor)

        # Inject activation for extracted concepts/virtues
        self._inject_activation(extracted)

        # Read current activation state
        new_state = self._compute_state(extracted, emotional_context)

        # Detect shifts
        if self._current_state:
            shift = self._detect_shift(self._current_state, new_state, utterance)
            if shift:
                self._shift_history.append(shift)
                self._notify_shift(shift)

        # Update state
        self._state_history.append(new_state)
        self._current_state = new_state

        return new_state

    def _inject_activation(self, extracted: ExtractedConcepts) -> None:
        """Inject activation into graph based on extracted concepts."""
        if not self.spreader:
            return

        # Inject into concepts
        for concept_id, relevance in extracted.concepts[:5]:  # Top 5
            strength = relevance * 0.8  # Scale activation
            self.spreader.inject_activation(concept_id, strength)

        # Inject into virtues (lower strength - virtues are attractors)
        for virtue_id, relevance in extracted.virtues[:3]:  # Top 3
            strength = relevance * 0.4  # Lower for virtues
            self.spreader.inject_activation(virtue_id, strength)

    def _compute_state(
        self,
        extracted: ExtractedConcepts,
        emotional_context: dict | None = None,
    ) -> TopicState:
        """Compute current topic state from graph activation."""
        # Get activation map
        activation_map: dict[str, float] = {}
        if self.spreader:
            activation_map = self.spreader.get_activation_map()

        # Compute region activations
        region_activations = self._compute_region_activations(activation_map)

        # Find primary and secondary regions
        sorted_regions = sorted(
            region_activations.items(), key=lambda x: x[1], reverse=True
        )

        primary_region = TopicRegion.UNKNOWN
        secondary_region = None
        confidence = 0.0

        if sorted_regions:
            primary_region = TopicRegion(sorted_regions[0][0])
            primary_activation = sorted_regions[0][1]

            if len(sorted_regions) > 1:
                secondary_region = TopicRegion(sorted_regions[1][0])
                secondary_activation = sorted_regions[1][1]

                # Confidence based on separation between top regions
                if primary_activation > 0:
                    confidence = 1.0 - (secondary_activation / primary_activation)
                    confidence = max(0.0, min(1.0, confidence))
            else:
                confidence = 1.0 if primary_activation > 0.1 else 0.5

        # Get top active nodes
        active_concepts = [
            node_id
            for node_id, act in sorted(
                activation_map.items(), key=lambda x: x[1], reverse=True
            )[:10]
            if not node_id.startswith("V") and act > 0.1
        ]

        active_virtues = [
            node_id
            for node_id, act in sorted(
                activation_map.items(), key=lambda x: x[1], reverse=True
            )
            if node_id.startswith("V") and act > 0.1
        ][:5]

        # Incorporate emotional context if available
        if emotional_context:
            confidence = self._adjust_confidence_for_emotion(
                confidence, emotional_context
            )

        return TopicState(
            primary_region=primary_region,
            secondary_region=secondary_region,
            confidence=confidence,
            active_concepts=active_concepts,
            active_virtues=active_virtues,
            activation_centroid=extracted.embedding,
            region_activations={k: v for k, v in sorted_regions[:5]},
        )

    def _compute_region_activations(
        self, activation_map: dict[str, float]
    ) -> dict[str, float]:
        """Compute total activation per region."""
        region_activations: dict[str, float] = {r.value: 0.0 for r in TopicRegion}

        for node_id, activation in activation_map.items():
            if node_id.startswith("V"):
                # Virtue node - use virtue region mapping
                region = VIRTUE_REGIONS.get(node_id, TopicRegion.UNKNOWN)
                region_activations[region.value] += activation
            elif node_id.startswith("concept_"):
                # Concept node - classify by metadata or default
                # For now, distribute to domain regions based on keywords
                region_activations[TopicRegion.PRACTICAL.value] += activation * 0.5
                region_activations[TopicRegion.TECHNICAL.value] += activation * 0.3
                region_activations[TopicRegion.ABSTRACT.value] += activation * 0.2

        return region_activations

    def _detect_shift(
        self, old_state: TopicState, new_state: TopicState, utterance: str
    ) -> TopicShift | None:
        """Detect if a significant topic shift has occurred."""
        # Check for region change
        if old_state.primary_region == new_state.primary_region:
            # Same primary region - might still be a subtle shift
            # Check activation centroid movement
            if old_state.activation_centroid is not None and new_state.activation_centroid is not None:
                centroid_distance = self._centroid_distance(
                    old_state.activation_centroid, new_state.activation_centroid
                )
                if centroid_distance > 0.6:  # Significant semantic movement
                    return TopicShift(
                        from_region=old_state.primary_region,
                        to_region=new_state.primary_region,
                        magnitude=centroid_distance * 0.5,  # Scale down for same-region
                        trigger_utterance=utterance,
                        shift_type="gradual",
                    )
            return None

        # Different primary region - calculate shift magnitude
        old_activation = old_state.region_activations.get(
            old_state.primary_region.value, 0.0
        )
        new_activation = new_state.region_activations.get(
            new_state.primary_region.value, 0.0
        )

        # Magnitude based on activation change
        magnitude = abs(new_activation - old_activation) / max(
            old_activation, new_activation, 0.1
        )
        magnitude = min(1.0, magnitude)

        # Check if this is below threshold
        if magnitude < self._shift_threshold:
            return None

        # Determine shift type
        shift_type = "abrupt"

        # Check if returning to a previous topic
        recent_regions = [
            s.primary_region for s in list(self._state_history)[-5:]
        ]
        if new_state.primary_region in recent_regions:
            shift_type = "return"
        elif len(self._state_history) > 2:
            # Check for gradual transition through history
            prev_prev = self._state_history[-2] if len(self._state_history) >= 2 else None
            if prev_prev and prev_prev.primary_region != old_state.primary_region:
                shift_type = "gradual"

        return TopicShift(
            from_region=old_state.primary_region,
            to_region=new_state.primary_region,
            magnitude=magnitude,
            trigger_utterance=utterance,
            shift_type=shift_type,
        )

    def _centroid_distance(self, a: np.ndarray, b: np.ndarray) -> float:
        """Calculate normalized distance between centroids."""
        diff = a - b
        distance = np.linalg.norm(diff)
        # Normalize to 0-1 range (assuming unit vectors)
        return min(1.0, distance / 2.0)

    def _adjust_confidence_for_emotion(
        self, base_confidence: float, emotional_context: dict
    ) -> float:
        """Adjust topic confidence based on emotional signals."""
        # High arousal (excitement, anger) often indicates strong topic engagement
        arousal = emotional_context.get("arousal", 0.5)
        valence = emotional_context.get("valence", 0.5)

        # Strong emotions (far from neutral) increase confidence
        emotional_intensity = abs(arousal - 0.5) + abs(valence - 0.5)
        confidence_boost = emotional_intensity * 0.2

        return min(1.0, base_confidence + confidence_boost)

    def on_shift(self, callback: Callable[[TopicShift], None]) -> None:
        """Register a callback for topic shifts."""
        self._shift_callbacks.append(callback)

    def _notify_shift(self, shift: TopicShift) -> None:
        """Notify callbacks of a topic shift."""
        for callback in self._shift_callbacks:
            try:
                callback(shift)
            except Exception as e:
                logger.error(f"Topic shift callback error: {e}")

    def get_topic_summary(self) -> dict:
        """Get summary of topic state and history."""
        recent_shifts = list(self._shift_history)[-5:]

        return {
            "current_topic": self.current_topic.value,
            "current_confidence": self._current_state.confidence if self._current_state else 0.0,
            "utterance_count": self._utterance_count,
            "recent_shifts": [s.to_dict() for s in recent_shifts],
            "topic_distribution": (
                self._current_state.region_activations if self._current_state else {}
            ),
        }

    def reset(self) -> None:
        """Reset detector state."""
        self._state_history.clear()
        self._shift_history.clear()
        self._current_state = None
        self._utterance_count = 0

        if self.spreader:
            self.spreader.reset_activations()


# Singleton instance
_detector: TopicDetector | None = None


def get_topic_detector() -> TopicDetector:
    """Get the singleton topic detector."""
    global _detector
    if _detector is None:
        _detector = TopicDetector()
    return _detector
