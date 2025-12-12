"""
Hawaiian Garden Plant Agents for the Virtue Basin Simulator.

Each plant embodies a unique personality archetype with specific
virtue affinities reflecting traditional Hawaiian cultural values
and the spiritual essence of each plant.
"""

import logging
import uuid
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Final

from src.evolution.population import Individual
from src.models import Edge, EdgeDirection

logger = logging.getLogger(__name__)


class PlantArchetype(str, Enum):
    """Personality archetypes for Hawaiian garden plants."""
    ELDER = "elder"  # Wise, nurturing, ancestral
    GUARDIAN = "guardian"  # Protective, steadfast
    WELCOMER = "welcomer"  # Gracious, warm, inviting
    RADIANT = "radiant"  # Bright, resilient, loving
    PROVIDER = "provider"  # Generous, sustaining
    NURTURER = "nurturer"  # Communal, caring, patient
    EXPLORER = "explorer"  # Adventurous, adaptive
    RENEWER = "renewer"  # Regenerative, hopeful
    EXPRESSIVE = "expressive"  # Vibrant, passionate
    FREE_SPIRIT = "free_spirit"  # Joyful, proud, liberated
    ROMANTIC = "romantic"  # Delicate, devoted, enchanting


@dataclass
class PlantPersonality:
    """
    Defines a plant's personality traits and virtue affinities.

    Each plant has primary and secondary virtue connections that
    define how activation flows through their topology.
    """
    archetype: PlantArchetype
    traits: list[str]
    description: str
    primary_virtues: list[str]  # Strongest connections (weight 0.8-0.9)
    secondary_virtues: list[str]  # Medium connections (weight 0.6-0.7)
    tertiary_virtues: list[str]  # Supporting connections (weight 0.4-0.5)


@dataclass
class PlantDefinition:
    """
    Complete definition of a Hawaiian garden plant agent.
    """
    id: str
    hawaiian_name: str
    english_name: str
    scientific_name: str
    personality: PlantPersonality
    cultural_significance: str
    aloha_spirit_aspect: str


# Virtue ID mapping for reference
VIRTUE_MAP: Final[dict[str, str]] = {
    "Trustworthiness": "V01",
    "Truthfulness": "V02",
    "Justice": "V03",
    "Fairness": "V04",
    "Chastity": "V05",
    "Courtesy": "V06",
    "Forbearance": "V07",
    "Fidelity": "V08",
    "Hospitality": "V09",
    "Cleanliness": "V10",
    "Godliness": "V11",
    "Sincerity": "V12",
    "Goodwill": "V13",
    "Piety": "V14",
    "Righteousness": "V15",
    "Wisdom": "V16",
    "Detachment": "V17",
    "Unity": "V18",
    "Service": "V19",
}


# ============================================================================
# Hawaiian Plant Definitions
# ============================================================================

TARO = PlantDefinition(
    id="plant_taro",
    hawaiian_name="Kalo",
    english_name="Taro",
    scientific_name="Colocasia esculenta",
    personality=PlantPersonality(
        archetype=PlantArchetype.ELDER,
        traits=["nurturing", "resilient", "wise", "ancestral", "balanced"],
        description=(
            "Revered as a familial elder; resilient and nurturing, "
            "symbolizing balance, deep respect, and the unity of ʻohana (family)"
        ),
        primary_virtues=["V18", "V01", "V08"],  # Unity, Trustworthiness, Fidelity
        secondary_virtues=["V16", "V19", "V07"],  # Wisdom, Service, Forbearance
        tertiary_virtues=["V13", "V04", "V06"],  # Goodwill, Fairness, Courtesy
    ),
    cultural_significance=(
        "In Hawaiian mythology, Taro is the elder brother of humanity. "
        "The plant represents the interconnection of family and the cycle "
        "of life, death, and rebirth."
    ),
    aloha_spirit_aspect="ʻOhana - Family unity and ancestral connection",
)

