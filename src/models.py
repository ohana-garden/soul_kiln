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


class EpisodeType(str, Enum):
    """Types of episodes that can be recorded."""
    THOUGHT = "thought"
    REFLECTION = "reflection"
    ACTION = "action"
    OBSERVATION = "observation"


class Episode(BaseModel):
    """
    An episode in the shared knowledge graph.

    Episodes record agent thoughts, reflections, and actions.
    All agents can query episodes from any other agent - this is telepathy.
    """
    id: str
    agent_id: str
    episode_type: EpisodeType
    content: str
    stimulus: str | None = None
    tokens_used: int = 0
    created_at: datetime = Field(default_factory=datetime.utcnow)
    metadata: dict = Field(default_factory=dict)
