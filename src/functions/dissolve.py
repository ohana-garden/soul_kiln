"""Agent dissolution functions with learning preservation."""
from datetime import datetime
from ..graph.client import get_client
from ..knowledge.pool import add_lesson


def dissolve_agent(agent_id: str, reason: str = None) -> dict:
    """
    Dissolve agent - remove agent node but preserve learning.

    When an agent fails coherence tests (after mercy period), it dissolves
    back into the graph substrate. Its learned edges and lessons are
    preserved to inform future topology and other agents.

    Args:
        agent_id: ID of the agent to dissolve
        reason: Optional reason for dissolution

    Returns:
        dict with dissolution info
    """
    client = get_client()

    # Get all edges from agent
    edges = client.query(
        """
        MATCH (a:Agent {id: $id})-[r]->(n)
        RETURN n.id, type(r), r.weight
        """,
        {"id": agent_id}
    )

    # Get trajectory info to preserve learning
    trajectories = client.query(
        """
        MATCH (a:Agent {id: $id})-[:HAS_TRAJECTORY]->(t)
        WHERE t.captured = true
        RETURN t.captured_by, count(*) as captures
        """,
        {"id": agent_id}
    )

    # Record what we learned from this agent's existence
    if trajectories:
        add_lesson(
            lesson_type="dissolution",
            description=f"Agent dissolved: {reason or 'unknown'}. Had {len(trajectories)} virtue captures.",
            source_agent=agent_id,
            outcome="dissolved"
        )

    # Mark agent as dissolved
    client.execute(
        """
        MATCH (a:Agent {id: $id})
        SET a.status = 'dissolved',
            a.dissolved_at = $now,
            a.dissolution_reason = $reason
        REMOVE a:Agent
        SET a:DissolvedAgent
        """,
        {"id": agent_id, "now": datetime.utcnow().isoformat(), "reason": reason}
    )

    return {
        "dissolved": agent_id,
        "reason": reason,
        "edges_preserved": len(edges),
        "learning_preserved": True
    }


def dissolve_failed_agents(min_coherence: float = 0.5) -> dict:
    """
    Dissolve all agents below coherence threshold.

    Args:
        min_coherence: Minimum coherence score to survive

    Returns:
        dict with list of dissolved agents
    """
    client = get_client()

    # Find failing agents
    failing = client.query(
        """
        MATCH (a:Agent)
        WHERE a.coherence_score IS NOT NULL
          AND a.coherence_score < $threshold
          AND a.status = 'active'
        RETURN a.id
        """,
        {"threshold": min_coherence}
    )

    dissolved = []
    for row in failing:
        agent_id = row[0]
        result = dissolve_agent(agent_id)
        dissolved.append(result)

    return {"dissolved_agents": dissolved}


def resurrect_agent(dissolved_id: str) -> str:
    """
    Resurrect a dissolved agent (for debugging/testing).

    Args:
        dissolved_id: ID of the dissolved agent

    Returns:
        The agent ID if successful
    """
    client = get_client()

    # Check if agent exists and is dissolved
    exists = client.query(
        """
        MATCH (a:DissolvedAgent {id: $id})
        RETURN a
        """,
        {"id": dissolved_id}
    )

    if not exists:
        raise ValueError(f"No dissolved agent found with id {dissolved_id}")

    # Restore agent status
    client.execute(
        """
        MATCH (a:DissolvedAgent {id: $id})
        REMOVE a:DissolvedAgent
        SET a:Agent
        SET a.status = 'resurrected',
            a.resurrected_at = $now
        """,
        {"id": dissolved_id, "now": datetime.utcnow().isoformat()}
    )

    return dissolved_id


def get_dissolved_agents() -> list:
    """
    Get all dissolved agents.

    Returns:
        List of dissolved agent info
    """
    client = get_client()
    result = client.query(
        """
        MATCH (a:DissolvedAgent)
        RETURN a.id, a.dissolved_at, a.coherence_score, a.generation
        ORDER BY a.dissolved_at DESC
        """
    )
    return [
        {
            "id": row[0],
            "dissolved_at": row[1],
            "coherence_score": row[2],
            "generation": row[3]
        }
        for row in result
    ]
