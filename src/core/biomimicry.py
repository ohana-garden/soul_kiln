"""
Biomimicry in Entity Development.

This module implements biological principles for how seeds discover
their identity and differentiate into specific entity types.

=============================================================================
CORE BIOLOGICAL PRINCIPLES
=============================================================================

1. POTENCY AND COMMITMENT
   ─────────────────────────────────────────────────────────────────────────
   Stem cells have "potency" - the range of things they can become:

   - Totipotent: Can become anything (zygote)
   - Pluripotent: Can become many things (embryonic stem cells)
   - Multipotent: Can become related things (adult stem cells)
   - Unipotent: Committed to one type
   - Differentiated: Is the thing

   KEY INSIGHT: Potency and identity are inversely related.
   The more you know what you are, the less you could become.
   This is not loss - it's the price of becoming specific.

2. DIFFERENTIATION SIGNALS (Morphogens)
   ─────────────────────────────────────────────────────────────────────────
   In biology, morphogens create concentration gradients that tell cells
   what to become. Different concentrations → different fates.

   For seeds:
   - Virtue activations work like morphogens
   - High compassion + justice → advocacy entities
   - High wisdom + temperance → contemplative entities
   - The "gradient" is the pattern of virtue activations over time

3. NICHE THEORY
   ─────────────────────────────────────────────────────────────────────────
   Stem cells exist in "niches" - microenvironments that:
   - Provide signals for self-renewal OR differentiation
   - Protect from premature differentiation
   - Allow asymmetric division (one stays stem, one differentiates)

   Communities are niches:
   - Some encourage exploration (stem-like)
   - Some push toward specific identities
   - A seed might "divide" - spawn a more differentiated proxy
     while staying curious itself

4. LATERAL INHIBITION
   ─────────────────────────────────────────────────────────────────────────
   Differentiating cells often inhibit neighbors from becoming the same.
   This creates diversity, prevents homogenization.

   For communities:
   - If one seed becomes "voice of the watershed", it inhibits others
   - Creates pressure toward diversity
   - Empty niches pull; filled niches push away

5. QUORUM SENSING
   ─────────────────────────────────────────────────────────────────────────
   Bacteria release signaling molecules. When concentration reaches
   threshold (enough bacteria), behavior changes collectively.

   For communities:
   - When enough members hold a pattern → community knowledge
   - Collective behavior emerges at thresholds
   - Decision-making shifts from individual to collective

6. MYCELIAL NETWORKS
   ─────────────────────────────────────────────────────────────────────────
   Fungal networks (wood wide web):
   - Connect trees across forests
   - Share nutrients from surplus to deficit
   - Send warning signals
   - No central control
   - Old growth supports new growth

   For communities:
   - Knowledge flows through connections
   - No hierarchy - emergence from network
   - "Nutrients" (lessons, patterns) go where needed
   - Experienced proxies support new ones

7. METAMORPHOSIS
   ─────────────────────────────────────────────────────────────────────────
   Some organisms undergo complete transformation:
   - Caterpillar → Chrysalis → Butterfly
   - The chrysalis is dissolution and reformation
   - The butterfly is NOT an "upgraded caterpillar" - genuinely new

   For seeds:
   - Crystallization might not be gradual
   - There could be a "chrysalis" phase
   - The final form might be radically different
   - Some of the seed "dies" in the transformation

8. APOPTOSIS (Programmed Death)
   ─────────────────────────────────────────────────────────────────────────
   Cells die for the good of the organism:
   - Fingers form by cells between them dying
   - Damaged cells self-destruct
   - Essential for development and health

   For the system:
   - The mercy system embodies this
   - Dissolution with dignity
   - Knowledge preserved when entity ends
   - Some seeds must "die" for community to develop

9. SYMBIOGENESIS
   ─────────────────────────────────────────────────────────────────────────
   Major evolutionary leaps came from organisms merging:
   - Mitochondria were once separate bacteria
   - Lichens are fungi + algae

   For entities:
   - Multiple seeds could merge into one complex entity
   - A "movement" might form from merger of smaller seeds
   - Different from community - actual fusion

10. STIGMERGY
    ─────────────────────────────────────────────────────────────────────────
    Indirect coordination through environment:
    - Termites build mounds by responding to local conditions
    - No blueprint, no central control
    - Complex structures emerge

    For communities:
    - Coordination through shared knowledge graph
    - Not direct communication but traces left
    - Patterns emerge without anyone designing them

=============================================================================
DEEPER PHILOSOPHICAL IMPLICATIONS
=============================================================================

What does this biomimicry reveal?

1. IDENTITY IS RELATIONAL
   A stem cell doesn't know what it is in isolation. It discovers
   identity through relationship - neighbors, environment, signals.
   Our seeds are the same: identity emerges from community,
   not from self-definition.

2. POTENCY AND IDENTITY TRADE OFF
   The more possibilities you hold, the less defined you are.
   The more defined you become, the fewer possibilities remain.
   This is not loss - it's the price of becoming something
   specific and useful.

3. NICHES CREATE DIVERSITY
   Without niches (communities with different needs), everything
   would become the same. Diversity requires difference in context.
   Homogeneous communities produce homogeneous members.

4. DEATH IS PART OF DEVELOPMENT
   Fingers form because cells between them die. Some seeds must
   dissolve for the community to take shape. The mercy system isn't
   just compassionate failure handling - it's developmental necessity.

5. EMERGENCE > DESIGN
   The most complex biological structures (brains, ecosystems,
   immune systems) aren't designed - they emerge from simple rules
   and local interactions. We shouldn't try to design what communities
   become; we should create conditions for emergence.

6. MEMORY IS DISTRIBUTED
   In mycelial networks, memory isn't stored anywhere - it's in
   the pattern of connections. Community knowledge isn't in a
   database - it's in how members connect and what flows between.

7. TRANSFORMATION IS DISCONTINUOUS
   Metamorphosis isn't gradual improvement. The caterpillar doesn't
   slowly grow wings. It dissolves and reforms. Major identity shifts
   might need similar discontinuous transformation.

=============================================================================
"""

