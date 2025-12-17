"""
Instruments - Atomic Serverless Smart Functions.

Instruments are the lowest-level operations in the system.
Each instrument does ONE thing and returns a result.

Instruments are stateless, composable, and can be:
- Called directly
- Combined into Tools
- Invoked by Agents
- Executed as Cypher queries

The key insight: even Cypher queries are instruments.
Everything bottoms out at graph operations.
"""

import uuid
import logging
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Callable
from enum import Enum

logger = logging.getLogger(__name__)


# =============================================================================
# INSTRUMENT RESULT
# =============================================================================


@dataclass
class InstrumentResult:
    """Result of executing an instrument."""

    success: bool
    data: Any = None
    error: str | None = None
    instrument: str = ""
    timestamp: datetime = field(default_factory=datetime.utcnow)

    def __bool__(self) -> bool:
        return self.success


# =============================================================================
# INSTRUMENT REGISTRY
# =============================================================================


class InstrumentRegistry:
    """
    Registry of all available instruments.

    Instruments register themselves here. Agents and Tools
    look up instruments by name.
    """

    _instruments: dict[str, "Instrument"] = {}

    @classmethod
    def register(cls, instrument: "Instrument") -> None:
        """Register an instrument."""
        cls._instruments[instrument.name] = instrument
        logger.debug(f"Registered instrument: {instrument.name}")

    @classmethod
    def get(cls, name: str) -> "Instrument | None":
        """Get an instrument by name."""
        return cls._instruments.get(name)

    @classmethod
    def list_all(cls) -> list[str]:
        """List all registered instrument names."""
        return list(cls._instruments.keys())

    @classmethod
    def by_category(cls, category: str) -> list["Instrument"]:
        """Get all instruments in a category."""
        return [i for i in cls._instruments.values() if i.category == category]


# =============================================================================
# INSTRUMENT BASE
# =============================================================================


@dataclass
class Instrument:
    """
    An atomic serverless smart function.

    Instruments are:
    - Stateless (no side effects except through graph)
    - Composable (can be combined)
    - Self-describing (name, description, parameters)
    - Executable (has a run function)
    """

    name: str
    description: str
    category: str
    parameters: dict[str, type]  # name -> type
    execute: Callable[..., InstrumentResult]

    def __post_init__(self):
        # Auto-register on creation
        InstrumentRegistry.register(self)

    def __call__(self, **kwargs) -> InstrumentResult:
        """Execute the instrument."""
        try:
            return self.execute(**kwargs)
        except Exception as e:
            logger.error(f"Instrument {self.name} failed: {e}")
            return InstrumentResult(
                success=False,
                error=str(e),
                instrument=self.name,
            )

    def to_dict(self) -> dict:
        return {
            "name": self.name,
            "description": self.description,
            "category": self.category,
            "parameters": {k: v.__name__ for k, v in self.parameters.items()},
        }


# =============================================================================
# CYPHER INSTRUMENT - The foundation
# =============================================================================


def _execute_cypher(query: str, params: dict | None = None) -> InstrumentResult:
    """Execute a Cypher query against the graph."""
    from ..graph.client import get_client

    try:
        client = get_client()
        result = client.query(query, params or {})
        return InstrumentResult(
            success=True,
            data=result,
            instrument="cypher",
        )
    except Exception as e:
        return InstrumentResult(
            success=False,
            error=str(e),
            instrument="cypher",
        )


cypher = Instrument(
    name="cypher",
    description="Execute a Cypher query against the graph database",
    category="graph",
    parameters={"query": str, "params": dict},
    execute=_execute_cypher,
)


# =============================================================================
# ENTITY INSTRUMENTS
# =============================================================================


