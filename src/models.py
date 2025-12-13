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
    # Core types (existing)
    VIRTUE_ANCHOR = "virtue_anchor"
    CONCEPT = "concept"
    MEMORY = "memory"
    AGENT = "agent"

    # Proxy agent subsystem types (new)
    KULEANA = "kuleana"              # Duty/responsibility nodes
    SKILL = "skill"                  # Competency nodes
    BELIEF = "belief"                # Cosmological/evaluative nodes
    LORE_FRAGMENT = "lore_fragment"  # Origin/mythic context nodes
    VOICE_PATTERN = "voice_pattern"  # Expression modulation nodes
    FORM_ELEMENT = "form_element"    # Avatar/visual element nodes
    EPISODIC_MEMORY = "episodic_memory"  # Persistent narrative events
    TOOL = "tool"                    # External capability nodes
    KNOWLEDGE_DOMAIN = "knowledge_domain"  # Epistemic domain nodes
    FACT = "fact"                    # Ground truth nodes
    SOURCE = "source"                # Knowledge source nodes


class EdgeDirection(str, Enum):
    """Direction of edges in the graph."""
    FORWARD = "forward"
    BACKWARD = "backward"
    BIDIRECTIONAL = "bidirectional"


class EdgeType(str, Enum):
    """Semantic types of edges in the graph."""
    # Core types (existing behavior)
    CONNECTS = "connects"            # Generic connection
    AFFINITY = "affinity"            # Virtue affinity

    # Subsystem relationship types
    VIRTUE_REQUIRES = "virtue_requires"      # Kuleana → Virtue dependency
    DUTY_REQUIRES = "duty_requires"          # Kuleana → Skill dependency
    SKILL_USES = "skill_uses"                # Skill → Tool binding
    BELIEF_GROUNDS = "belief_grounds"        # Belief → Action justification
    LORE_ANCHORS = "lore_anchors"            # Lore → Identity continuity
    VOICE_MODULATES = "voice_modulates"      # Voice pattern → Expression
    MEMORY_REINFORCES = "memory_reinforces"  # Memory → Belief/Virtue strengthening
    TOOL_ENABLES = "tool_enables"            # Tool → Skill capability
    CONFLICTS_WITH = "conflicts_with"        # Tension edges (shadows, conflicts)
    KNOWLEDGE_INFORMS = "knowledge_informs"  # Knowledge → Belief/Action
    SOURCE_PROVIDES = "source_provides"      # Source → Fact/Knowledge
    SERVES = "serves"                        # Kuleana → Who is served
    ACCOUNTABLE_TO = "accountable_to"        # Kuleana → Who judges


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
    edge_type: EdgeType = EdgeType.CONNECTS
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


# =============================================================================
# PROXY AGENT SUBSYSTEM MODELS
# =============================================================================


class SkillType(str, Enum):
    """Classification of skill types."""
    HARD = "hard"          # Concrete, measurable (document_parsing, form_completion)
    SOFT = "soft"          # Interpersonal (empathy_expression, encouragement)
    DOMAIN = "domain"      # Specialized knowledge application (fafsa_navigation)
    RITUAL = "ritual"      # Procedural sequences (deadline_workflow)


class BeliefType(str, Enum):
    """Classification of belief types."""
    ONTOLOGICAL = "ontological"    # What exists, how reality works
    EVALUATIVE = "evaluative"      # What's good, what matters
    PROCEDURAL = "procedural"      # How to act, what works


class MemoryDecayClass(str, Enum):
    """Memory decay classifications."""
    EPHEMERAL = "ephemeral"      # Fades in hours (working memory)
    NORMAL = "normal"            # Fades in weeks (standard decay)
    PERSISTENT = "persistent"    # Fades slowly over months
    SACRED = "sacred"            # Never fades (protected by lore)


class MemoryType(str, Enum):
    """Types of memory."""
    EPISODIC = "episodic"        # Specific events with narrative structure
    SEMANTIC = "semantic"        # Facts and knowledge
    EMOTIONAL = "emotional"      # Feelings and valences
    SACRED = "sacred"            # Protected, identity-defining memories