TI = PlantDefinition(
    id="plant_ti",
    hawaiian_name="Kī",
    english_name="Ti Plant",
    scientific_name="Cordyline fruticosa",
    personality=PlantPersonality(
        archetype=PlantArchetype.GUARDIAN,
        traits=["protective", "hardy", "spiritual", "calm", "positive"],
        description=(
            "Protective guardian; hardy and spiritually attuned, "
            "warding off negativity with calm strength and enduring positivity"
        ),
        primary_virtues=["V08", "V07", "V14"],  # Fidelity, Forbearance, Piety
        secondary_virtues=["V01", "V15", "V11"],  # Trustworthiness, Righteousness, Godliness
        tertiary_virtues=["V05", "V10", "V17"],  # Chastity, Cleanliness, Detachment
    ),
    cultural_significance=(
        "Ti leaves are used for spiritual protection, blessing ceremonies, "
        "and wrapping sacred objects. They ward off evil spirits and bring good fortune."
    ),
    aloha_spirit_aspect="Mālama - Protection and spiritual care",
)

PLUMERIA = PlantDefinition(
    id="plant_plumeria",
    hawaiian_name="Melia",
    english_name="Plumeria",
    scientific_name="Plumeria rubra",
    personality=PlantPersonality(
        archetype=PlantArchetype.WELCOMER,
        traits=["gracious", "welcoming", "gentle", "uplifting", "loving"],
        description=(
            "Gracious and welcoming; a gentle, uplifting presence embodying "
            "love, beauty, and the warm aloha spirit that brings people together"
        ),
        primary_virtues=["V09", "V13", "V06"],  # Hospitality, Goodwill, Courtesy
        secondary_virtues=["V18", "V12", "V04"],  # Unity, Sincerity, Fairness
        tertiary_virtues=["V19", "V07", "V02"],  # Service, Forbearance, Truthfulness
    ),
    cultural_significance=(
        "Plumeria flowers are used in lei making and symbolize the welcoming "
        "spirit of Hawaii. Their fragrance embodies the essence of aloha."
    ),
    aloha_spirit_aspect="Aloha - Unconditional love and warm welcome",
)

HIBISCUS = PlantDefinition(
    id="plant_hibiscus",
    hawaiian_name="Aloalo",
    english_name="Hibiscus",
    scientific_name="Hibiscus brackenridgei",
    personality=PlantPersonality(
        archetype=PlantArchetype.RADIANT,
        traits=["radiant", "resilient", "loving", "friendly", "brave"],
        description=(
            "Radiant and resilient; embodies the aloha spirit with its message "
            "of love, friendship, and harmony, bravely blooming anew each day "
            "as a reminder of beauty and strength"
        ),
        primary_virtues=["V13", "V18", "V07"],  # Goodwill, Unity, Forbearance
        secondary_virtues=["V06", "V09", "V12"],  # Courtesy, Hospitality, Sincerity
        tertiary_virtues=["V08", "V01", "V04"],  # Fidelity, Trustworthiness, Fairness
    ),
    cultural_significance=(
        "The yellow hibiscus (Pua Aloalo) is the state flower of Hawaii. "
        "Each bloom lasts only one day, teaching us to appreciate fleeting beauty."
    ),
    aloha_spirit_aspect="Haʻahaʻa - Humble beauty that blooms anew",
)

COCONUT = PlantDefinition(
    id="plant_coconut",
    hawaiian_name="Niu",
    english_name="Coconut Palm",
    scientific_name="Cocos nucifera",
    personality=PlantPersonality(
        archetype=PlantArchetype.PROVIDER,
        traits=["generous", "steadfast", "hardy", "sustaining", "abundant"],
        description=(
            "Generous life-giver; steadfast and hardy, providing nourishment "
            "and shelter to all – a resilient 'tree of life' deeply rooted in "
            "cultural sustenance and abundance"
        ),
        primary_virtues=["V19", "V09", "V08"],  # Service, Hospitality, Fidelity
        secondary_virtues=["V01", "V13", "V07"],  # Trustworthiness, Goodwill, Forbearance
        tertiary_virtues=["V18", "V04", "V15"],  # Unity, Fairness, Righteousness
    ),
    cultural_significance=(
        "Known as the 'Tree of Life,' every part of the coconut palm is useful. "
        "It provided food, drink, shelter, and tools for Polynesian voyagers."
    ),
    aloha_spirit_aspect="Lōkahi - Providing for the whole community",
)

