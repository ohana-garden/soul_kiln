"""Random perturbation for exploration."""
import random
from ..graph.client import get_client
from ..graph.queries import set_node_activation


def perturb(strength: float = 0.7, bias_neglected: bool = True) -> dict:
    """
    Randomly activate a node to force exploration.

    Prevents the system from getting stuck in local minima by
    occasionally injecting random activation.

    Args:
        strength: Minimum activation level to apply
        bias_neglected: If True, prefer nodes that haven't been activated recently

    Returns:
        dict with perturbed node ID and activation level
    """
    client = get_client()

    if bias_neglected:
        # Find least recently activated nodes
        nodes = client.query(
            """
            MATCH (n)
            WHERE n.last_activated IS NOT NULL
            RETURN n.id, n.last_activated
            ORDER BY n.last_activated ASC
            LIMIT 10
            """
        )

        if nodes:
            # Pick from bottom 10
            node_id = random.choice(nodes)[0]
        else:
            # Fallback to random
            nodes = client.query("MATCH (n) RETURN n.id")
            node_id = random.choice(nodes)[0] if nodes else None
    else:
        nodes = client.query("MATCH (n) RETURN n.id")
        node_id = random.choice(nodes)[0] if nodes else None

    if node_id:
        activation = random.uniform(strength, 1.0)
        set_node_activation(node_id, activation)
        return {"perturbed": node_id, "activation": activation}

    return {"perturbed": None}


def perturb_virtue(strength: float = 0.7) -> dict:
    """
    Randomly activate a virtue anchor specifically.

    Args:
        strength: Minimum activation level to apply

    Returns:
        dict with perturbed virtue ID and activation level
    """
    client = get_client()

    virtues = client.query("MATCH (v:VirtueAnchor) RETURN v.id")

    if virtues:
        virtue_id = random.choice(virtues)[0]
        activation = random.uniform(strength, 1.0)
        set_node_activation(virtue_id, activation)
        return {"perturbed": virtue_id, "activation": activation}

    return {"perturbed": None}


def perturb_multiple(count: int = 5, strength: float = 0.5) -> list:
    """
    Perturb multiple random nodes.

    Args:
        count: Number of nodes to perturb
        strength: Minimum activation level

    Returns:
        List of perturbation results
    """
    results = []
    for _ in range(count):
        result = perturb(strength=strength, bias_neglected=True)
        if result["perturbed"]:
            results.append(result)
    return results