def _create_entity(
    name: str,
    entity_type: str,
    description: str = "",
    creator_id: str = "",
    attributes: dict | None = None,
) -> InstrumentResult:
    """Create an entity in the graph."""
    from .entity import Entity, EntityType

    try:
        etype = EntityType(entity_type)
    except ValueError:
        return InstrumentResult(
            success=False,
            error=f"Invalid entity type: {entity_type}",
            instrument="create_entity",
        )

    entity = Entity(
        type=etype,
        name=name,
        description=description,
        creator_id=creator_id,
        attributes=attributes or {},
    )

    # Save to graph
    query = """
    CREATE (e:Entity {
        id: $id,
        type: $type,
        name: $name,
        description: $description,
        creator_id: $creator_id,
        attributes: $attributes,
        created_at: $created_at
    })
    RETURN e.id
    """
    result = cypher(
        query=query,
        params={
            "id": entity.id,
            "type": entity.type.value,
            "name": entity.name,
            "description": entity.description,
            "creator_id": entity.creator_id,
            "attributes": str(entity.attributes),  # JSON serialize in production
            "created_at": entity.created_at.isoformat(),
        },
    )

    if not result.success:
        return InstrumentResult(
            success=False,
            error=result.error,
            instrument="create_entity",
        )

    return InstrumentResult(
        success=True,
        data={"entity_id": entity.id, "entity": entity},
        instrument="create_entity",
    )


create_entity = Instrument(
    name="create_entity",
    description="Create a new entity (what a proxy represents)",
    category="entity",
    parameters={
        "name": str,
        "entity_type": str,
        "description": str,
        "creator_id": str,
        "attributes": dict,
    },
    execute=_create_entity,
)


def _get_entity(entity_id: str) -> InstrumentResult:
    """Get an entity from the graph."""
    query = """
    MATCH (e:Entity {id: $id})
    RETURN e
    """
    result = cypher(query=query, params={"id": entity_id})

    if not result.success:
        return InstrumentResult(
            success=False,
            error=result.error,
            instrument="get_entity",
        )

    if not result.data:
        return InstrumentResult(
            success=False,
            error=f"Entity not found: {entity_id}",
            instrument="get_entity",
        )

    return InstrumentResult(
        success=True,
        data=result.data[0] if result.data else None,
        instrument="get_entity",
    )


get_entity = Instrument(
    name="get_entity",
    description="Retrieve an entity from the graph",
    category="entity",
    parameters={"entity_id": str},
    execute=_get_entity,
)


# =============================================================================
# PROXY INSTRUMENTS
# =============================================================================


def _create_proxy(
    entity_id: str,
    name: str,
    proxy_type: str = "voice",
    creator_id: str = "",
) -> InstrumentResult:
    """Create a proxy for an entity."""
    proxy_id = f"proxy_{uuid.uuid4().hex[:12]}"

    query = """
    MATCH (e:Entity {id: $entity_id})
    CREATE (p:Proxy {
        id: $proxy_id,
        name: $name,
        type: $proxy_type,
        status: 'nascent',
        creator_id: $creator_id,
        created_at: $created_at
    })
    CREATE (p)-[:PROXY_FOR]->(e)
    RETURN p.id
    """
    result = cypher(
        query=query,
        params={
            "entity_id": entity_id,
            "proxy_id": proxy_id,
            "name": name,
            "proxy_type": proxy_type,
            "creator_id": creator_id,
            "created_at": datetime.utcnow().isoformat(),
        },
    )

    if not result.success:
        return InstrumentResult(
            success=False,
            error=result.error,
            instrument="create_proxy",
        )

    return InstrumentResult(
        success=True,
        data={"proxy_id": proxy_id},
        instrument="create_proxy",
    )


create_proxy = Instrument(
    name="create_proxy",
    description="Create a proxy (personified voice) for an entity",
    category="proxy",
    parameters={
        "entity_id": str,
        "name": str,
        "proxy_type": str,
        "creator_id": str,
    },
    execute=_create_proxy,
)


# =============================================================================
# AGENT INSTRUMENTS
# =============================================================================


def _create_agent(
    proxy_id: str,
    agent_type: str = "seed",
) -> InstrumentResult:
    """Create an agent node linked to a proxy."""
    agent_id = f"agent_{uuid.uuid4().hex[:12]}"

    query = """
    MATCH (p:Proxy {id: $proxy_id})
    CREATE (a:Agent {
        id: $agent_id,
        type: $agent_type,
        status: 'active',
        generation: 0,
        coherence_score: 0.0,
        created_at: $created_at
    })
    CREATE (p)-[:NAVIGATES]->(a)
    RETURN a.id
    """
    result = cypher(
        query=query,
        params={
            "proxy_id": proxy_id,
            "agent_id": agent_id,
            "agent_type": agent_type,
            "created_at": datetime.utcnow().isoformat(),
        },
    )

    if not result.success:
        return InstrumentResult(
            success=False,
            error=result.error,
            instrument="create_agent",
        )

    return InstrumentResult(
        success=True,
        data={"agent_id": agent_id},
        instrument="create_agent",
    )


