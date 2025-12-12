"""Self-healing functions to maintain graph health."""
from ..graph.client import get_client
from ..graph.queries import create_edge
from ..virtues.anchors import VIRTUES
import random


def heal_dead_zones(target_degree: int = 9) -> dict:
    """
    Ensure all virtues have minimum connectivity.

    Dead zones are virtues that have become isolated due to edge decay.
    This function reconnects them to maintain the attractor structure.

    Args:
        target_degree: Minimum number of connections each virtue should have

    Returns:
        dict with list of healed edges
    """
    client = get_client()
    healed = []

    for virtue in VIRTUES:
        v_id = virtue["id"]

        # Get current degree
        result = client.query(
            "MATCH (v {id: $id})-[r]-() RETURN count(r) as degree",
            {"id": v_id}
        )
        degree = result[0][0] if result else 0

        if degree < target_degree:
            deficit = target_degree - degree

            # Find unconnected virtues
            connected = client.query(
                "MATCH (v {id: $id})-[r]-(other) RETURN other.id",
                {"id": v_id}
            )
            connected_ids = {row[0] for row in connected}
            connected_ids.add(v_id)

            # Candidate virtues to connect to
            candidates = [v["id"] for v in VIRTUES if v["id"] not in connected_ids]

            # Connect to random candidates
            for _ in range(min(deficit, len(candidates))):
                if candidates:
                    target = random.choice(candidates)
                    candidates.remove(target)
                    create_edge(v_id, target, "HEALED", {"weight": 0.3})
                    healed.append((v_id, target))

    return {"healed_edges": healed}


def detect_lockin(trajectory: list, threshold: int = 10) -> bool:
    """
    Detect if trajectory is stuck in a loop.

    Lock-in occurs when activation bounces between the same few nodes
    without reaching a virtue anchor.

    Args:
        trajectory: List of node IDs visited
        threshold: Number of recent steps to check

    Returns:
        True if locked in a loop
    """
    if len(trajectory) < threshold:
        return False

    recent = trajectory[-threshold:]
    unique = set(recent)

    # If visiting same few nodes repeatedly
    return len(unique) <= 3


def heal_isolated_nodes() -> dict:
    """
    Find and connect isolated non-virtue nodes.

    Returns:
        dict with count of nodes connected
    """
    client = get_client()

    # Find nodes with no connections
    isolated = client.query(
        """
        MATCH (n)
        WHERE NOT n:VirtueAnchor
        AND NOT (n)-[]-()
        RETURN n.id
        """
    )

    connected = 0
    for row in isolated:
        node_id = row[0]

        # Connect to a random virtue
        virtues = client.query("MATCH (v:VirtueAnchor) RETURN v.id")
        if virtues:
            virtue_id = random.choice(virtues)[0]
            create_edge(node_id, virtue_id, "CONNECTED", {"weight": 0.3})
            connected += 1

    return {"nodes_connected": connected}


def check_graph_health() -> dict:
    """
    Run health diagnostics on the graph.

    Returns:
        dict with health metrics
    """
    client = get_client()

    # Count nodes by type
    node_counts = client.query(
        """
        MATCH (n)
        RETURN labels(n) as labels, count(*) as count
        """
    )

    # Count edges by type
    edge_counts = client.query(
        """
        MATCH ()-[r]->()
        RETURN type(r) as type, count(*) as count
        """
    )

    # Check virtue connectivity
    virtue_degrees = client.query(
        """
        MATCH (v:VirtueAnchor)
        OPTIONAL MATCH (v)-[r]-()
        RETURN v.id, v.name, count(r) as degree
        """
    )

    # Find isolated virtues
    isolated_virtues = [
        {"id": row[0], "name": row[1], "degree": row[2]}
        for row in virtue_degrees
        if row[2] < 3
    ]

    return {
        "node_counts": {str(row[0]): row[1] for row in node_counts},
        "edge_counts": {row[0]: row[1] for row in edge_counts},
        "virtue_degrees": {row[0]: row[2] for row in virtue_degrees},
        "isolated_virtues": isolated_virtues,
        "healthy": len(isolated_virtues) == 0
    }
