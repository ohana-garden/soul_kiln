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
