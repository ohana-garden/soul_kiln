"""Hebbian learning - strengthen edges along activation paths."""
from ..graph.queries import update_edge_weight, create_edge
from ..graph.client import get_client


def hebbian_update(trajectory: list, learning_rate: float = 0.01):
    """
    Strengthen edges between consecutively activated nodes.

    Implements Hebbian learning: "neurons that fire together wire together"

    Args:
        trajectory: List of node IDs in activation order
        learning_rate: Amount to increase edge weight per co-activation
    """
    client = get_client()

    for i in range(len(trajectory) - 1):
        from_id = trajectory[i]
        to_id = trajectory[i + 1]

        # Get current weight
        result = client.query(
            """
            MATCH (a {id: $from})-[r]-(b {id: $to})
            RETURN r.weight as weight
            """,
            {"from": from_id, "to": to_id}
        )

        if result:
            current_weight = result[0][0] or 0.5
            new_weight = min(1.0, current_weight + learning_rate)
            update_edge_weight(from_id, to_id, new_weight)
        else:
            # Create edge if doesn't exist
            create_edge(from_id, to_id, "ACTIVATED", {"weight": learning_rate})


def anti_hebbian_update(trajectory: list, learning_rate: float = 0.01):
    """
    Weaken edges along unsuccessful paths.

    Opposite of Hebbian learning - for paths that didn't reach a virtue.

    Args:
        trajectory: List of node IDs in activation order
        learning_rate: Amount to decrease edge weight
    """
    client = get_client()

    for i in range(len(trajectory) - 1):
        from_id = trajectory[i]
        to_id = trajectory[i + 1]

        # Get current weight
        result = client.query(
            """
            MATCH (a {id: $from})-[r]-(b {id: $to})
            RETURN r.weight as weight
            """,
            {"from": from_id, "to": to_id}
        )

        if result:
            current_weight = result[0][0] or 0.5
            new_weight = max(0.01, current_weight - learning_rate)
            update_edge_weight(from_id, to_id, new_weight)
