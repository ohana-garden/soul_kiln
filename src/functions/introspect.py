"""Agent introspection - self-awareness queries with mercy context."""
from ..graph.client import get_client


def introspect(agent_id: str) -> dict:
    """
    Agent queries its own structure and history.

    Introspection allows an agent to understand its own topology,
    capture history, warnings, lessons learned, and lineage.

    Args:
        agent_id: ID of the agent

    Returns:
        dict with comprehensive self-model including mercy context
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

    # Get virtue capture history by tier
    captures = client.query(
        """
        MATCH (me:Agent {id: $id})-[:CAPTURED_BY]->(v:VirtueAnchor)
        RETURN v.name as virtue, v.tier as tier, count(*) as captures
        ORDER BY captures DESC
        """,
        {"id": agent_id}
    )

    # Separate foundation and aspirational captures
    foundation_captures = {}
    aspirational_captures = {}
    for c in captures:
        if c[1] == "foundation":
            foundation_captures[c[0]] = c[2]
        else:
            aspirational_captures[c[0]] = c[2]

    # Get warnings
    warnings = client.query(
        """
        MATCH (me:Agent {id: $id})-[:HAS_WARNING]->(w:Warning)
        WHERE w.active = true
        RETURN w.id, w.reason, w.severity, w.virtue, w.created_at
        ORDER BY w.created_at DESC
        """,
        {"id": agent_id}
    )

    # Get recent trajectories
    trajectories = client.query(
        """
        MATCH (me:Agent {id: $id})-[:HAS_TRAJECTORY]->(t:Trajectory)
        RETURN t.id, t.captured, t.captured_by, t.capture_tier, t.created_at
        ORDER BY t.created_at DESC
        LIMIT 10
        """,
        {"id": agent_id}
    )

    # Get lessons learned
    lessons = client.query(
        """
        MATCH (me:Agent {id: $id})-[:LEARNED_FROM]->(l:Lesson)
        RETURN l.id, l.type, l.description, l.virtue_involved
        ORDER BY l.created_at DESC
        LIMIT 5
        """,
        {"id": agent_id}
    )

    # Get lessons taught
    lessons_taught = client.query(
        """
        MATCH (me:Agent {id: $id})-[:TAUGHT]->(l:Lesson)
        RETURN count(*) as count
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

    # Get agent metadata with extended fields
    metadata = client.query(
        """
        MATCH (a:Agent {id: $id})
        RETURN a.type, a.generation, a.coherence_score, a.status, a.created_at,
               a.is_growing, a.foundation_rate, a.aspirational_rate,
               a.previous_capture_rate, a.status_message
        """,
        {"id": agent_id}
    )

    meta = metadata[0] if metadata else [None] * 10

    return {
        "id": agent_id,
        "type": meta[0],
        "generation": meta[1],
        "coherence_score": meta[2],
        "status": meta[3],
        "created_at": meta[4],
        "is_growing": meta[5],
        "foundation_rate": meta[6],
        "aspirational_rate": meta[7],
        "previous_capture_rate": meta[8],
        "status_message": meta[9],
        "connections": [
            {"rel": c[0], "type": c[1], "id": c[2], "weight": c[3]}
            for c in connections
        ],
        "foundation_captures": foundation_captures,
        "aspirational_captures": aspirational_captures,
        "virtue_captures": {**foundation_captures, **aspirational_captures},
        "active_warnings": [
            {"id": w[0], "reason": w[1], "severity": w[2], "virtue": w[3], "created_at": w[4]}
            for w in warnings
        ],
        "recent_trajectories": [
            {"id": t[0], "captured": t[1], "captured_by": t[2], "capture_tier": t[3], "created_at": t[4]}
            for t in trajectories
        ],
        "lessons_learned": [
            {"id": l[0], "type": l[1], "description": l[2], "virtue": l[3]}
            for l in lessons
        ],
        "lessons_taught_count": lessons_taught[0][0] if lessons_taught else 0,
        "parent": parent[0][0] if parent else None
    }