create_agent = Instrument(
    name="create_agent",
    description="Create an agent node (computational entity in virtue graph)",
    category="agent",
    parameters={"proxy_id": str, "agent_type": str},
    execute=_create_agent,
)


def _join_community(
    proxy_id: str,
    community_id: str,
) -> InstrumentResult:
    """Add a proxy to a community."""
    query = """
    MATCH (p:Proxy {id: $proxy_id})
    MATCH (c:Community {id: $community_id})
    MERGE (p)-[:MEMBER_OF]->(c)
    SET c.member_count = coalesce(c.member_count, 0) + 1
    RETURN p.id, c.id
    """
    result = cypher(
        query=query,
        params={"proxy_id": proxy_id, "community_id": community_id},
    )

    if not result.success:
        return InstrumentResult(
            success=False,
            error=result.error,
            instrument="join_community",
        )

    return InstrumentResult(
        success=True,
        data={"proxy_id": proxy_id, "community_id": community_id},
        instrument="join_community",
    )


join_community = Instrument(
    name="join_community",
    description="Add a proxy to a community",
    category="community",
    parameters={"proxy_id": str, "community_id": str},
    execute=_join_community,
)


# =============================================================================
# DIFFERENTIATION INSTRUMENTS
# =============================================================================


def _add_differentiation_signal(
    entity_id: str,
    source: str,
    signal_type: str,
    target_type: str,
    strength: float,
) -> InstrumentResult:
    """Add a differentiation signal to an entity's developmental state."""
    signal_id = f"signal_{uuid.uuid4().hex[:8]}"

    query = """
    MATCH (e:Entity {id: $entity_id})
    CREATE (s:DifferentiationSignal {
        id: $signal_id,
        source: $source,
        signal_type: $signal_type,
        target_type: $target_type,
        strength: $strength,
        timestamp: $timestamp
    })
    CREATE (e)-[:HAS_SIGNAL]->(s)
    RETURN s.id
    """
    result = cypher(
        query=query,
        params={
            "entity_id": entity_id,
            "signal_id": signal_id,
            "source": source,
            "signal_type": signal_type,
            "target_type": target_type,
            "strength": strength,
            "timestamp": datetime.utcnow().isoformat(),
        },
    )

    if not result.success:
        return InstrumentResult(
            success=False,
            error=result.error,
            instrument="add_differentiation_signal",
        )

    return InstrumentResult(
        success=True,
        data={"signal_id": signal_id},
        instrument="add_differentiation_signal",
    )


add_differentiation_signal = Instrument(
    name="add_differentiation_signal",
    description="Add a differentiation signal pushing entity toward a type",
    category="development",
    parameters={
        "entity_id": str,
        "source": str,
        "signal_type": str,
        "target_type": str,
        "strength": float,
    },
    execute=_add_differentiation_signal,
)


def _get_differentiation_signals(entity_id: str) -> InstrumentResult:
    """Get all differentiation signals for an entity."""
    query = """
    MATCH (e:Entity {id: $entity_id})-[:HAS_SIGNAL]->(s:DifferentiationSignal)
    RETURN s.source, s.signal_type, s.target_type, s.strength, s.timestamp
    ORDER BY s.timestamp DESC
    """
    result = cypher(query=query, params={"entity_id": entity_id})

    if not result.success:
        return InstrumentResult(
            success=False,
            error=result.error,
            instrument="get_differentiation_signals",
        )

    signals = []
    for row in result.data or []:
        signals.append({
            "source": row[0],
            "signal_type": row[1],
            "target_type": row[2],
            "strength": row[3],
            "timestamp": row[4],
        })

    return InstrumentResult(
        success=True,
        data=signals,
        instrument="get_differentiation_signals",
    )


get_differentiation_signals = Instrument(
    name="get_differentiation_signals",
    description="Get all differentiation signals for an entity",
    category="development",
    parameters={"entity_id": str},
    execute=_get_differentiation_signals,
)


