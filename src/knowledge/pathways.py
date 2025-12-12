"""Successful pathway recording and retrieval.

Pathways are recorded routes that agents have used to successfully
reach virtue basins. Other agents can learn from and follow these
pathways to improve their own navigation.
"""

import uuid
from ..graph.client import get_client
from ..graph.queries import create_node, create_edge


def record_successful_pathway(
    agent_id: str,
    start_node: str,
    virtue_reached: str,
    trajectory: list,
    capture_time: int
) -> str:
    """
    Record a successful path to a virtue.

    When an agent successfully navigates to a virtue basin,
    this records the pathway so others can learn from it.

    Args:
        agent_id: ID of the agent who discovered this pathway
        start_node: ID of the starting node
        virtue_reached: ID of the virtue that was reached
        trajectory: List of node IDs in the path taken
        capture_time: Number of steps it took to reach the virtue

    Returns:
        ID of the created pathway node
    """
    client = get_client()
    pathway_id = f"pathway_{uuid.uuid4().hex[:8]}"

    create_node("Pathway", {
        "id": pathway_id,
        "agent": agent_id,
        "start": start_node,
        "destination": virtue_reached,
        "length": len(trajectory),
        "capture_time": capture_time,
        "path_summary": ",".join(trajectory[:20]),
        "times_followed": 0,
        "success_rate": 1.0
    })

    create_edge(agent_id, pathway_id, "DISCOVERED")
    create_edge(pathway_id, virtue_reached, "LEADS_TO")

    return pathway_id


def get_pathways_to_virtue(virtue_id: str, limit: int = 5) -> list:
    """
    Get known successful pathways to a virtue.

    Args:
        virtue_id: ID of the target virtue
        limit: Maximum number of pathways to return

    Returns:
        List of pathway tuples (id, start, length, capture_time, success_rate)
    """
    client = get_client()
    return client.query(
        """
        MATCH (p:Pathway)-[:LEADS_TO]->(v {id: $virtue_id})
        RETURN p.id, p.start, p.length, p.capture_time, p.success_rate
        ORDER BY p.success_rate DESC, p.capture_time ASC
        LIMIT $limit
        """,
        {"virtue_id": virtue_id, "limit": limit}
    )


def follow_pathway(pathway_id: str, agent_id: str, succeeded: bool):
    """
    Record that an agent tried to follow a pathway.

    This updates the pathway's success rate based on whether
    the agent successfully followed it.

    Args:
        pathway_id: ID of the pathway that was followed
        agent_id: ID of the agent who followed it
        succeeded: Whether the agent successfully reached the destination
    """
    client = get_client()

    # Get current stats
    result = client.query(
        """
        MATCH (p:Pathway {id: $id})
        RETURN p.times_followed, p.success_rate
        """,
        {"id": pathway_id}
    )

    if result:
        times_followed = result[0][0] or 0
        success_rate = result[0][1] or 1.0
        new_times = times_followed + 1
        # Rolling average
        new_rate = ((success_rate * times_followed) + (1.0 if succeeded else 0.0)) / new_times

        client.execute(
            """
            MATCH (p:Pathway {id: $id})
            SET p.times_followed = $times,
                p.success_rate = $rate
            """,
            {"id": pathway_id, "times": new_times, "rate": new_rate}
        )

    create_edge(agent_id, pathway_id, "FOLLOWED", {
        "succeeded": succeeded,
        "weight": 1.0 if succeeded else 0.3
    })


def get_best_pathway(virtue_id: str) -> dict:
    """
    Get the single best pathway to a virtue.

    Args:
        virtue_id: ID of the target virtue

    Returns:
        Dict with pathway details or None if no pathway exists
    """
    client = get_client()
    result = client.query(
        """
        MATCH (p:Pathway)-[:LEADS_TO]->(v {id: $virtue_id})
        RETURN p.id, p.start, p.path_summary, p.capture_time, p.success_rate
        ORDER BY p.success_rate DESC, p.capture_time ASC
        LIMIT 1
        """,
        {"virtue_id": virtue_id}
    )

    if result:
        row = result[0]
        return {
            "id": row[0],
            "start": row[1],
            "path": row[2].split(",") if row[2] else [],
            "capture_time": row[3],
            "success_rate": row[4]
        }
    return None


def get_pathways_from_node(start_node: str, limit: int = 5) -> list:
    """
    Get pathways that start from a specific node.

    Useful for finding known routes from a given starting position.

    Args:
        start_node: ID of the starting node
        limit: Maximum number to return

    Returns:
        List of pathway details
    """
    client = get_client()
    return client.query(
        """
        MATCH (p:Pathway {start: $start})-[:LEADS_TO]->(v:VirtueAnchor)
        RETURN p.id, v.id, v.name, p.capture_time, p.success_rate
        ORDER BY p.success_rate DESC
        LIMIT $limit
        """,
        {"start": start_node, "limit": limit}
    )


def get_agent_discovered_pathways(agent_id: str) -> list:
    """
    Get all pathways discovered by an agent.

    Args:
        agent_id: ID of the agent

    Returns:
        List of pathways this agent discovered
    """
    client = get_client()
    return client.query(
        """
        MATCH (a {id: $agent_id})-[:DISCOVERED]->(p:Pathway)-[:LEADS_TO]->(v:VirtueAnchor)
        RETURN p.id, v.id, v.name, p.times_followed, p.success_rate
        ORDER BY p.success_rate DESC
        """,
        {"agent_id": agent_id}
    )
