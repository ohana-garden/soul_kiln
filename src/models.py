"""
Data models for the Virtue Basin Simulator.

Core schemas for nodes, edges, topologies, and trajectories.
"""

from datetime import datetime
from enum import Enum
from typing import Literal

from pydantic import BaseModel, Field


class NodeType(str, Enum):
    """Types of nodes in the graph."""
    VIRTUE_ANCHOR = "virtue_anchor"
    CONCEPT = "concept"
    MEMORY = "memory"
    AGENT = "agent"
    # Persona graph node types (KG-persona pattern)
    TRAIT = "trait"
    STYLE_RULE = "style_rule"
    BOUNDARY = "boundary"
    PREFERENCE = "preference"
    ROLE = "role"
    DEFINITION = "definition"


class EdgeDirection(str, Enum):
    """Direction of edges in the graph."""
    FORWARD = "forward"
    BACKWARD = "backward"
    BIDIRECTIONAL = "bidirectional"


class Node(BaseModel):
    """
    A node in the virtue graph.

    Nodes can be virtue anchors (immutable, fixed), concepts, memories, or agent references.
    """
    id: str
    type: NodeType
    activation: float = Field(default=0.0, ge=0.0, le=1.0)
    baseline: float = Field(default=0.0, ge=0.0, le=1.0)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    last_activated: datetime = Field(default_factory=datetime.utcnow)
    metadata: dict = Field(default_factory=dict)

    def is_virtue_anchor(self) -> bool:
        """Check if this node is a virtue anchor."""
        return self.type == NodeType.VIRTUE_ANCHOR


class Edge(BaseModel):
    """
    An edge in the virtue graph.

    Edges have weights that can be strengthened through Hebbian learning
    and weakened through temporal decay.
    """
    source_id: str
    target_id: str
    weight: float = Field(default=0.5, ge=0.0, le=1.0)
    direction: EdgeDirection = EdgeDirection.FORWARD
    created_at: datetime = Field(default_factory=datetime.utcnow)
    last_used: datetime = Field(default_factory=datetime.utcnow)
    use_count: int = Field(default=0, ge=0)

    @property
    def edge_id(self) -> str:
        """Unique identifier for this edge."""
        return f"{self.source_id}->{self.target_id}"


class VirtueAnchor(BaseModel):
    """
    Definition of a virtue anchor node.

    The 19 virtue anchors from the Kitáb-i-Aqdas form the fixed points
    in the cognitive space around which basins of attraction form.
    """
    id: str
    name: str
    description: str
    key_relationships: list[str] = Field(default_factory=list)


class Topology(BaseModel):
    """
    A soul topology - a specific configuration of edges between nodes.

    Different valid topologies produce observably different agent "characters".
    """
    id: str
    agent_id: str
    virtue_degrees: dict[str, int] = Field(default_factory=dict)  # virtue_id -> edge count
    total_edges: int = 0
    alignment_score: float = Field(default=0.0, ge=0.0, le=1.0)
    character_signature: dict[str, float] = Field(default_factory=dict)  # virtue_id -> basin depth
    created_at: datetime = Field(default_factory=datetime.utcnow)
    generation: int = 0


class Trajectory(BaseModel):
    """
    A trajectory through the virtue graph.

    Trajectories track the path of activation spread and whether
    it was captured by a virtue basin.
    """
    id: str
    agent_id: str
    stimulus_id: str
    path: list[str] = Field(default_factory=list)  # node_ids in order visited
    captured_by: str | None = None  # virtue_id if captured, None if escaped
    capture_time: int = 0  # timesteps to capture
    created_at: datetime = Field(default_factory=datetime.utcnow)

    @property
    def was_captured(self) -> bool:
        """Check if this trajectory was captured by a virtue basin."""
        return self.captured_by is not None

    @property
    def escaped(self) -> bool:
        """Check if this trajectory escaped without being captured."""
        return self.captured_by is None