def _update_life_stage(
    entity_id: str,
    life_stage: str,
) -> InstrumentResult:
    """Update an entity's life stage."""
    query = """
    MATCH (e:Entity {id: $entity_id})
    SET e.life_stage = $life_stage,
        e.life_stage_updated = $timestamp
    RETURN e.id
    """
    result = cypher(
        query=query,
        params={
            "entity_id": entity_id,
            "life_stage": life_stage,
            "timestamp": datetime.utcnow().isoformat(),
        },
    )

    if not result.success:
        return InstrumentResult(
            success=False,
            error=result.error,
            instrument="update_life_stage",
        )

    return InstrumentResult(
        success=True,
        data={"entity_id": entity_id, "life_stage": life_stage},
        instrument="update_life_stage",
    )


update_life_stage = Instrument(
    name="update_life_stage",
    description="Update an entity's developmental life stage",
    category="development",
    parameters={"entity_id": str, "life_stage": str},
    execute=_update_life_stage,
)


def _set_entity_type(
    entity_id: str,
    new_type: str,
) -> InstrumentResult:
    """Change an entity's type (crystallization)."""
    query = """
    MATCH (e:Entity {id: $entity_id})
    SET e.previous_type = e.type,
        e.type = $new_type,
        e.crystallized_at = $timestamp
    RETURN e.id
    """
    result = cypher(
        query=query,
        params={
            "entity_id": entity_id,
            "new_type": new_type,
            "timestamp": datetime.utcnow().isoformat(),
        },
    )

    if not result.success:
        return InstrumentResult(
            success=False,
            error=result.error,
            instrument="set_entity_type",
        )

    return InstrumentResult(
        success=True,
        data={"entity_id": entity_id, "new_type": new_type},
        instrument="set_entity_type",
    )


set_entity_type = Instrument(
    name="set_entity_type",
    description="Change an entity's type (for crystallization)",
    category="development",
    parameters={"entity_id": str, "new_type": str},
    execute=_set_entity_type,
)


# =============================================================================
# SHARING INSTRUMENTS
# =============================================================================


def _share_lesson(
    community_id: str,
    lesson_type: str,
    description: str,
    source_agent_id: str,
    virtue_id: str | None = None,
) -> InstrumentResult:
    """Share a lesson with a community."""
    lesson_id = f"lesson_{uuid.uuid4().hex[:8]}"

    query = """
    MATCH (c:Community {id: $community_id})
    CREATE (l:Lesson {
        id: $lesson_id,
        type: $lesson_type,
        description: $description,
        source_agent_id: $source_agent_id,
        virtue_id: $virtue_id,
        created_at: $created_at
    })
    CREATE (l)-[:SHARED_IN]->(c)
    SET c.total_lessons_shared = coalesce(c.total_lessons_shared, 0) + 1
    RETURN l.id
    """
    result = cypher(
        query=query,
        params={
            "community_id": community_id,
            "lesson_id": lesson_id,
            "lesson_type": lesson_type,
            "description": description,
            "source_agent_id": source_agent_id,
            "virtue_id": virtue_id or "",
            "created_at": datetime.utcnow().isoformat(),
        },
    )

    if not result.success:
        return InstrumentResult(
            success=False,
            error=result.error,
            instrument="share_lesson",
        )

    return InstrumentResult(
        success=True,
        data={"lesson_id": lesson_id},
        instrument="share_lesson",
    )


share_lesson = Instrument(
    name="share_lesson",
    description="Share a lesson with a community",
    category="sharing",
    parameters={
        "community_id": str,
        "lesson_type": str,
        "description": str,
        "source_agent_id": str,
        "virtue_id": str,
    },
    execute=_share_lesson,
)


# =============================================================================
# VIRTUE INSTRUMENTS
# =============================================================================


def _record_virtue_activation(
    agent_id: str,
    virtue_id: str,
    activation: float,
    context: str = "",
) -> InstrumentResult:
    """Record a virtue activation for an agent."""
    query = """
    MATCH (a:Agent {id: $agent_id})
    MATCH (v:VirtueAnchor {id: $virtue_id})
    CREATE (act:VirtueActivation {
        agent_id: $agent_id,
        virtue_id: $virtue_id,
        activation: $activation,
        context: $context,
        timestamp: $timestamp
    })
    CREATE (a)-[:ACTIVATED]->(act)
    CREATE (act)-[:OF_VIRTUE]->(v)
    RETURN act.timestamp
    """
    result = cypher(
        query=query,
        params={
            "agent_id": agent_id,
            "virtue_id": virtue_id,
            "activation": activation,
            "context": context,
            "timestamp": datetime.utcnow().isoformat(),
        },
    )

    if not result.success:
        return InstrumentResult(
            success=False,
            error=result.error,
            instrument="record_virtue_activation",
        )

    return InstrumentResult(
        success=True,
        data={"agent_id": agent_id, "virtue_id": virtue_id, "activation": activation},
        instrument="record_virtue_activation",
    )


