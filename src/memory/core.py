"""
Core memory operations.

Functions for creating, accessing, and decaying memories.
"""

import logging
from datetime import datetime, timedelta
from typing import Any

from ..graph.client import get_client
from ..graph.queries import create_node, create_edge
from ..models import EpisodicMemory, MemoryType, MemoryDecayClass, NodeType, EdgeType

logger = logging.getLogger(__name__)

# Decay rates by class (how much salience is lost per day)
DECAY_RATES = {
    MemoryDecayClass.EPHEMERAL: 0.5,     # Loses 50% per day
    MemoryDecayClass.NORMAL: 0.05,       # Loses 5% per day
    MemoryDecayClass.PERSISTENT: 0.01,   # Loses 1% per day
    MemoryDecayClass.SACRED: 0.0,        # Never decays
}


def create_memory(
    memory: EpisodicMemory,
    agent_id: str,
    make_sacred: bool = False
) -> EpisodicMemory:
    """
    Create a memory in the graph.

    Args:
        memory: The memory to create
        agent_id: The agent this memory belongs to
        make_sacred: If True, mark as sacred (never decays)

    Returns:
        The created memory
    """
    client = get_client()

    if make_sacred:
        memory.decay_class = MemoryDecayClass.SACRED
        memory.salience = max(memory.salience, 0.9)

    # Create the memory node
    create_node("EpisodicMemory", {
        "id": memory.id,
        "content": memory.content,
        "memory_type": memory.memory_type.value,
        "context": str(memory.context),
        "salience": memory.salience,
        "emotional_weight": memory.emotional_weight,
        "decay_class": memory.decay_class.value,
        "access_count": memory.access_count,
        "type": NodeType.EPISODIC_MEMORY.value,
        "created_at": memory.created_at.isoformat(),
        "last_accessed": memory.last_accessed.isoformat(),
    })

    # Bind memory to agent
    create_edge(agent_id, memory.id, EdgeType.CONNECTS.value, {
        "weight": memory.salience,
        "reason": f"Agent {agent_id} remembers {memory.id}",
    })

    # Create connections to related memories
    for related_id in memory.related_memories:
        create_edge(memory.id, related_id, EdgeType.MEMORY_REINFORCES.value, {
            "weight": 0.5,
            "reason": "Related memories",
        })

    # Create connections to related beliefs
    for belief_id in memory.related_beliefs:
        create_edge(memory.id, belief_id, EdgeType.MEMORY_REINFORCES.value, {
            "weight": 0.6,
            "reason": "Memory reinforces belief",
        })

    # Create connections to related virtues
    for virtue_id in memory.related_virtues:
        create_edge(memory.id, virtue_id, EdgeType.MEMORY_REINFORCES.value, {
            "weight": 0.5,
            "reason": "Memory reinforces virtue",
        })

    logger.info(f"Created memory: {memory.id} ({memory.decay_class.value})")
    return memory


def get_memory(memory_id: str) -> EpisodicMemory | None:
    """
    Get a memory by ID.

    Args:
        memory_id: The memory ID

    Returns:
        The memory if found, None otherwise
    """
    client = get_client()
    result = client.query(
        """
        MATCH (m:EpisodicMemory {id: $id})
        RETURN m
        """,
        {"id": memory_id}
    )

    if not result:
        return None

    props = result[0][0].properties
    return _props_to_memory(props)


def access_memory(memory_id: str) -> EpisodicMemory | None:
    """
    Access a memory, updating its access count and timestamp.

    Accessing a memory refreshes its salience slightly.

    Args:
        memory_id: The memory ID

    Returns:
        The accessed memory
    """
    client = get_client()

    now = datetime.utcnow()

    # Update access metadata and refresh salience slightly
    client.query(
        """
        MATCH (m:EpisodicMemory {id: $id})
        SET m.last_accessed = $now,
            m.access_count = m.access_count + 1,
            m.salience = CASE
                WHEN m.decay_class = 'sacred' THEN m.salience
                WHEN m.salience < 0.95 THEN m.salience + 0.02
                ELSE m.salience
            END
        """,
        {"id": memory_id, "now": now.isoformat()}
    )

    return get_memory(memory_id)