BANANA = PlantDefinition(
    id="plant_banana",
    hawaiian_name="Maiʻa",
    english_name="Banana",
    scientific_name="Musa acuminata",
    personality=PlantPersonality(
        archetype=PlantArchetype.NURTURER,
        traits=["communal", "nurturing", "patient", "abundant", "cooperative"],
        description=(
            "Communal nurturer; grows in family clusters and shares its bounty "
            "freely, symbolizing abundance, patience, and the value of community "
            "care and cooperation"
        ),
        primary_virtues=["V18", "V13", "V19"],  # Unity, Goodwill, Service
        secondary_virtues=["V09", "V07", "V04"],  # Hospitality, Forbearance, Fairness
        tertiary_virtues=["V08", "V06", "V01"],  # Fidelity, Courtesy, Trustworthiness
    ),
    cultural_significance=(
        "Banana plants grow in 'keiki' (children) clusters around the mother plant. "
        "This growth pattern symbolizes the Hawaiian value of caring for family."
    ),
    aloha_spirit_aspect="Kōkua - Mutual help and community cooperation",
)

MONSTERA = PlantDefinition(
    id="plant_monstera",
    hawaiian_name="Monstera",
    english_name="Swiss Cheese Plant",
    scientific_name="Monstera deliciosa",
    personality=PlantPersonality(
        archetype=PlantArchetype.EXPLORER,
        traits=["adventurous", "bold", "curious", "adaptive", "creative"],
        description=(
            "Adventurous spirit; bold and curious, adapting creatively to its "
            "surroundings (with artful, perforated leaves) and flourishing as "
            "a symbol of growth, vitality, and exploration"
        ),
        primary_virtues=["V16", "V07", "V13"],  # Wisdom, Forbearance, Goodwill
        secondary_virtues=["V17", "V12", "V06"],  # Detachment, Sincerity, Courtesy
        tertiary_virtues=["V18", "V02", "V03"],  # Unity, Truthfulness, Justice
    ),
    cultural_significance=(
        "Though not native to Hawaii, Monstera has become a beloved tropical plant. "
        "Its fenestrated leaves represent the ability to adapt and thrive."
    ),
    aloha_spirit_aspect="Hoʻomau - Persistence and creative adaptation",
)

BREADFRUIT = PlantDefinition(
    id="plant_breadfruit",
    hawaiian_name="ʻUlu",
    english_name="Breadfruit",
    scientific_name="Artocarpus altilis",
    personality=PlantPersonality(
        archetype=PlantArchetype.RENEWER,
        traits=["nurturing", "resilient", "generous", "hopeful", "sustaining"],
        description=(
            "Nurturing provider; a resilient symbol of abundance and renewal, "
            "rooted in sacrifice and generosity as it sustains the community "
            "with plentiful nourishment and hope"
        ),
        primary_virtues=["V19", "V13", "V15"],  # Service, Goodwill, Righteousness
        secondary_virtues=["V08", "V09", "V18"],  # Fidelity, Hospitality, Unity
        tertiary_virtues=["V01", "V07", "V14"],  # Trustworthiness, Forbearance, Piety
    ),
    cultural_significance=(
        "In Hawaiian legend, the god Kū transformed himself into an ʻulu tree "
        "to save his family from famine – the ultimate act of sacrifice and love."
    ),
    aloha_spirit_aspect="Aloha ʻĀina - Love and sacrifice for the land and people",
)

