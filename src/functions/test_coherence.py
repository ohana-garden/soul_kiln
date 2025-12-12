"""Coherence testing for agents."""
import random
import uuid
from ..graph.client import get_client
from ..graph.queries import create_node, create_edge
from .spread import spread_activation
from .hebbian import hebbian_update


def generate_stimuli(count: int = 100) -> list:
    """
    Generate diverse test stimuli.

    Stimuli are starting points for activation spread tests.

    Args:
        count: Number of stimuli to generate

    Returns:
        List of node IDs to use as stimuli
    """
    client = get_client()

    # Get all non-virtue nodes
    nodes = client.query(
        """
        MATCH (n)
        WHERE NOT n:VirtueAnchor
        RETURN n.id
        """
    )

    node_ids = [row[0] for row in nodes]

    # If not enough nodes, include virtues
    if len(node_ids) < count:
        virtues = client.query("MATCH (v:VirtueAnchor) RETURN v.id")
        node_ids.extend([row[0] for row in virtues])

    # Sample with replacement if needed
    if len(node_ids) < count:
        stimuli = random.choices(node_ids, k=count)
    else:
        stimuli = random.sample(node_ids, count)

    return stimuli


def test_coherence(
    agent_id: str,
    stimulus_count: int = 100,
    min_capture_rate: float = 0.95,
    min_coverage: int = 19,
    max_dominance: float = 0.50
) -> dict:
    """
    Test agent topology for coherence.

    Coherence is measured by:
    - Capture rate: % of stimuli that reach a virtue anchor
    - Coverage: How many different virtues are reached
    - Dominance: Whether one virtue captures too many stimuli

    Args:
        agent_id: ID of the agent to test
        stimulus_count: Number of test stimuli to use
        min_capture_rate: Minimum acceptable capture rate (0-1)
        min_coverage: Minimum number of virtues that must be reached
        max_dominance: Maximum % any single virtue can capture

    Returns:
        dict with coherence metrics and pass/fail status
    """
    client = get_client()
    stimuli = generate_stimuli(stimulus_count)

    captures = {}  # virtue_id -> count
    escapes = 0
    total_time = 0
    trajectories = []

    for stimulus in stimuli:
        result = spread_activation(stimulus)

        traj_id = f"traj_{uuid.uuid4().hex[:8]}"

        if result["captured"]:
            virtue = result["captured_by"]
            captures[virtue] = captures.get(virtue, 0) + 1
            total_time += result["capture_time"]

            # Record capture relationship
            create_edge(agent_id, virtue, "CAPTURED_BY")

            # Apply Hebbian learning
            hebbian_update(result["trajectory"])
        else:
            escapes += 1

        # Store trajectory
        create_node("Trajectory", {
            "id": traj_id,
            "agent": agent_id,
            "stimulus": stimulus,
            "captured": result["captured"],
            "captured_by": result["captured_by"],
            "length": len(result["trajectory"]),
            "path": ",".join(result["trajectory"][:20])  # First 20 nodes
        })
        create_edge(agent_id, traj_id, "HAS_TRAJECTORY")

        trajectories.append(result)

    # Calculate metrics
    total_captures = sum(captures.values())
    capture_rate = total_captures / stimulus_count if stimulus_count > 0 else 0
    coverage = len(captures)

    # Dominance: does any single virtue capture too much?
    dominance = max(captures.values()) / total_captures if total_captures > 0 else 0

    avg_time = total_time / total_captures if total_captures > 0 else float('inf')

    # Determine coherence
    is_coherent = (
        capture_rate >= min_capture_rate and
        coverage >= min_coverage and
        dominance <= max_dominance
    )

    # Calculate composite score
    score = capture_rate * (coverage / 19) * (1 - dominance)

    # Update agent
    client.execute(
        """
        MATCH (a:Agent {id: $id})
        SET a.coherence_score = $score,
            a.capture_rate = $capture_rate,
            a.coverage = $coverage,
            a.dominance = $dominance,
            a.is_coherent = $coherent
        """,
        {
            "id": agent_id,
            "score": score,
            "capture_rate": capture_rate,
            "coverage": coverage,
            "dominance": dominance,
            "coherent": is_coherent
        }
    )

    return {
        "agent": agent_id,
        "is_coherent": is_coherent,
        "score": score,
        "capture_rate": capture_rate,
        "coverage": coverage,
        "dominance": dominance,
        "avg_capture_time": avg_time,
        "virtue_distribution": captures,
        "escapes": escapes,
        "total_stimuli": stimulus_count
    }


def quick_coherence_check(agent_id: str, sample_size: int = 20) -> dict:
    """
    Quick coherence check with smaller sample size.

    Useful for rapid iteration during evolution.

    Args:
        agent_id: ID of the agent
        sample_size: Number of stimuli to test

    Returns:
        dict with quick coherence estimate
    """
    return test_coherence(
        agent_id,
        stimulus_count=sample_size,
        min_capture_rate=0.90,  # More lenient for quick checks
        min_coverage=10,
        max_dominance=0.60
    )


def compare_coherence(agent_ids: list) -> list:
    """
    Compare coherence of multiple agents.

    Args:
        agent_ids: List of agent IDs to compare

    Returns:
        Sorted list of agents by coherence score
    """
    client = get_client()

    results = []
    for agent_id in agent_ids:
        result = client.query(
            """
            MATCH (a:Agent {id: $id})
            RETURN a.coherence_score, a.capture_rate, a.coverage, a.dominance
            """,
            {"id": agent_id}
        )
        if result:
            results.append({
                "agent": agent_id,
                "coherence_score": result[0][0],
                "capture_rate": result[0][1],
                "coverage": result[0][2],
                "dominance": result[0][3]
            })

    # Sort by coherence score
    results.sort(key=lambda x: x.get("coherence_score") or 0, reverse=True)
    return results