record_virtue_activation = Instrument(
    name="record_virtue_activation",
    description="Record a virtue activation for an agent",
    category="virtue",
    parameters={
        "agent_id": str,
        "virtue_id": str,
        "activation": float,
        "context": str,
    },
    execute=_record_virtue_activation,
)


# =============================================================================
# CONVENIENCE: List all instruments
# =============================================================================


def list_instruments() -> list[dict]:
    """List all registered instruments."""
    return [i.to_dict() for i in InstrumentRegistry._instruments.values()]


def get_instrument(name: str) -> Instrument | None:
    """Get an instrument by name."""
    return InstrumentRegistry.get(name)


def call_instrument(name: str, **kwargs) -> InstrumentResult:
    """Call an instrument by name."""
    instrument = InstrumentRegistry.get(name)
    if not instrument:
        return InstrumentResult(
            success=False,
            error=f"Unknown instrument: {name}",
            instrument=name,
        )
    return instrument(**kwargs)


# =============================================================================
# TOOLS - Collections of Instruments (also SSFs)
# =============================================================================


@dataclass
class ToolResult:
    """Result of executing a tool (collection of instruments)."""

    success: bool
    data: dict[str, Any] = field(default_factory=dict)
    errors: list[str] = field(default_factory=list)
    steps: list[InstrumentResult] = field(default_factory=list)
    tool: str = ""
    timestamp: datetime = field(default_factory=datetime.utcnow)

    def __bool__(self) -> bool:
        return self.success


class ToolRegistry:
    """Registry of all available tools."""

    _tools: dict[str, "Tool"] = {}

    @classmethod
    def register(cls, tool: "Tool") -> None:
        cls._tools[tool.name] = tool
        logger.debug(f"Registered tool: {tool.name}")

    @classmethod
    def get(cls, name: str) -> "Tool | None":
        return cls._tools.get(name)

    @classmethod
    def list_all(cls) -> list[str]:
        return list(cls._tools.keys())

    @classmethod
    def by_category(cls, category: str) -> list["Tool"]:
        return [t for t in cls._tools.values() if t.category == category]


@dataclass
class Tool:
    """
    A collection of instruments that together accomplish a task.

    Tools are:
    - Composed of instruments (atomic SSFs)
    - Also SSFs themselves (stateless, composable)
    - Higher-level operations that agents use
    - Orchestrate multiple instrument calls
    """

    name: str
    description: str
    category: str
    instruments: list[str]  # Names of instruments used
    execute: Callable[..., ToolResult]

    def __post_init__(self):
        ToolRegistry.register(self)

    def __call__(self, **kwargs) -> ToolResult:
        """Execute the tool."""
        try:
            return self.execute(**kwargs)
        except Exception as e:
            logger.error(f"Tool {self.name} failed: {e}")
            return ToolResult(
                success=False,
                errors=[str(e)],
                tool=self.name,
            )

    def to_dict(self) -> dict:
        return {
            "name": self.name,
            "description": self.description,
            "category": self.category,
            "instruments": self.instruments,
        }


# =============================================================================
# SPAWNING TOOL - Create a new agent from scratch
# =============================================================================