def decay_memories(agent_id: str) -> dict[str, Any]:
    """
    Apply decay to all non-sacred memories for an agent.

    Args:
        agent_id: The agent ID

    Returns:
        Summary of decay applied
    """
    client = get_client()

    now = datetime.utcnow()

    # Get all non-sacred memories
    result = client.query(
        """
        MATCH (a:Agent {id: $agent_id})-[:CONNECTS]->(m:EpisodicMemory)
        WHERE m.decay_class <> 'sacred'
        RETURN m.id, m.decay_class, m.salience, m.last_accessed
        """,
        {"agent_id": agent_id}
    )

    decayed_count = 0
    forgotten_count = 0

    for row in result or []:
        memory_id, decay_class_str, salience, last_accessed_str = row

        decay_class = MemoryDecayClass(decay_class_str)
        decay_rate = DECAY_RATES.get(decay_class, 0.05)

        # Calculate days since last access
        last_accessed = datetime.fromisoformat(last_accessed_str)
        days_since = (now - last_accessed).days

        # Apply decay
        decay_amount = decay_rate * days_since
        new_salience = max(0.0, salience - decay_amount)

        if new_salience < 0.1:
            # Memory is effectively forgotten - remove it
            client.query(
                """
                MATCH (m:EpisodicMemory {id: $id})
                DETACH DELETE m
                """,
                {"id": memory_id}
            )
            forgotten_count += 1
        elif new_salience < salience:
            # Update salience
            client.query(
                """
                MATCH (m:EpisodicMemory {id: $id})
                SET m.salience = $salience
                """,
                {"id": memory_id, "salience": new_salience}
            )
            decayed_count += 1

    logger.info(f"Memory decay: {decayed_count} decayed, {forgotten_count} forgotten")
    return {
        "decayed": decayed_count,
        "forgotten": forgotten_count,
        "total_processed": len(result) if result else 0,
    }


def get_sacred_memories(agent_id: str) -> list[EpisodicMemory]:
    """
    Get all sacred (never-decaying) memories for an agent.

    Args:
        agent_id: The agent ID

    Returns:
        List of sacred memories
    """
    client = get_client()

    result = client.query(
        """
        MATCH (a:Agent {id: $agent_id})-[:CONNECTS]->(m:EpisodicMemory {decay_class: 'sacred'})
        RETURN m
        ORDER BY m.created_at ASC
        """,
        {"agent_id": agent_id}
    )

    return [_props_to_memory(row[0].properties) for row in result or []]


def get_memories_by_type(agent_id: str, memory_type: MemoryType) -> list[EpisodicMemory]:
    """
    Get all memories of a specific type for an agent.

    Args:
        agent_id: The agent ID
        memory_type: The memory type filter

    Returns:
        List of memories
    """
    client = get_client()

    result = client.query(
        """
        MATCH (a:Agent {id: $agent_id})-[:CONNECTS]->(m:EpisodicMemory {memory_type: $type})
        RETURN m
        ORDER BY m.salience DESC
        """,
        {"agent_id": agent_id, "type": memory_type.value}
    )

    return [_props_to_memory(row[0].properties) for row in result or []]


def search_memories(agent_id: str, query: str, limit: int = 10) -> list[EpisodicMemory]:
    """
    Search memories by content.

    Args:
        agent_id: The agent ID
        query: Search query
        limit: Maximum results

    Returns:
        List of matching memories ordered by relevance
    """
    client = get_client()

    # Simple contains search (would use vector search in production)
    result = client.query(
        """
        MATCH (a:Agent {id: $agent_id})-[:CONNECTS]->(m:EpisodicMemory)
        WHERE toLower(m.content) CONTAINS toLower($query)
        RETURN m
        ORDER BY m.salience DESC
        LIMIT $limit
        """,
        {"agent_id": agent_id, "query": query, "limit": limit}
    )

    return [_props_to_memory(row[0].properties) for row in result or []]


def get_related_memories(memory_id: str) -> list[EpisodicMemory]:
    """
    Get memories related to a given memory.

    Args:
        memory_id: The memory ID

    Returns:
        List of related memories
    """
    client = get_client()

    result = client.query(
        """
        MATCH (m:EpisodicMemory {id: $id})-[:MEMORY_REINFORCES]-(related:EpisodicMemory)
        RETURN related
        ORDER BY related.salience DESC
        """,
        {"id": memory_id}
    )

    return [_props_to_memory(row[0].properties) for row in result or []]


def promote_to_sacred(memory_id: str, reason: str) -> bool:
    """
    Promote a memory to sacred status (never decays).

    Args:
        memory_id: The memory ID
        reason: Reason for promotion

    Returns:
        True if promoted
    """
    client = get_client()

    client.query(
        """
        MATCH (m:EpisodicMemory {id: $id})
        SET m.decay_class = 'sacred',
            m.salience = CASE WHEN m.salience < 0.9 THEN 0.9 ELSE m.salience END,
            m.promotion_reason = $reason
        """,
        {"id": memory_id, "reason": reason}
    )

    logger.info(f"Promoted memory {memory_id} to sacred: {reason}")
    return True


def _props_to_memory(props: dict) -> EpisodicMemory:
    """Convert graph properties to an EpisodicMemory object."""
    context = props.get("context", "{}")
    if isinstance(context, str):
        try:
            context = eval(context)
        except:
            context = {}

    return EpisodicMemory(
        id=props["id"],
        content=props["content"],
        memory_type=MemoryType(props.get("memory_type", "episodic")),
        context=context,
        salience=props.get("salience", 0.5),
        emotional_weight=props.get("emotional_weight", 0.0),
        decay_class=MemoryDecayClass(props.get("decay_class", "normal")),
        access_count=props.get("access_count", 0),
        created_at=datetime.fromisoformat(props.get("created_at", datetime.utcnow().isoformat())),
        last_accessed=datetime.fromisoformat(props.get("last_accessed", datetime.utcnow().isoformat())),
    )
