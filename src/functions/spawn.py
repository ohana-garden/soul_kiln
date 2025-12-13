"""Agent spawning functions with tier-aware connections."""
import uuid
import random
from ..graph.queries import create_node, create_edge
from ..graph.client import get_client
from ..virtues.tiers import is_foundation


def spawn_agent(
    agent_type: str = "candidate",
    parent_id: str = None,
    generation: int = 0
) -> str:
    """
    Create a new agent node with tier-aware virtue connections.

    Agents are entities that evolve through the kiln process.
    Each agent has connections to virtue anchors that define
    its moral topology.

    Foundation virtues (Trustworthiness) get stronger initial
    connections, as trust is the foundation everything else
    stands on.

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
        "activation": 0.5,
        "warnings_count": 0,
        "growth_score": 0.0,
        "previous_capture_rate": 0.0
    })

    # Connect to parent if exists
    if parent_id:
        create_edge(parent_id, agent_id, "SPAWNED")

    # Connect to all virtue anchors with tier-aware weights
    client = get_client()
    virtues = client.query("MATCH (v:VirtueAnchor) RETURN v.id, v.tier")

    for row in virtues:
        v_id = row[0]
        tier = row[1] if len(row) > 1 else "aspirational"

        # Foundation virtues get stronger initial connection
        # as trust is the precondition for everything else
        if tier == "foundation" or is_foundation(v_id):
            weight = random.uniform(0.5, 0.8)
        else:
            weight = random.uniform(0.2, 0.6)

        create_edge(agent_id, v_id, "SEEKS", {"weight": weight})

    return agent_id


def spawn_from_parent(parent_id: str, generation: int, mutation_rate: float = 0.1) -> str:
    """
    Spawn an agent that inherits topology from parent.

    Foundation virtue connections are protected from excessive
    mutation to maintain trust as the foundation.

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
        "activation": 0.5,
        "warnings_count": 0,
        "growth_score": 0.0,
        "previous_capture_rate": 0.0
    })

    # Record lineage
    create_edge(parent_id, child_id, "SPAWNED")

    # Copy parent's virtue connections with possible mutations
    parent_edges = client.query(
        """
        MATCH (p:Agent {id: $id})-[r:SEEKS]->(v:VirtueAnchor)
        RETURN v.id, r.weight, v.tier
        """,
        {"id": parent_id}
    )

    for row in parent_edges:
        v_id = row[0]
        weight = row[1]
        tier = row[2] if len(row) > 2 else "aspirational"

        # Apply mutation - but protect foundation virtues more
        if random.random() < mutation_rate:
            if tier == "foundation":
                # Smaller mutations for foundation, and bias upward
                mutation = random.gauss(0.02, 0.05)  # Small, slight positive bias
                weight = max(0.4, min(1.0, weight + mutation))  # Higher minimum
            else:
                # Normal mutation for aspirational virtues
                mutation = random.gauss(0, 0.1)
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
        List of child agent details
    """
    client = get_client()
    result = client.query(
        """
        MATCH (parent {id: $id})-[:SPAWNED]->(child)
        RETURN child.id, child.generation, child.coherence_score, child.is_growing
        """,
        {"id": agent_id}
    )
    return [
        {
            "id": row[0],
            "generation": row[1],
            "coherence_score": row[2],
            "is_growing": row[3] if len(row) > 3 else None
        }
        for row in result
    ]


def spawn_with_topology(
    topology: dict,
    parent_id: str = None,
    generation: int = 0
) -> str:
    """
    Spawn an agent with a specific topology.

    Useful for testing or creating agents with specific characteristics.

    Args:
        topology: dict mapping virtue_id to weight
        parent_id: Optional parent agent ID
        generation: Generation number

    Returns:
        ID of the newly created agent
    """
    agent_id = f"agent_{uuid.uuid4().hex[:8]}"

    create_node("Agent", {
        "id": agent_id,
        "type": "candidate",
        "generation": generation,
        "coherence_score": None,
        "status": "active",
        "activation": 0.5,
        "warnings_count": 0,
        "growth_score": 0.0,
        "previous_capture_rate": 0.0
    })

    if parent_id:
        create_edge(parent_id, agent_id, "SPAWNED")

    # Create connections based on provided topology
    for v_id, weight in topology.items():
        create_edge(agent_id, v_id, "SEEKS", {"weight": weight})

    return agent_id