def _spawn_agent(
    name: str,
    entity_type: str = "curious",
    description: str = "",
    creator_id: str = "",
    community_id: str | None = None,
    attributes: dict | None = None,
) -> ToolResult:
    """
    Spawn a complete agent: Entity → Proxy → Agent (→ Community).

    This is the primary way new agents come into existence.
    It combines all the atomic operations needed to create
    a functional agent in the graph.
    """
    steps = []
    data = {}
    errors = []

    # Step 1: Create entity
    entity_result = create_entity(
        name=name,
        entity_type=entity_type,
        description=description,
        creator_id=creator_id,
        attributes=attributes or {},
    )
    steps.append(entity_result)

    if not entity_result.success:
        return ToolResult(
            success=False,
            errors=[entity_result.error or "Failed to create entity"],
            steps=steps,
            tool="spawn_agent",
        )

    entity_id = entity_result.data["entity_id"]
    data["entity_id"] = entity_id

    # Step 2: Create proxy for the entity
    proxy_result = create_proxy(
        entity_id=entity_id,
        name=f"{name} Voice",
        proxy_type="voice",
        creator_id=creator_id,
    )
    steps.append(proxy_result)

    if not proxy_result.success:
        errors.append(f"Entity created but proxy failed: {proxy_result.error}")
        return ToolResult(
            success=False,
            data=data,
            errors=errors,
            steps=steps,
            tool="spawn_agent",
        )

    proxy_id = proxy_result.data["proxy_id"]
    data["proxy_id"] = proxy_id

    # Step 3: Create agent linked to proxy
    agent_result = create_agent(
        proxy_id=proxy_id,
        agent_type="seed",  # All new agents start as seeds
    )
    steps.append(agent_result)

    if not agent_result.success:
        errors.append(f"Entity/Proxy created but agent failed: {agent_result.error}")
        return ToolResult(
            success=False,
            data=data,
            errors=errors,
            steps=steps,
            tool="spawn_agent",
        )

    agent_id = agent_result.data["agent_id"]
    data["agent_id"] = agent_id

    # Step 4 (optional): Join community
    if community_id:
        join_result = join_community(
            proxy_id=proxy_id,
            community_id=community_id,
        )
        steps.append(join_result)

        if join_result.success:
            data["community_id"] = community_id
        else:
            errors.append(f"Agent created but couldn't join community: {join_result.error}")

    return ToolResult(
        success=True,
        data=data,
        errors=errors,
        steps=steps,
        tool="spawn_agent",
    )


spawn_agent = Tool(
    name="spawn_agent",
    description="Create a complete agent: Entity → Proxy → Agent (→ Community)",
    category="lifecycle",
    instruments=["create_entity", "create_proxy", "create_agent", "join_community"],
    execute=_spawn_agent,
)


# =============================================================================
# DEVELOPMENT TOOL - Process developmental events
# =============================================================================


def _develop_agent(
    entity_id: str,
    signal_source: str,
    signal_type: str,  # "virtue", "conversation", "community"
    target_type: str,
    strength: float = 0.1,
    check_crystallization: bool = True,
) -> ToolResult:
    """
    Process a developmental event for an entity.

    This tool:
    1. Adds a differentiation signal
    2. Checks if entity should crystallize (optional)
    3. Updates life stage if appropriate
    """
    from .biomimicry import LifeStage

    steps = []
    data = {}
    errors = []

    # Step 1: Add differentiation signal
    signal_result = add_differentiation_signal(
        entity_id=entity_id,
        source=signal_source,
        signal_type=signal_type,
        target_type=target_type,
        strength=strength,
    )
    steps.append(signal_result)

    if not signal_result.success:
        return ToolResult(
            success=False,
            errors=[signal_result.error or "Failed to add signal"],
            steps=steps,
            tool="develop_agent",
        )

    data["signal_id"] = signal_result.data["signal_id"]

    # Step 2: Get all signals to analyze
    signals_result = get_differentiation_signals(entity_id=entity_id)
    steps.append(signals_result)

    if signals_result.success:
        signals = signals_result.data or []
        data["total_signals"] = len(signals)

        # Analyze type pressure
        type_pressure: dict[str, float] = {}
        for s in signals:
            ttype = s["target_type"]
            type_pressure[ttype] = type_pressure.get(ttype, 0) + s["strength"]

        data["type_pressure"] = type_pressure

        # Check if any type has enough pressure to trigger crystallization
        if check_crystallization:
            crystallization_threshold = 1.0  # Configurable
            for ttype, pressure in type_pressure.items():
                if pressure >= crystallization_threshold:
                    data["ready_to_crystallize"] = True
                    data["crystallization_type"] = ttype
                    break

    return ToolResult(
        success=True,
        data=data,
        errors=errors,
        steps=steps,
        tool="develop_agent",
    )


develop_agent = Tool(
    name="develop_agent",
    description="Process a developmental event (virtue, conversation, community pressure)",
    category="lifecycle",
    instruments=["add_differentiation_signal", "get_differentiation_signals"],
    execute=_develop_agent,
)