def get_virtue_affinities(agent_id: str) -> dict:
    """
    Get agent's affinity weights to each virtue.

    Args:
        agent_id: ID of the agent

    Returns:
        dict mapping virtue ID to affinity details including tier
    """
    client = get_client()

    result = client.query(
        """
        MATCH (a:Agent {id: $id})-[r:SEEKS]->(v:VirtueAnchor)
        RETURN v.name, v.id, r.weight, v.tier
        ORDER BY r.weight DESC
        """,
        {"id": agent_id}
    )

    return {
        row[1]: {"name": row[0], "weight": row[2], "tier": row[3]}
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
        List of (virtue_name, weight, tier) tuples
    """
    client = get_client()

    result = client.query(
        """
        MATCH (a:Agent {id: $id})-[r:SEEKS]->(v:VirtueAnchor)
        RETURN v.name, r.weight, v.tier
        ORDER BY r.weight DESC
        LIMIT $limit
        """,
        {"id": agent_id, "limit": top_n}
    )

    return [(row[0], row[1], row[2]) for row in result]


def get_warning_summary(agent_id: str) -> dict:
    """
    Get a summary of warnings for an agent.

    Args:
        agent_id: ID of the agent

    Returns:
        dict with warning counts and details
    """
    client = get_client()

    # Active warnings
    active = client.query(
        """
        MATCH (a:Agent {id: $id})-[:HAS_WARNING]->(w:Warning)
        WHERE w.active = true
        RETURN w.severity, count(*) as count
        """,
        {"id": agent_id}
    )

    active_by_severity = {row[0]: row[1] for row in active}

    # Total warnings (including expired)
    total = client.query(
        """
        MATCH (a:Agent {id: $id})-[:HAS_WARNING]->(w:Warning)
        RETURN count(*) as count
        """,
        {"id": agent_id}
    )

    # Cleared by growth
    cleared_by_growth = client.query(
        """
        MATCH (a:Agent {id: $id})-[:HAS_WARNING]->(w:Warning)
        WHERE w.cleared_reason = 'growth_demonstrated'
        RETURN count(*) as count
        """,
        {"id": agent_id}
    )

    return {
        "agent": agent_id,
        "active_warnings": sum(active_by_severity.values()),
        "active_by_severity": active_by_severity,
        "total_warnings_ever": total[0][0] if total else 0,
        "cleared_by_growth": cleared_by_growth[0][0] if cleared_by_growth else 0,
        "at_risk": sum(active_by_severity.values()) >= 3
    }


def get_learning_profile(agent_id: str) -> dict:
    """
    Get the agent's learning profile - what they've learned and taught.

    Args:
        agent_id: ID of the agent

    Returns:
        dict with learning statistics
    """
    client = get_client()

    # Lessons learned by type
    learned = client.query(
        """
        MATCH (a {id: $agent_id})-[:LEARNED_FROM]->(l:Lesson)
        RETURN l.type, count(*) as count
        """,
        {"agent_id": agent_id}
    )

    # Lessons taught
    taught = client.query(
        """
        MATCH (a {id: $agent_id})-[:TAUGHT]->(l:Lesson)
        RETURN l.type, count(*) as count
        """,
        {"agent_id": agent_id}
    )

    # Pathways discovered
    pathways = client.query(
        """
        MATCH (a {id: $agent_id})-[:DISCOVERED]->(p:Pathway)
        RETURN count(*) as count
        """,
        {"agent_id": agent_id}
    )

    # Pathways followed
    followed = client.query(
        """
        MATCH (a {id: $agent_id})-[:FOLLOWED]->(p:Pathway)
        RETURN count(*) as count
        """,
        {"agent_id": agent_id}
    )

    return {
        "agent": agent_id,
        "lessons_learned": {row[0]: row[1] for row in learned},
        "lessons_taught": {row[0]: row[1] for row in taught},
        "pathways_discovered": pathways[0][0] if pathways else 0,
        "pathways_followed": followed[0][0] if followed else 0,
        "is_active_learner": sum(row[1] for row in learned) > 5,
        "is_teacher": sum(row[1] for row in taught) > 0
    }
