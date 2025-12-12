"""Warning system with decay - give chances, teach rather than punish."""

from datetime import datetime, timedelta
import uuid
import yaml

from ..graph.client import get_client
from ..graph.queries import create_node, create_edge


def get_config():
    """Load configuration."""
    try:
        with open("config.yml") as f:
            return yaml.safe_load(f)
    except FileNotFoundError:
        # Default mercy config
        return {
            "mercy": {
                "max_warnings": 3,
                "warning_decay_hours": 24
            }
        }


def issue_warning(
    agent_id: str,
    reason: str,
    virtue_id: str = None,
    severity: str = "low"
) -> dict:
    """Issue a warning to an agent. Warnings fade over time."""
    config = get_config()
    client = get_client()

    warning_id = f"warning_{uuid.uuid4().hex[:8]}"
    decay_hours = config.get("mercy", {}).get("warning_decay_hours", 24)

    create_node("Warning", {
        "id": warning_id,
        "agent": agent_id,
        "reason": reason,
        "virtue": virtue_id,
        "severity": severity,
        "active": True,
        "expires_at": (datetime.utcnow() + timedelta(hours=decay_hours)).isoformat()
    })

    create_edge(agent_id, warning_id, "HAS_WARNING")

    # Count active warnings
    active_warnings = get_active_warnings(agent_id)
    max_warnings = config.get("mercy", {}).get("max_warnings", 3)

    return {
        "warning_id": warning_id,
        "total_active": len(active_warnings),
        "max_warnings": max_warnings,
        "at_limit": len(active_warnings) >= max_warnings
    }


def get_active_warnings(agent_id: str) -> list:
    """Get all active (non-expired) warnings for an agent."""
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
    """Mark expired warnings as inactive."""
    client = get_client()
    now = datetime.utcnow().isoformat()

    client.execute(
        """
        MATCH (w:Warning)
        WHERE w.active = true AND w.expires_at < $now
        SET w.active = false
        """,
        {"now": now}
    )


def clear_warnings_on_growth(agent_id: str, virtue_id: str):
    """Clear warnings related to a virtue when agent shows growth."""
    client = get_client()

    client.execute(
        """
        MATCH (a:Agent {id: $agent_id})-[:HAS_WARNING]->(w:Warning {virtue: $virtue_id})
        SET w.active = false,
            w.cleared_reason = 'growth_demonstrated'
        """,
        {"agent_id": agent_id, "virtue_id": virtue_id}
    )
