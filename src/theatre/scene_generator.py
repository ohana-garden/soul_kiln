"""
Scene Generator.

Maps graph activation state to visual representation.

Key insight: The scene is INFORMATIVE, not just decorative.
It conveys meaning about the current topic and emotional state.

Scene = projection of graph state + emotional context
- Which region is hot → scene setting
- Activation intensity → visual energy
- Emotional state → atmosphere/lighting
- Topic shift → scene transition
"""

import logging
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any

from .topic_detector import TopicRegion, TopicState, TopicShift
from .hume_integration import EmotionalState

logger = logging.getLogger(__name__)


class SceneType(str, Enum):
    """Types of scenes that can be generated."""

    # Environment types
    GARDEN = "garden"  # Growth, nurturing, service
    LIBRARY = "library"  # Wisdom, knowledge, learning
    HEARTH = "hearth"  # Warmth, hospitality, community
    TEMPLE = "temple"  # Spirituality, transcendence, devotion
    WORKSHOP = "workshop"  # Practical work, creation, craft
    FORUM = "forum"  # Discussion, justice, debate
    MOUNTAIN = "mountain"  # Challenge, perseverance, clarity
    RIVER = "river"  # Flow, transition, cleansing
    STARFIELD = "starfield"  # Vastness, possibility, wonder

    # Transitional
    CROSSROADS = "crossroads"
    THRESHOLD = "threshold"

    # Fallback
    NEUTRAL = "neutral"


class Atmosphere(str, Enum):
    """Atmospheric qualities for scenes."""

    SERENE = "serene"
    VIBRANT = "vibrant"
    CONTEMPLATIVE = "contemplative"
    ENERGETIC = "energetic"
    WARM = "warm"
    COOL = "cool"
    TENSE = "tense"
    MYSTERIOUS = "mysterious"
    JOYFUL = "joyful"
    SOLEMN = "solemn"


class LightingStyle(str, Enum):
    """Lighting styles for scenes."""

    DAWN = "dawn"  # New beginnings
    MIDDAY = "midday"  # Clarity, productivity
    GOLDEN_HOUR = "golden_hour"  # Warmth, reflection
    DUSK = "dusk"  # Transition, contemplation
    NIGHT = "night"  # Mystery, depth
    CANDLELIT = "candlelit"  # Intimacy
    STARLIT = "starlit"  # Wonder
    OVERCAST = "overcast"  # Subdued, thoughtful
    BRIGHT = "bright"  # Energy, activity


# Mapping from topic regions to scene types
REGION_SCENES = {
    TopicRegion.FOUNDATION: [SceneType.TEMPLE, SceneType.MOUNTAIN],
    TopicRegion.CORE: [SceneType.LIBRARY, SceneType.FORUM],
    TopicRegion.RELATIONAL: [SceneType.HEARTH, SceneType.GARDEN, SceneType.FORUM],
    TopicRegion.PERSONAL: [SceneType.GARDEN, SceneType.RIVER, SceneType.WORKSHOP],
    TopicRegion.TRANSCENDENT: [SceneType.TEMPLE, SceneType.STARFIELD, SceneType.MOUNTAIN],
    TopicRegion.TECHNICAL: [SceneType.WORKSHOP, SceneType.LIBRARY],
    TopicRegion.EMOTIONAL: [SceneType.HEARTH, SceneType.GARDEN, SceneType.RIVER],
    TopicRegion.PRACTICAL: [SceneType.WORKSHOP, SceneType.FORUM],
    TopicRegion.ABSTRACT: [SceneType.STARFIELD, SceneType.LIBRARY],
    TopicRegion.MIXED: [SceneType.CROSSROADS],
    TopicRegion.TRANSITIONAL: [SceneType.THRESHOLD, SceneType.RIVER],
    TopicRegion.UNKNOWN: [SceneType.NEUTRAL],
}


@dataclass
class SceneElement:
    """An element within a scene."""

    type: str  # e.g., "light", "object", "ambient", "character"
    name: str
    properties: dict[str, Any] = field(default_factory=dict)
    position: tuple[float, float, float] | None = None  # x, y, z (normalized 0-1)
    intensity: float = 1.0  # 0-1