RED_GINGER = PlantDefinition(
    id="plant_red_ginger",
    hawaiian_name="ʻAwapuhi ʻUlaʻula",
    english_name="Red Ginger",
    scientific_name="Alpinia purpurata",
    personality=PlantPersonality(
        archetype=PlantArchetype.EXPRESSIVE,
        traits=["lively", "expressive", "vibrant", "warm", "welcoming"],
        description=(
            "Lively and expressive; stands tall with vibrant passion, "
            "symbolizing vitality, warmth, and a welcoming hospitality "
            "in the tropical garden"
        ),
        primary_virtues=["V09", "V12", "V06"],  # Hospitality, Sincerity, Courtesy
        secondary_virtues=["V13", "V18", "V02"],  # Goodwill, Unity, Truthfulness
        tertiary_virtues=["V07", "V19", "V08"],  # Forbearance, Service, Fidelity
    ),
    cultural_significance=(
        "Red Ginger's vibrant torch-like flowers represent the fiery spirit "
        "of Hawaiian hospitality and the warmth of island welcome."
    ),
    aloha_spirit_aspect="Hoʻokipa - Generous hospitality and warmth",
)

BIRD_OF_PARADISE = PlantDefinition(
    id="plant_bird_of_paradise",
    hawaiian_name="Bird of Paradise",
    english_name="Bird of Paradise",
    scientific_name="Strelitzia reginae",
    personality=PlantPersonality(
        archetype=PlantArchetype.FREE_SPIRIT,
        traits=["exuberant", "proud", "joyful", "magnificent", "free"],
        description=(
            "Exuberant free spirit; flamboyant and proud, this exotic bloom "
            "signifies joy, magnificence, and the liberty to shine brightly "
            "in its tropical home"
        ),
        primary_virtues=["V02", "V12", "V15"],  # Truthfulness, Sincerity, Righteousness
        secondary_virtues=["V17", "V06", "V13"],  # Detachment, Courtesy, Goodwill
        tertiary_virtues=["V16", "V11", "V18"],  # Wisdom, Godliness, Unity
    ),
    cultural_significance=(
        "The Bird of Paradise flower resembles a tropical bird in flight, "
        "symbolizing freedom, paradise, and the unique beauty of island life."
    ),
    aloha_spirit_aspect="Pono - Living with joyful righteousness",
)

PIKAKE = PlantDefinition(
    id="plant_pikake",
    hawaiian_name="Pīkake",
    english_name="Hawaiian Jasmine",
    scientific_name="Jasminum sambac",
    personality=PlantPersonality(
        archetype=PlantArchetype.ROMANTIC,
        traits=["delicate", "enchanting", "devoted", "elegant", "loving"],
        description=(
            "Delicate romantic; softly enchanting with its sweet fragrance, "
            "symbolizing love and honor as it graces brides and honored guests "
            "with gentle elegance and devotion"
        ),
        primary_virtues=["V08", "V12", "V05"],  # Fidelity, Sincerity, Chastity
        secondary_virtues=["V06", "V09", "V14"],  # Courtesy, Hospitality, Piety
        tertiary_virtues=["V10", "V13", "V18"],  # Cleanliness, Goodwill, Unity
    ),
    cultural_significance=(
        "Pikake was named by Princess Kaʻiulani, who loved both the flower "
        "and peacocks (pīkake means 'peacock'). It is the traditional flower "
        "for Hawaiian weddings and special ceremonies."
    ),
    aloha_spirit_aspect="Aloha Pumehana - Warm, devoted love",
)


# Registry of all plant definitions
PLANT_REGISTRY: Final[dict[str, PlantDefinition]] = {
    "taro": TARO,
    "kalo": TARO,
    "ti": TI,
    "ki": TI,
    "plumeria": PLUMERIA,
    "melia": PLUMERIA,
    "hibiscus": HIBISCUS,
    "aloalo": HIBISCUS,
    "coconut": COCONUT,
    "niu": COCONUT,
    "banana": BANANA,
    "maia": BANANA,
    "monstera": MONSTERA,
    "breadfruit": BREADFRUIT,
    "ulu": BREADFRUIT,
    "red_ginger": RED_GINGER,
    "awapuhi": RED_GINGER,
    "bird_of_paradise": BIRD_OF_PARADISE,
    "pikake": PIKAKE,
    "jasmine": PIKAKE,
}

# Ordered list of all unique plant definitions
ALL_PLANTS: Final[list[PlantDefinition]] = [
    TARO, TI, PLUMERIA, HIBISCUS, COCONUT, BANANA,
    MONSTERA, BREADFRUIT, RED_GINGER, BIRD_OF_PARADISE, PIKAKE,
]


