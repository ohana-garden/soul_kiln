"""
Developmental Manager.

High-level API for managing seed development through biological principles.

This manager coordinates:
- Potency tracking and differentiation
- Life stage transitions
- Niche dynamics and community context
- Quorum sensing for collective emergence
- Metamorphosis and crystallization
- Symbiogenesis (entity fusion)

Usage:
    from src.core.development import get_dev_manager

    dev = get_dev_manager()

    # Process a conversation's effect on a seed
    dev.process_conversation(entity_id, topics=["ecology", "stewardship"])

    # Check if seed is ready to crystallize
    state = dev.get_state(entity_id)
    if state.potency == Potency.UNIPOTENT:
        dev.begin_crystallization(entity_id)

    # Get community niche dynamics
    niche = dev.get_niche(community_id)
    print(niche.get_vacuum_types())  # What types are needed?
"""

import logging
import uuid
from datetime import datetime
from typing import Any

from .entity import Entity, EntityType
from .proxy import Proxy
from .community import Community
from .graph_store import get_core_store
from .biomimicry import (
    Potency,
    LifeStage,
    DifferentiationSignal,
    DifferentiationPressure,
    CommunityNiche,
    QuorumState,
    ChrysalisState,
    MetamorphosisPhase,
    FusionProposal,
    DevelopmentalState,
    VIRTUE_TYPE_ASSOCIATIONS,
    ENTITY_CATEGORIES,
)

logger = logging.getLogger(__name__)


# Topic -> EntityType associations for conversation signals
TOPIC_TYPE_ASSOCIATIONS: dict[str, dict[EntityType, float]] = {
    # Ecology and nature
    "ecology": {EntityType.ECOSYSTEM: 0.8, EntityType.SPECIES: 0.6, EntityType.LAND: 0.5},
    "environment": {EntityType.ECOSYSTEM: 0.7, EntityType.LAND: 0.5, EntityType.FUTURE_GENERATION: 0.4},
    "nature": {EntityType.ECOSYSTEM: 0.6, EntityType.SPECIES: 0.5, EntityType.PLACE: 0.4},
    "water": {EntityType.ECOSYSTEM: 0.7, EntityType.COMMONS: 0.4},
    "forest": {EntityType.ECOSYSTEM: 0.8, EntityType.LAND: 0.5},
    "river": {EntityType.ECOSYSTEM: 0.8, EntityType.COMMONS: 0.4},
    "ocean": {EntityType.ECOSYSTEM: 0.7, EntityType.COMMONS: 0.5},
    "wildlife": {EntityType.SPECIES: 0.8, EntityType.ECOSYSTEM: 0.5},
    "biodiversity": {EntityType.SPECIES: 0.7, EntityType.ECOSYSTEM: 0.7},

    # Social and collective
    "community": {EntityType.NEIGHBORHOOD: 0.7, EntityType.NETWORK: 0.5},
    "neighborhood": {EntityType.NEIGHBORHOOD: 0.9, EntityType.PLACE: 0.4},
    "solidarity": {EntityType.MOVEMENT: 0.7, EntityType.NETWORK: 0.5},
    "mutual aid": {EntityType.NETWORK: 0.8, EntityType.COOPERATIVE: 0.6},
    "cooperation": {EntityType.COOPERATIVE: 0.8, EntityType.NETWORK: 0.5},
    "collective": {EntityType.COOPERATIVE: 0.6, EntityType.MOVEMENT: 0.5, EntityType.COMMONS: 0.5},

    # Justice and change
    "justice": {EntityType.MOVEMENT: 0.8, EntityType.VALUE: 0.5},
    "rights": {EntityType.MOVEMENT: 0.7, EntityType.VALUE: 0.4},
    "equity": {EntityType.MOVEMENT: 0.6, EntityType.COMMONS: 0.4},
    "change": {EntityType.MOVEMENT: 0.6, EntityType.FUTURE_SELF: 0.4},
    "activism": {EntityType.MOVEMENT: 0.8},
    "advocacy": {EntityType.MOVEMENT: 0.7, EntityType.SPECIES: 0.4},

    # Temporal
    "future": {EntityType.FUTURE_GENERATION: 0.8, EntityType.FUTURE_SELF: 0.6},
    "children": {EntityType.FUTURE_GENERATION: 0.7},
    "legacy": {EntityType.FUTURE_GENERATION: 0.6, EntityType.ANCESTOR: 0.5},
    "ancestors": {EntityType.ANCESTOR: 0.9, EntityType.TRADITION: 0.6},
    "tradition": {EntityType.TRADITION: 0.9, EntityType.ANCESTOR: 0.5},
    "history": {EntityType.ERA: 0.6, EntityType.MEMORY: 0.5, EntityType.ANCESTOR: 0.4},
    "memory": {EntityType.MEMORY: 0.8, EntityType.ANCESTOR: 0.3},

    # Land and place
    "land": {EntityType.LAND: 0.9, EntityType.PLACE: 0.5},
    "territory": {EntityType.LAND: 0.8},
    "indigenous": {EntityType.LAND: 0.7, EntityType.TRADITION: 0.6, EntityType.ANCESTOR: 0.5},
    "place": {EntityType.PLACE: 0.8, EntityType.NEIGHBORHOOD: 0.4},
    "home": {EntityType.PLACE: 0.7, EntityType.NEIGHBORHOOD: 0.5},

    # Sharing and commons
    "sharing": {EntityType.COMMONS: 0.7, EntityType.COOPERATIVE: 0.5},
    "commons": {EntityType.COMMONS: 0.9},
    "stewardship": {EntityType.COMMONS: 0.7, EntityType.ECOSYSTEM: 0.5, EntityType.LAND: 0.4},
    "care": {EntityType.NETWORK: 0.5, EntityType.SPECIES: 0.4},

    # Diaspora and migration
    "diaspora": {EntityType.DIASPORA: 0.9},
    "migration": {EntityType.DIASPORA: 0.7, EntityType.MOVEMENT: 0.3},
    "exile": {EntityType.DIASPORA: 0.6, EntityType.MEMORY: 0.4},
    "belonging": {EntityType.DIASPORA: 0.5, EntityType.NEIGHBORHOOD: 0.5},

    # Technology and creation
    "code": {EntityType.CODEBASE: 0.8, EntityType.PROJECT: 0.5},
    "software": {EntityType.CODEBASE: 0.9},
    "open source": {EntityType.CODEBASE: 0.8, EntityType.COMMONS: 0.5},
    "project": {EntityType.PROJECT: 0.8, EntityType.TEAM: 0.4},
    "artifact": {EntityType.ARTIFACT: 0.8, EntityType.MEMORY: 0.4},
}


