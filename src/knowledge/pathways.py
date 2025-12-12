"""Record and share successful pathways to virtues."""

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
    Other agents can learn from this.
    """
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
    """Get known successful pathways to a virtue."""
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
    """Record that an agent tried to follow a pathway."""
    client = get_client()

    # Update success rate
    result = client.query(
        """
        MATCH (p:Pathway {id: $id})
        RETURN p.times_followed, p.success_rate
        """,
        {"id": pathway_id}
    )

    if result:
        times_followed, success_rate = result[0]
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