@dataclass
class Scene:
    """A generated scene representing the current conversation state."""

    scene_type: SceneType
    atmosphere: Atmosphere
    lighting: LightingStyle
    energy_level: float  # 0-1, based on activation intensity
    elements: list[SceneElement] = field(default_factory=list)
    color_palette: list[str] = field(default_factory=list)  # Hex colors
    description: str = ""  # Human-readable description
    transition_from: SceneType | None = None
    transition_progress: float = 1.0  # 0-1, for blending
    timestamp: datetime = field(default_factory=datetime.utcnow)

    def to_dict(self) -> dict:
        """Convert to dictionary for rendering."""
        return {
            "scene_type": self.scene_type.value,
            "atmosphere": self.atmosphere.value,
            "lighting": self.lighting.value,
            "energy_level": self.energy_level,
            "elements": [
                {
                    "type": e.type,
                    "name": e.name,
                    "properties": e.properties,
                    "position": e.position,
                    "intensity": e.intensity,
                }
                for e in self.elements
            ],
            "color_palette": self.color_palette,
            "description": self.description,
            "transition_from": self.transition_from.value if self.transition_from else None,
            "transition_progress": self.transition_progress,
            "timestamp": self.timestamp.isoformat(),
        }


class SceneGenerator:
    """
    Generates scenes from graph activation state.

    The generator maps:
    - Topic region → scene type
    - Activation intensity → energy level
    - Emotional state → atmosphere and lighting
    - Topic shifts → scene transitions

    Scenes are INFORMATIVE - they help convey the conversation's
    semantic and emotional state visually.
    """

    # Color palettes for different regions
    COLOR_PALETTES = {
        TopicRegion.FOUNDATION: ["#1a237e", "#283593", "#3949ab", "#5c6bc0", "#7986cb"],  # Deep blues
        TopicRegion.CORE: ["#4a148c", "#6a1b9a", "#7b1fa2", "#8e24aa", "#ab47bc"],  # Purples
        TopicRegion.RELATIONAL: ["#e65100", "#ef6c00", "#f57c00", "#fb8c00", "#ff9800"],  # Warm oranges
        TopicRegion.PERSONAL: ["#1b5e20", "#2e7d32", "#388e3c", "#43a047", "#4caf50"],  # Greens
        TopicRegion.TRANSCENDENT: ["#311b92", "#4527a0", "#512da8", "#5e35b1", "#673ab7"],  # Deep purples
        TopicRegion.TECHNICAL: ["#263238", "#37474f", "#455a64", "#546e7a", "#607d8b"],  # Blue-grays
        TopicRegion.EMOTIONAL: ["#c62828", "#d32f2f", "#e53935", "#f44336", "#ef5350"],  # Reds
        TopicRegion.PRACTICAL: ["#4e342e", "#5d4037", "#6d4c41", "#795548", "#8d6e63"],  # Browns
        TopicRegion.ABSTRACT: ["#0d47a1", "#1565c0", "#1976d2", "#1e88e5", "#2196f3"],  # Blues
        TopicRegion.MIXED: ["#424242", "#616161", "#757575", "#9e9e9e", "#bdbdbd"],  # Grays
        TopicRegion.TRANSITIONAL: ["#37474f", "#455a64", "#78909c", "#90a4ae", "#b0bec5"],  # Transitional grays
        TopicRegion.UNKNOWN: ["#212121", "#424242", "#616161", "#757575", "#9e9e9e"],  # Dark grays
    }

    def __init__(self, blend_duration: float = 2.0):
        """
        Initialize the scene generator.

        Args:
            blend_duration: Seconds for scene transitions
        """
        self._blend_duration = blend_duration
        self._current_scene: Scene | None = None
        self._transition_start: datetime | None = None
        self._target_scene: Scene | None = None

    @property
    def current_scene(self) -> Scene | None:
        """Get the current scene (accounting for transitions)."""
        if self._target_scene and self._transition_start:
            elapsed = (datetime.utcnow() - self._transition_start).total_seconds()
            progress = min(1.0, elapsed / self._blend_duration)

            if progress >= 1.0:
                # Transition complete
                self._current_scene = self._target_scene
                self._target_scene = None
                self._transition_start = None
            else:
                # Return blended scene
                return self._create_blended_scene(
                    self._current_scene, self._target_scene, progress
                )

        return self._current_scene

    def generate(
        self,
        topic_state: TopicState,
        emotional_state: EmotionalState | None = None,
        shift: TopicShift | None = None,
    ) -> Scene:
        """
        Generate a scene from topic and emotional state.

        Args:
            topic_state: Current topic detection state
            emotional_state: Optional emotional signals
            shift: Optional topic shift that triggered generation

        Returns:
            Generated Scene
        """
        # Determine scene type from topic region
        scene_type = self._select_scene_type(topic_state, emotional_state)

        # Determine atmosphere from emotional state
        atmosphere = self._select_atmosphere(topic_state, emotional_state)

        # Determine lighting
        lighting = self._select_lighting(topic_state, emotional_state, atmosphere)

        # Calculate energy level from activation
        energy_level = self._calculate_energy(topic_state)

        # Get color palette
        colors = self.COLOR_PALETTES.get(
            topic_state.primary_region, self.COLOR_PALETTES[TopicRegion.UNKNOWN]
        )

        # Generate scene elements
        elements = self._generate_elements(
            scene_type, topic_state, emotional_state, energy_level
        )

        # Generate description
        description = self._generate_description(
            scene_type, atmosphere, lighting, topic_state
        )

        new_scene = Scene(
            scene_type=scene_type,
            atmosphere=atmosphere,
            lighting=lighting,
            energy_level=energy_level,
            elements=elements,
            color_palette=colors,
            description=description,
        )

        # Handle transitions
        if self._current_scene and shift:
            # Start a transition
            self._transition_start = datetime.utcnow()
            self._target_scene = new_scene
            new_scene.transition_from = self._current_scene.scene_type
            new_scene.transition_progress = 0.0
        else:
            self._current_scene = new_scene

        return new_scene

    def _select_scene_type(
        self, topic_state: TopicState, emotional_state: EmotionalState | None
    ) -> SceneType:
        """Select appropriate scene type for the current state."""
        region = topic_state.primary_region
        options = REGION_SCENES.get(region, [SceneType.NEUTRAL])

        if not options:
            return SceneType.NEUTRAL

        # If we have emotional context, use it to influence selection
        if emotional_state:
            # High arousal -> more dynamic scenes
            if emotional_state.arousal > 0.7:
                if SceneType.FORUM in options:
                    return SceneType.FORUM
                if SceneType.WORKSHOP in options:
                    return SceneType.WORKSHOP

            # Negative valence -> contemplative scenes
            if emotional_state.valence < 0.3:
                if SceneType.TEMPLE in options:
                    return SceneType.TEMPLE
                if SceneType.RIVER in options:
                    return SceneType.RIVER

            # Positive valence -> warm scenes
            if emotional_state.valence > 0.7:
                if SceneType.GARDEN in options:
                    return SceneType.GARDEN
                if SceneType.HEARTH in options:
                    return SceneType.HEARTH

        # Default to first option
        return options[0]

    def _select_atmosphere(
        self, topic_state: TopicState, emotional_state: EmotionalState | None
    ) -> Atmosphere:
        """Select atmosphere based on emotional state."""
        if not emotional_state:
            # Default based on confidence
            if topic_state.confidence > 0.8:
                return Atmosphere.SERENE
            elif topic_state.confidence < 0.3:
                return Atmosphere.MYSTERIOUS
            return Atmosphere.CONTEMPLATIVE

        arousal = emotional_state.arousal
        valence = emotional_state.valence

        # High arousal + positive valence = vibrant/joyful
        if arousal > 0.6 and valence > 0.6:
            return Atmosphere.JOYFUL if valence > 0.75 else Atmosphere.VIBRANT

        # High arousal + negative valence = tense/energetic
        if arousal > 0.6 and valence < 0.4:
            return Atmosphere.TENSE if valence < 0.25 else Atmosphere.ENERGETIC

        # Low arousal + positive valence = serene/warm
        if arousal < 0.4 and valence > 0.5:
            return Atmosphere.SERENE if valence > 0.7 else Atmosphere.WARM

        # Low arousal + negative valence = solemn/cool
        if arousal < 0.4 and valence < 0.5:
            return Atmosphere.SOLEMN if valence < 0.3 else Atmosphere.COOL

        # Mid-range = contemplative
        return Atmosphere.CONTEMPLATIVE

    def _select_lighting(
        self,
        topic_state: TopicState,
        emotional_state: EmotionalState | None,
        atmosphere: Atmosphere,
    ) -> LightingStyle:
        """Select lighting style based on state and atmosphere."""
        # Map atmospheres to natural lighting
        atmosphere_lighting = {
            Atmosphere.SERENE: LightingStyle.GOLDEN_HOUR,
            Atmosphere.VIBRANT: LightingStyle.MIDDAY,
            Atmosphere.CONTEMPLATIVE: LightingStyle.DUSK,
            Atmosphere.ENERGETIC: LightingStyle.BRIGHT,
            Atmosphere.WARM: LightingStyle.CANDLELIT,
            Atmosphere.COOL: LightingStyle.OVERCAST,
            Atmosphere.TENSE: LightingStyle.NIGHT,
            Atmosphere.MYSTERIOUS: LightingStyle.STARLIT,
            Atmosphere.JOYFUL: LightingStyle.DAWN,
            Atmosphere.SOLEMN: LightingStyle.DUSK,
        }

        return atmosphere_lighting.get(atmosphere, LightingStyle.MIDDAY)

    def _calculate_energy(self, topic_state: TopicState) -> float:
        """Calculate energy level from activation state."""
        if not topic_state.region_activations:
            return 0.5

        total_activation = sum(topic_state.region_activations.values())
        # Normalize to 0-1 range (assuming max total around 5.0)
        energy = min(1.0, total_activation / 5.0)
        return energy

    def _generate_elements(
        self,
        scene_type: SceneType,
        topic_state: TopicState,
        emotional_state: EmotionalState | None,
        energy_level: float,
    ) -> list[SceneElement]:
        """Generate scene elements based on context."""
        elements = []

        # Base elements for each scene type
        scene_elements = {
            SceneType.GARDEN: [
                SceneElement(type="ambient", name="gentle_breeze", intensity=0.6),
                SceneElement(type="light", name="dappled_sunlight", intensity=0.8),
                SceneElement(type="object", name="flowering_plants", properties={"variety": "mixed"}),
            ],
            SceneType.LIBRARY: [
                SceneElement(type="ambient", name="quiet_rustle", intensity=0.3),
                SceneElement(type="light", name="reading_lamps", intensity=0.7),
                SceneElement(type="object", name="bookshelves", properties={"filled": True}),
            ],
            SceneType.HEARTH: [
                SceneElement(type="ambient", name="crackling_fire", intensity=0.7),
                SceneElement(type="light", name="firelight", intensity=0.8),
                SceneElement(type="object", name="comfortable_seating", properties={"arranged": "circle"}),
            ],
            SceneType.TEMPLE: [
                SceneElement(type="ambient", name="resonant_silence", intensity=0.4),
                SceneElement(type="light", name="filtered_light", intensity=0.5),
                SceneElement(type="object", name="sacred_geometry", properties={"pattern": "complex"}),
            ],
            SceneType.WORKSHOP: [
                SceneElement(type="ambient", name="productive_hum", intensity=0.6),
                SceneElement(type="light", name="task_lighting", intensity=0.9),
                SceneElement(type="object", name="tools_and_materials", properties={"organized": True}),
            ],
            SceneType.FORUM: [
                SceneElement(type="ambient", name="dialogue_murmur", intensity=0.5),
                SceneElement(type="light", name="even_illumination", intensity=0.8),
                SceneElement(type="object", name="gathering_space", properties={"open": True}),
            ],
            SceneType.MOUNTAIN: [
                SceneElement(type="ambient", name="mountain_wind", intensity=0.7),
                SceneElement(type="light", name="clear_sky", intensity=0.9),
                SceneElement(type="object", name="vista", properties={"expansive": True}),
            ],
            SceneType.RIVER: [
                SceneElement(type="ambient", name="flowing_water", intensity=0.8),
                SceneElement(type="light", name="reflections", intensity=0.6),
                SceneElement(type="object", name="riverbanks", properties={"verdant": True}),
            ],
            SceneType.STARFIELD: [
                SceneElement(type="ambient", name="cosmic_silence", intensity=0.2),
                SceneElement(type="light", name="starlight", intensity=0.4),
                SceneElement(type="object", name="constellations", properties={"visible": True}),
            ],
        }

        elements = list(scene_elements.get(scene_type, []))

        # Add dynamic elements based on energy level
        if energy_level > 0.7:
            elements.append(
                SceneElement(
                    type="dynamic",
                    name="heightened_activity",
                    intensity=energy_level,
                    properties={"pulsing": True},
                )
            )
        elif energy_level < 0.3:
            elements.append(
                SceneElement(
                    type="dynamic",
                    name="stillness",
                    intensity=1.0 - energy_level,
                    properties={"calm": True},
                )
            )

        # Add emotional overlay
        if emotional_state and emotional_state.dominant_emotion:
            elements.append(
                SceneElement(
                    type="emotional",
                    name=emotional_state.dominant_emotion,
                    intensity=emotional_state.arousal,
                    properties={"valence": emotional_state.valence},
                )
            )

        # Add topic-specific elements based on active virtues
        for virtue_id in topic_state.active_virtues[:2]:
            elements.append(
                SceneElement(
                    type="virtue",
                    name=virtue_id,
                    intensity=0.6,
                    properties={"anchored": True},
                )
            )

        return elements

    def _generate_description(
        self,
        scene_type: SceneType,
        atmosphere: Atmosphere,
        lighting: LightingStyle,
        topic_state: TopicState,
    ) -> str:
        """Generate human-readable scene description."""
        descriptions = {
            SceneType.GARDEN: "A nurturing garden space",
            SceneType.LIBRARY: "A quiet library filled with knowledge",
            SceneType.HEARTH: "A warm gathering place around the fire",
            SceneType.TEMPLE: "A sacred space for contemplation",
            SceneType.WORKSHOP: "A productive workshop for creation",
            SceneType.FORUM: "An open forum for dialogue",
            SceneType.MOUNTAIN: "A mountain summit with clear views",
            SceneType.RIVER: "A flowing river of change",
            SceneType.STARFIELD: "An infinite starfield of possibility",
            SceneType.CROSSROADS: "A crossroads of decisions",
            SceneType.THRESHOLD: "A threshold between states",
            SceneType.NEUTRAL: "A neutral space",
        }

        base = descriptions.get(scene_type, "A scene")
        return f"{base} with {atmosphere.value} atmosphere, {lighting.value.replace('_', ' ')} lighting."

    def _create_blended_scene(
        self, from_scene: Scene | None, to_scene: Scene, progress: float
    ) -> Scene:
        """Create a blended scene during transition."""
        if not from_scene:
            return to_scene

        # Blend energy levels
        blended_energy = (
            from_scene.energy_level * (1 - progress) + to_scene.energy_level * progress
        )

        # Blend color palettes
        blended_colors = []
        for i in range(min(len(from_scene.color_palette), len(to_scene.color_palette))):
            blended_colors.append(
                self._blend_colors(
                    from_scene.color_palette[i], to_scene.color_palette[i], progress
                )
            )

        # Use target scene type but indicate transition
        return Scene(
            scene_type=to_scene.scene_type,
            atmosphere=to_scene.atmosphere if progress > 0.5 else from_scene.atmosphere,
            lighting=to_scene.lighting if progress > 0.5 else from_scene.lighting,
            energy_level=blended_energy,
            elements=to_scene.elements if progress > 0.5 else from_scene.elements,
            color_palette=blended_colors or to_scene.color_palette,
            description=to_scene.description,
            transition_from=from_scene.scene_type,
            transition_progress=progress,
        )

    def _blend_colors(self, color1: str, color2: str, progress: float) -> str:
        """Blend two hex colors."""
        try:
            r1, g1, b1 = int(color1[1:3], 16), int(color1[3:5], 16), int(color1[5:7], 16)
            r2, g2, b2 = int(color2[1:3], 16), int(color2[3:5], 16), int(color2[5:7], 16)

            r = int(r1 * (1 - progress) + r2 * progress)
            g = int(g1 * (1 - progress) + g2 * progress)
            b = int(b1 * (1 - progress) + b2 * progress)

            return f"#{r:02x}{g:02x}{b:02x}"
        except (ValueError, IndexError):
            return color2


# Singleton instance
_generator: SceneGenerator | None = None


def get_scene_generator() -> SceneGenerator:
    """Get the singleton scene generator."""
    global _generator
    if _generator is None:
        _generator = SceneGenerator()
    return _generator