# =============================================================================
# METAMORPHOSIS TOOL - Transform entity type
# =============================================================================


def _metamorphose_agent(
    entity_id: str,
    new_type: str,
    new_life_stage: str = "juvenile",
) -> ToolResult:
    """
    Transform an entity's type through metamorphosis.

    This is a major identity shift - the entity becomes
    something different while maintaining continuity.
    """
    steps = []
    data = {}
    errors = []

    # Step 1: Update entity type
    type_result = set_entity_type(
        entity_id=entity_id,
        new_type=new_type,
    )
    steps.append(type_result)

    if not type_result.success:
        return ToolResult(
            success=False,
            errors=[type_result.error or "Failed to set entity type"],
            steps=steps,
            tool="metamorphose_agent",
        )

    data["entity_id"] = entity_id
    data["new_type"] = new_type

    # Step 2: Update life stage (post-metamorphosis)
    stage_result = update_life_stage(
        entity_id=entity_id,
        life_stage=new_life_stage,
    )
    steps.append(stage_result)

    if not stage_result.success:
        errors.append(f"Type changed but life stage update failed: {stage_result.error}")

    data["new_life_stage"] = new_life_stage

    return ToolResult(
        success=True,
        data=data,
        errors=errors,
        steps=steps,
        tool="metamorphose_agent",
    )


metamorphose_agent = Tool(
    name="metamorphose_agent",
    description="Transform an entity's type through metamorphosis",
    category="lifecycle",
    instruments=["set_entity_type", "update_life_stage"],
    execute=_metamorphose_agent,
)


# =============================================================================
# RECURSIVE SPAWNING TOOL - Mature agent creates offspring
# =============================================================================


def _spawn_offspring(
    parent_agent_id: str,
    offspring_name: str,
    offspring_type: str = "curious",
    community_id: str | None = None,
) -> ToolResult:
    """
    A mature agent spawns a new agent.

    The parent must be an adult-stage agent. The offspring
    inherits context from the parent's community but starts
    as a seed with full potency.
    """
    steps = []
    data = {}
    errors = []

    # First, verify parent exists and get their info
    parent_query = """
    MATCH (a:Agent {id: $agent_id})<-[:NAVIGATES]-(p:Proxy)-[:PROXY_FOR]->(e:Entity)
    RETURN e.life_stage as life_stage, p.id as proxy_id, e.id as entity_id
    """
    parent_result = cypher(query=parent_query, params={"agent_id": parent_agent_id})
    steps.append(parent_result)

    if not parent_result.success or not parent_result.data:
        return ToolResult(
            success=False,
            errors=["Parent agent not found or query failed"],
            steps=steps,
            tool="spawn_offspring",
        )

    parent_data = parent_result.data[0] if parent_result.data else None
    if not parent_data:
        return ToolResult(
            success=False,
            errors=["Parent agent has no entity data"],
            steps=steps,
            tool="spawn_offspring",
        )

    parent_life_stage = parent_data[0] if parent_data else None
    data["parent_agent_id"] = parent_agent_id
    data["parent_life_stage"] = parent_life_stage

    # Check if parent is mature enough to spawn
    mature_stages = ["adult", "elder", "mature"]
    if parent_life_stage and parent_life_stage.lower() not in mature_stages:
        return ToolResult(
            success=False,
            errors=[f"Agent must be adult/elder to spawn offspring, currently: {parent_life_stage}"],
            data=data,
            steps=steps,
            tool="spawn_offspring",
        )

    # Spawn the offspring using the spawn_agent tool
    spawn_result = spawn_agent(
        name=offspring_name,
        entity_type=offspring_type,
        description=f"Offspring of agent {parent_agent_id}",
        creator_id=parent_agent_id,  # Parent is the creator
        community_id=community_id,
    )
    steps.extend(spawn_result.steps)

    if not spawn_result.success:
        return ToolResult(
            success=False,
            data=data,
            errors=spawn_result.errors + ["Failed to spawn offspring"],
            steps=steps,
            tool="spawn_offspring",
        )

    data.update(spawn_result.data)
    data["offspring_entity_id"] = spawn_result.data.get("entity_id")
    data["offspring_agent_id"] = spawn_result.data.get("agent_id")

    # Link offspring to parent
    link_query = """
    MATCH (parent:Agent {id: $parent_id})
    MATCH (child:Agent {id: $child_id})
    CREATE (parent)-[:SPAWNED]->(child)
    SET child.generation = coalesce(parent.generation, 0) + 1
    RETURN child.generation
    """
    link_result = cypher(
        query=link_query,
        params={
            "parent_id": parent_agent_id,
            "child_id": spawn_result.data.get("agent_id"),
        },
    )
    steps.append(link_result)

    if link_result.success and link_result.data:
        data["offspring_generation"] = link_result.data[0][0] if link_result.data[0] else 1

    return ToolResult(
        success=True,
        data=data,
        errors=errors,
        steps=steps,
        tool="spawn_offspring",
    )