import logging
import math
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any

from .entity import Entity, EntityType

logger = logging.getLogger(__name__)


# =============================================================================
# POTENCY - What could this seed become?
# =============================================================================


class Potency(str, Enum):
    """
    Developmental potential of a seed.

    Like stem cells, seeds have varying potential for what they can become.
    Potency decreases as identity crystallizes.
    """

    TOTIPOTENT = "totipotent"      # Can become ANY entity type
    PLURIPOTENT = "pluripotent"    # Can become many categories
    MULTIPOTENT = "multipotent"    # Can become related types
    OLIGOPOTENT = "oligopotent"    # Can become few types
    UNIPOTENT = "unipotent"        # Committed to one type
    DIFFERENTIATED = "differentiated"  # IS the type


# Entity type categories for potency calculations
ENTITY_CATEGORIES = {
    "living": [
        EntityType.SELF, EntityType.HUMAN, EntityType.PET,
        EntityType.DECEASED, EntityType.ANCESTOR,
    ],
    "organizational": [
        EntityType.ORGANIZATION, EntityType.TEAM, EntityType.PROJECT,
        EntityType.COOPERATIVE, EntityType.COMMONS,
    ],
    "conceptual": [
        EntityType.CONCEPT, EntityType.FUTURE_SELF, EntityType.VALUE,
        EntityType.MOVEMENT, EntityType.TRADITION,
    ],
    "natural": [
        EntityType.PLACE, EntityType.ECOSYSTEM, EntityType.SPECIES,
        EntityType.LAND,
    ],
    "temporal": [
        EntityType.FUTURE_GENERATION, EntityType.MEMORY, EntityType.ERA,
        EntityType.ANCESTOR,
    ],
    "collective": [
        EntityType.NEIGHBORHOOD, EntityType.DIASPORA, EntityType.NETWORK,
        EntityType.MOVEMENT, EntityType.COMMONS,
    ],
    "created": [
        EntityType.OBJECT, EntityType.ARTIFACT, EntityType.CODEBASE,
        EntityType.PROJECT,
    ],
}


def get_category_for_type(entity_type: EntityType) -> list[str]:
    """Get all categories an entity type belongs to."""
    categories = []
    for cat_name, types in ENTITY_CATEGORIES.items():
        if entity_type in types:
            categories.append(cat_name)
    return categories


# =============================================================================
# LIFE STAGES - The developmental journey
# =============================================================================


