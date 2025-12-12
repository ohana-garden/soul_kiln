"""Temporal decay of edge weights."""
from datetime import datetime
from ..graph.client import get_client


def apply_decay(
    decay_constant: float = 0.97,
    min_weight: float = 0.01,
    protect_virtues: bool = True,
    target_degree: int = 9
):
    """
    Decay all edges based on time since last use.

    Implements forgetting - edges that aren't used weaken over time.

    Args:
        decay_constant: Multiplier per hour (0.97 = 3% decay per hour)
        min_weight: Minimum weight before edge is deleted
        protect_virtues: If True, don't delete edges that would leave virtue
                        below target_degree connectivity
        target_degree: Minimum connections each virtue should maintain
    """
    client = get_client()
    now = datetime.utcnow()

    # Get all edges with timestamps
    edges = client.query(
        """
        MATCH (a)-[r]->(b)
        RETURN a.id, b.id, r.weight, r.last_used, type(r) as rel_type,
               labels(a) as a_labels, labels(b) as b_labels
        """
    )

    for edge in edges:
        from_id, to_id, weight, last_used, rel_type, a_labels, b_labels = edge

        if not last_used or not weight:
            continue

        # Calculate decay
        try:
            last_used_dt = datetime.fromisoformat(last_used)
        except (ValueError, TypeError):
            continue

        hours_since = (now - last_used_dt).total_seconds() / 3600
        decayed_weight = weight * (decay_constant ** hours_since)

        # Check if this would violate virtue min-degree
        should_delete = decayed_weight < min_weight

        if should_delete and protect_virtues:
            # Check if either endpoint is a virtue anchor
            is_virtue_edge = (
                "VirtueAnchor" in (a_labels or []) or
                "VirtueAnchor" in (b_labels or [])
            )

            if is_virtue_edge:
                # Check degrees
                for node_id, labels in [(from_id, a_labels), (to_id, b_labels)]:
                    if "VirtueAnchor" in (labels or []):
                        degree_result = client.query(
                            "MATCH (v {id: $id})-[r]-() RETURN count(r) as degree",
                            {"id": node_id}
                        )
                        degree = degree_result[0][0] if degree_result else 0

                        if degree <= target_degree:
                            # Don't delete, just set to minimum
                            should_delete = False
                            decayed_weight = min_weight
                            break

        if should_delete:
            client.execute(
                """
                MATCH (a {id: $from})-[r]->(b {id: $to})
                DELETE r
                """,
                {"from": from_id, "to": to_id}
            )
        else:
            client.execute(
                """
                MATCH (a {id: $from})-[r]->(b {id: $to})
                SET r.weight = $weight
                """,
                {"from": from_id, "to": to_id, "weight": decayed_weight}
            )


def decay_activations(decay_rate: float = 0.95):
    """
    Decay all node activations toward baseline.

    Args:
        decay_rate: Multiplier per cycle
    """
    client = get_client()

    # Decay non-virtue nodes toward 0
    client.execute(
        """
        MATCH (n)
        WHERE NOT n:VirtueAnchor AND n.activation IS NOT NULL
        SET n.activation = n.activation * $rate
        """,
        {"rate": decay_rate}
    )

    # Decay virtue anchors toward baseline
    client.execute(
        """
        MATCH (v:VirtueAnchor)
        WHERE v.activation IS NOT NULL AND v.baseline IS NOT NULL
        SET v.activation = v.baseline + (v.activation - v.baseline) * $rate
        """,
        {"rate": decay_rate}
    )