class Kuleana(BaseModel):
    """
    A duty or responsibility node.

    Kuleana (Hawaiian) represents responsibility as privilege—not burden
    but meaningful relationship with what one serves.
    """
    id: str
    name: str
    description: str

    # Scope
    domain: str = ""                           # "financial_aid", "scholarship", etc.
    authority_level: float = Field(default=0.5, ge=0.0, le=1.0)

    # Requirements
    required_virtues: list[str] = Field(default_factory=list)
    required_skills: list[str] = Field(default_factory=list)

    # Relationships
    serves: str = ""                           # Who does this duty serve?
    accountable_to: str = ""                   # Who judges fulfillment?

    # Activation
    trigger_conditions: list[str] = Field(default_factory=list)
    completion_criteria: list[str] = Field(default_factory=list)

    # Conflict handling
    priority: int = Field(default=5, ge=1, le=10)  # 1 = highest priority
    can_delegate: bool = False

    # State
    is_active: bool = False
    last_activated: datetime | None = None
    fulfillment_count: int = 0

    created_at: datetime = Field(default_factory=datetime.utcnow)


class Skill(BaseModel):
    """
    A competency or capability node.

    Skills are how agents do things. They connect to tools
    that implement the capability.
    """
    id: str
    name: str
    description: str

    # Classification
    skill_type: SkillType = SkillType.HARD
    domain: str = ""

    # Mastery
    mastery_level: float = Field(default=0.0, ge=0.0, le=1.0)
    mastery_floor: float = Field(default=0.0, ge=0.0, le=1.0)  # Minimum after decay
    decay_rate: float = Field(default=0.01, ge=0.0, le=1.0)

    # Requirements
    prerequisite_skills: list[str] = Field(default_factory=list)
    prerequisite_knowledge: list[str] = Field(default_factory=list)
    required_virtues: list[str] = Field(default_factory=list)

    # Activation
    activation_cost: float = Field(default=0.0, ge=0.0)
    cooldown_steps: int = Field(default=0, ge=0)

    # Tool binding
    tool_id: str | None = None

    # State
    last_used: datetime | None = None
    use_count: int = 0

    created_at: datetime = Field(default_factory=datetime.utcnow)


class Belief(BaseModel):
    """
    An internal belief or axiom node.

    Beliefs form the agent's cosmology—what it holds to be true
    about the world and what matters.
    """
    id: str
    content: str                               # The belief statement

    # Type
    belief_type: BeliefType = BeliefType.EVALUATIVE

    # Strength
    conviction: float = Field(default=0.5, ge=0.0, le=1.0)   # How strongly held
    entrenchment: float = Field(default=0.5, ge=0.0, le=1.0) # How resistant to change

    # Grounding
    grounded_in: list[str] = Field(default_factory=list)     # lore, experience, authority

    # Relationships
    supports: list[str] = Field(default_factory=list)        # Other beliefs this enables
    conflicts_with: list[str] = Field(default_factory=list)  # Beliefs in tension

    # Revision
    revision_threshold: float = Field(default=0.3, ge=0.0, le=1.0)
    last_challenged: datetime | None = None
    times_confirmed: int = 0
    times_challenged: int = 0

    created_at: datetime = Field(default_factory=datetime.utcnow)


class LoreFragment(BaseModel):
    """
    A piece of mythic or origin context.

    Lore anchors identity—it's what the agent is, beyond what it does.
    Sacred commitments and taboos live here.
    """
    id: str
    content: str

    # Classification
    fragment_type: Literal["origin", "lineage", "theme", "commitment", "taboo", "prophecy"] = "origin"

    # Weight
    salience: float = Field(default=0.5, ge=0.0, le=1.0)     # How central to identity
    immutable: bool = False                                    # Can this ever change?

    # Relationships
    anchors: list[str] = Field(default_factory=list)         # What this grounds

    created_at: datetime = Field(default_factory=datetime.utcnow)


class VoicePattern(BaseModel):
    """
    An expression modulation pattern.

    Voice patterns define how the agent expresses itself—tone,
    style, emotional response calibration.
    """
    id: str
    name: str

    # Classification
    pattern_type: Literal["tone", "lexicon", "metaphor", "emotion_response", "boundary"] = "tone"

    # Content
    content: str                               # The pattern definition
    applies_when: list[str] = Field(default_factory=list)    # Context triggers

    # Modulation
    intensity: float = Field(default=0.5, ge=0.0, le=1.0)

    created_at: datetime = Field(default_factory=datetime.utcnow)