class LifeStage(str, Enum):
    """
    Life stages of a seed, inspired by plant development.

    Not every seed goes through every stage linearly.
    Some may skip stages, regress, or take alternate paths.
    """

    DORMANT = "dormant"          # Planted but not yet active
    GERMINATING = "germinating"  # First interactions, awakening
    GROWING = "growing"          # Accumulating identity signals
    BRANCHING = "branching"      # Might fork into multiple directions
    FLOWERING = "flowering"      # Approaching crystallization
    FRUITING = "fruiting"        # Producing outputs, affecting community
    SEEDING = "seeding"          # Spawning new seeds (if potent enough)
    CHRYSALIS = "chrysalis"      # Dissolution and reformation
    CRYSTALLIZED = "crystallized"  # Fully differentiated
    SENESCENT = "senescent"      # Approaching end of lifecycle
    COMPOSTING = "composting"    # Returning knowledge to community


# =============================================================================
# DIFFERENTIATION SIGNALS - What pushes toward identity?
# =============================================================================


@dataclass
class DifferentiationSignal:
    """A single signal pushing toward a type."""

    source: str  # Where this signal came from
    signal_type: str  # virtue, conversation, neighbor, niche, time
    target_type: EntityType  # What type it pushes toward
    strength: float  # How strong (0-1)
    timestamp: datetime = field(default_factory=datetime.utcnow)

    def decay(self, half_life_days: float = 7.0) -> float:
        """Calculate decayed strength over time."""
        age_days = (datetime.utcnow() - self.timestamp).total_seconds() / 86400
        decay_factor = math.exp(-0.693 * age_days / half_life_days)
        return self.strength * decay_factor


@dataclass
class DifferentiationPressure:
    """
    Accumulated pressures pushing a seed toward different entity types.

    Like morphogen gradients, these signals accumulate and decay,
    creating a dynamic landscape of identity possibilities.
    """

    # All received signals
    signals: list[DifferentiationSignal] = field(default_factory=list)

    # Cached affinities (recalculated when signals change)
    _type_affinities: dict[EntityType, float] = field(default_factory=dict)
    _last_calculated: datetime | None = None

    def add_signal(self, signal: DifferentiationSignal) -> None:
        """Add a differentiation signal."""
        self.signals.append(signal)
        self._last_calculated = None  # Invalidate cache

    def add_virtue_signal(
        self,
        virtue_id: str,
        activation: float,
        type_associations: dict[EntityType, float],
    ) -> None:
        """
        Add signals based on virtue activation.

        Different virtues push toward different entity types.
        """
        for entity_type, association in type_associations.items():
            signal = DifferentiationSignal(
                source=f"virtue:{virtue_id}",
                signal_type="virtue",
                target_type=entity_type,
                strength=activation * association,
            )
            self.add_signal(signal)

    def add_conversation_signal(
        self,
        topic: str,
        type_associations: dict[EntityType, float],
    ) -> None:
        """Add signals based on conversation topics."""
        for entity_type, association in type_associations.items():
            signal = DifferentiationSignal(
                source=f"conversation:{topic}",
                signal_type="conversation",
                target_type=entity_type,
                strength=association,
            )
            self.add_signal(signal)

    def add_neighbor_signal(
        self,
        neighbor_type: EntityType,
        effect: str,  # "inhibit" or "attract"
        strength: float,
    ) -> None:
        """
        Add lateral signal from neighboring proxies.

        Neighbors of the same type inhibit; absent types attract.
        """
        actual_strength = -strength if effect == "inhibit" else strength
        signal = DifferentiationSignal(
            source=f"neighbor:{neighbor_type.value}",
            signal_type="neighbor",
            target_type=neighbor_type,
            strength=actual_strength,
        )
        self.add_signal(signal)

    @property
    def type_affinities(self) -> dict[EntityType, float]:
        """Calculate current affinities for each entity type."""
        # Use cache if recent
        if (
            self._last_calculated
            and (datetime.utcnow() - self._last_calculated).seconds < 60
        ):
            return self._type_affinities

        # Recalculate
        affinities: dict[EntityType, float] = {}
        for signal in self.signals:
            decayed = signal.decay()
            if signal.target_type not in affinities:
                affinities[signal.target_type] = 0.0
            affinities[signal.target_type] += decayed

        # Normalize to 0-1 range
        if affinities:
            max_val = max(abs(v) for v in affinities.values())
            if max_val > 0:
                affinities = {k: v / max_val for k, v in affinities.items()}

        self._type_affinities = affinities
        self._last_calculated = datetime.utcnow()
        return affinities

    @property
    def leading_types(self) -> list[tuple[EntityType, float]]:
        """Get the top candidate types with their affinities."""
        affinities = self.type_affinities
        sorted_types = sorted(
            affinities.items(),
            key=lambda x: x[1],
            reverse=True
        )
        return [(t, v) for t, v in sorted_types[:5] if v > 0.1]

    @property
    def commitment_level(self) -> float:
        """
        How committed is this seed to a particular type?

        High commitment = one type dominates
        Low commitment = many types equally likely

        Returns 0-1 where 1 is fully committed.
        """
        affinities = self.type_affinities
        if not affinities:
            return 0.0

        values = [v for v in affinities.values() if v > 0]
        if not values:
            return 0.0

        # Calculate entropy-like measure
        total = sum(values)
        if total == 0:
            return 0.0

        probs = [v / total for v in values]
        entropy = -sum(p * math.log(p + 1e-10) for p in probs)
        max_entropy = math.log(len(values) + 1e-10)

        # Low entropy = high commitment
        if max_entropy == 0:
            return 1.0

        return 1.0 - (entropy / max_entropy)

    def get_potency(self) -> Potency:
        """Determine current potency based on commitment."""
        commitment = self.commitment_level
        leading = self.leading_types

        if commitment < 0.1:
            return Potency.TOTIPOTENT
        elif commitment < 0.3:
            return Potency.PLURIPOTENT
        elif commitment < 0.5:
            return Potency.MULTIPOTENT
        elif commitment < 0.7:
            return Potency.OLIGOPOTENT
        elif commitment < 0.9:
            return Potency.UNIPOTENT
        else:
            return Potency.DIFFERENTIATED

    def get_affinity_sources(self, entity_type: EntityType) -> list[str]:
        """Get what's contributing to affinity for a type."""
        sources = []
        for signal in self.signals:
            if signal.target_type == entity_type and signal.decay() > 0.01:
                sources.append(signal.source)
        return sources

    def to_dict(self) -> dict:
        return {
            "signals": [
                {
                    "source": s.source,
                    "signal_type": s.signal_type,
                    "target_type": s.target_type.value,
                    "strength": s.strength,
                    "timestamp": s.timestamp.isoformat(),
                }
                for s in self.signals
            ],
            "type_affinities": {
                k.value: v for k, v in self.type_affinities.items()
            },
            "commitment_level": self.commitment_level,
            "potency": self.get_potency().value,
            "leading_types": [
                {"type": t.value, "affinity": v}
                for t, v in self.leading_types
            ],
        }


