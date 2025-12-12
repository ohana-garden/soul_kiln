"""Evaluate failures with empathy."""

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
    Returns judgment and recommended response.
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
        WHERE t.created_at > datetime() - duration('P1D')
        RETURN count(*) as recent_attempts
        """,
        {"agent_id": agent_id}
    )

    recent_attempts = recent[0][0] if recent else 0

    # Build empathetic assessment
    assessment = {
        "agent": agent_id,
        "virtue": virtue_id,
        "is_foundation": is_foundation(virtue_id),
        "past_successes": past_successes,
        "recent_attempts": recent_attempts,
        "has_history": past_successes > 0,
    }

    # Determine response
    if is_foundation(virtue_id):
        # Trustworthiness - serious but still give context
        assessment["severity"] = "high"
        assessment["response"] = "warning"  # Not immediate dissolution
        assessment["message"] = "Trust is foundational. This is a serious matter, but we seek to understand."
    else:
        # Aspirational virtue - be gentle
        assessment["severity"] = "low"
        assessment["response"] = "teach"
        assessment["message"] = "Growth is a journey. This failure is an opportunity to learn."

        # Extra mercy if they've succeeded before
        if past_successes > 5:
            assessment["message"] += " You've walked this path before - you can find it again."

    return assessment
