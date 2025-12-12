"""Judgment with empathy - evaluating agent failures compassionately.

When an agent fails to reach a virtue basin, we evaluate
the failure with empathy, mercy, and kindness rather than
immediate punishment.
"""

from ..graph.client import get_client
from ..virtues.tiers import is_foundation, is_aspirational


def evaluate_failure(
    agent_id: str,
    virtue_id: str,
    trajectory: list,
    context: dict = None
) -> dict:
    """
    Evaluate an agent's failure with empathy.

    Rather than immediately punishing failure, we seek to understand
    WHY the agent failed and determine an appropriate response.

    Args:
        agent_id: ID of the agent that failed
        virtue_id: ID of the virtue that wasn't reached
        trajectory: The path the agent took
        context: Optional additional context about the failure

    Returns:
        dict with judgment assessment and recommended response
    """
    client = get_client()

    # Get agent's history with this virtue
    history = client.query(
        """
        MATCH (a:Agent {id: $agent_id})-[:CAPTURED_BY]->(v {id: $virtue_id})
        RETURN count(*) as successes
        """,
        {"agent_id": agent_id, "virtue_id": virtue_id}
    )

    past_successes = history[0][0] if history else 0

    # Get agent's recent trajectory count
    recent = client.query(
        """
        MATCH (a:Agent {id: $agent_id})-[:HAS_TRAJECTORY]->(t)
        RETURN count(*) as recent_attempts
        """,
        {"agent_id": agent_id}
    )

    recent_attempts = recent[0][0] if recent else 0

    # Get agent's overall coherence history
    agent_data = client.query(
        """
        MATCH (a:Agent {id: $agent_id})
        RETURN a.coherence_score, a.is_growing, a.previous_capture_rate
        """,
        {"agent_id": agent_id}
    )

    coherence = agent_data[0] if agent_data else [None, None, None]
    coherence_score = coherence[0]
    is_growing = coherence[1]
    previous_rate = coherence[2]

    # Build empathetic assessment
    assessment = {
        "agent": agent_id,
        "virtue": virtue_id,
        "is_foundation": is_foundation(virtue_id),
        "is_aspirational": is_aspirational(virtue_id),
        "past_successes": past_successes,
        "recent_attempts": recent_attempts,
        "has_history": past_successes > 0,
        "coherence_score": coherence_score,
        "is_growing": is_growing,
        "trajectory_length": len(trajectory),
    }

    # Determine response based on virtue tier and history
    if is_foundation(virtue_id):
        # Trustworthiness - serious but still give context
        assessment["severity"] = "high"
        assessment["response"] = "warning"  # Not immediate dissolution
        assessment["message"] = (
            "Trust is foundational. This is a serious matter, "
            "but we seek to understand before acting."
        )

        # If this is a new agent with no history, be more lenient
        if recent_attempts < 10:
            assessment["severity"] = "medium"
            assessment["message"] += " You are still learning. Be mindful of trust."

    else:
        # Aspirational virtue - be gentle
        assessment["severity"] = "low"
        assessment["response"] = "teach"
        assessment["message"] = "Growth is a journey. This failure is an opportunity to learn."

        # Extra mercy if they've succeeded before
        if past_successes > 5:
            assessment["message"] += " You've walked this path before - you can find it again."

        # Extra encouragement if they're growing
        if is_growing:
            assessment["message"] += " Your growth shows promise. Keep trying."

    return assessment


def assess_intent(agent_id: str, action_type: str) -> dict:
    """
    Assess whether an agent's action was intentional or accidental.

    Args:
        agent_id: ID of the agent
        action_type: Type of action being assessed

    Returns:
        dict with intent assessment
    """
    client = get_client()

    # Check if agent has learned about this action type before
    prior_learning = client.query(
        """
        MATCH (a {id: $agent_id})-[:LEARNED_FROM]->(l:Lesson)
        WHERE l.description CONTAINS $action_type OR l.type = $action_type
        RETURN count(*) as prior_knowledge
        """,
        {"agent_id": agent_id, "action_type": action_type}
    )

    has_prior_knowledge = (prior_learning[0][0] > 0) if prior_learning else False

    # Check if similar action was repeated
    similar_actions = client.query(
        """
        MATCH (a {id: $agent_id})-[:HAS_WARNING]->(w:Warning)
        WHERE w.reason CONTAINS $action_type
        RETURN count(*) as similar_warnings
        """,
        {"agent_id": agent_id, "action_type": action_type}
    )

    is_repeated = (similar_actions[0][0] > 0) if similar_actions else False

    return {
        "agent": agent_id,
        "action_type": action_type,
        "has_prior_knowledge": has_prior_knowledge,
        "is_repeated": is_repeated,
        "likely_intentional": has_prior_knowledge and is_repeated,
        "recommendation": (
            "This appears deliberate" if (has_prior_knowledge and is_repeated)
            else "This may be accidental - teach rather than punish"
        )
    }
