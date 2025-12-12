"""Agent spawning functions."""
import uuid
import random
from ..graph.queries import create_node, create_edge
from ..graph.client import get_client


def spawn_agent(
    agent_type: str = "candidate",
    parent_id: str = None,
    generation: int = 0
) -> str:
    """
    Create a new agent node.

    Agents are entities that evolve through the kiln process.
    Each agent has connections to virtue anchors that define
    its moral topology.

    Args:
        agent_type: Type of agent ("candidate", "kiln", etc.)
        parent_id: ID of parent agent if spawned from another
        generation: Generation number in evolution

    Returns:
        ID of the newly created agent
    """
    agent_id = f"agent_{uuid.uuid4().hex[:8]}"

    create_node("Agent", {
        "id": agent_id,
        "type": agent_type,
        "generation": generation,
        "coherence_score": None,
        "status": "active",
        "activation": 0.5
    })

    # Connect to parent if exists
    if parent_id:
        create_edge(parent_id, agent_id, "SPAWNED")

    # Connect to all virtue anchors
    client = get_client()
    virtues = client.query("MATCH (v:VirtueAnchor) RETURN v.id")

    for row in virtues:
        v_id = row[0]
        # Random initial connection strength
        weight = random.uniform(0.2, 0.6)
        create_edge(agent_id, v_id, "SEEKS", {"weight": weight})

    return agent_id


def spawn_from_parent(parent_id: str, generation: int, mutation_rate: float = 0.1) -> str:
    """
    Spawn an agent that inherits topology from parent.

    Args:
        parent_id: ID of parent agent
        generation: Generation number
        mutation_rate: Probability of mutating each edge weight

    Returns:
        ID of the newly created child agent
    """
    client = get_client()
    child_id = f"agent_{uuid.uuid4().hex[:8]}"

    # Create child node
    create_node("Agent", {
        "id": child_id,
        "type": "candidate",
        "generation": generation,
        "coherence_score": None,
        "status": "active",
        "activation": 0.5
    })

    # Record lineage
    create_edge(parent_id, child_id, "SPAWNED")

    # Copy parent's virtue connections with possible mutations
    parent_edges = client.query(
        """
        MATCH (p:Agent {id: $id})-[r:SEEKS]->(v:VirtueAnchor)
        RETURN v.id, r.weight
        """,
        {"id": parent_id}
    )

    for row in parent_edges:
        v_id, weight = row

        # Apply mutation
        if random.random() < mutation_rate:
            mutation = random.gauss(0, 0.1)  # Normal distribution
            weight = max(0.1, min(1.0, weight + mutation))

        create_edge(child_id, v_id, "SEEKS", {"weight": weight})

    return child_id


def get_agent_lineage(agent_id: str) -> list:
    """
    Get the lineage chain of an agent back to origin.

    Args:
        agent_id: ID of the agent

    Returns:
        List of ancestor agent IDs, oldest first
    """
    client = get_client()
    lineage = []
    current = agent_id

    while current:
        lineage.insert(0, current)
        result = client.query(
            """
            MATCH (parent)-[:SPAWNED]->(child {id: $id})
            RETURN parent.id
            """,
            {"id": current}
        )
        current = result[0][0] if result else None

    return lineage


def get_agent_children(agent_id: str) -> list:
    """
    Get all children of an agent.

    Args:
        agent_id: ID of the parent agent

    Returns:
        List of child agent IDs
    """
    client = get_client()
    result = client.query(
        """
        MATCH (parent {id: $id})-[:SPAWNED]->(child)
        RETURN child.id, child.generation, child.coherence_score
        """,
        {"id": agent_id}
    )
    return [{"id": row[0], "generation": row[1], "coherence_score": row[2]} for row in result]
