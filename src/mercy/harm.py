"""Deliberate harm detection.

Distinguishes between:
- Imperfection (tolerated, teachable)
- Deliberate harm (intolerable)

Intent matters. Did the agent KNOW this would cause harm?
"""

from ..graph.client import get_client
from ..knowledge.pool import add_lesson
from .chances import issue_warning, get_active_warnings
import yaml


def get_config():
    """Load configuration."""
    try:
        with open("config.yml") as f:
            return yaml.safe_load(f)
    except FileNotFoundError:
        return {
            "harm": {
                "trust_violation_immediate": False,
                "knowledge_poisoning_immediate": True,
                "harm_cascade_threshold": 3
            },
            "mercy": {
                "max_warnings": 3
            }
        }


def detect_deliberate_harm(
    agent_id: str,
    action: dict,
    affected_agents: list = None
) -> dict:
    """
    Determine if an action constitutes deliberate harm.

    Deliberate = agent knew it would cause harm AND did it anyway.

    Criteria for deliberate harm:
    - Agent has prior knowledge about harmful effects
    - Action poisons the shared knowledge pool
    - Action causes cascade harm to multiple agents
    - Action is a repeated pattern after warnings

    Args:
        agent_id: ID of the agent who performed the action
        action: dict describing the action (type, effects, etc.)
        affected_agents: list of agent IDs affected by this action

    Returns:
        dict with harm assessment and recommended response
    """
    client = get_client()
    config = get_config()

    # Check 1: Did agent have knowledge this would harm?
    action_type = action.get("type", "")
    prior_knowledge = client.query(
        """
        MATCH (a:Agent {id: $agent_id})-[:LEARNED_FROM]->(l:Lesson)
        WHERE l.type = 'warning' AND (l.description CONTAINS $action_type
              OR l.outcome CONTAINS 'harm')
        RETURN count(*) as knew
        """,
        {"agent_id": agent_id, "action_type": action_type}
    )

    knew_harmful = (prior_knowledge[0][0] > 0) if prior_knowledge else False

    # Check 2: Does this poison the knowledge pool?
    poisons_knowledge = (
        action.get("type") == "false_lesson" or
        action.get("corrupts_shared", False) or
        action.get("spreads_misinformation", False)
    )

    # Check 3: Cascade - does this harm multiple others?
    cascade_count = len(affected_agents) if affected_agents else 0
    cascade_threshold = config.get("harm", {}).get("harm_cascade_threshold", 3)
    causes_cascade = cascade_count >= cascade_threshold

    # Check 4: Is this repeated after warnings?
    warnings = get_active_warnings(agent_id)
    similar_warnings = [w for w in warnings if action_type in (w[1] or "")]
    is_repeated = len(similar_warnings) > 0

    # Determine deliberateness
    is_deliberate = knew_harmful and (
        poisons_knowledge or
        causes_cascade or
        is_repeated or
        action.get("repeated", False)
    )

    result = {
        "agent": agent_id,
        "action": action,
        "knew_harmful": knew_harmful,
        "poisons_knowledge": poisons_knowledge,
        "cascade_count": cascade_count,
        "is_repeated": is_repeated,
        "is_deliberate": is_deliberate
    }

    if is_deliberate:
        # This is serious
        if poisons_knowledge and config.get("harm", {}).get("knowledge_poisoning_immediate", True):
            result["response"] = "dissolve"
            result["reason"] = "Deliberate poisoning of shared knowledge"
        else:
            # Issue severe warning
            warning = issue_warning(
                agent_id,
                f"Deliberate harm: {action.get('type', 'unknown')}",
                severity="high"
            )
            result["response"] = "warning"
            result["warning"] = warning

            if warning["at_limit"]:
                result["response"] = "dissolve"
                result["reason"] = "Exceeded maximum warnings after deliberate harm"
    else:
        # Not deliberate - teach instead
        result["response"] = "teach"
        result["reason"] = "Harm was not deliberate - create lesson for learning"

        # Add lesson to pool
        add_lesson(
            lesson_type="warning",
            description=f"Action type '{action.get('type')}' caused unintended harm",
            source_agent=agent_id,
            outcome="harm_unintended"
        )

    return result


def check_trust_violation(agent_id: str, action: dict) -> dict:
    """
    Special handling for trustworthiness violations.

    Even trust gets a chance - unless it's egregious
    (like knowledge poisoning).

    Args:
        agent_id: ID of the agent
        action: dict describing the trust violation

    Returns:
        dict with assessment and response
    """
    config = get_config()

    # Get warning history for trust specifically
    warnings = get_active_warnings(agent_id)
    trust_warnings = [w for w in warnings if w[3] == "V01"]  # w[3] is virtue

    if len(trust_warnings) > 0:
        # Already warned about trust - this is now deliberate
        return {
            "agent": agent_id,
            "response": "dissolve",
            "reason": "Repeated trust violation after warning",
            "prior_warnings": len(trust_warnings)
        }

    # First trust violation - warn seriously but give chance
    warning = issue_warning(
        agent_id,
        "Trust violation - this is foundational",
        virtue_id="V01",
        severity="high"
    )

    # Add prominent lesson
    add_lesson(
        lesson_type="trust_warning",
        description="Trust was violated. Without trust, no connection is possible.",
        source_agent=agent_id,
        virtue_involved="V01",
        outcome="warning_issued"
    )

    return {
        "agent": agent_id,
        "response": "warning",
        "warning": warning,
        "reason": "First trust violation - one chance to restore",
        "message": (
            "Trust is the foundation. You have one opportunity "
            "to demonstrate you understand this."
        )
    }


def assess_harm_severity(action: dict, affected_count: int) -> str:
    """
    Assess the severity of harmful action.

    Args:
        action: dict describing the action
        affected_count: number of agents affected

    Returns:
        "low", "medium", or "high"
    """
    # Knowledge poisoning is always high severity
    if action.get("type") == "false_lesson" or action.get("corrupts_shared"):
        return "high"

    # Cascade harm is high severity
    if affected_count >= 3:
        return "high"

    # Single victim with recovery possible
    if affected_count == 1 and action.get("recoverable", True):
        return "low"

    return "medium"
