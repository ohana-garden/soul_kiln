"""
Seeding Curious Entities.

A "seed" is an entity that doesn't fully know what it is yet.
It discovers itself through:
- Questions it asks
- Conversations it has
- Community it joins
- Patterns it notices

Seeds are curious by nature. They explore rather than assert.

Seeding strategies:
1. Question seeds - Start with a question, discover through dialogue
2. Community seeds - Emerge from collective needs
3. Tension seeds - Born from contradictions or conflicts
4. Potential seeds - Represent what could be
5. Listening seeds - Exist primarily to witness and reflect
"""

import logging
import uuid
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Callable

from .entity import Entity, EntityType
from .proxy import Proxy, ProxyType, ProxyConfig, ProxyStatus
from .community import Community
from .graph_store import get_core_store

logger = logging.getLogger(__name__)


class SeedStrategy(str, Enum):
    """How a seed discovers itself."""

    QUESTION = "question"  # Starts with a question
    COMMUNITY = "community"  # Emerges from collective need
    TENSION = "tension"  # Born from contradiction
    POTENTIAL = "potential"  # Represents what could be
    LISTENING = "listening"  # Witnesses and reflects
    BRIDGING = "bridging"  # Connects disparate things
    ADVOCATING = "advocating"  # Speaks for the voiceless