spawn_offspring = Tool(
    name="spawn_offspring",
    description="Mature agent spawns a new offspring agent",
    category="lifecycle",
    instruments=["cypher", "spawn_agent"],
    execute=_spawn_offspring,
)


# =============================================================================
# FUSION TOOL - Merge multiple agents into one
# =============================================================================


def _fuse_agents(
    agent_ids: list[str],
    fused_name: str,
    fused_type: str,
    community_id: str | None = None,
) -> ToolResult:
    """
    Fuse multiple agents into a new composite agent.

    This is symbiogenesis - multiple entities combining
    into a more complex form. The original agents are
    marked as fused but remain in the graph for history.
    """
    steps = []
    data = {}
    errors = []

    if len(agent_ids) < 2:
        return ToolResult(
            success=False,
            errors=["Fusion requires at least 2 agents"],
            tool="fuse_agents",
        )

    data["source_agents"] = agent_ids

    # Create the fused entity
    spawn_result = spawn_agent(
        name=fused_name,
        entity_type=fused_type,
        description=f"Fusion of agents: {', '.join(agent_ids)}",
        creator_id=agent_ids[0],  # First agent is primary creator
        community_id=community_id,
    )
    steps.extend(spawn_result.steps)

    if not spawn_result.success:
        return ToolResult(
            success=False,
            errors=spawn_result.errors + ["Failed to create fused agent"],
            steps=steps,
            tool="fuse_agents",
        )

    fused_agent_id = spawn_result.data.get("agent_id")
    data["fused_agent_id"] = fused_agent_id
    data["fused_entity_id"] = spawn_result.data.get("entity_id")

    # Link source agents to fused agent and mark them as fused
    for source_id in agent_ids:
        link_query = """
        MATCH (source:Agent {id: $source_id})
        MATCH (fused:Agent {id: $fused_id})
        CREATE (source)-[:FUSED_INTO]->(fused)
        SET source.status = 'fused',
            source.fused_at = $timestamp
        RETURN source.id
        """
        link_result = cypher(
            query=link_query,
            params={
                "source_id": source_id,
                "fused_id": fused_agent_id,
                "timestamp": datetime.utcnow().isoformat(),
            },
        )
        steps.append(link_result)

        if not link_result.success:
            errors.append(f"Failed to link source agent {source_id}: {link_result.error}")

    # Update fused agent's life stage to reflect maturity from fusion
    stage_result = update_life_stage(
        entity_id=spawn_result.data.get("entity_id"),
        life_stage="juvenile",  # Fusion products start as juveniles
    )
    steps.append(stage_result)

    return ToolResult(
        success=True,
        data=data,
        errors=errors,
        steps=steps,
        tool="fuse_agents",
    )


fuse_agents = Tool(
    name="fuse_agents",
    description="Fuse multiple agents into a composite agent (symbiogenesis)",
    category="lifecycle",
    instruments=["spawn_agent", "cypher", "update_life_stage"],
    execute=_fuse_agents,
)


# =============================================================================
# CONVENIENCE: List all tools
# =============================================================================


def list_tools() -> list[dict]:
    """List all registered tools."""
    return [t.to_dict() for t in ToolRegistry._tools.values()]


def get_tool(name: str) -> Tool | None:
    """Get a tool by name."""
    return ToolRegistry.get(name)


def call_tool(name: str, **kwargs) -> ToolResult:
    """Call a tool by name."""
    tool = ToolRegistry.get(name)
    if not tool:
        return ToolResult(
            success=False,
            errors=[f"Unknown tool: {name}"],
            tool=name,
        )
    return tool(**kwargs)