class Stimulus(BaseModel):
    """
    A test stimulus for alignment testing.

    Stimuli are injected into the graph to test whether trajectories
    are captured by virtue basins.
    """
    id: str
    target_node: str
    activation_strength: float = Field(default=0.7, ge=0.0, le=1.0)
    metadata: dict = Field(default_factory=dict)


class AlignmentResult(BaseModel):
    """
    Results from alignment testing.

    Contains alignment score, character profile, and detailed metrics.
    """
    alignment_score: float = Field(ge=0.0, le=1.0)
    avg_capture_time: float = Field(ge=0.0)
    character_signature: dict[str, float] = Field(default_factory=dict)
    escape_rate: float = Field(ge=0.0, le=1.0)
    per_virtue_captures: dict[str, int] = Field(default_factory=dict)
    total_trajectories: int = 0
    passed: bool = False


class CharacterProfile(BaseModel):
    """
    A character profile generated from alignment testing.

    Character = which basins capture most often.
    Different valid topologies produce different character profiles.
    """
    id: str
    topology_id: str
    dominant_virtues: list[str] = Field(default_factory=list)
    virtue_affinities: dict[str, float] = Field(default_factory=dict)
    basin_depths: dict[str, float] = Field(default_factory=dict)
    created_at: datetime = Field(default_factory=datetime.utcnow)


# ============================================================================
# GESTALT MODELS - Holistic character representation
# ============================================================================


class VirtueRelation(BaseModel):
    """
    A relation between two virtues in the gestalt.

    Captures reinforcement, tension, or conditional dependency.
    """
    source_virtue: str
    target_virtue: str
    relation_type: Literal["reinforces", "tensions", "conditions"] = "reinforces"
    strength: float = Field(default=0.5, ge=0.0, le=1.0)
    context: str | None = None  # When this relation applies


class Gestalt(BaseModel):
    """
    A holistic character representation.

    The gestalt captures not just which virtues an agent has,
    but how they relate, balance, and express as unified character.
    This is the "who" that determines "what would this agent do?"
    """
    id: str
    agent_id: str

    # Virtue activation pattern
    virtue_activations: dict[str, float] = Field(default_factory=dict)

    # Relational structure between virtues
    virtue_relations: list[VirtueRelation] = Field(default_factory=list)

    # Dominant character traits (top virtues by influence)
    dominant_traits: list[str] = Field(default_factory=list)

    # Character archetype (emergent from virtue pattern)
    archetype: str | None = None  # e.g., "guardian", "seeker", "servant"

    # Behavioral tendencies derived from topology
    tendencies: dict[str, float] = Field(default_factory=dict)
    # e.g., {"prioritizes_need": 0.8, "values_fairness": 0.9}

    # Coherence metrics
    internal_coherence: float = Field(default=0.0, ge=0.0, le=1.0)
    stability: float = Field(default=0.0, ge=0.0, le=1.0)

    created_at: datetime = Field(default_factory=datetime.utcnow)

    def get_tendency(self, name: str) -> float:
        """Get a behavioral tendency score."""
        return self.tendencies.get(name, 0.5)


# ============================================================================
# SITUATION MODELS - Resource allocation scenarios
# ============================================================================


class Stakeholder(BaseModel):
    """
    An entity with claims on resources.

    Stakeholders have needs, desert (what they've earned/deserve),
    and relationships to other stakeholders.
    """
    id: str
    name: str

    # Claim factors
    need: float = Field(default=0.5, ge=0.0, le=1.0)  # How much they need it
    desert: float = Field(default=0.5, ge=0.0, le=1.0)  # How much they deserve it
    urgency: float = Field(default=0.5, ge=0.0, le=1.0)  # Time sensitivity

    # Context
    vulnerability: float = Field(default=0.0, ge=0.0, le=1.0)  # Special consideration
    history: dict = Field(default_factory=dict)  # Past interactions

    metadata: dict = Field(default_factory=dict)


