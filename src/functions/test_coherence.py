"""Coherence testing for agents with two-tier virtue evaluation."""
import random
import uuid
import yaml
from ..graph.client import get_client
from ..graph.queries import create_node, create_edge
from .spread import spread_activation
from .hebbian import hebbian_update
from ..virtues.tiers import is_foundation


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
                "growth_matters": True,
                "growth_threshold": 0.05,
                "stimulus_count": 100
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


def test_coherence(agent_id: str, stimulus_count: int = 100) -> dict:
    """
    Test agent topology for coherence using two-tier evaluation.

    Uses separate thresholds for:
    - Foundation (Trustworthiness): Must be near-perfect (99%)
    - Aspirational (other 18): More lenient (60%), with room for growth

    Args:
        agent_id: ID of the agent to test
        stimulus_count: Number of test stimuli to use

    Returns:
        dict with coherence metrics including tier-based evaluation
    """
    config = get_config()
    coherence_config = config.get("coherence", {})
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

            if tier == "foundation" or is_foundation(virtue):
                foundation_captures[virtue] = foundation_captures.get(virtue, 0) + 1
            else:
                aspirational_captures[virtue] = aspirational_captures.get(virtue, 0) + 1

            total_time += result["capture_time"]

            create_edge(agent_id, virtue, "CAPTURED_BY")
            hebbian_update(result["trajectory"])

            # Record successful pathway for collective learning
            try:
                from ..knowledge.pathways import record_successful_pathway
                record_successful_pathway(
                    agent_id, stimulus, virtue,
                    result["trajectory"], result["capture_time"]
                )
            except ImportError:
                pass
        else:
            escapes += 1

            # Evaluate with empathy - which virtue was closest?
            try:
                from ..mercy.judgment import evaluate_failure
                from ..mercy.lessons import create_failure_lesson

                closest_virtue = find_closest_virtue(result["trajectory"])
                if closest_virtue:
                    evaluate_failure(agent_id, closest_virtue, result["trajectory"])
                    create_failure_lesson(agent_id, closest_virtue, result["trajectory"])
            except ImportError:
                pass

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

    # Foundation rate (should be very high)
    # Estimate foundation stimuli as ~10% of total (those starting near V01)
    foundation_stimuli = max(1, stimulus_count // 10)
    foundation_rate = foundation_total / max(1, foundation_stimuli) if foundation_total > 0 else (1.0 if foundation_stimuli == 0 else 0.0)
    foundation_rate = min(1.0, foundation_rate)

    # Aspirational rate (more lenient)
    aspirational_stimuli = max(1, stimulus_count - foundation_stimuli)
    aspirational_rate = aspirational_total / max(1, aspirational_stimuli)
    aspirational_rate = min(1.0, aspirational_rate)

    # Overall capture rate
    total_captures = foundation_total + aspirational_total
    overall_rate = total_captures / stimulus_count if stimulus_count > 0 else 0

    # Coverage (count of distinct virtues reached - aspirational only)
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

    # Average capture time
    avg_time = total_time / total_captures if total_captures > 0 else 0

    # Growth check
    growth = overall_rate - previous_rate
    growth_threshold = coherence_config.get("growth_threshold", 0.05)
    is_growing = growth > growth_threshold

    # Determine coherence with mercy
    foundation_threshold = coherence_config.get("foundation_capture_rate", 0.99)
    aspirational_threshold = coherence_config.get("aspirational_capture_rate", 0.60)
    min_coverage = coherence_config.get("min_coverage", 10)
    max_dominance = coherence_config.get("max_dominance", 0.40)

    # Be lenient with foundation rate if no foundation captures expected
    foundation_ok = foundation_rate >= foundation_threshold or foundation_total == 0
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
        try:
            from ..mercy.chances import clear_warnings_on_growth
            for virtue in aspirational_captures.keys():
                clear_warnings_on_growth(agent_id, virtue)
        except ImportError:
            pass
    else:
        is_coherent = False
        status = "needs_growth"
        message = "Growth has stalled. Seek new paths."

    # Calculate composite score
    score = overall_rate * (aspirational_coverage / 18) * (1 - dominance) if aspirational_coverage > 0 else 0

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
            a.status_message = $message,
            a.capture_rate = $capture_rate
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
            "message": message,
            "capture_rate": overall_rate
        }
    )

    return {
        "agent": agent_id,
        "is_coherent": is_coherent,
        "status": status,
        "message": message,
        "score": score,
        "foundation_rate": foundation_rate,
        "aspirational_rate": aspirational_rate,
        "capture_rate": overall_rate,
        "overall_rate": overall_rate,
        "coverage": aspirational_coverage,
        "dominance": dominance,
        "avg_capture_time": avg_time,
        "is_growing": is_growing,
        "growth": growth,
        "foundation_captures": foundation_captures,
        "aspirational_captures": aspirational_captures,
        "virtue_distribution": {**foundation_captures, **aspirational_captures},
        "escapes": escapes
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
            RETURN a.coherence_score, a.capture_rate, a.coverage, a.dominance,
                   a.foundation_rate, a.aspirational_rate, a.is_growing
            """,
            {"id": agent_id}
        )
        if result:
            results.append({
                "agent": agent_id,
                "coherence_score": result[0][0],
                "capture_rate": result[0][1],
                "coverage": result[0][2],
                "dominance": result[0][3],
                "foundation_rate": result[0][4],
                "aspirational_rate": result[0][5],
                "is_growing": result[0][6]
            })

    # Sort by coherence score
    results.sort(key=lambda x: x.get("coherence_score") or 0, reverse=True)
    return results