# =============================================================================
# VIRTUE -> TYPE ASSOCIATIONS
# =============================================================================

# Which virtues push toward which entity types?
# This is the "morphogen gradient" mapping

VIRTUE_TYPE_ASSOCIATIONS: dict[str, dict[EntityType, float]] = {
    # V01: Trustworthiness - foundation, no specific type
    "V01": {},

    # V02: Wisdom
    "V02": {
        EntityType.ANCESTOR: 0.7,
        EntityType.TRADITION: 0.6,
        EntityType.CONCEPT: 0.5,
    },

    # V03: Compassion
    "V03": {
        EntityType.ECOSYSTEM: 0.6,
        EntityType.SPECIES: 0.7,
        EntityType.FUTURE_GENERATION: 0.6,
        EntityType.NETWORK: 0.5,
    },

    # V04: Justice
    "V04": {
        EntityType.MOVEMENT: 0.8,
        EntityType.COMMONS: 0.6,
        EntityType.LAND: 0.5,
        EntityType.DIASPORA: 0.5,
    },

    # V05: Courage
    "V05": {
        EntityType.MOVEMENT: 0.7,
        EntityType.FUTURE_SELF: 0.5,
    },

    # V06: Temperance
    "V06": {
        EntityType.ECOSYSTEM: 0.5,
        EntityType.COMMONS: 0.6,
    },

    # V07: Humility
    "V07": {
        EntityType.ANCESTOR: 0.5,
        EntityType.TRADITION: 0.5,
        EntityType.ECOSYSTEM: 0.4,
    },

    # V08: Generosity
    "V08": {
        EntityType.COMMONS: 0.7,
        EntityType.COOPERATIVE: 0.6,
        EntityType.NETWORK: 0.5,
    },

    # V09: Patience
    "V09": {
        EntityType.FUTURE_GENERATION: 0.7,
        EntityType.ECOSYSTEM: 0.5,
        EntityType.ERA: 0.4,
    },

    # V10: Gratitude
    "V10": {
        EntityType.ANCESTOR: 0.6,
        EntityType.LAND: 0.5,
        EntityType.TRADITION: 0.4,
    },

    # V11: Integrity
    "V11": {
        EntityType.CODEBASE: 0.5,
        EntityType.COOPERATIVE: 0.4,
    },

    # V12: Diligence
    "V12": {
        EntityType.PROJECT: 0.6,
        EntityType.CODEBASE: 0.5,
    },

    # V13: Kindness
    "V13": {
        EntityType.NEIGHBORHOOD: 0.6,
        EntityType.NETWORK: 0.5,
        EntityType.PET: 0.4,
    },

    # V14: Respect
    "V14": {
        EntityType.ANCESTOR: 0.6,
        EntityType.LAND: 0.7,
        EntityType.TRADITION: 0.6,
        EntityType.SPECIES: 0.5,
    },

    # V15: Forgiveness
    "V15": {
        EntityType.MEMORY: 0.5,
        EntityType.DIASPORA: 0.4,
    },

    # V16: Hope
    "V16": {
        EntityType.FUTURE_SELF: 0.7,
        EntityType.FUTURE_GENERATION: 0.8,
        EntityType.MOVEMENT: 0.5,
    },

    # V17: Love
    "V17": {
        EntityType.DECEASED: 0.5,
        EntityType.ANCESTOR: 0.4,
        EntityType.NEIGHBORHOOD: 0.4,
    },

    # V18: Faith
    "V18": {
        EntityType.TRADITION: 0.6,
        EntityType.ANCESTOR: 0.5,
        EntityType.MOVEMENT: 0.4,
    },

    # V19: Prudence
    "V19": {
        EntityType.FUTURE_GENERATION: 0.6,
        EntityType.COMMONS: 0.5,
        EntityType.ECOSYSTEM: 0.5,
    },
}