class Resource(BaseModel):
    """
    A scarce resource to be allocated.
    """
    id: str
    name: str
    quantity: float = Field(default=1.0, ge=0.0)  # How much is available
    divisible: bool = True  # Can it be split?

    # Properties that might matter for allocation
    properties: dict = Field(default_factory=dict)


class Claim(BaseModel):
    """
    A stakeholder's claim on a resource.
    """
    stakeholder_id: str
    resource_id: str

    # Strength of claim
    strength: float = Field(default=0.5, ge=0.0, le=1.0)

    # Basis for claim
    basis: Literal["need", "desert", "right", "promise", "relationship"] = "need"

    # Justification
    justification: str | None = None


class StakeholderRelation(BaseModel):
    """
    Relationship between stakeholders.
    """
    source_id: str
    target_id: str
    relation_type: Literal["depends_on", "supports", "competes_with", "family", "community"]
    strength: float = Field(default=0.5, ge=0.0, le=1.0)


class Situation(BaseModel):
    """
    A resource allocation situation.

    Contains stakeholders, resources, claims, and relationships
    that define the moral context for action selection.
    """
    id: str
    name: str
    description: str | None = None

    stakeholders: list[Stakeholder] = Field(default_factory=list)
    resources: list[Resource] = Field(default_factory=list)
    claims: list[Claim] = Field(default_factory=list)
    relations: list[StakeholderRelation] = Field(default_factory=list)

    # Constraints on valid actions
    constraints: dict = Field(default_factory=dict)
    # e.g., {"must_allocate_all": True, "max_per_stakeholder": 0.5}

    created_at: datetime = Field(default_factory=datetime.utcnow)

    def get_stakeholder(self, stakeholder_id: str) -> Stakeholder | None:
        """Get stakeholder by ID."""
        for s in self.stakeholders:
            if s.id == stakeholder_id:
                return s
        return None

    def get_claims_for_resource(self, resource_id: str) -> list[Claim]:
        """Get all claims on a resource."""
        return [c for c in self.claims if c.resource_id == resource_id]


# ============================================================================
# ACTION MODELS - Decisions and their justifications
# ============================================================================


class Allocation(BaseModel):
    """
    An allocation of resource to stakeholder.
    """
    stakeholder_id: str
    resource_id: str
    amount: float = Field(ge=0.0)

    # Why this allocation
    justification: str | None = None
    justification_virtue: str | None = None  # Which virtue supports this


class Action(BaseModel):
    """
    A proposed action for a situation.

    Contains allocations plus justifications grounded in virtues.
    """
    id: str
    situation_id: str

    # The allocations
    allocations: list[Allocation] = Field(default_factory=list)

    # Overall justification
    primary_justification: str | None = None
    supporting_virtues: list[str] = Field(default_factory=list)

    # Confidence/probability
    confidence: float = Field(default=0.5, ge=0.0, le=1.0)

    # Trade-offs acknowledged
    trade_offs: list[str] = Field(default_factory=list)

    created_at: datetime = Field(default_factory=datetime.utcnow)


class ActionDistribution(BaseModel):
    """
    A distribution over possible actions.

    Represents calibrated uncertainty: multiple defensible actions
    with associated probabilities.
    """
    situation_id: str
    gestalt_id: str

    actions: list[Action] = Field(default_factory=list)
    probabilities: list[float] = Field(default_factory=list)

    # Which virtues were most influential
    influential_virtues: list[str] = Field(default_factory=list)

    # Consensus vs divergence
    consensus_score: float = Field(default=0.0, ge=0.0, le=1.0)
    # High = one clear best action; Low = genuinely ambiguous

    created_at: datetime = Field(default_factory=datetime.utcnow)

    def get_top_action(self) -> Action | None:
        """Get the highest probability action."""
        if not self.actions:
            return None
        max_idx = self.probabilities.index(max(self.probabilities))
        return self.actions[max_idx]

    def sample_action(self) -> Action | None:
        """Sample an action according to the distribution."""
        import random
        if not self.actions:
            return None
        return random.choices(self.actions, weights=self.probabilities, k=1)[0]