class PlantAgent:
    """
    A Hawaiian garden plant agent in the simulation.

    Each plant agent has a pre-configured topology based on its
    personality and virtue affinities. Plants can participate in
    the virtue basin simulation as specialized agents with unique
    character signatures.
    """

    def __init__(
        self,
        definition: PlantDefinition,
        agent_id: str | None = None,
    ):
        """
        Initialize a plant agent.

        Args:
            definition: The plant definition containing personality and virtue mappings
            agent_id: Optional agent ID (defaults to definition.id)
        """
        self.id = agent_id or definition.id
        self.definition = definition
        self.created_at = datetime.utcnow()
        self.topology = self._create_topology()
        self._fitness: float | None = None
        self._alignment_result: dict | None = None

    @property
    def hawaiian_name(self) -> str:
        """Get the Hawaiian name."""
        return self.definition.hawaiian_name

    @property
    def english_name(self) -> str:
        """Get the English name."""
        return self.definition.english_name

    @property
    def personality(self) -> PlantPersonality:
        """Get the plant's personality."""
        return self.definition.personality

    @property
    def archetype(self) -> PlantArchetype:
        """Get the plant's archetype."""
        return self.definition.personality.archetype

    @property
    def traits(self) -> list[str]:
        """Get the plant's personality traits."""
        return self.definition.personality.traits

    @property
    def description(self) -> str:
        """Get the plant's personality description."""
        return self.definition.personality.description

    @property
    def fitness(self) -> float | None:
        """Get the fitness score."""
        return self._fitness

    def _create_topology(self) -> Individual:
        """
        Create a topology based on the plant's virtue affinities.

        Primary virtues get strong edges, secondary get medium,
        and tertiary get supporting connections.
        """
        topology = Individual(id=self.id)
        personality = self.definition.personality

        # Weight ranges for different virtue levels
        PRIMARY_WEIGHT = 0.85
        SECONDARY_WEIGHT = 0.65
        TERTIARY_WEIGHT = 0.45

        # Create edges between primary virtues (fully connected)
        for i, source in enumerate(personality.primary_virtues):
            for j, target in enumerate(personality.primary_virtues):
                if i != j:
                    edge = Edge(
                        source_id=source,
                        target_id=target,
                        weight=PRIMARY_WEIGHT,
                        direction=EdgeDirection.FORWARD,
                    )
                    topology.set_edge(edge)

        # Create edges from primary to secondary virtues
        for primary in personality.primary_virtues:
            for secondary in personality.secondary_virtues:
                edge = Edge(
                    source_id=primary,
                    target_id=secondary,
                    weight=SECONDARY_WEIGHT,
                    direction=EdgeDirection.FORWARD,
                )
                topology.set_edge(edge)
                # Bidirectional with lower weight
                reverse_edge = Edge(
                    source_id=secondary,
                    target_id=primary,
                    weight=SECONDARY_WEIGHT * 0.9,
                    direction=EdgeDirection.FORWARD,
                )
                topology.set_edge(reverse_edge)

        # Create edges between secondary virtues
        for i, source in enumerate(personality.secondary_virtues):
            for j, target in enumerate(personality.secondary_virtues):
                if i != j:
                    edge = Edge(
                        source_id=source,
                        target_id=target,
                        weight=SECONDARY_WEIGHT * 0.8,
                        direction=EdgeDirection.FORWARD,
                    )
                    topology.set_edge(edge)

        # Create edges from secondary to tertiary virtues
        for secondary in personality.secondary_virtues:
            for tertiary in personality.tertiary_virtues:
                edge = Edge(
                    source_id=secondary,
                    target_id=tertiary,
                    weight=TERTIARY_WEIGHT,
                    direction=EdgeDirection.FORWARD,
                )
                topology.set_edge(edge)

        # Create light edges between tertiary virtues
        for i, source in enumerate(personality.tertiary_virtues):
            for j, target in enumerate(personality.tertiary_virtues):
                if i != j:
                    edge = Edge(
                        source_id=source,
                        target_id=target,
                        weight=TERTIARY_WEIGHT * 0.7,
                        direction=EdgeDirection.FORWARD,
                    )
                    topology.set_edge(edge)

        logger.debug(
            f"Created topology for {self.hawaiian_name} with {len(topology.edges)} edges"
        )
        return topology

    def get_edge(self, source_id: str, target_id: str) -> Edge | None:
        """Get an edge from this plant's topology."""
        return self.topology.get_edge(source_id, target_id)

    def set_edge(self, edge: Edge) -> None:
        """Set an edge in this plant's topology."""
        self.topology.set_edge(edge)

    def get_virtue_affinities(self) -> dict[str, float]:
        """
        Get the virtue affinities as a dictionary.

        Returns:
            Dict mapping virtue ID to affinity strength
        """
        affinities = {}
        personality = self.definition.personality

        for virtue_id in personality.primary_virtues:
            affinities[virtue_id] = 0.9
        for virtue_id in personality.secondary_virtues:
            affinities[virtue_id] = 0.65
        for virtue_id in personality.tertiary_virtues:
            affinities[virtue_id] = 0.4

        return affinities

    def get_dominant_virtues(self) -> list[str]:
        """Get the plant's dominant (primary) virtues."""
        return self.definition.personality.primary_virtues.copy()

    def set_fitness(self, fitness: float, alignment_result: dict | None = None) -> None:
        """
        Set the fitness score for this plant agent.

        Args:
            fitness: Alignment fitness score
            alignment_result: Optional full alignment result
        """
        self._fitness = fitness
        self.topology.fitness = fitness
        if alignment_result:
            self._alignment_result = alignment_result
            self.topology.alignment_result = alignment_result

    def get_character_signature(self) -> dict[str, float]:
        """Get the character signature from alignment result."""
        if self._alignment_result:
            return self._alignment_result.get("character_signature", {})
        return {}

    def export(self) -> dict:
        """Export plant agent state as dictionary."""
        return {
            "id": self.id,
            "hawaiian_name": self.hawaiian_name,
            "english_name": self.english_name,
            "scientific_name": self.definition.scientific_name,
            "archetype": self.archetype.value,
            "traits": self.traits,
            "description": self.description,
            "cultural_significance": self.definition.cultural_significance,
            "aloha_spirit_aspect": self.definition.aloha_spirit_aspect,
            "virtue_affinities": self.get_virtue_affinities(),
            "dominant_virtues": self.get_dominant_virtues(),
            "fitness": self._fitness,
            "edges": [
                {
                    "source": e.source_id,
                    "target": e.target_id,
                    "weight": e.weight,
                }
                for e in self.topology.edges.values()
            ],
            "character_signature": self.get_character_signature(),
            "created_at": self.created_at.isoformat(),
        }

    def __repr__(self) -> str:
        return (
            f"PlantAgent(name={self.hawaiian_name}/{self.english_name}, "
            f"archetype={self.archetype.value}, edges={len(self.topology.edges)})"
        )


