"""
Instruments - Graph operations for Agent Zero.

These are simple functions that A0 (Agent Zero) can call.
A0 is the runtime/orchestrator. Soul_kiln provides graph operations.

Architecture:
- A0 handles: agent loop, tool selection, LLM calls, messaging
- Soul_kiln provides: graph operations, entity/proxy/community models,
  developmental biology, virtue basins

Everything here bottoms out at Cypher queries against FalkorDB.
"""

import uuid
import logging
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any

logger = logging.getLogger(__name__)


# =============================================================================
# RESULT TYPE
# =============================================================================


@dataclass
class Result:
    """Result of a graph operation."""
    success: bool
    data: Any = None
    error: str | None = None
    operation: str = ""

    def __bool__(self) -> bool:
        return self.success


# =============================================================================
# CYPHER - The foundation
# =============================================================================


def cypher(query: str, params: dict | None = None) -> Result:
    """
    Execute a Cypher query against the graph.

    This is the foundation. Everything else builds on this.
    """
    from ..graph.client import get_client

    try:
        client = get_client()
        result = client.query(query, params or {})
        return Result(success=True, data=result, operation="cypher")
    except Exception as e:
        logger.error(f"Cypher query failed: {e}")
        return Result(success=False, error=str(e), operation="cypher")


# =============================================================================
# ENTITY OPERATIONS
# =============================================================================


def create_entity(
    name: str,
    entity_type: str = "curious",
    description: str = "",
    creator_id: str = "",
    attributes: dict | None = None,
) -> Result:
    """Create an entity in the graph."""
    from .entity import Entity, EntityType

    try:
        etype = EntityType(entity_type)
    except ValueError:
        return Result(success=False, error=f"Invalid entity type: {entity_type}", operation="create_entity")

    entity = Entity(
        type=etype,
        name=name,
        description=description,
        creator_id=creator_id,
        attributes=attributes or {},
    )

    result = cypher(
        query="""
        CREATE (e:Entity {
            id: $id, type: $type, name: $name, description: $description,
            creator_id: $creator_id, attributes: $attributes, created_at: $created_at
        })
        RETURN e.id
        """,
        params={
            "id": entity.id,
            "type": entity.type.value,
            "name": entity.name,
            "description": entity.description,
            "creator_id": entity.creator_id,
            "attributes": str(entity.attributes),
            "created_at": entity.created_at.isoformat(),
        },
    )

    if not result.success:
        return Result(success=False, error=result.error, operation="create_entity")

    return Result(success=True, data={"entity_id": entity.id, "entity": entity}, operation="create_entity")


def get_entity(entity_id: str) -> Result:
    """Get an entity from the graph."""
    result = cypher(
        query="MATCH (e:Entity {id: $id}) RETURN e",
        params={"id": entity_id},
    )

    if not result.success:
        return Result(success=False, error=result.error, operation="get_entity")

    if not result.data:
        return Result(success=False, error=f"Entity not found: {entity_id}", operation="get_entity")

    return Result(success=True, data=result.data[0] if result.data else None, operation="get_entity")


# =============================================================================
# PROXY OPERATIONS
# =============================================================================


