"""
Core kuleana operations.

Functions for creating, activating, and managing kuleana (duty) nodes.
"""

import logging
from datetime import datetime
from typing import Any

from src.graph.client import get_client
from src.graph.queries import create_node, create_edge, get_node
from src.models import Kuleana, NodeType, EdgeType

logger = logging.getLogger(__name__)


def create_kuleana(kuleana: Kuleana, agent_id: str | None = None) -> Kuleana:
    """
    Create a kuleana node in the graph.

    Args:
        kuleana: The kuleana definition
        agent_id: Optional agent to bind this kuleana to

    Returns:
        The created kuleana
    """
    client = get_client()

    # Create the kuleana node
    create_node("Kuleana", {
        "id": kuleana.id,
        "name": kuleana.name,
        "description": kuleana.description,
        "domain": kuleana.domain,
        "authority_level": kuleana.authority_level,
        "priority": kuleana.priority,
        "serves": kuleana.serves,
        "accountable_to": kuleana.accountable_to,
        "can_delegate": kuleana.can_delegate,
        "is_active": kuleana.is_active,
        "fulfillment_count": kuleana.fulfillment_count,
        "type": NodeType.KULEANA.value,
        "trigger_conditions": str(kuleana.trigger_conditions),
        "completion_criteria": str(kuleana.completion_criteria),
    })

    # Create edges to required virtues
    for virtue_id in kuleana.required_virtues:
        create_edge(kuleana.id, virtue_id, EdgeType.VIRTUE_REQUIRES.value, {
            "weight": 0.8,
            "reason": f"Kuleana {kuleana.name} requires virtue {virtue_id}",
        })

    # If agent specified, bind kuleana to agent
    if agent_id:
        create_edge(agent_id, kuleana.id, EdgeType.DUTY_REQUIRES.value, {
            "weight": 1.0,
            "reason": f"Agent {agent_id} has kuleana {kuleana.name}",
        })

    logger.info(f"Created kuleana: {kuleana.id} ({kuleana.name})")
    return kuleana


def get_kuleana(kuleana_id: str) -> Kuleana | None:
    """
    Get a kuleana by ID.

    Args:
        kuleana_id: The kuleana ID

    Returns:
        The kuleana if found, None otherwise
    """
    client = get_client()
    result = client.query(
        """
        MATCH (k:Kuleana {id: $id})
        RETURN k
        """,
        {"id": kuleana_id}
    )

    if not result:
        return None

    props = result[0][0].properties
    return _props_to_kuleana(props)


def activate_kuleana(kuleana_id: str, trigger: str) -> bool:
    """
    Activate a kuleana when its trigger conditions are met.

    Args:
        kuleana_id: The kuleana ID
        trigger: The trigger condition that activated it

    Returns:
        True if activated, False otherwise
    """
    client = get_client()

    # Check requirements first
    if not check_kuleana_requirements(kuleana_id):
        logger.warning(f"Cannot activate kuleana {kuleana_id}: requirements not met")
        return False

    # Update the kuleana state
    client.query(
        """
        MATCH (k:Kuleana {id: $id})
        SET k.is_active = true,
            k.last_activated = $now,
            k.current_trigger = $trigger
        """,
        {
            "id": kuleana_id,
            "now": datetime.utcnow().isoformat(),
            "trigger": trigger,
        }
    )

    logger.info(f"Activated kuleana {kuleana_id} via trigger: {trigger}")
    return True


def fulfill_kuleana(kuleana_id: str) -> bool:
    """
    Mark a kuleana as fulfilled.

    Args:
        kuleana_id: The kuleana ID

    Returns:
        True if fulfilled, False otherwise
    """
    client = get_client()

    client.query(
        """
        MATCH (k:Kuleana {id: $id})
        SET k.is_active = false,
            k.fulfillment_count = k.fulfillment_count + 1,
            k.last_fulfilled = $now
        """,
        {
            "id": kuleana_id,
            "now": datetime.utcnow().isoformat(),
        }
    )

    logger.info(f"Fulfilled kuleana {kuleana_id}")
    return True


def check_kuleana_requirements(kuleana_id: str) -> dict[str, Any]:
    """
    Check if a kuleana's requirements are met.

    Returns a dict with:
        - met: bool - whether all requirements are met
        - missing_virtues: list - virtues below threshold
        - missing_skills: list - skills not available

    Args:
        kuleana_id: The kuleana ID

    Returns:
        Requirements check result
    """
    client = get_client()

    # Get required virtues and their activation levels
    virtue_result = client.query(
        """
        MATCH (k:Kuleana {id: $id})-[:VIRTUE_REQUIRES]->(v:VirtueAnchor)
        RETURN v.id, v.activation, v.threshold
        """,
        {"id": kuleana_id}
    )

    missing_virtues = []
    for row in virtue_result or []:
        virtue_id, activation, threshold = row
        # Default threshold for aspirational virtues
        threshold = threshold or 0.6
        if activation < threshold:
            missing_virtues.append(virtue_id)

    # Get required skills and their availability
    skill_result = client.query(
        """
        MATCH (k:Kuleana {id: $id})-[:DUTY_REQUIRES]->(s:Skill)
        RETURN s.id, s.mastery_level, s.mastery_floor
        """,
        {"id": kuleana_id}
    )

    missing_skills = []
    for row in skill_result or []:
        skill_id, mastery, floor = row
        floor = floor or 0.0
        if mastery < floor:
            missing_skills.append(skill_id)

    return {
        "met": len(missing_virtues) == 0 and len(missing_skills) == 0,
        "missing_virtues": missing_virtues,
        "missing_skills": missing_skills,
    }


def get_active_kuleanas(agent_id: str | None = None) -> list[Kuleana]:
    """
    Get all active kuleanas, optionally filtered by agent.

    Args:
        agent_id: Optional agent filter

    Returns:
        List of active kuleanas
    """
    client = get_client()

    if agent_id:
        result = client.query(
            """
            MATCH (a:Agent {id: $agent_id})-[:DUTY_REQUIRES]->(k:Kuleana {is_active: true})
            RETURN k
            """,
            {"agent_id": agent_id}
        )
    else:
        result = client.query(
            """
            MATCH (k:Kuleana {is_active: true})
            RETURN k
            """
        )

    return [_props_to_kuleana(row[0].properties) for row in result or []]


def get_kuleanas_for_agent(agent_id: str) -> list[Kuleana]:
    """
    Get all kuleanas assigned to an agent.

    Args:
        agent_id: The agent ID

    Returns:
        List of kuleanas
    """
    client = get_client()

    result = client.query(
        """
        MATCH (a:Agent {id: $agent_id})-[:DUTY_REQUIRES]->(k:Kuleana)
        RETURN k
        ORDER BY k.priority ASC
        """,
        {"agent_id": agent_id}
    )

    return [_props_to_kuleana(row[0].properties) for row in result or []]


def _props_to_kuleana(props: dict) -> Kuleana:
    """Convert graph properties to a Kuleana object."""
    return Kuleana(
        id=props["id"],
        name=props["name"],
        description=props["description"],
        domain=props.get("domain", ""),
        authority_level=props.get("authority_level", 0.5),
        priority=props.get("priority", 5),
        serves=props.get("serves", ""),
        accountable_to=props.get("accountable_to", ""),
        can_delegate=props.get("can_delegate", False),
        is_active=props.get("is_active", False),
        fulfillment_count=props.get("fulfillment_count", 0),
        trigger_conditions=eval(props.get("trigger_conditions", "[]")),
        completion_criteria=eval(props.get("completion_criteria", "[]")),
    )