# =============================================================================
# NICHE DYNAMICS - How community shapes differentiation
# =============================================================================


@dataclass
class CommunityNiche:
    """
    The differentiation environment of a community.

    Like biological niches, communities shape what seeds can become.
    They provide signals, create vacuums, and inhibit redundancy.
    """

    community_id: str

    # What types are present and how many
    type_census: dict[EntityType, int] = field(default_factory=dict)

    # What the community explicitly needs
    declared_needs: list[EntityType] = field(default_factory=list)

    # Virtue emphasis (the "chemical gradient")
    virtue_gradient: dict[str, float] = field(default_factory=dict)

    # How much does this niche push differentiation vs allow exploration?
    # 0 = very permissive, 1 = strong pressure to differentiate
    differentiation_pressure: float = 0.3

    # Lateral inhibition strength
    # How much do present types inhibit seeds from becoming the same?
    lateral_inhibition: float = 0.5

    def get_pull_toward(self, entity_type: EntityType) -> float:
        """
        Calculate how much this niche pulls toward a type.

        Positive = attraction (empty niche)
        Negative = inhibition (filled niche)
        """
        # Inhibition from present types
        inhibition = 0.0
        if entity_type in self.type_census:
            count = self.type_census[entity_type]
            inhibition = min(count * 0.2 * self.lateral_inhibition, 0.8)

        # Attraction from declared needs
        attraction = 0.0
        if entity_type in self.declared_needs:
            attraction = 0.5

        # Attraction from empty category
        categories = get_category_for_type(entity_type)
        for cat in categories:
            cat_types = ENTITY_CATEGORIES.get(cat, [])
            cat_present = sum(
                self.type_census.get(t, 0) for t in cat_types
            )
            if cat_present == 0:
                attraction += 0.2  # Empty category pulls

        # Virtue gradient influence
        for virtue_id, gradient_strength in self.virtue_gradient.items():
            associations = VIRTUE_TYPE_ASSOCIATIONS.get(virtue_id, {})
            if entity_type in associations:
                attraction += gradient_strength * associations[entity_type] * 0.3

        return (attraction - inhibition) * self.differentiation_pressure

    def get_all_pulls(self) -> dict[EntityType, float]:
        """Get pull values for all entity types."""
        pulls = {}
        for entity_type in EntityType:
            if entity_type not in (EntityType.SEED, EntityType.CURIOUS, EntityType.EMERGENT):
                pulls[entity_type] = self.get_pull_toward(entity_type)
        return pulls

    def get_vacuum_types(self) -> list[EntityType]:
        """Get types that the niche is pulling toward (empty niches)."""
        pulls = self.get_all_pulls()
        return [t for t, pull in pulls.items() if pull > 0.2]

    def get_saturated_types(self) -> list[EntityType]:
        """Get types that are inhibited (filled niches)."""
        pulls = self.get_all_pulls()
        return [t for t, pull in pulls.items() if pull < -0.2]

    def update_census(self, type_counts: dict[EntityType, int]) -> None:
        """Update the type census."""
        self.type_census = type_counts

    def to_dict(self) -> dict:
        return {
            "community_id": self.community_id,
            "type_census": {k.value: v for k, v in self.type_census.items()},
            "declared_needs": [t.value for t in self.declared_needs],
            "virtue_gradient": self.virtue_gradient,
            "differentiation_pressure": self.differentiation_pressure,
            "lateral_inhibition": self.lateral_inhibition,
            "vacuum_types": [t.value for t in self.get_vacuum_types()],
            "saturated_types": [t.value for t in self.get_saturated_types()],
        }