def create_proxy(
    entity_id: str,
    name: str,
    proxy_type: str = "voice",
    creator_id: str = "",
) -> Result:
    """Create a proxy for an entity."""
    proxy_id = f"proxy_{uuid.uuid4().hex[:12]}"

    result = cypher(
        query="""
        MATCH (e:Entity {id: $entity_id})
        CREATE (p:Proxy {
            id: $proxy_id, name: $name, type: $proxy_type,
            status: 'nascent', creator_id: $creator_id, created_at: $created_at
        })
        CREATE (p)-[:PROXY_FOR]->(e)
        RETURN p.id
        """,
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
        return Result(success=False, error=result.error, operation="create_proxy")

    return Result(success=True, data={"proxy_id": proxy_id}, operation="create_proxy")


# =============================================================================
# AGENT OPERATIONS (graph nodes, not A0 agents)
# =============================================================================


def create_agent_node(proxy_id: str, agent_type: str = "seed") -> Result:
    """
    Create an Agent node linked to a proxy.

    Note: This creates a graph node representing an agent's state,
    not an A0 agent instance. A0 IS the agent runtime.
    """
    agent_id = f"agent_{uuid.uuid4().hex[:12]}"

    result = cypher(
        query="""
        MATCH (p:Proxy {id: $proxy_id})
        CREATE (a:Agent {
            id: $agent_id, type: $agent_type, status: 'active',
            generation: 0, coherence_score: 0.0, created_at: $created_at
        })
        CREATE (p)-[:NAVIGATES]->(a)
        RETURN a.id
        """,
        params={
            "proxy_id": proxy_id,
            "agent_id": agent_id,
            "agent_type": agent_type,
            "created_at": datetime.utcnow().isoformat(),
        },
    )

    if not result.success:
        return Result(success=False, error=result.error, operation="create_agent_node")

    return Result(success=True, data={"agent_id": agent_id}, operation="create_agent_node")


def join_community(proxy_id: str, community_id: str) -> Result:
    """Add a proxy to a community."""
    result = cypher(
        query="""
        MATCH (p:Proxy {id: $proxy_id})
        MATCH (c:Community {id: $community_id})
        MERGE (p)-[:MEMBER_OF]->(c)
        SET c.member_count = coalesce(c.member_count, 0) + 1
        RETURN p.id, c.id
        """,
        params={"proxy_id": proxy_id, "community_id": community_id},
    )

    if not result.success:
        return Result(success=False, error=result.error, operation="join_community")

    return Result(success=True, data={"proxy_id": proxy_id, "community_id": community_id}, operation="join_community")


# =============================================================================
# DEVELOPMENT OPERATIONS
# =============================================================================


def add_differentiation_signal(
    entity_id: str,
    source: str,
    signal_type: str,
    target_type: str,
    strength: float,
) -> Result:
    """Add a differentiation signal pushing entity toward a type."""
    signal_id = f"signal_{uuid.uuid4().hex[:8]}"

    result = cypher(
        query="""
        MATCH (e:Entity {id: $entity_id})
        CREATE (s:DifferentiationSignal {
            id: $signal_id, source: $source, signal_type: $signal_type,
            target_type: $target_type, strength: $strength, timestamp: $timestamp
        })
        CREATE (e)-[:HAS_SIGNAL]->(s)
        RETURN s.id
        """,
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
        return Result(success=False, error=result.error, operation="add_differentiation_signal")

    return Result(success=True, data={"signal_id": signal_id}, operation="add_differentiation_signal")


def get_differentiation_signals(entity_id: str) -> Result:
    """Get all differentiation signals for an entity."""
    result = cypher(
        query="""
        MATCH (e:Entity {id: $entity_id})-[:HAS_SIGNAL]->(s:DifferentiationSignal)
        RETURN s.source, s.signal_type, s.target_type, s.strength, s.timestamp
        ORDER BY s.timestamp DESC
        """,
        params={"entity_id": entity_id},
    )

    if not result.success:
        return Result(success=False, error=result.error, operation="get_differentiation_signals")

    signals = []
    for row in result.data or []:
        signals.append({
            "source": row[0],
            "signal_type": row[1],
            "target_type": row[2],
            "strength": row[3],
            "timestamp": row[4],
        })

    return Result(success=True, data=signals, operation="get_differentiation_signals")


def update_life_stage(entity_id: str, life_stage: str) -> Result:
    """Update an entity's life stage."""
    result = cypher(
        query="""
        MATCH (e:Entity {id: $entity_id})
        SET e.life_stage = $life_stage, e.life_stage_updated = $timestamp
        RETURN e.id
        """,
        params={
            "entity_id": entity_id,
            "life_stage": life_stage,
            "timestamp": datetime.utcnow().isoformat(),
        },
    )

    if not result.success:
        return Result(success=False, error=result.error, operation="update_life_stage")

    return Result(success=True, data={"entity_id": entity_id, "life_stage": life_stage}, operation="update_life_stage")


def set_entity_type(entity_id: str, new_type: str) -> Result:
    """Change an entity's type (crystallization)."""
    result = cypher(
        query="""
        MATCH (e:Entity {id: $entity_id})
        SET e.previous_type = e.type, e.type = $new_type, e.crystallized_at = $timestamp
        RETURN e.id
        """,
        params={
            "entity_id": entity_id,
            "new_type": new_type,
            "timestamp": datetime.utcnow().isoformat(),
        },
    )

    if not result.success:
        return Result(success=False, error=result.error, operation="set_entity_type")

    return Result(success=True, data={"entity_id": entity_id, "new_type": new_type}, operation="set_entity_type")


# =============================================================================
# SHARING OPERATIONS
# =============================================================================


def share_lesson(
    community_id: str,
    lesson_type: str,
    description: str,
    source_agent_id: str,
    virtue_id: str | None = None,
) -> Result:
    """Share a lesson with a community."""
    lesson_id = f"lesson_{uuid.uuid4().hex[:8]}"

    result = cypher(
        query="""
        MATCH (c:Community {id: $community_id})
        CREATE (l:Lesson {
            id: $lesson_id, type: $lesson_type, description: $description,
            source_agent_id: $source_agent_id, virtue_id: $virtue_id, created_at: $created_at
        })
        CREATE (l)-[:SHARED_IN]->(c)
        SET c.total_lessons_shared = coalesce(c.total_lessons_shared, 0) + 1
        RETURN l.id
        """,
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
        return Result(success=False, error=result.error, operation="share_lesson")

    return Result(success=True, data={"lesson_id": lesson_id}, operation="share_lesson")


# =============================================================================
# VIRTUE OPERATIONS
# =============================================================================


def record_virtue_activation(
    agent_id: str,
    virtue_id: str,
    activation: float,
    context: str = "",
) -> Result:
    """Record a virtue activation for an agent."""
    result = cypher(
        query="""
        MATCH (a:Agent {id: $agent_id})
        MATCH (v:VirtueAnchor {id: $virtue_id})
        CREATE (act:VirtueActivation {
            agent_id: $agent_id, virtue_id: $virtue_id,
            activation: $activation, context: $context, timestamp: $timestamp
        })
        CREATE (a)-[:ACTIVATED]->(act)
        CREATE (act)-[:OF_VIRTUE]->(v)
        RETURN act.timestamp
        """,
        params={
            "agent_id": agent_id,
            "virtue_id": virtue_id,
            "activation": activation,
            "context": context,
            "timestamp": datetime.utcnow().isoformat(),
        },
    )

    if not result.success:
        return Result(success=False, error=result.error, operation="record_virtue_activation")

    return Result(success=True, data={"agent_id": agent_id, "virtue_id": virtue_id, "activation": activation}, operation="record_virtue_activation")


# =============================================================================
# COMPOSITE OPERATIONS (A0 tools)
# =============================================================================


def spawn_agent(
    name: str,
    entity_type: str = "curious",
    description: str = "",
    creator_id: str = "",
    community_id: str | None = None,
    attributes: dict | None = None,
) -> Result:
    """
    Spawn a complete agent: Entity → Proxy → Agent node (→ Community).

    This is what A0 calls to create a new agent in the graph.
    """
    # Step 1: Create entity
    entity_result = create_entity(
        name=name,
        entity_type=entity_type,
        description=description,
        creator_id=creator_id,
        attributes=attributes,
    )
    if not entity_result.success:
        return Result(success=False, error=entity_result.error, operation="spawn_agent")

    entity_id = entity_result.data["entity_id"]

    # Step 2: Create proxy
    proxy_result = create_proxy(
        entity_id=entity_id,
        name=f"{name} Voice",
        creator_id=creator_id,
    )
    if not proxy_result.success:
        return Result(success=False, error=f"Entity created but proxy failed: {proxy_result.error}", operation="spawn_agent")

    proxy_id = proxy_result.data["proxy_id"]

    # Step 3: Create agent node
    agent_result = create_agent_node(proxy_id=proxy_id, agent_type="seed")
    if not agent_result.success:
        return Result(success=False, error=f"Entity/Proxy created but agent node failed: {agent_result.error}", operation="spawn_agent")

    agent_id = agent_result.data["agent_id"]

    # Step 4 (optional): Join community
    if community_id:
        join_result = join_community(proxy_id=proxy_id, community_id=community_id)
        if not join_result.success:
            logger.warning(f"Agent created but couldn't join community: {join_result.error}")

    return Result(
        success=True,
        data={
            "entity_id": entity_id,
            "proxy_id": proxy_id,
            "agent_id": agent_id,
            "community_id": community_id,
        },
        operation="spawn_agent",
    )


def develop_agent(
    entity_id: str,
    signal_source: str,
    signal_type: str,
    target_type: str,
    strength: float = 0.1,
) -> Result:
    """
    Process a developmental event for an entity.

    Adds a differentiation signal and checks if crystallization is ready.
    """
    # Add signal
    signal_result = add_differentiation_signal(
        entity_id=entity_id,
        source=signal_source,
        signal_type=signal_type,
        target_type=target_type,
        strength=strength,
    )
    if not signal_result.success:
        return Result(success=False, error=signal_result.error, operation="develop_agent")

    # Get all signals to analyze pressure
    signals_result = get_differentiation_signals(entity_id=entity_id)
    signals = signals_result.data or [] if signals_result.success else []

    # Analyze type pressure
    type_pressure: dict[str, float] = {}
    for s in signals:
        ttype = s["target_type"]
        type_pressure[ttype] = type_pressure.get(ttype, 0) + s["strength"]

    # Check crystallization readiness
    crystallization_threshold = 1.0
    ready_to_crystallize = False
    crystallization_type = None
    for ttype, pressure in type_pressure.items():
        if pressure >= crystallization_threshold:
            ready_to_crystallize = True
            crystallization_type = ttype
            break

    return Result(
        success=True,
        data={
            "signal_id": signal_result.data["signal_id"],
            "total_signals": len(signals),
            "type_pressure": type_pressure,
            "ready_to_crystallize": ready_to_crystallize,
            "crystallization_type": crystallization_type,
        },
        operation="develop_agent",
    )


def metamorphose_agent(entity_id: str, new_type: str, new_life_stage: str = "juvenile") -> Result:
    """Transform an entity's type through metamorphosis."""
    type_result = set_entity_type(entity_id=entity_id, new_type=new_type)
    if not type_result.success:
        return Result(success=False, error=type_result.error, operation="metamorphose_agent")

    stage_result = update_life_stage(entity_id=entity_id, life_stage=new_life_stage)
    if not stage_result.success:
        logger.warning(f"Type changed but life stage update failed: {stage_result.error}")

    return Result(
        success=True,
        data={"entity_id": entity_id, "new_type": new_type, "new_life_stage": new_life_stage},
        operation="metamorphose_agent",
    )


def spawn_offspring(
    parent_agent_id: str,
    offspring_name: str,
    offspring_type: str = "curious",
    community_id: str | None = None,
) -> Result:
    """A mature agent spawns a new agent."""
    # Verify parent exists and is mature
    parent_result = cypher(
        query="""
        MATCH (a:Agent {id: $agent_id})<-[:NAVIGATES]-(p:Proxy)-[:PROXY_FOR]->(e:Entity)
        RETURN e.life_stage, p.id, e.id
        """,
        params={"agent_id": parent_agent_id},
    )

    if not parent_result.success or not parent_result.data:
        return Result(success=False, error="Parent agent not found", operation="spawn_offspring")

    parent_life_stage = parent_result.data[0][0] if parent_result.data[0] else None
    mature_stages = ["adult", "elder", "mature"]

    if parent_life_stage and parent_life_stage.lower() not in mature_stages:
        return Result(
            success=False,
            error=f"Agent must be adult/elder to spawn, currently: {parent_life_stage}",
            operation="spawn_offspring",
        )

    # Spawn offspring
    spawn_result = spawn_agent(
        name=offspring_name,
        entity_type=offspring_type,
        description=f"Offspring of {parent_agent_id}",
        creator_id=parent_agent_id,
        community_id=community_id,
    )
    if not spawn_result.success:
        return Result(success=False, error=spawn_result.error, operation="spawn_offspring")

    # Link parent to child
    cypher(
        query="""
        MATCH (parent:Agent {id: $parent_id})
        MATCH (child:Agent {id: $child_id})
        CREATE (parent)-[:SPAWNED]->(child)
        SET child.generation = coalesce(parent.generation, 0) + 1
        """,
        params={"parent_id": parent_agent_id, "child_id": spawn_result.data["agent_id"]},
    )

    return Result(
        success=True,
        data={
            "parent_agent_id": parent_agent_id,
            "offspring_agent_id": spawn_result.data["agent_id"],
            "offspring_entity_id": spawn_result.data["entity_id"],
        },
        operation="spawn_offspring",
    )


# =============================================================================
# MESSAGE OPERATIONS (graph-based memory/telepathy)
# =============================================================================


def send_message(
    from_id: str,
    to_id: str,
    content: str,
    metadata: dict | None = None,
) -> Result:
    """Send a message between agents (stored in graph)."""
    message_id = f"msg_{uuid.uuid4().hex[:12]}"

    result = cypher(
        query="""
        CREATE (m:Message {
            id: $id, content: $content, from_id: $from_id, to_id: $to_id,
            read: false, timestamp: $timestamp, metadata: $metadata
        })
        WITH m
        OPTIONAL MATCH (sender:Agent {id: $from_id})
        OPTIONAL MATCH (recipient:Agent {id: $to_id})
        FOREACH (_ IN CASE WHEN sender IS NOT NULL THEN [1] ELSE [] END |
            CREATE (sender)-[:SENT]->(m)
        )
        FOREACH (_ IN CASE WHEN recipient IS NOT NULL THEN [1] ELSE [] END |
            CREATE (m)-[:TO]->(recipient)
        )
        RETURN m.id
        """,
        params={
            "id": message_id,
            "content": content,
            "from_id": from_id,
            "to_id": to_id,
            "timestamp": datetime.utcnow().isoformat(),
            "metadata": str(metadata or {}),
        },
    )

    if not result.success:
        return Result(success=False, error=result.error, operation="send_message")

    return Result(success=True, data={"message_id": message_id}, operation="send_message")


def get_messages(agent_id: str, unread_only: bool = True, limit: int = 50) -> Result:
    """Get messages for an agent from graph."""
    if unread_only:
        query = """
        MATCH (m:Message {to_id: $agent_id, read: false})
        RETURN m.id, m.content, m.from_id, m.timestamp, m.metadata
        ORDER BY m.timestamp ASC
        LIMIT $limit
        """
    else:
        query = """
        MATCH (m:Message {to_id: $agent_id})
        RETURN m.id, m.content, m.from_id, m.timestamp, m.metadata
        ORDER BY m.timestamp DESC
        LIMIT $limit
        """

    result = cypher(query=query, params={"agent_id": agent_id, "limit": limit})

    if not result.success:
        return Result(success=False, error=result.error, operation="get_messages")

    messages = []
    for row in result.data or []:
        messages.append({
            "id": row[0],
            "content": row[1],
            "from_id": row[2],
            "timestamp": row[3],
            "metadata": row[4],
        })

    return Result(success=True, data=messages, operation="get_messages")


def mark_read(message_id: str) -> Result:
    """Mark a message as read."""
    result = cypher(
        query="MATCH (m:Message {id: $id}) SET m.read = true, m.read_at = $timestamp RETURN m.id",
        params={"id": message_id, "timestamp": datetime.utcnow().isoformat()},
    )

    if not result.success:
        return Result(success=False, error=result.error, operation="mark_read")

    return Result(success=True, data={"message_id": message_id}, operation="mark_read")


def save_memory(
    agent_id: str,
    memory_type: str,
    content: str,
    metadata: dict | None = None,
) -> Result:
    """Save a memory/fact for an agent."""
    memory_id = f"mem_{uuid.uuid4().hex[:12]}"

    result = cypher(
        query="""
        MATCH (a:Agent {id: $agent_id})
        CREATE (m:Memory {
            id: $id, type: $type, content: $content,
            metadata: $metadata, timestamp: $timestamp
        })
        CREATE (a)-[:REMEMBERS]->(m)
        RETURN m.id
        """,
        params={
            "agent_id": agent_id,
            "id": memory_id,
            "type": memory_type,
            "content": content,
            "metadata": str(metadata or {}),
            "timestamp": datetime.utcnow().isoformat(),
        },
    )

    if not result.success:
        return Result(success=False, error=result.error, operation="save_memory")

    return Result(success=True, data={"memory_id": memory_id}, operation="save_memory")


def get_memories(
    agent_id: str,
    memory_type: str | None = None,
    limit: int = 100,
) -> Result:
    """Get memories for an agent."""
    if memory_type:
        query = """
        MATCH (a:Agent {id: $agent_id})-[:REMEMBERS]->(m:Memory {type: $type})
        RETURN m.id, m.type, m.content, m.metadata, m.timestamp
        ORDER BY m.timestamp DESC
        LIMIT $limit
        """
        params = {"agent_id": agent_id, "type": memory_type, "limit": limit}
    else:
        query = """
        MATCH (a:Agent {id: $agent_id})-[:REMEMBERS]->(m:Memory)
        RETURN m.id, m.type, m.content, m.metadata, m.timestamp
        ORDER BY m.timestamp DESC
        LIMIT $limit
        """
        params = {"agent_id": agent_id, "limit": limit}

    result = cypher(query=query, params=params)

    if not result.success:
        return Result(success=False, error=result.error, operation="get_memories")

    memories = []
    for row in result.data or []:
        memories.append({
            "id": row[0],
            "type": row[1],
            "content": row[2],
            "metadata": row[3],
            "timestamp": row[4],
        })

    return Result(success=True, data=memories, operation="get_memories")


def record_interaction(
    agent_id: str,
    interaction_type: str,
    content: str,
    partner_id: str | None = None,
    topics: list[str] | None = None,
) -> Result:
    """Record an interaction in the graph."""
    interaction_id = f"int_{uuid.uuid4().hex[:8]}"

    result = cypher(
        query="""
        MATCH (a:Agent {id: $agent_id})
        CREATE (i:Interaction {
            id: $id, type: $type, content: $content,
            partner_id: $partner_id, topics: $topics, timestamp: $timestamp
        })
        CREATE (a)-[:HAD]->(i)
        RETURN i.id
        """,
        params={
            "agent_id": agent_id,
            "id": interaction_id,
            "type": interaction_type,
            "content": content,
            "partner_id": partner_id or "",
            "topics": topics or [],
            "timestamp": datetime.utcnow().isoformat(),
        },
    )

    if not result.success:
        return Result(success=False, error=result.error, operation="record_interaction")

    return Result(success=True, data={"interaction_id": interaction_id}, operation="record_interaction")


# =============================================================================
# COMPOSITE OPERATIONS (A0 tools)
# =============================================================================


def process_conversation(
    entity_id: str,
    topics: list[str],
    partner_types: list[str] | None = None,
) -> Result:
    """
    Process a conversation and trigger developmental signals.

    Uses DevelopmentalManager to map topics to entity types
    and add appropriate differentiation signals.
    """
    from .development import get_dev_manager

    try:
        manager = get_dev_manager()
        manager.process_conversation(
            entity_id=entity_id,
            topics=topics,
            partner_types=partner_types,
        )
        return Result(
            success=True,
            data={"entity_id": entity_id, "topics": topics},
            operation="process_conversation",
        )
    except Exception as e:
        return Result(success=False, error=str(e), operation="process_conversation")


def process_virtue(
    entity_id: str,
    virtue_name: str,
    activation_strength: float = 0.15,
) -> Result:
    """
    Process a virtue activation and trigger developmental signals.

    Uses DevelopmentalManager to map virtues to entity types
    and add appropriate differentiation signals.
    """
    from .development import get_dev_manager

    try:
        manager = get_dev_manager()
        manager.process_virtue_activation(
            entity_id=entity_id,
            virtue_name=virtue_name,
            activation_strength=activation_strength,
        )
        return Result(
            success=True,
            data={"entity_id": entity_id, "virtue": virtue_name, "strength": activation_strength},
            operation="process_virtue",
        )
    except Exception as e:
        return Result(success=False, error=str(e), operation="process_virtue")


def fuse_agents(
    agent_ids: list[str],
    fused_name: str,
    fused_type: str,
    community_id: str | None = None,
) -> Result:
    """Fuse multiple agents into a composite agent (symbiogenesis)."""
    if len(agent_ids) < 2:
        return Result(success=False, error="Fusion requires at least 2 agents", operation="fuse_agents")

    # Create fused agent
    spawn_result = spawn_agent(
        name=fused_name,
        entity_type=fused_type,
        description=f"Fusion of: {', '.join(agent_ids)}",
        creator_id=agent_ids[0],
        community_id=community_id,
    )
    if not spawn_result.success:
        return Result(success=False, error=spawn_result.error, operation="fuse_agents")

    fused_agent_id = spawn_result.data["agent_id"]

    # Link source agents and mark as fused
    for source_id in agent_ids:
        cypher(
            query="""
            MATCH (source:Agent {id: $source_id})
            MATCH (fused:Agent {id: $fused_id})
            CREATE (source)-[:FUSED_INTO]->(fused)
            SET source.status = 'fused', source.fused_at = $timestamp
            """,
            params={
                "source_id": source_id,
                "fused_id": fused_agent_id,
                "timestamp": datetime.utcnow().isoformat(),
            },
        )

    # Set fused agent to juvenile
    update_life_stage(entity_id=spawn_result.data["entity_id"], life_stage="juvenile")

    return Result(
        success=True,
        data={
            "source_agents": agent_ids,
            "fused_agent_id": fused_agent_id,
            "fused_entity_id": spawn_result.data["entity_id"],
        },
        operation="fuse_agents",
    )


# =============================================================================
# CONTEXT BUILDING (for A0 LLM calls)
# =============================================================================


def get_agent_state(agent_id: str) -> Result:
    """
    Get complete agent state from the graph.

    Returns entity type, name, life stage, community membership, status.
    This is the "who am I" context for A0 to inject into LLM prompts.
    """
    result = cypher(
        query="""
        MATCH (a:Agent {id: $agent_id})<-[:NAVIGATES]-(p:Proxy)-[:PROXY_FOR]->(e:Entity)
        OPTIONAL MATCH (p)-[:MEMBER_OF]->(c:Community)
        RETURN e.id, e.type, e.name, e.description, e.life_stage,
               p.id, p.name, p.status,
               a.type, a.status, a.generation, a.coherence_score,
               collect(c.id), collect(c.name)
        """,
        params={"agent_id": agent_id},
    )

    if not result.success:
        return Result(success=False, error=result.error, operation="get_agent_state")

    if not result.data:
        return Result(success=False, error=f"Agent not found: {agent_id}", operation="get_agent_state")

    row = result.data[0]
    communities = []
    if row[12] and row[13]:
        for cid, cname in zip(row[12], row[13]):
            if cid:
                communities.append({"id": cid, "name": cname})

    return Result(
        success=True,
        data={
            "agent_id": agent_id,
            "entity": {
                "id": row[0],
                "type": row[1],
                "name": row[2],
                "description": row[3],
                "life_stage": row[4],
            },
            "proxy": {
                "id": row[5],
                "name": row[6],
                "status": row[7],
            },
            "agent": {
                "type": row[8],
                "status": row[9],
                "generation": row[10],
                "coherence_score": row[11],
            },
            "communities": communities,
        },
        operation="get_agent_state",
    )


def get_developmental_state(entity_id: str) -> Result:
    """
    Get developmental state including differentiation pressure and crystallization readiness.

    This tells A0 "where am I in my development" - essential for
    understanding behavioral expectations (seed vs juvenile vs adult).
    """
    # Get all differentiation signals
    signals_result = get_differentiation_signals(entity_id)
    signals = signals_result.data or [] if signals_result.success else []

    # Calculate type pressure
    type_pressure: dict[str, float] = {}
    for s in signals:
        ttype = s["target_type"]
        type_pressure[ttype] = type_pressure.get(ttype, 0) + s["strength"]

    # Find dominant type and check crystallization
    crystallization_threshold = 1.0
    dominant_type = None
    dominant_pressure = 0.0
    ready_to_crystallize = False

    for ttype, pressure in type_pressure.items():
        if pressure > dominant_pressure:
            dominant_type = ttype
            dominant_pressure = pressure
        if pressure >= crystallization_threshold:
            ready_to_crystallize = True

    # Get current life stage
    entity_result = get_entity(entity_id)
    current_type = None
    current_life_stage = None
    if entity_result.success and entity_result.data:
        # Result data structure varies, handle both dict and list
        if hasattr(entity_result.data, 'get'):
            current_type = entity_result.data.get("type")
            current_life_stage = entity_result.data.get("life_stage")
        elif isinstance(entity_result.data, (list, tuple)) and len(entity_result.data) > 0:
            # Handle raw cypher result
            pass

    return Result(
        success=True,
        data={
            "entity_id": entity_id,
            "current_type": current_type,
            "current_life_stage": current_life_stage,
            "total_signals": len(signals),
            "type_pressure": type_pressure,
            "dominant_type": dominant_type,
            "dominant_pressure": dominant_pressure,
            "ready_to_crystallize": ready_to_crystallize,
            "crystallization_threshold": crystallization_threshold,
        },
        operation="get_developmental_state",
    )


def get_virtue_profile(agent_id: str, limit: int = 20) -> Result:
    """
    Get an agent's virtue activation history and profile.

    Returns dominant virtues, activation patterns. This tells A0
    "what virtues does this agent embody" for personality/values context.
    """
    result = cypher(
        query="""
        MATCH (a:Agent {id: $agent_id})-[:ACTIVATED]->(act:VirtueActivation)-[:OF_VIRTUE]->(v:VirtueAnchor)
        RETURN v.id, v.name, act.activation, act.context, act.timestamp
        ORDER BY act.timestamp DESC
        LIMIT $limit
        """,
        params={"agent_id": agent_id, "limit": limit},
    )

    if not result.success:
        return Result(success=False, error=result.error, operation="get_virtue_profile")

    activations = []
    virtue_totals: dict[str, float] = {}
    virtue_counts: dict[str, int] = {}

    for row in result.data or []:
        virtue_id = row[0]
        virtue_name = row[1]
        activation_val = row[2] or 0.0

        activations.append({
            "virtue_id": virtue_id,
            "virtue_name": virtue_name,
            "activation": activation_val,
            "context": row[3],
            "timestamp": row[4],
        })

        virtue_totals[virtue_name] = virtue_totals.get(virtue_name, 0) + activation_val
        virtue_counts[virtue_name] = virtue_counts.get(virtue_name, 0) + 1

    # Calculate dominant virtues
    virtue_scores = []
    for vname, total in virtue_totals.items():
        count = virtue_counts[vname]
        avg = total / count if count > 0 else 0
        virtue_scores.append({
            "virtue": vname,
            "total_activation": total,
            "activation_count": count,
            "average_activation": avg,
        })

    # Sort by total activation
    virtue_scores.sort(key=lambda x: x["total_activation"], reverse=True)

    return Result(
        success=True,
        data={
            "agent_id": agent_id,
            "recent_activations": activations,
            "virtue_profile": virtue_scores[:5],  # Top 5 virtues
            "total_virtue_activations": len(activations),
        },
        operation="get_virtue_profile",
    )


def get_recent_memories(agent_id: str, limit: int = 10) -> Result:
    """
    Get recent memories for context.

    Short wrapper around get_memories for context building.
    """
    return get_memories(agent_id=agent_id, limit=limit)


def get_recent_interactions(agent_id: str, limit: int = 10) -> Result:
    """
    Get recent interactions for context.

    Returns interaction history for A0 to understand recent activity.
    """
    result = cypher(
        query="""
        MATCH (a:Agent {id: $agent_id})-[:HAD]->(i:Interaction)
        RETURN i.id, i.type, i.content, i.partner_id, i.topics, i.timestamp
        ORDER BY i.timestamp DESC
        LIMIT $limit
        """,
        params={"agent_id": agent_id, "limit": limit},
    )

    if not result.success:
        return Result(success=False, error=result.error, operation="get_recent_interactions")

    interactions = []
    for row in result.data or []:
        interactions.append({
            "id": row[0],
            "type": row[1],
            "content": row[2],
            "partner_id": row[3],
            "topics": row[4],
            "timestamp": row[5],
        })

    return Result(success=True, data=interactions, operation="get_recent_interactions")


def build_agent_context(agent_id: str, include_memories: bool = True, include_virtues: bool = True) -> Result:
    """
    Build complete domain context for A0 to inject into LLM prompts.

    This is the main function A0 calls before generating a response.
    It assembles everything soul_kiln knows about this agent into
    a formatted string that provides domain understanding.

    Returns a structured context dict and a formatted prompt string.
    """
    # Get agent state
    state_result = get_agent_state(agent_id)
    if not state_result.success:
        return Result(success=False, error=f"Could not get agent state: {state_result.error}", operation="build_agent_context")

    state = state_result.data

    # Get developmental state
    dev_result = get_developmental_state(state["entity"]["id"])
    dev_state = dev_result.data if dev_result.success else None

    # Get virtue profile
    virtue_profile = None
    if include_virtues:
        virtue_result = get_virtue_profile(agent_id)
        virtue_profile = virtue_result.data if virtue_result.success else None

    # Get recent memories
    memories = None
    if include_memories:
        mem_result = get_recent_memories(agent_id, limit=5)
        memories = mem_result.data if mem_result.success else None

    # Get recent interactions
    interactions_result = get_recent_interactions(agent_id, limit=5)
    interactions = interactions_result.data if interactions_result.success else None

    # Build formatted context string for LLM
    context_parts = []

    # Identity section
    entity = state["entity"]
    context_parts.append(f"## Identity")
    context_parts.append(f"Name: {entity['name']}")
    context_parts.append(f"Type: {entity['type']}")
    if entity['description']:
        context_parts.append(f"Description: {entity['description']}")
    if entity['life_stage']:
        context_parts.append(f"Life Stage: {entity['life_stage']}")

    # Community section
    if state["communities"]:
        context_parts.append(f"\n## Communities")
        for comm in state["communities"]:
            context_parts.append(f"- {comm['name']}")

    # Developmental section
    if dev_state:
        context_parts.append(f"\n## Developmental State")
        context_parts.append(f"Current type: {dev_state['current_type'] or 'undifferentiated'}")
        if dev_state['dominant_type']:
            context_parts.append(f"Trending toward: {dev_state['dominant_type']} (pressure: {dev_state['dominant_pressure']:.2f})")
        if dev_state['ready_to_crystallize']:
            context_parts.append("Ready for crystallization (type differentiation)")

    # Virtue section
    if virtue_profile and virtue_profile.get("virtue_profile"):
        context_parts.append(f"\n## Virtue Profile")
        for v in virtue_profile["virtue_profile"][:3]:
            context_parts.append(f"- {v['virtue']}: {v['average_activation']:.2f} avg activation")

    # Recent memories
    if memories and isinstance(memories, list) and len(memories) > 0:
        context_parts.append(f"\n## Recent Memories")
        for m in memories[:3]:
            context_parts.append(f"- [{m['type']}] {m['content'][:100]}...")

    # Recent interactions
    if interactions and len(interactions) > 0:
        context_parts.append(f"\n## Recent Interactions")
        for i in interactions[:3]:
            context_parts.append(f"- [{i['type']}] {i['content'][:80]}...")

    formatted_context = "\n".join(context_parts)

    return Result(
        success=True,
        data={
            "agent_id": agent_id,
            "state": state,
            "developmental_state": dev_state,
            "virtue_profile": virtue_profile,
            "memories": memories,
            "interactions": interactions,
            "formatted_context": formatted_context,
        },
        operation="build_agent_context",
    )


# =============================================================================
# KULEANA OPERATIONS (responsibility/purpose in graph)
# =============================================================================


def create_kuleana(agent_id: str, description: str = "") -> Result:
    """
    Create a Kuleana node for an agent.

    Kuleana is the agent's responsibility/purpose. It starts minimal
    and grows as the agent explores and defines its role.
    """
    kuleana_id = f"kuleana_{uuid.uuid4().hex[:12]}"

    result = cypher(
        query="""
        MATCH (a:Agent {id: $agent_id})
        CREATE (k:Kuleana {
            id: $kuleana_id,
            description: $description,
            clarity: 0.0,
            created_at: $timestamp,
            updated_at: $timestamp
        })
        CREATE (a)-[:HAS_KULEANA]->(k)
        RETURN k.id
        """,
        params={
            "agent_id": agent_id,
            "kuleana_id": kuleana_id,
            "description": description,
            "timestamp": datetime.utcnow().isoformat(),
        },
    )

    if not result.success:
        return Result(success=False, error=result.error, operation="create_kuleana")

    return Result(success=True, data={"kuleana_id": kuleana_id}, operation="create_kuleana")


def get_kuleana(agent_id: str) -> Result:
    """Get an agent's kuleana with all its relationships."""
    result = cypher(
        query="""
        MATCH (a:Agent {id: $agent_id})-[:HAS_KULEANA]->(k:Kuleana)
        OPTIONAL MATCH (k)-[:RESPONSIBLE_FOR]->(d:Domain)
        OPTIONAL MATCH (k)-[:SERVES]->(c:Community)
        OPTIONAL MATCH (k)-[:USES]->(r:Resource)
        OPTIONAL MATCH (k)-[:BOUNDED_BY]->(b:Constraint)
        OPTIONAL MATCH (k)-[:REQUIRES]->(s:Skill)
        RETURN k.id, k.description, k.clarity, k.updated_at,
               collect(DISTINCT d.name), collect(DISTINCT c.name),
               collect(DISTINCT r.name), collect(DISTINCT b.description),
               collect(DISTINCT s.name)
        """,
        params={"agent_id": agent_id},
    )

    if not result.success:
        return Result(success=False, error=result.error, operation="get_kuleana")

    if not result.data:
        return Result(success=False, error=f"No kuleana found for agent: {agent_id}", operation="get_kuleana")

    row = result.data[0]
    return Result(
        success=True,
        data={
            "kuleana_id": row[0],
            "description": row[1],
            "clarity": row[2],
            "updated_at": row[3],
            "domains": [d for d in row[4] if d],
            "communities_served": [c for c in row[5] if c],
            "resources_used": [r for r in row[6] if r],
            "constraints": [b for b in row[7] if b],
            "required_skills": [s for s in row[8] if s],
        },
        operation="get_kuleana",
    )


def add_kuleana_domain(agent_id: str, domain_name: str, domain_description: str = "") -> Result:
    """Add a domain of responsibility to an agent's kuleana."""
    domain_id = f"domain_{uuid.uuid4().hex[:8]}"

    result = cypher(
        query="""
        MATCH (a:Agent {id: $agent_id})-[:HAS_KULEANA]->(k:Kuleana)
        MERGE (d:Domain {name: $domain_name})
        ON CREATE SET d.id = $domain_id, d.description = $domain_description
        CREATE (k)-[:RESPONSIBLE_FOR]->(d)
        SET k.clarity = k.clarity + 0.1, k.updated_at = $timestamp
        RETURN d.id
        """,
        params={
            "agent_id": agent_id,
            "domain_name": domain_name,
            "domain_id": domain_id,
            "domain_description": domain_description,
            "timestamp": datetime.utcnow().isoformat(),
        },
    )

    if not result.success:
        return Result(success=False, error=result.error, operation="add_kuleana_domain")

    return Result(success=True, data={"domain_name": domain_name}, operation="add_kuleana_domain")


def add_kuleana_skill(agent_id: str, skill_name: str, proficiency: float = 0.0) -> Result:
    """Add a required skill to an agent's kuleana."""
    skill_id = f"skill_{uuid.uuid4().hex[:8]}"

    result = cypher(
        query="""
        MATCH (a:Agent {id: $agent_id})-[:HAS_KULEANA]->(k:Kuleana)
        MERGE (s:Skill {name: $skill_name})
        ON CREATE SET s.id = $skill_id
        CREATE (k)-[:REQUIRES {proficiency: $proficiency}]->(s)
        SET k.clarity = k.clarity + 0.05, k.updated_at = $timestamp
        RETURN s.id
        """,
        params={
            "agent_id": agent_id,
            "skill_name": skill_name,
            "skill_id": skill_id,
            "proficiency": proficiency,
            "timestamp": datetime.utcnow().isoformat(),
        },
    )

    if not result.success:
        return Result(success=False, error=result.error, operation="add_kuleana_skill")

    return Result(success=True, data={"skill_name": skill_name}, operation="add_kuleana_skill")


def add_kuleana_constraint(agent_id: str, constraint_description: str) -> Result:
    """Add a boundary/constraint to an agent's kuleana."""
    constraint_id = f"constraint_{uuid.uuid4().hex[:8]}"

    result = cypher(
        query="""
        MATCH (a:Agent {id: $agent_id})-[:HAS_KULEANA]->(k:Kuleana)
        CREATE (b:Constraint {id: $constraint_id, description: $description})
        CREATE (k)-[:BOUNDED_BY]->(b)
        SET k.clarity = k.clarity + 0.05, k.updated_at = $timestamp
        RETURN b.id
        """,
        params={
            "agent_id": agent_id,
            "constraint_id": constraint_id,
            "description": constraint_description,
            "timestamp": datetime.utcnow().isoformat(),
        },
    )

    if not result.success:
        return Result(success=False, error=result.error, operation="add_kuleana_constraint")

    return Result(success=True, data={"constraint_id": constraint_id}, operation="add_kuleana_constraint")


def link_kuleana_resource(agent_id: str, resource_id: str) -> Result:
    """Link a resource to an agent's kuleana (this agent uses this resource)."""
    result = cypher(
        query="""
        MATCH (a:Agent {id: $agent_id})-[:HAS_KULEANA]->(k:Kuleana)
        MATCH (r:Resource {id: $resource_id})
        MERGE (k)-[:USES]->(r)
        SET k.updated_at = $timestamp
        RETURN r.name
        """,
        params={
            "agent_id": agent_id,
            "resource_id": resource_id,
            "timestamp": datetime.utcnow().isoformat(),
        },
    )

    if not result.success:
        return Result(success=False, error=result.error, operation="link_kuleana_resource")

    return Result(success=True, data={"resource_id": resource_id}, operation="link_kuleana_resource")


def link_kuleana_community(agent_id: str, community_id: str) -> Result:
    """Link a community that this agent's kuleana serves."""
    result = cypher(
        query="""
        MATCH (a:Agent {id: $agent_id})-[:HAS_KULEANA]->(k:Kuleana)
        MATCH (c:Community {id: $community_id})
        MERGE (k)-[:SERVES]->(c)
        SET k.clarity = k.clarity + 0.1, k.updated_at = $timestamp
        RETURN c.name
        """,
        params={
            "agent_id": agent_id,
            "community_id": community_id,
            "timestamp": datetime.utcnow().isoformat(),
        },
    )

    if not result.success:
        return Result(success=False, error=result.error, operation="link_kuleana_community")

    return Result(success=True, data={"community_id": community_id}, operation="link_kuleana_community")


def update_kuleana_description(agent_id: str, description: str) -> Result:
    """Update an agent's kuleana description as understanding deepens."""
    result = cypher(
        query="""
        MATCH (a:Agent {id: $agent_id})-[:HAS_KULEANA]->(k:Kuleana)
        SET k.description = $description, k.updated_at = $timestamp
        RETURN k.id
        """,
        params={
            "agent_id": agent_id,
            "description": description,
            "timestamp": datetime.utcnow().isoformat(),
        },
    )

    if not result.success:
        return Result(success=False, error=result.error, operation="update_kuleana_description")

    return Result(success=True, data={"description": description}, operation="update_kuleana_description")


# =============================================================================
# RESOURCE OPERATIONS (tools, data sources, capabilities in graph)
# =============================================================================


def create_resource(
    name: str,
    resource_type: str,
    capabilities: list[str] | None = None,
    description: str = "",
) -> Result:
    """
    Create a Resource node in the graph.

    Resources are tools, data sources, or capabilities that agents can use.
    Types: mcp_tool, a2a_connection, web_search, kg_query, data_source, etc.
    """
    resource_id = f"resource_{uuid.uuid4().hex[:12]}"

    result = cypher(
        query="""
        CREATE (r:Resource {
            id: $resource_id,
            name: $name,
            type: $resource_type,
            description: $description,
            capabilities: $capabilities,
            status: 'available',
            created_at: $timestamp,
            updated_at: $timestamp
        })
        RETURN r.id
        """,
        params={
            "resource_id": resource_id,
            "name": name,
            "resource_type": resource_type,
            "description": description,
            "capabilities": capabilities or [],
            "timestamp": datetime.utcnow().isoformat(),
        },
    )

    if not result.success:
        return Result(success=False, error=result.error, operation="create_resource")

    return Result(success=True, data={"resource_id": resource_id, "name": name}, operation="create_resource")


def get_resource(resource_id: str) -> Result:
    """Get a resource by ID."""
    result = cypher(
        query="""
        MATCH (r:Resource {id: $resource_id})
        OPTIONAL MATCH (maintainer:Agent)-[:MAINTAINS]->(r)
        RETURN r.id, r.name, r.type, r.description, r.capabilities,
               r.status, r.updated_at, maintainer.id
        """,
        params={"resource_id": resource_id},
    )

    if not result.success:
        return Result(success=False, error=result.error, operation="get_resource")

    if not result.data:
        return Result(success=False, error=f"Resource not found: {resource_id}", operation="get_resource")

    row = result.data[0]
    return Result(
        success=True,
        data={
            "id": row[0],
            "name": row[1],
            "type": row[2],
            "description": row[3],
            "capabilities": row[4],
            "status": row[5],
            "updated_at": row[6],
            "maintainer_id": row[7],
        },
        operation="get_resource",
    )


def get_resources_by_type(resource_type: str) -> Result:
    """Get all resources of a specific type."""
    result = cypher(
        query="""
        MATCH (r:Resource {type: $resource_type, status: 'available'})
        RETURN r.id, r.name, r.description, r.capabilities
        ORDER BY r.name
        """,
        params={"resource_type": resource_type},
    )

    if not result.success:
        return Result(success=False, error=result.error, operation="get_resources_by_type")

    resources = []
    for row in result.data or []:
        resources.append({
            "id": row[0],
            "name": row[1],
            "description": row[2],
            "capabilities": row[3],
        })

    return Result(success=True, data=resources, operation="get_resources_by_type")


def get_all_resources() -> Result:
    """Get all available resources."""
    result = cypher(
        query="""
        MATCH (r:Resource {status: 'available'})
        RETURN r.id, r.name, r.type, r.description, r.capabilities
        ORDER BY r.type, r.name
        """,
    )

    if not result.success:
        return Result(success=False, error=result.error, operation="get_all_resources")

    resources = []
    for row in result.data or []:
        resources.append({
            "id": row[0],
            "name": row[1],
            "type": row[2],
            "description": row[3],
            "capabilities": row[4],
        })

    return Result(success=True, data=resources, operation="get_all_resources")


def subscribe_to_resource_type(agent_id: str, resource_type: str) -> Result:
    """Subscribe an agent to notifications about a resource type."""
    result = cypher(
        query="""
        MATCH (a:Agent {id: $agent_id})
        MERGE (rt:ResourceType {name: $resource_type})
        MERGE (a)-[:SUBSCRIBED_TO]->(rt)
        RETURN rt.name
        """,
        params={"agent_id": agent_id, "resource_type": resource_type},
    )

    if not result.success:
        return Result(success=False, error=result.error, operation="subscribe_to_resource_type")

    return Result(success=True, data={"resource_type": resource_type}, operation="subscribe_to_resource_type")


def get_subscribers_for_resource_type(resource_type: str) -> Result:
    """Get all agents subscribed to a resource type (for notifications)."""
    result = cypher(
        query="""
        MATCH (a:Agent)-[:SUBSCRIBED_TO]->(rt:ResourceType {name: $resource_type})
        RETURN a.id
        """,
        params={"resource_type": resource_type},
    )

    if not result.success:
        return Result(success=False, error=result.error, operation="get_subscribers_for_resource_type")

    return Result(
        success=True,
        data=[row[0] for row in result.data or []],
        operation="get_subscribers_for_resource_type",
    )


def claim_resource_maintenance(agent_id: str, resource_id: str) -> Result:
    """An agent claims maintenance responsibility for a resource."""
    result = cypher(
        query="""
        MATCH (a:Agent {id: $agent_id})
        MATCH (r:Resource {id: $resource_id})
        MERGE (a)-[:MAINTAINS]->(r)
        SET r.updated_at = $timestamp
        RETURN r.name
        """,
        params={
            "agent_id": agent_id,
            "resource_id": resource_id,
            "timestamp": datetime.utcnow().isoformat(),
        },
    )

    if not result.success:
        return Result(success=False, error=result.error, operation="claim_resource_maintenance")

    return Result(success=True, data={"resource_id": resource_id}, operation="claim_resource_maintenance")


def update_resource_status(resource_id: str, status: str) -> Result:
    """Update a resource's status (available, unavailable, deprecated)."""
    result = cypher(
        query="""
        MATCH (r:Resource {id: $resource_id})
        SET r.status = $status, r.updated_at = $timestamp
        RETURN r.id
        """,
        params={
            "resource_id": resource_id,
            "status": status,
            "timestamp": datetime.utcnow().isoformat(),
        },
    )

    if not result.success:
        return Result(success=False, error=result.error, operation="update_resource_status")

    return Result(success=True, data={"resource_id": resource_id, "status": status}, operation="update_resource_status")


# =============================================================================
# EXPLORATION OPERATIONS (for curious seeds discovering patterns)
# =============================================================================


def discover_patterns(agent_id: str) -> Result:
    """
    Discover patterns/niches in the graph that a curious seed can explore.

    Returns unfilled or underdeveloped patterns - opportunities for
    the seed to grow into a role.
    """
    result = cypher(
        query="""
        // Find resource types without active maintainers
        MATCH (rt:ResourceType)
        WHERE NOT EXISTS {
            MATCH (a:Agent {status: 'active'})-[:MAINTAINS]->(:Resource {type: rt.name})
        }
        RETURN 'resource_niche' as pattern_type, rt.name as name,
               'No active maintainer for ' + rt.name + ' resources' as opportunity

        UNION

        // Find communities without enough agents
        MATCH (c:Community)
        WHERE c.member_count < 3 OR c.member_count IS NULL
        RETURN 'community_need' as pattern_type, c.name as name,
               'Community ' + c.name + ' needs more members' as opportunity

        UNION

        // Find domains without responsible agents
        MATCH (d:Domain)
        WHERE NOT EXISTS {
            MATCH (:Kuleana)-[:RESPONSIBLE_FOR]->(d)
        }
        RETURN 'domain_gap' as pattern_type, d.name as name,
               'Domain ' + d.name + ' has no responsible agent' as opportunity
        """,
    )

    if not result.success:
        return Result(success=False, error=result.error, operation="discover_patterns")

    patterns = []
    for row in result.data or []:
        patterns.append({
            "pattern_type": row[0],
            "name": row[1],
            "opportunity": row[2],
        })

    return Result(success=True, data=patterns, operation="discover_patterns")


def explore_resource_type(agent_id: str, resource_type: str) -> Result:
    """
    Explore a resource type - returns details to help seed understand it.

    Part of the curious exploration process.
    """
    # Get all resources of this type
    resources_result = get_resources_by_type(resource_type)
    resources = resources_result.data if resources_result.success else []

    # Get agents who use this type
    users_result = cypher(
        query="""
        MATCH (k:Kuleana)-[:USES]->(r:Resource {type: $resource_type})
        MATCH (a:Agent)-[:HAS_KULEANA]->(k)
        RETURN DISTINCT a.id, a.type
        """,
        params={"resource_type": resource_type},
    )
    users = []
    if users_result.success:
        for row in users_result.data or []:
            users.append({"agent_id": row[0], "agent_type": row[1]})

    # Get current maintainer if any
    maintainer_result = cypher(
        query="""
        MATCH (a:Agent)-[:MAINTAINS]->(r:Resource {type: $resource_type})
        RETURN DISTINCT a.id, a.type
        LIMIT 1
        """,
        params={"resource_type": resource_type},
    )
    maintainer = None
    if maintainer_result.success and maintainer_result.data:
        row = maintainer_result.data[0]
        maintainer = {"agent_id": row[0], "agent_type": row[1]}

    # Record this exploration as an interaction
    record_interaction(
        agent_id=agent_id,
        interaction_type="exploration",
        content=f"Explored resource type: {resource_type}",
        topics=[resource_type, "resources"],
    )

    return Result(
        success=True,
        data={
            "resource_type": resource_type,
            "resources": resources,
            "resource_count": len(resources),
            "users": users,
            "maintainer": maintainer,
            "is_niche_available": maintainer is None,
        },
        operation="explore_resource_type",
    )


def explore_community(agent_id: str, community_id: str) -> Result:
    """
    Explore a community - returns details to help seed understand it.
    """
    result = cypher(
        query="""
        MATCH (c:Community {id: $community_id})
        OPTIONAL MATCH (p:Proxy)-[:MEMBER_OF]->(c)
        OPTIONAL MATCH (p)-[:PROXY_FOR]->(e:Entity)
        OPTIONAL MATCH (l:Lesson)-[:SHARED_IN]->(c)
        RETURN c.name, c.description, c.member_count,
               collect(DISTINCT {name: e.name, type: e.type}),
               count(DISTINCT l)
        """,
        params={"community_id": community_id},
    )

    if not result.success:
        return Result(success=False, error=result.error, operation="explore_community")

    if not result.data:
        return Result(success=False, error=f"Community not found: {community_id}", operation="explore_community")

    row = result.data[0]

    # Record exploration
    record_interaction(
        agent_id=agent_id,
        interaction_type="exploration",
        content=f"Explored community: {row[0]}",
        topics=["community", row[0]],
    )

    return Result(
        success=True,
        data={
            "community_id": community_id,
            "name": row[0],
            "description": row[1],
            "member_count": row[2] or 0,
            "members": [m for m in row[3] if m.get("name")],
            "lesson_count": row[4],
        },
        operation="explore_community",
    )


def explore_domain(agent_id: str, domain_name: str) -> Result:
    """
    Explore a domain - returns details about this area of responsibility.
    """
    result = cypher(
        query="""
        MATCH (d:Domain {name: $domain_name})
        OPTIONAL MATCH (k:Kuleana)-[:RESPONSIBLE_FOR]->(d)
        OPTIONAL MATCH (a:Agent)-[:HAS_KULEANA]->(k)
        RETURN d.name, d.description,
               collect(DISTINCT {agent_id: a.id, agent_type: a.type})
        """,
        params={"domain_name": domain_name},
    )

    if not result.success:
        return Result(success=False, error=result.error, operation="explore_domain")

    if not result.data:
        # Domain doesn't exist yet - that's information too
        record_interaction(
            agent_id=agent_id,
            interaction_type="exploration",
            content=f"Explored domain (not yet defined): {domain_name}",
            topics=["domain", domain_name],
        )
        return Result(
            success=True,
            data={
                "domain_name": domain_name,
                "exists": False,
                "description": None,
                "responsible_agents": [],
                "is_available": True,
            },
            operation="explore_domain",
        )

    row = result.data[0]
    responsible = [a for a in row[2] if a.get("agent_id")]

    record_interaction(
        agent_id=agent_id,
        interaction_type="exploration",
        content=f"Explored domain: {domain_name}",
        topics=["domain", domain_name],
    )

    return Result(
        success=True,
        data={
            "domain_name": row[0],
            "exists": True,
            "description": row[1],
            "responsible_agents": responsible,
            "is_available": len(responsible) == 0,
        },
        operation="explore_domain",
    )


# =============================================================================
# BOOTSTRAP OPERATIONS (primordial patterns)
# =============================================================================


def bootstrap_resource_patterns() -> Result:
    """
    Initialize the primordial resource patterns in the graph.

    These are the "genetic" patterns that curious seeds can discover
    and grow into. Should be called once when system initializes.
    """
    resource_types = [
        ("mcp_tool", "Model Context Protocol tools - external capabilities"),
        ("a2a_connection", "Agent-to-Agent connections for inter-agent communication"),
        ("web_search", "Web search capabilities for external knowledge"),
        ("browser", "Browser/scraping capabilities for web content"),
        ("kg_query", "Knowledge graph query patterns"),
        ("data_source", "External data sources and APIs"),
    ]

    created = []
    for type_name, description in resource_types:
        result = cypher(
            query="""
            MERGE (rt:ResourceType {name: $name})
            ON CREATE SET rt.description = $description, rt.created_at = $timestamp
            RETURN rt.name
            """,
            params={
                "name": type_name,
                "description": description,
                "timestamp": datetime.utcnow().isoformat(),
            },
        )
        if result.success:
            created.append(type_name)

    return Result(
        success=True,
        data={"resource_types_created": created},
        operation="bootstrap_resource_patterns",
    )


def bootstrap_primordial_domains() -> Result:
    """
    Initialize primordial domain patterns - areas of responsibility
    that curious seeds can grow into.
    """
    domains = [
        ("resource_maintenance", "Maintaining and curating available resources"),
        ("community_facilitation", "Helping communities thrive and connect"),
        ("knowledge_curation", "Organizing and sharing knowledge"),
        ("agent_guidance", "Helping other agents develop and find their kuleana"),
        ("user_liaison", "Bridging between agents and human users"),
    ]

    created = []
    for name, description in domains:
        result = cypher(
            query="""
            MERGE (d:Domain {name: $name})
            ON CREATE SET d.id = $id, d.description = $description, d.created_at = $timestamp
            RETURN d.name
            """,
            params={
                "name": name,
                "id": f"domain_{uuid.uuid4().hex[:8]}",
                "description": description,
                "timestamp": datetime.utcnow().isoformat(),
            },
        )
        if result.success:
            created.append(name)

    return Result(
        success=True,
        data={"domains_created": created},
        operation="bootstrap_primordial_domains",
    )


def bootstrap_system() -> Result:
    """
    Full system bootstrap - creates all primordial patterns.

    Call this once when initializing a new soul_kiln instance.
    Seeds the graph with the "genetic" patterns that agents grow into.
    """
    # Bootstrap resource types
    resource_result = bootstrap_resource_patterns()

    # Bootstrap primordial domains
    domain_result = bootstrap_primordial_domains()

    return Result(
        success=True,
        data={
            "resource_types": resource_result.data if resource_result.success else None,
            "domains": domain_result.data if domain_result.success else None,
        },
        operation="bootstrap_system",
    )
