"""Activation spread function with collective learning support."""
import math
from ..graph.client import get_client
from ..graph.queries import get_neighbors, get_node_activation, set_node_activation
from ..virtues.tiers import is_foundation


def tanh(x: float) -> float:
    """Hyperbolic tangent activation function."""
    return math.tanh(x)


def sigmoid(x: float) -> float:
    """Sigmoid activation function."""
    if x < -500:
        return 0.0
    if x > 500:
        return 1.0
    return 1 / (1 + math.exp(-x))


def spread_activation(
    start_node: str,
    agent_id: str = None,
    max_steps: int = 1000,
    activation_threshold: float = 0.1,
    capture_threshold: float = 0.7,
    dampening: float = 0.8,
    use_lessons: bool = True
) -> dict:
    """
    Spread activation from start_node.
    Returns trajectory and capture info with tier classification.

    Args:
        start_node: ID of node to start spreading from
        agent_id: Optional agent ID for learning context
        max_steps: Maximum number of propagation steps
        activation_threshold: Minimum activation to continue spreading
        capture_threshold: Activation level to consider a virtue "captured"
        dampening: Factor to reduce activation as it spreads
        use_lessons: Whether to use collective lessons for guidance

    Returns:
        dict with trajectory, capture status, tier, and timing info
    """
    client = get_client()
    trajectory = [start_node]
    visited_activations = {}

    # Initialize start node
    set_node_activation(start_node, 1.0)
    visited_activations[start_node] = 1.0

    current = start_node

    for step in range(max_steps):
        neighbors = get_neighbors(current)

        if not neighbors:
            break

        # Compute new activations
        new_activations = {}
        for neighbor in neighbors:
            n_id = neighbor[0]
            weight = neighbor[2] or 0.5

            # Get neighbor's baseline (if virtue anchor)
            baseline_result = client.query(
                "MATCH (n {id: $id}) RETURN n.baseline as baseline",
                {"id": n_id}
            )
            baseline = baseline_result[0][0] if baseline_result and baseline_result[0][0] else 0.0

            # Current activation of neighbor
            current_act = visited_activations.get(n_id, get_node_activation(n_id))

            # New activation: sigmoid(baseline + weight * tanh(incoming))
            incoming = visited_activations.get(current, 0) * dampening
            new_act = sigmoid(baseline + weight * tanh(incoming))

            new_activations[n_id] = max(current_act, new_act)

        # Find most activated neighbor
        if not new_activations:
            break

        next_node = max(new_activations, key=new_activations.get)
        next_activation = new_activations[next_node]

        # Update graph
        set_node_activation(next_node, next_activation)
        visited_activations[next_node] = next_activation

        # Record trajectory
        trajectory.append(next_node)

        # Check for basin capture (virtue anchor above threshold)
        is_virtue = client.query(
            "MATCH (n:VirtueAnchor {id: $id}) RETURN n.tier LIMIT 1",
            {"id": next_node}
        )

        if is_virtue and next_activation >= capture_threshold:
            tier = is_virtue[0][0] if is_virtue[0] else ("foundation" if is_foundation(next_node) else "aspirational")
            return {
                "trajectory": trajectory,
                "captured": True,
                "captured_by": next_node,
                "capture_tier": tier,
                "capture_time": step + 1,
                "final_activation": next_activation,
                "used_guidance": agent_id is not None and use_lessons
            }

        # Move to next
        current = next_node

        # Stop if activation too low
        if next_activation < activation_threshold:
            break

    return {
        "trajectory": trajectory,
        "captured": False,
        "captured_by": None,
        "capture_tier": None,
        "capture_time": None,
        "final_activation": visited_activations.get(trajectory[-1], 0),
        "used_guidance": agent_id is not None and use_lessons
    }