class DevelopmentalManager:
    """
    Manages the developmental processes of seed entities.

    Coordinates all biological principles to guide seeds
    from undifferentiated potential to crystallized identity.
    """

    def __init__(self, store=None):
        """
        Initialize the developmental manager.

        Args:
            store: Graph store (defaults to singleton)
        """
        self.store = store or get_core_store()

        # In-memory caches (would be persisted in production)
        self._states: dict[str, DevelopmentalState] = {}
        self._niches: dict[str, CommunityNiche] = {}
        self._quorums: dict[str, QuorumState] = {}
        self._fusion_proposals: dict[str, FusionProposal] = {}

    # =========================================================================
    # State Management
    # =========================================================================

    def get_state(self, entity_id: str) -> DevelopmentalState | None:
        """Get or create developmental state for an entity."""
        if entity_id not in self._states:
            # Check if entity exists and is a seed
            entity = self.store.get_entity(entity_id)
            if not entity:
                return None
            if entity.type not in (EntityType.SEED, EntityType.CURIOUS, EntityType.EMERGENT):
                # Non-seed entities don't have developmental state
                return None

            # Create new state
            self._states[entity_id] = DevelopmentalState(entity_id=entity_id)

        return self._states[entity_id]

    def save_state(self, entity_id: str) -> None:
        """Persist developmental state to entity attributes."""
        state = self._states.get(entity_id)
        if not state:
            return

        entity = self.store.get_entity(entity_id)
        if entity:
            entity.attributes["developmental_state"] = state.to_dict()
            self.store.save_entity(entity)

    # =========================================================================
    # Signal Processing
    # =========================================================================

    def process_virtue_activation(
        self,
        entity_id: str,
        virtue_id: str,
        activation: float,
    ) -> None:
        """
        Process a virtue activation's effect on differentiation.

        Args:
            entity_id: The seed entity
            virtue_id: Which virtue was activated (e.g., "V03")
            activation: Activation strength (0-1)
        """
        state = self.get_state(entity_id)
        if not state:
            return

        associations = VIRTUE_TYPE_ASSOCIATIONS.get(virtue_id, {})
        state.differentiation.add_virtue_signal(
            virtue_id=virtue_id,
            activation=activation,
            type_associations=associations,
        )

        self._check_stage_transition(entity_id)

    def process_conversation(
        self,
        entity_id: str,
        topics: list[str],
        partner_types: list[EntityType] | None = None,
    ) -> dict:
        """
        Process a conversation's effect on differentiation.

        Args:
            entity_id: The seed entity
            topics: Topics discussed in the conversation
            partner_types: Types of entities conversed with (for lateral effects)

        Returns:
            Summary of differentiation effects
        """
        state = self.get_state(entity_id)
        if not state:
            return {"error": "Entity not found or not a seed"}

        # Germinate if dormant
        if state.life_stage == LifeStage.DORMANT:
            state.germinate()

        effects = {
            "signals_added": 0,
            "topics_processed": [],
            "lateral_effects": [],
        }

        # Process topic signals
        for topic in topics:
            topic_lower = topic.lower()
            if topic_lower in TOPIC_TYPE_ASSOCIATIONS:
                associations = TOPIC_TYPE_ASSOCIATIONS[topic_lower]
                state.differentiation.add_conversation_signal(
                    topic=topic,
                    type_associations=associations,
                )
                effects["signals_added"] += len(associations)
                effects["topics_processed"].append(topic)

        # Process lateral effects from conversation partners
        if partner_types:
            for partner_type in partner_types:
                # Slight inhibition from same-type neighbors
                state.differentiation.add_neighbor_signal(
                    neighbor_type=partner_type,
                    effect="inhibit",
                    strength=0.1,
                )
                effects["lateral_effects"].append(f"inhibit:{partner_type.value}")

        # Check for stage transitions
        self._check_stage_transition(entity_id)

        effects["new_potency"] = state.potency.value
        effects["life_stage"] = state.life_stage.value
        effects["leading_types"] = [
            {"type": t.value, "affinity": a}
            for t, a in state.differentiation.leading_types
        ]

        return effects

    def apply_niche_pressure(self, entity_id: str, community_id: str) -> dict:
        """
        Apply community niche pressure to a seed.

        The community's composition and needs influence differentiation.

        Args:
            entity_id: The seed entity
            community_id: The community context

        Returns:
            Summary of niche effects
        """
        state = self.get_state(entity_id)
        if not state:
            return {"error": "Entity not found or not a seed"}

        niche = self.get_niche(community_id)

        effects = {
            "vacuum_pulls": [],
            "saturation_pushes": [],
            "signals_added": 0,
        }

        # Apply pull/push for each type
        all_pulls = niche.get_all_pulls()
        for entity_type, pull in all_pulls.items():
            if abs(pull) > 0.1:
                signal = DifferentiationSignal(
                    source=f"niche:{community_id}",
                    signal_type="niche",
                    target_type=entity_type,
                    strength=pull,
                )
                state.differentiation.add_signal(signal)
                effects["signals_added"] += 1

                if pull > 0:
                    effects["vacuum_pulls"].append(entity_type.value)
                else:
                    effects["saturation_pushes"].append(entity_type.value)

        self._check_stage_transition(entity_id)

        return effects

    # =========================================================================
    # Niche Management
    # =========================================================================

    def get_niche(self, community_id: str) -> CommunityNiche:
        """Get or create niche state for a community."""
        if community_id not in self._niches:
            self._niches[community_id] = CommunityNiche(community_id=community_id)
            self._update_niche_census(community_id)

        return self._niches[community_id]

    def _update_niche_census(self, community_id: str) -> None:
        """Update the type census for a community niche."""
        niche = self._niches.get(community_id)
        if not niche:
            return

        # Get all proxies in community
        proxies = self.store.get_proxies_in_community(community_id)

        # Count entity types
        type_counts: dict[EntityType, int] = {}
        for proxy in proxies:
            entity = self.store.get_entity(proxy.entity_id)
            if entity and entity.type not in (EntityType.SEED, EntityType.CURIOUS, EntityType.EMERGENT):
                if entity.type not in type_counts:
                    type_counts[entity.type] = 0
                type_counts[entity.type] += 1

        niche.update_census(type_counts)

    def set_community_virtue_gradient(
        self,
        community_id: str,
        virtue_emphasis: dict[str, float],
    ) -> None:
        """
        Set the virtue gradient (morphogen field) for a community.

        Args:
            community_id: The community
            virtue_emphasis: Virtue ID -> emphasis strength mapping
        """
        niche = self.get_niche(community_id)
        niche.virtue_gradient = virtue_emphasis

    def declare_community_need(
        self,
        community_id: str,
        needed_types: list[EntityType],
    ) -> None:
        """
        Declare what types a community needs.

        Creates attraction toward these types.
        """
        niche = self.get_niche(community_id)
        niche.declared_needs = needed_types

    # =========================================================================
    # Quorum Sensing
    # =========================================================================

    def get_quorum(self, community_id: str) -> QuorumState:
        """Get or create quorum state for a community."""
        if community_id not in self._quorums:
            self._quorums[community_id] = QuorumState(community_id=community_id)
        return self._quorums[community_id]

    def add_pattern_holder(
        self,
        community_id: str,
        pattern: str,
        member_id: str,
    ) -> bool:
        """
        Record that a member holds a pattern.

        Returns True if this causes quorum to be reached.
        """
        quorum = self.get_quorum(community_id)
        reached = quorum.add_pattern_holder(pattern, member_id)

        # Also track in member's state
        state = self.get_state(member_id)
        if state:
            state.held_patterns.add(pattern)

        return reached

    def get_community_patterns(self, community_id: str) -> list[str]:
        """Get patterns that have reached quorum in a community."""
        quorum = self.get_quorum(community_id)
        return quorum.community_patterns

    # =========================================================================
    # Life Stage Transitions
    # =========================================================================

    def _check_stage_transition(self, entity_id: str) -> LifeStage | None:
        """Check if entity should transition to a new life stage."""
        state = self.get_state(entity_id)
        if not state:
            return None

        old_stage = state.life_stage
        potency = state.potency
        commitment = state.differentiation.commitment_level

        # Stage transition logic
        if state.life_stage == LifeStage.GERMINATING:
            # Move to growing after some interaction
            if len(state.differentiation.signals) >= 3:
                state.life_stage = LifeStage.GROWING

        elif state.life_stage == LifeStage.GROWING:
            # Move to branching when multiple paths become viable
            leading = state.differentiation.leading_types
            if len(leading) >= 2 and all(a > 0.3 for _, a in leading[:2]):
                state.life_stage = LifeStage.BRANCHING

        elif state.life_stage == LifeStage.BRANCHING:
            # Move to flowering when one path dominates
            if commitment > 0.5:
                state.life_stage = LifeStage.FLOWERING

        elif state.life_stage == LifeStage.FLOWERING:
            # Ready for chrysalis when highly committed
            if commitment > 0.7 and potency in (Potency.UNIPOTENT, Potency.OLIGOPOTENT):
                # Don't auto-transition to chrysalis - that's a deliberate choice
                pass

        if old_stage != state.life_stage:
            logger.info(f"Entity {entity_id} transitioned from {old_stage.value} to {state.life_stage.value}")

        return state.life_stage

    # =========================================================================
    # Metamorphosis
    # =========================================================================

    def begin_crystallization(
        self,
        entity_id: str,
        target_type: EntityType | None = None,
    ) -> ChrysalisState | None:
        """
        Begin the metamorphosis process for a seed.

        Args:
            entity_id: The seed to crystallize
            target_type: Target type (defaults to highest affinity)

        Returns:
            Chrysalis state or None if not ready
        """
        state = self.get_state(entity_id)
        if not state:
            return None

        # Determine target type
        if target_type is None:
            leading = state.differentiation.leading_types
            if not leading:
                logger.warning(f"Entity {entity_id} has no leading types for crystallization")
                return None
            target_type = leading[0][0]

        # Check readiness
        if state.potency not in (Potency.UNIPOTENT, Potency.OLIGOPOTENT):
            logger.warning(f"Entity {entity_id} not ready for crystallization (potency: {state.potency.value})")
            return None

        # Begin metamorphosis
        state.begin_metamorphosis(target_type)

        # Determine what to preserve
        entity = self.store.get_entity(entity_id)
        if entity:
            seed_state = entity.attributes.get("seed_state", {})
            state.chrysalis.preserved_questions = seed_state.get("active_questions", [])[:3]
            state.chrysalis.preserved_patterns = list(state.held_patterns)[:5]

        logger.info(f"Entity {entity_id} beginning crystallization toward {target_type.value}")

        return state.chrysalis

    def advance_metamorphosis(self, entity_id: str) -> MetamorphosisPhase | None:
        """Advance the metamorphosis process."""
        state = self.get_state(entity_id)
        if not state or not state.chrysalis:
            return None

        old_phase = state.chrysalis.phase
        new_phase = state.chrysalis.advance_phase()

        if old_phase != new_phase:
            logger.info(f"Entity {entity_id} metamorphosis: {old_phase.value} -> {new_phase.value}")

        # If complete, update the entity
        if state.chrysalis.is_complete:
            self._complete_crystallization(entity_id)

        return new_phase

    def _complete_crystallization(self, entity_id: str) -> Entity | None:
        """Complete the crystallization and update entity type."""
        state = self.get_state(entity_id)
        if not state or not state.chrysalis:
            return None

        target_type = state.chrysalis.emerging_type
        if not target_type:
            return None

        entity = self.store.get_entity(entity_id)
        if not entity:
            return None

        # Transform the entity
        old_type = entity.type
        entity.type = target_type

        # Preserve chrysalis history
        entity.attributes["chrysalis_history"] = state.chrysalis.to_dict()
        entity.attributes["pre_crystallization_type"] = old_type.value

        # Add fact about transformation
        entity.add_fact(f"Crystallized from {old_type.value} to {target_type.value}")
        entity.add_fact(f"Preserved questions: {state.chrysalis.preserved_questions}")

        self.store.save_entity(entity)

        # Update state
        state.life_stage = LifeStage.CRYSTALLIZED
        state.crystallized_at = datetime.utcnow()

        logger.info(f"Entity {entity_id} crystallized: {old_type.value} -> {target_type.value}")

        return entity

    # =========================================================================
    # Symbiogenesis (Fusion)
    # =========================================================================

    def propose_fusion(
        self,
        source_entity_ids: list[str],
        target_type: EntityType,
        target_name: str,
    ) -> FusionProposal | None:
        """
        Propose merging multiple entities into one.

        All source entities must approve for fusion to proceed.

        Args:
            source_entity_ids: Entities to merge
            target_type: What the merged entity becomes
            target_name: Name of the merged entity

        Returns:
            Fusion proposal or None if invalid
        """
        # Validate all sources exist
        for eid in source_entity_ids:
            entity = self.store.get_entity(eid)
            if not entity:
                logger.warning(f"Cannot fuse: entity {eid} not found")
                return None

        proposal = FusionProposal(
            proposal_id=f"fusion_{uuid.uuid4().hex[:12]}",
            source_entity_ids=source_entity_ids,
            target_type=target_type,
            target_name=target_name,
        )

        self._fusion_proposals[proposal.proposal_id] = proposal

        # Track in each entity's state
        for eid in source_entity_ids:
            state = self.get_state(eid)
            if state:
                state.fusion_proposals.append(proposal.proposal_id)

        logger.info(f"Fusion proposed: {source_entity_ids} -> {target_name} ({target_type.value})")

        return proposal

    def approve_fusion(self, proposal_id: str, entity_id: str) -> bool:
        """
        Approve a fusion proposal from one entity's perspective.

        Returns True if this completes the approval (all approved).
        """
        proposal = self._fusion_proposals.get(proposal_id)
        if not proposal:
            return False

        if entity_id not in proposal.source_entity_ids:
            return False

        if entity_id not in proposal.approved_by:
            proposal.approved_by.append(entity_id)

        return proposal.is_approved

    def execute_fusion(self, proposal_id: str) -> Entity | None:
        """
        Execute an approved fusion, creating the merged entity.

        Returns the new merged entity or None if not ready.
        """
        proposal = self._fusion_proposals.get(proposal_id)
        if not proposal or not proposal.is_approved:
            return None

        # Gather attributes from all sources
        combined_facts = []
        combined_attributes = {}

        for eid in proposal.source_entity_ids:
            entity = self.store.get_entity(eid)
            if entity:
                combined_facts.extend(entity.facts)
                combined_attributes[f"from_{eid}"] = entity.attributes

        # Create merged entity
        merged = Entity(
            type=proposal.target_type,
            name=proposal.target_name,
            description=f"Merged from {len(proposal.source_entity_ids)} entities",
            creator_id="fusion",
            facts=combined_facts[:20],  # Keep reasonable number
            attributes={
                "fusion_sources": proposal.source_entity_ids,
                "source_attributes": combined_attributes,
                "fused_at": datetime.utcnow().isoformat(),
            },
        )
        self.store.save_entity(merged)

        # Mark source entities as fused
        for eid in proposal.source_entity_ids:
            entity = self.store.get_entity(eid)
            if entity:
                entity.attributes["fused_into"] = merged.id
                entity.type = EntityType.EMERGENT  # Mark as transformed
                self.store.save_entity(entity)

        logger.info(f"Fusion complete: {proposal.source_entity_ids} -> {merged.id}")

        return merged

    # =========================================================================
    # Diagnostics
    # =========================================================================

    def get_development_summary(self, entity_id: str) -> dict:
        """Get a complete summary of an entity's developmental state."""
        state = self.get_state(entity_id)
        if not state:
            return {"error": "No developmental state found"}

        entity = self.store.get_entity(entity_id)

        return {
            "entity_id": entity_id,
            "entity_name": entity.name if entity else "Unknown",
            "entity_type": entity.type.value if entity else "Unknown",
            "life_stage": state.life_stage.value,
            "potency": state.potency.value,
            "commitment": state.differentiation.commitment_level,
            "leading_types": [
                {"type": t.value, "affinity": round(a, 3)}
                for t, a in state.differentiation.leading_types
            ],
            "signal_count": len(state.differentiation.signals),
            "held_patterns": list(state.held_patterns),
            "in_chrysalis": state.is_in_chrysalis,
            "chrysalis_phase": state.chrysalis.phase.value if state.chrysalis else None,
            "fusion_proposals": state.fusion_proposals,
        }

    def get_community_development_summary(self, community_id: str) -> dict:
        """Get development summary for all seeds in a community."""
        niche = self.get_niche(community_id)
        quorum = self.get_quorum(community_id)

        proxies = self.store.get_proxies_in_community(community_id)

        seed_summaries = []
        for proxy in proxies:
            entity = self.store.get_entity(proxy.entity_id)
            if entity and entity.type in (EntityType.SEED, EntityType.CURIOUS, EntityType.EMERGENT):
                summary = self.get_development_summary(proxy.entity_id)
                seed_summaries.append(summary)

        return {
            "community_id": community_id,
            "niche": niche.to_dict(),
            "quorum": quorum.to_dict(),
            "seeds": seed_summaries,
            "vacuum_types": [t.value for t in niche.get_vacuum_types()],
            "saturated_types": [t.value for t in niche.get_saturated_types()],
        }


# Singleton
_manager: DevelopmentalManager | None = None


def get_dev_manager() -> DevelopmentalManager:
    """Get the singleton developmental manager."""
    global _manager
    if _manager is None:
        _manager = DevelopmentalManager()
    return _manager