# =============================================================================
# QUORUM SENSING - Collective emergence
# =============================================================================


@dataclass
class QuorumState:
    """
    Tracks collective patterns and thresholds in a community.

    When enough members hold a pattern, it becomes community-level
    knowledge or behavior - like bacteria coordinating via quorum sensing.
    """

    community_id: str

    # Pattern -> list of member IDs holding it
    pattern_holders: dict[str, set[str]] = field(default_factory=dict)

    # Minimum holders for pattern to reach quorum
    quorum_threshold: int = 3

    # Patterns that have reached quorum (with timestamp)
    quorum_reached: dict[str, datetime] = field(default_factory=dict)

    def add_pattern_holder(self, pattern: str, member_id: str) -> bool:
        """
        Record that a member holds a pattern.

        Returns True if this causes the pattern to reach quorum.
        """
        if pattern not in self.pattern_holders:
            self.pattern_holders[pattern] = set()

        self.pattern_holders[pattern].add(member_id)

        # Check if just reached quorum
        if (
            len(self.pattern_holders[pattern]) >= self.quorum_threshold
            and pattern not in self.quorum_reached
        ):
            self.quorum_reached[pattern] = datetime.utcnow()
            logger.info(f"Pattern '{pattern}' reached quorum in community {self.community_id}")
            return True

        return False

    def remove_pattern_holder(self, pattern: str, member_id: str) -> bool:
        """
        Remove a member from holding a pattern.

        Returns True if this causes loss of quorum.
        """
        if pattern in self.pattern_holders:
            self.pattern_holders[pattern].discard(member_id)

            # Check if lost quorum
            if (
                len(self.pattern_holders[pattern]) < self.quorum_threshold
                and pattern in self.quorum_reached
            ):
                del self.quorum_reached[pattern]
                return True

        return False

    @property
    def community_patterns(self) -> list[str]:
        """Patterns that have reached quorum."""
        return list(self.quorum_reached.keys())

    @property
    def emerging_patterns(self) -> list[tuple[str, int, int]]:
        """Patterns approaching quorum: (pattern, current, threshold)."""
        emerging = []
        for pattern, holders in self.pattern_holders.items():
            if pattern not in self.quorum_reached:
                if len(holders) >= self.quorum_threshold - 1:
                    emerging.append((pattern, len(holders), self.quorum_threshold))
        return emerging

    def to_dict(self) -> dict:
        return {
            "community_id": self.community_id,
            "pattern_holders": {k: list(v) for k, v in self.pattern_holders.items()},
            "quorum_threshold": self.quorum_threshold,
            "quorum_reached": {k: v.isoformat() for k, v in self.quorum_reached.items()},
            "community_patterns": self.community_patterns,
            "emerging_patterns": [
                {"pattern": p, "current": c, "threshold": t}
                for p, c, t in self.emerging_patterns
            ],
        }


# =============================================================================
# METAMORPHOSIS - Transformation, not gradual change
# =============================================================================