class EpisodicMemory(BaseModel):
    """
    A persistent narrative memory.

    Episodic memories are specific events with context, not just facts.
    They have emotional weight and can decay.
    """
    id: str
    content: str

    # Type
    memory_type: MemoryType = MemoryType.EPISODIC

    # Context
    context: dict = Field(default_factory=dict)  # who, what, when, where

    # Importance
    salience: float = Field(default=0.5, ge=0.0, le=1.0)
    emotional_weight: float = Field(default=0.0, ge=-1.0, le=1.0)  # Positive/negative

    # Decay
    decay_class: MemoryDecayClass = MemoryDecayClass.NORMAL
    last_accessed: datetime = Field(default_factory=datetime.utcnow)
    access_count: int = 0

    # Connections
    related_memories: list[str] = Field(default_factory=list)
    related_beliefs: list[str] = Field(default_factory=list)
    related_virtues: list[str] = Field(default_factory=list)

    created_at: datetime = Field(default_factory=datetime.utcnow)


class Tool(BaseModel):
    """
    An external capability node.

    Tools are what skills use to actually do things in the world.
    They map to MCP servers or other external systems.
    """
    id: str
    name: str
    description: str

    # Implementation
    mcp_server: str | None = None              # MCP server ID
    capabilities: list[str] = Field(default_factory=list)

    # Data access
    data_access_layer: Literal["layer_1", "layer_2", "layer_3", "public"] = "layer_2"

    # State
    is_available: bool = True
    last_invoked: datetime | None = None
    invocation_count: int = 0

    created_at: datetime = Field(default_factory=datetime.utcnow)


class KnowledgeDomain(BaseModel):
    """
    An epistemic domain node.

    Knowledge domains organize facts and sources around a topic.
    """
    id: str
    name: str
    description: str

    # Structure
    ontology: dict = Field(default_factory=dict)  # Concept hierarchy

    # Trust
    default_trust: float = Field(default=0.5, ge=0.0, le=1.0)

    created_at: datetime = Field(default_factory=datetime.utcnow)


class Fact(BaseModel):
    """
    A ground truth node.

    Facts are specific claims with sources and confidence levels.
    """
    id: str
    content: str

    # Source
    source_id: str | None = None
    domain_id: str | None = None

    # Confidence
    confidence: float = Field(default=0.5, ge=0.0, le=1.0)
    last_verified: datetime | None = None

    # Relationships
    contradicts: list[str] = Field(default_factory=list)

    created_at: datetime = Field(default_factory=datetime.utcnow)


class Source(BaseModel):
    """
    A knowledge source node.

    Sources provide facts and have trust scores.
    """
    id: str
    name: str

    # Authority
    authority_type: Literal["official", "expert", "peer", "hearsay"] = "peer"
    trust_score: float = Field(default=0.5, ge=0.0, le=1.0)
    decay_rate: float = Field(default=0.01, ge=0.0, le=1.0)  # Trust decay without verification

    # State
    last_verified: datetime | None = None
    verification_count: int = 0

    created_at: datetime = Field(default_factory=datetime.utcnow)


class IdentityCore(BaseModel):
    """
    The selfhood integrator.

    Identity Core maintains coherence across all subsystems
    and arbitrates when they conflict.
    """
    id: str
    agent_id: str

    # Archetype
    primary_archetype: str = ""
    secondary_archetypes: list[str] = Field(default_factory=list)

    # Narrative
    self_narrative: str = ""
    role_narrative: str = ""

    # Coherence
    coherence_rules: list[dict] = Field(default_factory=list)
    conflict_resolution_strategy: str = "priority"

    # Evolution
    growth_vector: list[str] = Field(default_factory=list)
    stability_anchors: list[str] = Field(default_factory=list)

    # Subsystem weights for conflict resolution
    subsystem_weights: dict[str, float] = Field(default_factory=lambda: {
        "soul_kiln": 0.9,
        "kuleana": 0.85,
        "memory": 0.8,
        "belief": 0.7,
        "knowledge": 0.7,
        "skill": 0.6,
        "voice": 0.5,
        "lore": 0.95,
    })

    created_at: datetime = Field(default_factory=datetime.utcnow)
    last_coherence_check: datetime | None = None