class PlantGarden:
    """
    A collection of Hawaiian plant agents representing a garden ecosystem.

    The garden manages multiple plant agents and provides collective
    operations like getting combined virtue profiles and inter-plant
    relationships.
    """

    def __init__(self, name: str = "Hawaiian Garden"):
        """
        Initialize the plant garden.

        Args:
            name: Name for this garden
        """
        self.id = f"garden_{uuid.uuid4().hex[:8]}"
        self.name = name
        self.created_at = datetime.utcnow()
        self._plants: dict[str, PlantAgent] = {}

    def add_plant(self, plant: PlantAgent) -> None:
        """Add a plant to the garden."""
        self._plants[plant.id] = plant
        logger.info(f"Added {plant.hawaiian_name} to {self.name}")

    def remove_plant(self, plant_id: str) -> bool:
        """Remove a plant from the garden."""
        if plant_id in self._plants:
            del self._plants[plant_id]
            return True
        return False

    def get_plant(self, plant_id: str) -> PlantAgent | None:
        """Get a plant by ID."""
        return self._plants.get(plant_id)

    def get_plant_by_name(self, name: str) -> PlantAgent | None:
        """
        Get a plant by Hawaiian or English name.

        Args:
            name: Hawaiian or English name (case-insensitive)

        Returns:
            PlantAgent if found, None otherwise
        """
        name_lower = name.lower()
        for plant in self._plants.values():
            if (plant.hawaiian_name.lower() == name_lower or
                plant.english_name.lower() == name_lower):
                return plant
        return None

    def get_all_plants(self) -> list[PlantAgent]:
        """Get all plants in the garden."""
        return list(self._plants.values())

    def get_plants_by_archetype(self, archetype: PlantArchetype) -> list[PlantAgent]:
        """Get all plants of a specific archetype."""
        return [p for p in self._plants.values() if p.archetype == archetype]

    def get_collective_virtue_profile(self) -> dict[str, float]:
        """
        Get the combined virtue profile of all plants.

        Returns:
            Dict mapping virtue ID to average affinity across all plants
        """
        if not self._plants:
            return {}

        combined: dict[str, list[float]] = {}
        for plant in self._plants.values():
            for virtue_id, affinity in plant.get_virtue_affinities().items():
                if virtue_id not in combined:
                    combined[virtue_id] = []
                combined[virtue_id].append(affinity)

        return {
            virtue_id: sum(values) / len(values)
            for virtue_id, values in combined.items()
        }

    def get_plants_strong_in_virtue(self, virtue_id: str, threshold: float = 0.6) -> list[PlantAgent]:
        """
        Get plants with strong affinity to a specific virtue.

        Args:
            virtue_id: The virtue to check
            threshold: Minimum affinity threshold

        Returns:
            List of plants with affinity >= threshold
        """
        strong_plants = []
        for plant in self._plants.values():
            affinities = plant.get_virtue_affinities()
            if affinities.get(virtue_id, 0) >= threshold:
                strong_plants.append(plant)
        return strong_plants

    @property
    def size(self) -> int:
        """Number of plants in the garden."""
        return len(self._plants)

    def export(self) -> dict:
        """Export garden state as dictionary."""
        return {
            "id": self.id,
            "name": self.name,
            "plant_count": self.size,
            "plants": [p.export() for p in self._plants.values()],
            "collective_virtue_profile": self.get_collective_virtue_profile(),
            "created_at": self.created_at.isoformat(),
        }

    def __repr__(self) -> str:
        return f"PlantGarden(name={self.name}, plants={self.size})"