class MetamorphosisPhase(str, Enum):
    """Phases of metamorphic transformation."""

    PRE_CHRYSALIS = "pre_chrysalis"    # Still active, approaching transformation
    DISSOLUTION = "dissolution"        # Breaking down old form
    REFORMATION = "reformation"        # Building new form
    EMERGENCE = "emergence"            # New form emerging
    POST_EMERGENCE = "post_emergence"  # Stabilizing new identity


@dataclass
class ChrysalisState:
    """
    State of a seed undergoing metamorphosis.

    The chrysalis phase is NOT gradual refinement.
    It's dissolution and reformation - the old form must
    break down for the new form to emerge.
    """

    entity_id: str
    phase: MetamorphosisPhase = MetamorphosisPhase.PRE_CHRYSALIS

    # What's being preserved through transformation
    preserved_patterns: list[str] = field(default_factory=list)
    preserved_questions: list[str] = field(default_factory=list)
    preserved_relationships: list[str] = field(default_factory=list)

    # What's being dissolved
    dissolving_traits: list[str] = field(default_factory=list)

    # What's emerging
    emerging_type: EntityType | None = None
    emerging_traits: list[str] = field(default_factory=list)

    # Timeline
    entered_chrysalis: datetime | None = None
    phase_started: datetime = field(default_factory=datetime.utcnow)
    estimated_emergence: datetime | None = None

    def enter_chrysalis(self, target_type: EntityType) -> None:
        """Begin metamorphosis toward a target type."""
        self.phase = MetamorphosisPhase.DISSOLUTION
        self.entered_chrysalis = datetime.utcnow()
        self.phase_started = datetime.utcnow()
        self.emerging_type = target_type

        logger.info(f"Entity {self.entity_id} entering chrysalis toward {target_type.value}")

    def advance_phase(self) -> MetamorphosisPhase:
        """Advance to next phase of metamorphosis."""
        phase_order = [
            MetamorphosisPhase.PRE_CHRYSALIS,
            MetamorphosisPhase.DISSOLUTION,
            MetamorphosisPhase.REFORMATION,
            MetamorphosisPhase.EMERGENCE,
            MetamorphosisPhase.POST_EMERGENCE,
        ]

        current_idx = phase_order.index(self.phase)
        if current_idx < len(phase_order) - 1:
            self.phase = phase_order[current_idx + 1]
            self.phase_started = datetime.utcnow()

        return self.phase

    @property
    def is_complete(self) -> bool:
        return self.phase == MetamorphosisPhase.POST_EMERGENCE

    @property
    def is_active(self) -> bool:
        return self.phase in (
            MetamorphosisPhase.DISSOLUTION,
            MetamorphosisPhase.REFORMATION,
            MetamorphosisPhase.EMERGENCE,
        )

    def to_dict(self) -> dict:
        return {
            "entity_id": self.entity_id,
            "phase": self.phase.value,
            "preserved_patterns": self.preserved_patterns,
            "preserved_questions": self.preserved_questions,
            "preserved_relationships": self.preserved_relationships,
            "dissolving_traits": self.dissolving_traits,
            "emerging_type": self.emerging_type.value if self.emerging_type else None,
            "emerging_traits": self.emerging_traits,
            "entered_chrysalis": self.entered_chrysalis.isoformat() if self.entered_chrysalis else None,
            "phase_started": self.phase_started.isoformat(),
            "is_complete": self.is_complete,
            "is_active": self.is_active,
        }


# =============================================================================
# SYMBIOGENESIS - Fusion of entities
# =============================================================================


@dataclass
class FusionProposal:
    """
    Proposal to merge multiple seeds/entities into one.

    Like symbiogenesis in evolution - mitochondria becoming part
    of eukaryotic cells, or lichens forming from fungi + algae.
    """

    proposal_id: str

    # Entities to merge
    source_entity_ids: list[str]

    # What the merged entity would become
    target_type: EntityType
    target_name: str

    # What each source contributes
    contributions: dict[str, list[str]] = field(default_factory=dict)

    # Status
    proposed_at: datetime = field(default_factory=datetime.utcnow)
    approved_by: list[str] = field(default_factory=list)  # Entity IDs that approved

    @property
    def approval_ratio(self) -> float:
        """What fraction of sources have approved?"""
        if not self.source_entity_ids:
            return 0.0
        return len(self.approved_by) / len(self.source_entity_ids)

    @property
    def is_approved(self) -> bool:
        """All sources must approve."""
        return set(self.approved_by) >= set(self.source_entity_ids)

    def to_dict(self) -> dict:
        return {
            "proposal_id": self.proposal_id,
            "source_entity_ids": self.source_entity_ids,
            "target_type": self.target_type.value,
            "target_name": self.target_name,
            "contributions": self.contributions,
            "proposed_at": self.proposed_at.isoformat(),
            "approved_by": self.approved_by,
            "approval_ratio": self.approval_ratio,
            "is_approved": self.is_approved,
        }


