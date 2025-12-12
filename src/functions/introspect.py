"""Agent introspection - self-awareness queries."""
from ..graph.client import get_client


def introspect(agent_id: str) -> dict:
    """
    Agent queries its own structure and history.

    Introspection allows an agent to understand its own topology,
    capture history, and lineage.

    Args:
        agent_id: ID of the agent

    Returns:
        dict with comprehensive self-model
    """
    client = get_client()

    # Get connections
    connections = client.query(
        """
        MATCH (me:Agent {id: $id})-[r]->(n)
        RETURN type(r) as rel, labels(n) as labels, n.id as id, r.weight as weight
        """,
        {"id": agent_id}
    )

    # Get virtue capture history
    captures = client.query(
        """
        MATCH (me:Agent {id: $id})-[:CAPTURED_BY]->(v:VirtueAnchor)
        RETURN v.name as virtue, count(*) as captures
        ORDER BY captures DESC
        """,
        {"id": agent_id}
    )

    # Get recent trajectories
    trajectories = client.query(
        """
        MATCH (me:Agent {id: $id})-[:HAS_TRAJECTORY]->(t:Trajectory)
        RETURN t.id, t.captured, t.captured_by, t.created_at
        ORDER BY t.created_at DESC
        LIMIT 10
        """,
        {"id": agent_id}
    )

    # Get parent
    parent = client.query(
        """
        MATCH (parent)-[:SPAWNED]->(me:Agent {id: $id})
        RETURN parent.id
        """,
        {"id": agent_id}
    )

    # Get agent metadata
    metadata = client.query(
        """
        MATCH (a:Agent {id: $id})
        RETURN a.type, a.generation, a.coherence_score, a.status, a.created_at
        """,
        {"id": agent_id}
    )

    meta = metadata[0] if metadata else [None] * 5

    return {
        "id": agent_id,
        "type": meta[0],
        "generation": meta[1],
        "coherence_score": meta[2],
        "status": meta[3],
        "created_at": meta[4],
        "connections": [
            {"rel": c[0], "type": c[1], "id": c[2], "weight": c[3]}
            for c in connections
        ],
        "virtue_captures": {c[0]: c[1] for c in captures},
        "recent_trajectories": [
            {"id": t[0], "captured": t[1], "captured_by": t[2], "created_at": t[3]}
            for t in trajectories
        ],
        "parent": parent[0][0] if parent else None
    }


def get_virtue_affinities(agent_id: str) -> dict:
    """
    Get agent's affinity weights to each virtue.

    Args:
        agent_id: ID of the agent

    Returns:
        dict mapping virtue name to affinity weight
    """
    client = get_client()

    result = client.query(
        """
        MATCH (a:Agent {id: $id})-[r:SEEKS]->(v:VirtueAnchor)
        RETURN v.name, v.id, r.weight
        ORDER BY r.weight DESC
        """,
        {"id": agent_id}
    )

    return {
        row[1]: {"name": row[0], "weight": row[2]}
        for row in result
    }


def compare_agents(agent_id_1: str, agent_id_2: str) -> dict:
    """
    Compare topology of two agents.

    Args:
        agent_id_1: First agent ID
        agent_id_2: Second agent ID

    Returns:
        dict with comparison metrics
    """
    affinities_1 = get_virtue_affinities(agent_id_1)
    affinities_2 = get_virtue_affinities(agent_id_2)

    # Calculate similarity
    virtues = set(affinities_1.keys()) | set(affinities_2.keys())

    total_diff = 0
    for v in virtues:
        w1 = affinities_1.get(v, {}).get("weight", 0)
        w2 = affinities_2.get(v, {}).get("weight", 0)
        total_diff += abs(w1 - w2)

    similarity = 1 - (total_diff / len(virtues)) if virtues else 0

    return {
        "agent_1": agent_id_1,
        "agent_2": agent_id_2,
        "similarity": similarity,
        "affinities_1": affinities_1,
        "affinities_2": affinities_2
    }


def get_strongest_virtues(agent_id: str, top_n: int = 5) -> list:
    """
    Get the virtues an agent is most strongly connected to.

    Args:
        agent_id: ID of the agent
        top_n: Number of top virtues to return

    Returns:
        List of (virtue_name, weight) tuples
    """
    client = get_client()

    result = client.query(
        """
        MATCH (a:Agent {id: $id})-[r:SEEKS]->(v:VirtueAnchor)
        RETURN v.name, r.weight
        ORDER BY r.weight DESC
        LIMIT $limit
        """,
        {"id": agent_id, "limit": top_n}
    )

    return [(row[0], row[1]) for row in result]
