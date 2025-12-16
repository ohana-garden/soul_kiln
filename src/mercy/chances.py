"""Warning and chance management.

Agents get multiple chances before dissolution. Warnings
track issues and fade over time, giving agents opportunity
to learn and improve.
"""

from datetime import datetime, timedelta
import uuid
from ..graph.client import get_client
from ..graph.queries import create_node, create_edge
from ..utils.config import get_config


def issue_warning(
    agent_id: str,
    reason: str,
    virtue_id: str = None,
    severity: str = "low"
) -> dict:
    """
    Issue a warning to an agent.

    Warnings track issues but don't immediately dissolve agents.
    They fade over time, giving agents chance to improve.

    Args:
        agent_id: ID of the agent to warn
        reason: Why the warning is being issued
        virtue_id: Optional virtue the warning relates to
        severity: "low", "medium", or "high"

    Returns:
        dict with warning details and status
    """
    config = get_config()
    client = get_client()

    warning_id = f"warning_{uuid.uuid4().hex[:8]}"
    decay_hours = config.get("mercy", {}).get("warning_decay_hours", 24)
    expires_at = datetime.utcnow() + timedelta(hours=decay_hours)

    create_node("Warning", {
        "id": warning_id,
        "agent": agent_id,
        "reason": reason,
        "virtue": virtue_id,
        "severity": severity,
        "active": True,
        "expires_at": expires_at.isoformat()
    })

    create_edge(agent_id, warning_id, "HAS_WARNING")

    # Count active warnings
    active_warnings = get_active_warnings(agent_id)
    max_warnings = config.get("mercy", {}).get("max_warnings", 3)

    return {
        "warning_id": warning_id,
        "total_active": len(active_warnings),
        "max_warnings": max_warnings,
        "at_limit": len(active_warnings) >= max_warnings,
        "expires_at": expires_at.isoformat()
    }


def get_active_warnings(agent_id: str) -> list:
    """
    Get all active (non-expired) warnings for an agent.

    Args:
        agent_id: ID of the agent

    Returns:
        List of warning tuples (id, reason, severity, virtue, created_at)
    """
    client = get_client()
    now = datetime.utcnow().isoformat()

    return client.query(
        """
        MATCH (a:Agent {id: $agent_id})-[:HAS_WARNING]->(w:Warning)
        WHERE w.active = true AND w.expires_at > $now
        RETURN w.id, w.reason, w.severity, w.virtue, w.created_at
        ORDER BY w.created_at DESC
        """,
        {"agent_id": agent_id, "now": now}
    )


def expire_old_warnings():
    """
    Mark expired warnings as inactive.

    Should be called periodically to clean up old warnings.
    """
    client = get_client()
    now = datetime.utcnow().isoformat()

    client.execute(
        """
        MATCH (w:Warning)
        WHERE w.active = true AND w.expires_at < $now
        SET w.active = false,
            w.expired_at = $now
        """,
        {"now": now}
    )


def clear_warnings_on_growth(agent_id: str, virtue_id: str = None):
    """
    Clear warnings related to a virtue when agent shows growth.

    When an agent demonstrates improvement in an area they
    previously struggled with, we clear related warnings
    as a reward for growth.

    Args:
        agent_id: ID of the agent showing growth
        virtue_id: Optional specific virtue to clear warnings for.
                   If None, clears all warnings with "growth_demonstrated"
    """
    client = get_client()
    now = datetime.utcnow().isoformat()

    if virtue_id:
        client.execute(
            """
            MATCH (a:Agent {id: $agent_id})-[:HAS_WARNING]->(w:Warning)
            WHERE w.virtue = $virtue_id AND w.active = true
            SET w.active = false,
                w.cleared_reason = 'growth_demonstrated',
                w.cleared_at = $now
            """,
            {"agent_id": agent_id, "virtue_id": virtue_id, "now": now}
        )
    else:
        # Clear lowest severity warnings when general growth shown
        client.execute(
            """
            MATCH (a:Agent {id: $agent_id})-[:HAS_WARNING]->(w:Warning)
            WHERE w.active = true AND w.severity = 'low'
            SET w.active = false,
                w.cleared_reason = 'growth_demonstrated',
                w.cleared_at = $now
            """,
            {"agent_id": agent_id, "now": now}
        )


def get_warning_history(agent_id: str, include_expired: bool = False) -> list:
    """
    Get full warning history for an agent.

    Args:
        agent_id: ID of the agent
        include_expired: Whether to include expired warnings

    Returns:
        List of all warnings (active and optionally expired)
    """
    client = get_client()

    if include_expired:
        return client.query(
            """
            MATCH (a:Agent {id: $agent_id})-[:HAS_WARNING]->(w:Warning)
            RETURN w.id, w.reason, w.severity, w.virtue, w.active,
                   w.created_at, w.cleared_reason
            ORDER BY w.created_at DESC
            """,
            {"agent_id": agent_id}
        )
    else:
        return get_active_warnings(agent_id)


def count_warnings_by_severity(agent_id: str) -> dict:
    """
    Count active warnings by severity level.

    Args:
        agent_id: ID of the agent

    Returns:
        dict with counts per severity level
    """
    warnings = get_active_warnings(agent_id)
    counts = {"low": 0, "medium": 0, "high": 0}

    for warning in warnings:
        severity = warning[2] if len(warning) > 2 else "low"
        if severity in counts:
            counts[severity] += 1

    return counts