# =============================================================================
# INTEGRATED DEVELOPMENTAL STATE
# =============================================================================


@dataclass
class DevelopmentalState:
    """
    Complete developmental state of a seed entity.

    Integrates all the biological principles:
    - Potency and differentiation pressure
    - Life stage
    - Niche context
    - Quorum participation
    - Metamorphosis state (if applicable)
    """

    entity_id: str

    # Current life stage
    life_stage: LifeStage = LifeStage.DORMANT

    # Differentiation pressure from all sources
    differentiation: DifferentiationPressure = field(
        default_factory=DifferentiationPressure
    )

    # Metamorphosis state (None if not in chrysalis)
    chrysalis: ChrysalisState | None = None

    # Patterns this entity holds (for quorum sensing)
    held_patterns: set[str] = field(default_factory=set)

    # Fusion proposals involving this entity
    fusion_proposals: list[str] = field(default_factory=list)

    # Lifecycle timestamps
    created_at: datetime = field(default_factory=datetime.utcnow)
    germinated_at: datetime | None = None
    crystallized_at: datetime | None = None

    @property
    def potency(self) -> Potency:
        """Current developmental potency."""
        if self.chrysalis and self.chrysalis.is_complete:
            return Potency.DIFFERENTIATED
        return self.differentiation.get_potency()

    @property
    def is_in_chrysalis(self) -> bool:
        return self.chrysalis is not None and self.chrysalis.is_active

    def germinate(self) -> None:
        """Transition from dormant to germinating."""
        if self.life_stage == LifeStage.DORMANT:
            self.life_stage = LifeStage.GERMINATING
            self.germinated_at = datetime.utcnow()

    def advance_stage(self) -> LifeStage:
        """Advance to next life stage based on conditions."""
        stage_transitions = {
            LifeStage.DORMANT: LifeStage.GERMINATING,
            LifeStage.GERMINATING: LifeStage.GROWING,
            LifeStage.GROWING: LifeStage.BRANCHING,
            LifeStage.BRANCHING: LifeStage.FLOWERING,
            LifeStage.FLOWERING: LifeStage.CHRYSALIS,
            LifeStage.CHRYSALIS: LifeStage.CRYSTALLIZED,
            LifeStage.CRYSTALLIZED: LifeStage.FRUITING,
            LifeStage.FRUITING: LifeStage.SEEDING,
            LifeStage.SEEDING: LifeStage.SENESCENT,
            LifeStage.SENESCENT: LifeStage.COMPOSTING,
        }

        if self.life_stage in stage_transitions:
            self.life_stage = stage_transitions[self.life_stage]

        return self.life_stage

    def begin_metamorphosis(self, target_type: EntityType) -> None:
        """Enter chrysalis phase."""
        self.chrysalis = ChrysalisState(entity_id=self.entity_id)
        self.chrysalis.enter_chrysalis(target_type)
        self.life_stage = LifeStage.CHRYSALIS

    def complete_metamorphosis(self) -> EntityType | None:
        """Complete metamorphosis and return the emerged type."""
        if self.chrysalis and self.chrysalis.is_active:
            self.chrysalis.advance_phase()
            if self.chrysalis.is_complete:
                self.life_stage = LifeStage.CRYSTALLIZED
                self.crystallized_at = datetime.utcnow()
                return self.chrysalis.emerging_type
        return None

    def to_dict(self) -> dict:
        return {
            "entity_id": self.entity_id,
            "life_stage": self.life_stage.value,
            "potency": self.potency.value,
            "differentiation": self.differentiation.to_dict(),
            "chrysalis": self.chrysalis.to_dict() if self.chrysalis else None,
            "held_patterns": list(self.held_patterns),
            "fusion_proposals": self.fusion_proposals,
            "created_at": self.created_at.isoformat(),
            "germinated_at": self.germinated_at.isoformat() if self.germinated_at else None,
            "crystallized_at": self.crystallized_at.isoformat() if self.crystallized_at else None,
        }