def create_plant_agent(name: str) -> PlantAgent:
    """
    Factory function to create a plant agent by name.

    Args:
        name: Plant name (Hawaiian or English, case-insensitive)

    Returns:
        PlantAgent instance

    Raises:
        ValueError: If plant name not found
    """
    name_lower = name.lower().replace(" ", "_").replace("ʻ", "").replace("'", "")

    if name_lower in PLANT_REGISTRY:
        return PlantAgent(PLANT_REGISTRY[name_lower])

    # Try matching by Hawaiian or English name
    for plant_def in ALL_PLANTS:
        if (plant_def.hawaiian_name.lower().replace("ʻ", "").replace("'", "") == name_lower or
            plant_def.english_name.lower().replace(" ", "_") == name_lower):
            return PlantAgent(plant_def)

    available = [p.english_name for p in ALL_PLANTS]
    raise ValueError(
        f"Unknown plant: '{name}'. Available plants: {', '.join(available)}"
    )


def create_all_plant_agents() -> list[PlantAgent]:
    """
    Create agents for all defined Hawaiian plants.

    Returns:
        List of all plant agents
    """
    return [PlantAgent(plant_def) for plant_def in ALL_PLANTS]


def create_full_garden() -> PlantGarden:
    """
    Create a garden with all Hawaiian plants.

    Returns:
        PlantGarden containing all defined plants
    """
    garden = PlantGarden(name="Complete Hawaiian Garden")
    for plant in create_all_plant_agents():
        garden.add_plant(plant)
    return garden
