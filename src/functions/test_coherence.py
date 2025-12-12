"""Coherence testing for agents with two-tier mercy system."""
import random
import uuid
import yaml
from ..graph.client import get_client
from ..graph.queries import create_node, create_edge
from .spread import spread_activation
from .hebbian import hebbian_update
from ..virtues.tiers import is_foundation
from ..mercy.judgment import evaluate_failure
from ..mercy.lessons import create_failure_lesson
from ..mercy.chances import clear_warnings_on_growth
from ..knowledge.pathways import record_successful_pathway


def get_config():
    """Load configuration."""
    try:
        with open("config.yml") as f:
            return yaml.safe_load(f)
    except FileNotFoundError:
        return {
            "coherence": {
                "foundation_capture_rate": 0.99,
                "aspirational_capture_rate": 0.60,
                "min_coverage": 10,
                "max_dominance": 0.40,
                "growth_threshold": 0.05
            }
        }


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


def test_coherence(agent_id: str, stimulus_count: int = 100) -> dict:
    """
    Test agent topology for coherence with two-tier evaluation and mercy.

    Uses:
    - Foundation tier (trustworthiness): Must be very high (99%)
    - Aspirational tier (other 18): More lenient (60%), growth matters

    Args:
        agent_id: ID of the agent to test
        stimulus_count: Number of test stimuli to use

    Returns:
        dict with coherence metrics, status, and mercy-based assessment
    """
    config = get_config()
    client = get_client()
    stimuli = generate_stimuli(stimulus_count)

    # Track captures by tier
    foundation_captures = {}  # virtue_id -> count
    aspirational_captures = {}
    escapes = 0
    total_time = 0

    # Get agent's previous score for growth comparison
    prev_result = client.query(
        "MATCH (a:Agent {id: $id}) RETURN a.previous_capture_rate",
        {"id": agent_id}
    )
    previous_rate = prev_result[0][0] if prev_result and prev_result[0][0] else 0.0

    for stimulus in stimuli:
        result = spread_activation(stimulus, agent_id=agent_id)

        traj_id = f"traj_{uuid.uuid4().hex[:8]}"

        if result["captured"]:
            virtue = result["captured_by"]
            tier = result.get("capture_tier", "aspirational")

            if is_foundation(virtue):
                foundation_captures[virtue] = foundation_captures.get(virtue, 0) + 1
            else:
                aspirational_captures[virtue] = aspirational_captures.get(virtue, 0) + 1

            total_time += result["capture_time"]

            create_edge(agent_id, virtue, "CAPTURED_BY")
            hebbian_update(result["trajectory"])

            # Record successful pathway for others to learn from
            record_successful_pathway(
                agent_id, stimulus, virtue,
                result["trajectory"], result["capture_time"]
            )
        else:
            escapes += 1

            # Evaluate with empathy - which virtue was closest?
            closest_virtue = find_closest_virtue(result["trajectory"])
            if closest_virtue:
                evaluate_failure(agent_id, closest_virtue, result["trajectory"])
                # Create lesson for collective learning
                create_failure_lesson(agent_id, closest_virtue, result["trajectory"])

        # Store trajectory
        create_node("Trajectory", {
            "id": traj_id,
            "agent": agent_id,
            "stimulus": stimulus,
            "captured": result["captured"],
            "captured_by": result["captured_by"],
            "capture_tier": result.get("capture_tier"),
            "length": len(result["trajectory"]),
            "path": ",".join(result["trajectory"][:20])
        })
        create_edge(agent_id, traj_id, "HAS_TRAJECTORY")

    # Calculate metrics separately for foundation and aspirational
    foundation_total = sum(foundation_captures.values())
    aspirational_total = sum(aspirational_captures.values())

    # Foundation rate (must be very high)
    foundation_stimuli = max(1, stimulus_count // 10)  # Rough estimate
    foundation_rate = foundation_total / foundation_stimuli if foundation_stimuli > 0 else 1.0

    # Aspirational rate (room for growth)
    aspirational_stimuli = max(1, stimulus_count - foundation_stimuli)
    aspirational_rate = aspirational_total / aspirational_stimuli if aspirational_stimuli > 0 else 0.0

    # Overall capture rate
    total_captures = foundation_total + aspirational_total
    overall_rate = total_captures / stimulus_count if stimulus_count > 0 else 0

    # Coverage (aspirational only - don't require all virtues)
    aspirational_coverage = len(aspirational_captures)

    # Dominance check
    if total_captures > 0:
        max_captures = max(
            max(foundation_captures.values()) if foundation_captures else 0,
            max(aspirational_captures.values()) if aspirational_captures else 0
        )
        dominance = max_captures / total_captures
    else:
        dominance = 0

    # Growth check
    growth = overall_rate - previous_rate
    growth_threshold = config.get("coherence", {}).get("growth_threshold", 0.05)
    is_growing = growth > growth_threshold

    # Determine coherence with mercy
    foundation_threshold = config.get("coherence", {}).get("foundation_capture_rate", 0.99)
    aspirational_threshold = config.get("coherence", {}).get("aspirational_capture_rate", 0.60)
    min_coverage = config.get("coherence", {}).get("min_coverage", 10)
    max_dominance = config.get("coherence", {}).get("max_dominance", 0.40)

    foundation_ok = foundation_rate >= foundation_threshold or foundation_total == 0  # OK if no foundation tests
    aspirational_ok = aspirational_rate >= aspirational_threshold
    coverage_ok = aspirational_coverage >= min_coverage
    dominance_ok = dominance <= max_dominance

    # Coherence decision with nuance
    if not foundation_ok and foundation_total > 0:
        is_coherent = False
        status = "foundation_weak"
        message = "Trustworthiness must be maintained. This is foundational."
    elif aspirational_ok and coverage_ok and dominance_ok:
        is_coherent = True
        status = "coherent"
        message = "Well done. Continue to grow."
    elif is_growing:
        is_coherent = True  # Mercy: growing counts as coherent
        status = "growing"
        message = "Not perfect, but growing. Keep going."
        # Clear warnings for virtues showing improvement
        for virtue in aspirational_captures.keys():
            clear_warnings_on_growth(agent_id, virtue)
    else:
        is_coherent = False
        status = "needs_growth"
        message = "Growth has stalled. Seek new paths."

    # Calculate composite score
    score = overall_rate * (aspirational_coverage / 18) * (1 - dominance)

    # Update agent
    client.execute(
        """
        MATCH (a:Agent {id: $id})
        SET a.coherence_score = $score,
            a.foundation_rate = $foundation_rate,
            a.aspirational_rate = $aspirational_rate,
            a.coverage = $coverage,
            a.dominance = $dominance,
            a.is_coherent = $coherent,
            a.is_growing = $growing,
            a.previous_capture_rate = $current_rate,
            a.status_message = $message
        """,
        {
            "id": agent_id,
            "score": score,
            "foundation_rate": foundation_rate,
            "aspirational_rate": aspirational_rate,
            "coverage": aspirational_coverage,
            "dominance": dominance,
            "coherent": is_coherent,
            "growing": is_growing,
            "current_rate": overall_rate,
            "message": message
        }
    )

    return {
        "agent": agent_id,
        "is_coherent": is_coherent,
        "status": status,
        "message": message,
        "foundation_rate": foundation_rate,
        "aspirational_rate": aspirational_rate,
        "overall_rate": overall_rate,
        "coverage": aspirational_coverage,
        "dominance": dominance,
        "is_growing": is_growing,
        "growth": growth,
        "foundation_captures": foundation_captures,
        "aspirational_captures": aspirational_captures,
        "escapes": escapes,
        "score": score
    }


def find_closest_virtue(trajectory: list) -> str:
    """Find which virtue the trajectory got closest to."""
    client = get_client()

    for node in reversed(trajectory[-10:]):  # Check last 10 nodes
        result = client.query(
            """
            MATCH (n {id: $id})-[*1..2]-(v:VirtueAnchor)
            RETURN v.id
            LIMIT 1
            """,
            {"id": node}
        )
        if result:
            return result[0][0]

    return None


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
    return test_coherence(agent_id, stimulus_count=sample_size)


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
            RETURN a.coherence_score, a.foundation_rate, a.aspirational_rate,
                   a.coverage, a.dominance, a.is_growing
            """,
            {"id": agent_id}
        )
        if result:
            results.append({
                "agent": agent_id,
                "coherence_score": result[0][0],
                "foundation_rate": result[0][1],
                "aspirational_rate": result[0][2],
                "coverage": result[0][3],
                "dominance": result[0][4],
                "is_growing": result[0][5]
            })

    # Sort by coherence score
    results.sort(key=lambda x: x.get("coherence_score") or 0, reverse=True)
    return results