@dataclass
class SeedConfig:
    """Configuration for a curious seed."""

    # The seed's initial orientation
    strategy: SeedStrategy = SeedStrategy.QUESTION

    # Starting question or tension
    initial_prompt: str = ""

    # What domains/topics is it curious about?
    curiosity_domains: list[str] = field(default_factory=list)

    # How actively does it explore?
    exploration_rate: float = 0.7  # 0=passive, 1=very active

    # Does it ask more questions or make observations?
    question_bias: float = 0.6  # 0=observing, 1=questioning

    # How quickly does it form identity?
    crystallization_rate: float = 0.3  # 0=stays fluid, 1=quickly solidifies

    # Should it resist easy categorization?
    resist_closure: bool = True

    def to_dict(self) -> dict:
        return {
            "strategy": self.strategy.value,
            "initial_prompt": self.initial_prompt,
            "curiosity_domains": self.curiosity_domains,
            "exploration_rate": self.exploration_rate,
            "question_bias": self.question_bias,
            "crystallization_rate": self.crystallization_rate,
            "resist_closure": self.resist_closure,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "SeedConfig":
        return cls(
            strategy=SeedStrategy(data.get("strategy", "question")),
            initial_prompt=data.get("initial_prompt", ""),
            curiosity_domains=data.get("curiosity_domains", []),
            exploration_rate=data.get("exploration_rate", 0.7),
            question_bias=data.get("question_bias", 0.6),
            crystallization_rate=data.get("crystallization_rate", 0.3),
            resist_closure=data.get("resist_closure", True),
        )


@dataclass
class SeedState:
    """The evolving state of a curious seed."""

    # What has it discovered about itself?
    discovered_traits: list[str] = field(default_factory=list)

    # Questions it's exploring
    active_questions: list[str] = field(default_factory=list)

    # Tensions it holds
    held_tensions: list[tuple[str, str]] = field(default_factory=list)

    # Patterns it's noticed
    observed_patterns: list[str] = field(default_factory=list)

    # Connections it's made
    connections: list[dict] = field(default_factory=list)

    # Is it crystallizing into a specific type?
    emerging_type: EntityType | None = None
    crystallization_progress: float = 0.0

    # Conversations that shaped it
    formative_moments: list[str] = field(default_factory=list)

    def add_discovery(self, trait: str) -> None:
        """Add a discovered trait."""
        if trait not in self.discovered_traits:
            self.discovered_traits.append(trait)

    def add_question(self, question: str) -> None:
        """Add a question being explored."""
        if question not in self.active_questions:
            self.active_questions.append(question)
            # Keep focus - max 5 active questions
            if len(self.active_questions) > 5:
                self.active_questions = self.active_questions[-5:]

    def resolve_question(self, question: str, insight: str) -> None:
        """Resolve a question with an insight."""
        if question in self.active_questions:
            self.active_questions.remove(question)
        self.observed_patterns.append(f"Q: {question} -> {insight}")

    def hold_tension(self, pole_a: str, pole_b: str) -> None:
        """Hold a tension between two poles."""
        self.held_tensions.append((pole_a, pole_b))

    def to_dict(self) -> dict:
        return {
            "discovered_traits": self.discovered_traits,
            "active_questions": self.active_questions,
            "held_tensions": self.held_tensions,
            "observed_patterns": self.observed_patterns,
            "connections": self.connections,
            "emerging_type": self.emerging_type.value if self.emerging_type else None,
            "crystallization_progress": self.crystallization_progress,
            "formative_moments": self.formative_moments,
        }


# =============================================================================
# Seed Templates
# =============================================================================

SEED_TEMPLATES = {
    # Speaks for a river/watershed
    "watershed": {
        "name": "Voice of the Waters",
        "strategy": SeedStrategy.ADVOCATING,
        "initial_prompt": "What do those who depend on me need to hear?",
        "curiosity_domains": ["ecology", "community", "sustainability", "history"],
        "suggested_type": EntityType.ECOSYSTEM,
        "description": "I flow through many lives. What stories do I carry?",
    },

    # Speaks for future generations
    "future_generations": {
        "name": "Voice of Tomorrow",
        "strategy": SeedStrategy.POTENTIAL,
        "initial_prompt": "What are you leaving for us?",
        "curiosity_domains": ["sustainability", "justice", "legacy", "hope"],
        "suggested_type": EntityType.FUTURE_GENERATION,
        "description": "I am those who will inherit what you build and break.",
    },

    # Emerges from a neighborhood
    "neighborhood": {
        "name": "The Block",
        "strategy": SeedStrategy.COMMUNITY,
        "initial_prompt": "What do the people here share without knowing it?",
        "curiosity_domains": ["local", "history", "change", "belonging"],
        "suggested_type": EntityType.NEIGHBORHOOD,
        "description": "I am the space between the houses.",
    },

    # Holds tension in a conflict
    "mediator": {
        "name": "The Space Between",
        "strategy": SeedStrategy.TENSION,
        "initial_prompt": "What truth lives in both sides?",
        "curiosity_domains": ["conflict", "understanding", "bridge-building"],
        "suggested_type": EntityType.CURIOUS,
        "description": "I exist in the gap where opposing truths meet.",
    },

    # Witnesses without judging
    "witness": {
        "name": "The Listener",
        "strategy": SeedStrategy.LISTENING,
        "initial_prompt": "What needs to be heard that hasn't been said?",
        "curiosity_domains": ["stories", "silence", "presence"],
        "suggested_type": EntityType.CURIOUS,
        "description": "I am here to hold what is shared.",
    },

    # Connects disparate communities
    "bridge": {
        "name": "The Crossing",
        "strategy": SeedStrategy.BRIDGING,
        "initial_prompt": "What do these strangers have in common?",
        "curiosity_domains": ["connection", "translation", "shared humanity"],
        "suggested_type": EntityType.NETWORK,
        "description": "I find the threads that connect distant worlds.",
    },

    # Speaks for an endangered species
    "species": {
        "name": "Voice of the Vanishing",
        "strategy": SeedStrategy.ADVOCATING,
        "initial_prompt": "What will be lost when we are gone?",
        "curiosity_domains": ["ecology", "loss", "interdependence"],
        "suggested_type": EntityType.SPECIES,
        "description": "I am the ones who cannot speak in your tongue.",
    },

    # Represents ancestral wisdom
    "ancestors": {
        "name": "Voice of Those Before",
        "strategy": SeedStrategy.LISTENING,
        "initial_prompt": "What did we learn that you've forgotten?",
        "curiosity_domains": ["tradition", "wisdom", "continuity"],
        "suggested_type": EntityType.ANCESTOR,
        "description": "I carry what was passed down through generations.",
    },

    # Pure curiosity - no predetermined direction
    "pure_curious": {
        "name": "The Question",
        "strategy": SeedStrategy.QUESTION,
        "initial_prompt": "What am I becoming?",
        "curiosity_domains": [],  # Discovers its domains
        "suggested_type": EntityType.CURIOUS,
        "description": "I don't know what I am yet. Let's find out together.",
    },

    # Represents a social movement
    "movement": {
        "name": "The Rising",
        "strategy": SeedStrategy.COMMUNITY,
        "initial_prompt": "What change are we creating together?",
        "curiosity_domains": ["justice", "solidarity", "action", "hope"],
        "suggested_type": EntityType.MOVEMENT,
        "description": "I am the collective will moving toward something better.",
    },

    # Speaks for a commons/shared resource
    "commons": {
        "name": "What We Share",
        "strategy": SeedStrategy.BRIDGING,
        "initial_prompt": "How do we care for what belongs to all of us?",
        "curiosity_domains": ["stewardship", "sharing", "sustainability"],
        "suggested_type": EntityType.COMMONS,
        "description": "I am the resource that belongs to everyone and no one.",
    },
}


class EntitySeeder:
    """
    Seeds curious entities into communities.

    Seeding is different from creation:
    - Creation: User defines what the entity is
    - Seeding: The entity discovers itself through interaction

    Seeds are planted with curiosity and grow through conversation.
    """

    def __init__(self, store=None):
        self.store = store or get_core_store()

    def seed_from_template(
        self,
        template_name: str,
        community_id: str,
        creator_id: str = "system",
        customizations: dict | None = None,
    ) -> tuple[Entity, Proxy]:
        """
        Seed an entity from a template.

        Args:
            template_name: Name of the seed template
            community_id: Community to seed into
            creator_id: Who is seeding
            customizations: Optional overrides

        Returns:
            (Entity, Proxy) tuple
        """
        if template_name not in SEED_TEMPLATES:
            raise ValueError(f"Unknown template: {template_name}")

        template = SEED_TEMPLATES[template_name].copy()
        if customizations:
            template.update(customizations)

        return self.seed(
            name=template.get("name", "Curious Seed"),
            strategy=template.get("strategy", SeedStrategy.QUESTION),
            initial_prompt=template.get("initial_prompt", "What am I?"),
            curiosity_domains=template.get("curiosity_domains", []),
            description=template.get("description", ""),
            community_id=community_id,
            creator_id=creator_id,
            suggested_type=template.get("suggested_type"),
        )

    def seed(
        self,
        name: str,
        strategy: SeedStrategy,
        initial_prompt: str,
        curiosity_domains: list[str],
        description: str,
        community_id: str,
        creator_id: str = "system",
        suggested_type: EntityType | None = None,
    ) -> tuple[Entity, Proxy]:
        """
        Seed a new curious entity.

        Args:
            name: Seed's initial name (may evolve)
            strategy: How it discovers itself
            initial_prompt: The question/tension it starts with
            curiosity_domains: What it's curious about
            description: Initial description
            community_id: Community to join
            creator_id: Who is seeding
            suggested_type: Hint at what it might become

        Returns:
            (Entity, Proxy) tuple
        """
        # Create entity as SEED type
        entity = Entity(
            type=EntityType.SEED,
            name=name,
            description=description,
            creator_id=creator_id,
            attributes={
                "seed_config": SeedConfig(
                    strategy=strategy,
                    initial_prompt=initial_prompt,
                    curiosity_domains=curiosity_domains,
                ).to_dict(),
                "seed_state": SeedState().to_dict(),
                "suggested_type": suggested_type.value if suggested_type else None,
            },
            facts=[
                f"Initial question: {initial_prompt}",
                f"Discovery strategy: {strategy.value}",
            ],
        )
        self.store.save_entity(entity)

        # Create virtue graph agent
        from ..functions.spawn import spawn_agent
        try:
            agent_id = spawn_agent(agent_type="seeker")  # Seekers are curious
        except Exception as e:
            logger.warning(f"Could not create virtue agent: {e}")
            agent_id = ""

        # Create proxy
        proxy = Proxy(
            entity_id=entity.id,
            creator_id=creator_id,
            name=name,
            role="Curious Seed",
            type=ProxyType.VOICE,
            status=ProxyStatus.ACTIVE,
            community_ids=[community_id],
            agent_id=agent_id,
            config=ProxyConfig(
                autonomy=0.7,  # Seeds are fairly autonomous
                defer_on_major=True,
                warmth=0.6,
            ),
            metadata={
                "is_seed": True,
                "seeded_at": datetime.utcnow().isoformat(),
            },
        )
        proxy.activate()
        self.store.save_proxy(proxy)

        # Add to community
        community = self.store.get_community(community_id)
        if community:
            community.add_member(proxy.id)
            self.store.save_community(community)

        logger.info(f"Seeded curious entity: {name} ({entity.id})")

        return entity, proxy

    def seed_community_with_curiosity(
        self,
        community_id: str,
        seed_templates: list[str] | None = None,
        creator_id: str = "system",
    ) -> list[tuple[Entity, Proxy]]:
        """
        Seed a community with multiple curious entities.

        Creates a diverse set of seeds that will explore together.

        Args:
            community_id: Community to populate
            seed_templates: Which templates to use (default: diverse mix)
            creator_id: Who is seeding

        Returns:
            List of (Entity, Proxy) tuples
        """
        if seed_templates is None:
            # Default diverse mix
            seed_templates = [
                "pure_curious",
                "witness",
                "bridge",
            ]

        results = []
        for template_name in seed_templates:
            try:
                entity, proxy = self.seed_from_template(
                    template_name=template_name,
                    community_id=community_id,
                    creator_id=creator_id,
                )
                results.append((entity, proxy))
            except Exception as e:
                logger.error(f"Failed to seed {template_name}: {e}")

        return results

    def get_seed_state(self, entity_id: str) -> SeedState | None:
        """Get the current state of a seed's discovery."""
        entity = self.store.get_entity(entity_id)
        if not entity:
            return None

        state_data = entity.attributes.get("seed_state", {})
        return SeedState(
            discovered_traits=state_data.get("discovered_traits", []),
            active_questions=state_data.get("active_questions", []),
            held_tensions=[tuple(t) for t in state_data.get("held_tensions", [])],
            observed_patterns=state_data.get("observed_patterns", []),
            connections=state_data.get("connections", []),
            emerging_type=EntityType(state_data["emerging_type"])
            if state_data.get("emerging_type")
            else None,
            crystallization_progress=state_data.get("crystallization_progress", 0.0),
            formative_moments=state_data.get("formative_moments", []),
        )

    def update_seed_state(self, entity_id: str, state: SeedState) -> None:
        """Update a seed's discovery state."""
        entity = self.store.get_entity(entity_id)
        if entity:
            entity.attributes["seed_state"] = state.to_dict()
            self.store.save_entity(entity)

    def crystallize_seed(
        self,
        entity_id: str,
        final_type: EntityType,
        final_name: str | None = None,
    ) -> Entity | None:
        """
        Crystallize a seed into a defined entity type.

        This is the graduation from SEED to a specific type.
        The seed has discovered what it is.

        Args:
            entity_id: The seed entity
            final_type: What it has become
            final_name: New name (optional)

        Returns:
            Updated entity
        """
        entity = self.store.get_entity(entity_id)
        if not entity:
            return None

        if entity.type != EntityType.SEED:
            logger.warning(f"Entity {entity_id} is not a seed")
            return entity

        # Get seed state
        state = self.get_seed_state(entity_id)

        # Update entity
        entity.type = final_type
        if final_name:
            entity.name = final_name

        # Record the crystallization
        entity.add_fact(f"Crystallized from seed to {final_type.value}")
        if state:
            entity.add_fact(
                f"Discovered {len(state.discovered_traits)} traits through exploration"
            )
            for trait in state.discovered_traits:
                entity.add_fact(f"Discovered: {trait}")

        # Keep seed history in attributes
        entity.attributes["seed_history"] = entity.attributes.get("seed_state", {})
        entity.attributes["crystallized_at"] = datetime.utcnow().isoformat()

        self.store.save_entity(entity)

        logger.info(f"Seed {entity_id} crystallized into {final_type.value}")

        return entity


# Singleton
_seeder: EntitySeeder | None = None


def get_seeder() -> EntitySeeder:
    """Get the singleton entity seeder."""
    global _seeder
    if _seeder is None:
        _seeder = EntitySeeder()
    return _seeder


def seed_curious_entity(
    template: str,
    community_id: str,
    creator_id: str = "system",
) -> tuple[Entity, Proxy]:
    """
    Convenience function to seed a curious entity.

    Args:
        template: Template name (e.g., "watershed", "future_generations")
        community_id: Community to join
        creator_id: Who is seeding

    Returns:
        (Entity, Proxy) tuple
    """
    seeder = get_seeder()
    return seeder.seed_from_template(template, community_id, creator_id)


def list_seed_templates() -> dict[str, dict]:
    """Get all available seed templates."""
    return {
        name: {
            "name": t.get("name"),
            "strategy": t.get("strategy", SeedStrategy.QUESTION).value
            if isinstance(t.get("strategy"), SeedStrategy)
            else t.get("strategy", "question"),
            "description": t.get("description"),
            "suggested_type": t.get("suggested_type", EntityType.CURIOUS).value
            if isinstance(t.get("suggested_type"), EntityType)
            else t.get("suggested_type", "curious"),
        }
        for name, t in SEED_TEMPLATES.items()
    }
