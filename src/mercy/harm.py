"""Detect deliberate harm vs honest mistakes."""

import yaml

from ..graph.client import get_client
from ..knowledge.pool import add_lesson
from .chances import issue_warning, get_active_warnings


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
            }
        }


def detect_deliberate_harm(
    agent_id: str,
    action: dict,
    affected_agents: list = None
) -> dict:
    """
    Determine if an action constitutes deliberate harm.
    Deliberate = agent knew it would cause harm and did it anyway.
    """
    client = get_client()
    config = get_config()

    # Check 1: Did agent have knowledge this would harm?
    # Look for lessons they've accessed about this type of action
    prior_knowledge = client.query(
        """
        MATCH (a:Agent {id: $agent_id})-[:LEARNED_FROM]->(l:Lesson)
        WHERE l.type = 'warning' AND l.description CONTAINS $action_type
        RETURN count(*) as knew
        """,
        {"agent_id": agent_id, "action_type": action.get("type", "")}
    )

    knew_harmful = prior_knowledge[0][0] > 0 if prior_knowledge else False

    # Check 2: Does this poison the knowledge pool?
    poisons_knowledge = action.get("type") == "false_lesson" or action.get("corrupts_shared", False)

    # Check 3: Cascade - does this harm multiple others?
    cascade_count = len(affected_agents) if affected_agents else 0
    cascade_threshold = config.get("harm", {}).get("harm_cascade_threshold", 3)
    causes_cascade = cascade_count >= cascade_threshold

    # Determine deliberateness
    is_deliberate = knew_harmful and (poisons_knowledge or causes_cascade or action.get("repeated", False))

    result = {
        "agent": agent_id,
        "action": action,
        "knew_harmful": knew_harmful,
        "poisons_knowledge": poisons_knowledge,
        "cascade_count": cascade_count,
        "is_deliberate": is_deliberate
    }

    if is_deliberate:
        # This is serious
        knowledge_poisoning_immediate = config.get("harm", {}).get("knowledge_poisoning_immediate", True)
        if poisons_knowledge and knowledge_poisoning_immediate:
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
    Even trust gets a chance, unless it's egregious.
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
            "reason": "Repeated trust violation after warning"
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
        "message": "Trust is the foundation. You have one opportunity to demonstrate you understand this."
    }
