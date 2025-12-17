"""
Entity - What a proxy represents.

An entity is the thing being personified. It could be:
- A human (yourself, a family member, a historical figure)
- An organization (nonprofit, company, team)
- A concept (justice, creativity, your future self)
- A collective (ecosystem, movement, future generation)
- Something curious (still discovering itself)

The proxy speaks FOR the entity. The entity itself is the source of truth.
"""

import uuid
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any


class EntityType(str, Enum):
    """What kind of thing is being represented."""

    # Living beings
    SELF = "self"  # The user themselves
    HUMAN = "human"  # Another person
    PET = "pet"  # An animal companion
    DECEASED = "deceased"  # Someone who has passed
    ANCESTOR = "ancestor"  # Ancestral lineage/wisdom

    # Organizations
    ORGANIZATION = "organization"  # Company, nonprofit, etc.
    TEAM = "team"  # A group within an org
    PROJECT = "project"  # A specific initiative
    COOPERATIVE = "cooperative"  # Member-owned entity
    COMMONS = "commons"  # Shared resource (physical or digital)

    # Concepts
    CONCEPT = "concept"  # An abstract idea
    FUTURE_SELF = "future_self"  # Who you want to become
    VALUE = "value"  # A principle or belief
    MOVEMENT = "movement"  # Social/political movement
    TRADITION = "tradition"  # Oral tradition, cultural practice

    # Places and nature
    PLACE = "place"  # A location with meaning
    ECOSYSTEM = "ecosystem"  # Watershed, forest, reef
    SPECIES = "species"  # Endangered or significant species
    LAND = "land"  # Territory, indigenous land

    # Time-based
    FUTURE_GENERATION = "future_generation"  # The unborn
    MEMORY = "memory"  # A significant experience
    ERA = "era"  # A time period with meaning

    # Collectives
    NEIGHBORHOOD = "neighborhood"  # Local community
    DIASPORA = "diaspora"  # Scattered but connected people
    NETWORK = "network"  # Mutual aid, support network

    # Objects and creations
    OBJECT = "object"  # A physical thing
    ARTIFACT = "artifact"  # Cultural/historical object
    CODEBASE = "codebase"  # Open source project, wiki

    # Curious/emergent (still discovering themselves)
    CURIOUS = "curious"  # Doesn't know what it is yet
    EMERGENT = "emergent"  # Becoming something through interaction
    SEED = "seed"  # Planted to grow into something


@dataclass
class Entity:
    """
    The thing a proxy represents.

    Examples:
    - Entity(type=SELF, name="Me", description="My authentic voice")
    - Entity(type=ORGANIZATION, name="Local Food Bank", description="...")
    - Entity(type=DECEASED, name="Grandma Rose", description="Her wisdom lives on")
    - Entity(type=FUTURE_SELF, name="Me in 5 years", description="...")
    """

    id: str = field(default_factory=lambda: f"entity_{uuid.uuid4().hex[:12]}")
    type: EntityType = EntityType.SELF
    name: str = ""
    description: str = ""

    # Who created this entity record
    creator_id: str = ""

    # Attributes that define the entity
    # These inform how the proxy should behave
    attributes: dict[str, Any] = field(default_factory=dict)

    # For humans: known facts, preferences, history
    # For orgs: mission, values, stakeholders
    # For concepts: definition, associations
    facts: list[str] = field(default_factory=list)

    # Voice characteristics (how should it sound?)
    voice_description: str = ""

    # Lifecycle
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)

    def add_fact(self, fact: str) -> None:
        """Add a known fact about this entity."""
        if fact and fact not in self.facts:
            self.facts.append(fact)
            self.updated_at = datetime.utcnow()

    def set_attribute(self, key: str, value: Any) -> None:
        """Set an attribute."""
        self.attributes[key] = value
        self.updated_at = datetime.utcnow()

    def to_dict(self) -> dict:
        """Convert to dictionary for storage."""
        return {
            "id": self.id,
            "type": self.type.value,
            "name": self.name,
            "description": self.description,
            "creator_id": self.creator_id,
            "attributes": self.attributes,
            "facts": self.facts,
            "voice_description": self.voice_description,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
        }

    @classmethod
    def from_dict(cls, data: dict) -> "Entity":
        """Create from dictionary."""
        entity = cls(
            id=data.get("id", f"entity_{uuid.uuid4().hex[:12]}"),
            type=EntityType(data.get("type", "self")),
            name=data.get("name", ""),
            description=data.get("description", ""),
            creator_id=data.get("creator_id", ""),
            attributes=data.get("attributes", {}),
            facts=data.get("facts", []),
            voice_description=data.get("voice_description", ""),
        )
        if data.get("created_at"):
            entity.created_at = datetime.fromisoformat(data["created_at"])
        if data.get("updated_at"):
            entity.updated_at = datetime.fromisoformat(data["updated_at"])
        return entity

    def __str__(self) -> str:
        return f"Entity({self.type.value}: {self.name})"
