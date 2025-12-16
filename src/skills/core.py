"""
Core skill operations.

Functions for creating, using, and managing skill nodes.
"""

import logging
from datetime import datetime
from typing import Any

from ..graph.client import get_client
from ..graph.queries import create_node, create_edge, get_node
from ..models import Skill, SkillType, NodeType, EdgeType

logger = logging.getLogger(__name__)


def create_skill(skill: Skill, agent_id: str | None = None) -> Skill:
    """
    Create a skill node in the graph.

    Args:
        skill: The skill definition
        agent_id: Optional agent to bind this skill to

    Returns:
        The created skill
    """
    client = get_client()

    # Create the skill node
    create_node("Skill", {
        "id": skill.id,
        "name": skill.name,
        "description": skill.description,
        "skill_type": skill.skill_type.value,
        "domain": skill.domain,
        "mastery_level": skill.mastery_level,
        "mastery_floor": skill.mastery_floor,
        "decay_rate": skill.decay_rate,
        "activation_cost": skill.activation_cost,
        "cooldown_steps": skill.cooldown_steps,
        "tool_id": skill.tool_id,
        "use_count": skill.use_count,
        "type": NodeType.SKILL.value,
    })

    # Create edges to prerequisite skills
    for prereq_id in skill.prerequisite_skills:
        create_edge(skill.id, prereq_id, EdgeType.DUTY_REQUIRES.value, {
            "weight": 0.9,
            "reason": f"Skill {skill.name} requires skill {prereq_id}",
        })

    # Create edges to required virtues
    for virtue_id in skill.required_virtues:
        create_edge(skill.id, virtue_id, EdgeType.VIRTUE_REQUIRES.value, {
            "weight": 0.7,
            "reason": f"Skill {skill.name} requires virtue {virtue_id}",
        })

    # Create edge to tool if specified
    if skill.tool_id:
        create_edge(skill.id, skill.tool_id, EdgeType.SKILL_USES.value, {
            "weight": 1.0,
            "reason": f"Skill {skill.name} uses tool {skill.tool_id}",
        })

    # If agent specified, bind skill to agent
    if agent_id:
        create_edge(agent_id, skill.id, EdgeType.CONNECTS.value, {
            "weight": 1.0,
            "reason": f"Agent {agent_id} has skill {skill.name}",
        })

    logger.info(f"Created skill: {skill.id} ({skill.name})")
    return skill


def get_skill(skill_id: str) -> Skill | None:
    """
    Get a skill by ID.

    Args:
        skill_id: The skill ID

    Returns:
        The skill if found, None otherwise
    """
    client = get_client()
    result = client.query(
        """
        MATCH (s:Skill {id: $id})
        RETURN s
        """,
        {"id": skill_id}
    )

    if not result:
        return None

    props = result[0][0].properties
    return _props_to_skill(props)


def use_skill(skill_id: str, agent_id: str) -> dict[str, Any]:
    """
    Use a skill, updating mastery and state.

    Args:
        skill_id: The skill ID
        agent_id: The agent using the skill

    Returns:
        Result dict with success status and any messages
    """
    client = get_client()

    # Check prerequisites
    prereq_check = check_skill_prerequisites(skill_id)
    if not prereq_check["met"]:
        return {
            "success": False,
            "reason": "prerequisites_not_met",
            "missing": prereq_check["missing"],
        }

    # Update the skill state
    now = datetime.utcnow().isoformat()
    client.query(
        """
        MATCH (s:Skill {id: $id})
        SET s.last_used = $now,
            s.use_count = s.use_count + 1,
            s.mastery_level = CASE
                WHEN s.mastery_level < 1.0
                THEN s.mastery_level + 0.01
                ELSE 1.0
            END
        """,
        {"id": skill_id, "now": now}
    )

    logger.info(f"Agent {agent_id} used skill {skill_id}")
    return {"success": True, "skill_id": skill_id}


def update_mastery(skill_id: str, delta: float) -> float:
    """
    Update a skill's mastery level.

    Args:
        skill_id: The skill ID
        delta: Change in mastery (positive or negative)

    Returns:
        New mastery level
    """
    client = get_client()

    # Get current mastery and floor
    result = client.query(
        """
        MATCH (s:Skill {id: $id})
        RETURN s.mastery_level, s.mastery_floor
        """,
        {"id": skill_id}
    )

    if not result:
        return 0.0

    current, floor = result[0]
    new_mastery = max(floor, min(1.0, current + delta))

    client.query(
        """
        MATCH (s:Skill {id: $id})
        SET s.mastery_level = $new_mastery
        """,
        {"id": skill_id, "new_mastery": new_mastery}
    )

    return new_mastery


def check_skill_prerequisites(skill_id: str) -> dict[str, Any]:
    """
    Check if a skill's prerequisites are met.

    Args:
        skill_id: The skill ID

    Returns:
        Dict with met status and missing prerequisites
    """
    client = get_client()

    # Check prerequisite skills
    result = client.query(
        """
        MATCH (s:Skill {id: $id})-[:DUTY_REQUIRES]->(prereq:Skill)
        WHERE prereq.mastery_level < prereq.mastery_floor
        RETURN prereq.id
        """,
        {"id": skill_id}
    )

    missing_skills = [row[0] for row in result or []]

    # Check required virtues
    virtue_result = client.query(
        """
        MATCH (s:Skill {id: $id})-[:VIRTUE_REQUIRES]->(v:VirtueAnchor)
        WHERE v.activation < 0.5
        RETURN v.id
        """,
        {"id": skill_id}
    )

    missing_virtues = [row[0] for row in virtue_result or []]

    return {
        "met": len(missing_skills) == 0 and len(missing_virtues) == 0,
        "missing_skills": missing_skills,
        "missing_virtues": missing_virtues,
        "missing": missing_skills + missing_virtues,
    }


def get_skills_for_agent(agent_id: str) -> list[Skill]:
    """
    Get all skills for an agent.

    Args:
        agent_id: The agent ID

    Returns:
        List of skills
    """
    client = get_client()

    result = client.query(
        """
        MATCH (a:Agent {id: $agent_id})-[:CONNECTS]->(s:Skill)
        RETURN s
        ORDER BY s.mastery_level DESC
        """,
        {"agent_id": agent_id}
    )

    return [_props_to_skill(row[0].properties) for row in result or []]


def decay_unused_skills(agent_id: str | None = None, min_hours_since_use: int = 168) -> int:
    """
    Apply decay to skills that haven't been used recently.

    Args:
        agent_id: Optional agent filter
        min_hours_since_use: Hours since last use before decay applies (default: 1 week)

    Returns:
        Number of skills decayed
    """
    client = get_client()

    cutoff = datetime.utcnow().isoformat()

    if agent_id:
        query = """
        MATCH (a:Agent {id: $agent_id})-[:CONNECTS]->(s:Skill)
        WHERE s.last_used IS NOT NULL
          AND s.mastery_level > s.mastery_floor
        SET s.mastery_level = CASE
            WHEN s.mastery_level - s.decay_rate < s.mastery_floor
            THEN s.mastery_floor
            ELSE s.mastery_level - s.decay_rate
        END
        RETURN count(s)
        """
        result = client.query(query, {"agent_id": agent_id})
    else:
        query = """
        MATCH (s:Skill)
        WHERE s.last_used IS NOT NULL
          AND s.mastery_level > s.mastery_floor
        SET s.mastery_level = CASE
            WHEN s.mastery_level - s.decay_rate < s.mastery_floor
            THEN s.mastery_floor
            ELSE s.mastery_level - s.decay_rate
        END
        RETURN count(s)
        """
        result = client.query(query)

    count = result[0][0] if result else 0
    logger.info(f"Decayed {count} skills")
    return count


def _props_to_skill(props: dict) -> Skill:
    """Convert graph properties to a Skill object."""
    return Skill(
        id=props["id"],
        name=props["name"],
        description=props["description"],
        skill_type=SkillType(props.get("skill_type", "hard")),
        domain=props.get("domain", ""),
        mastery_level=props.get("mastery_level", 0.0),
        mastery_floor=props.get("mastery_floor", 0.0),
        decay_rate=props.get("decay_rate", 0.01),
        activation_cost=props.get("activation_cost", 0.0),
        cooldown_steps=props.get("cooldown_steps", 0),
        tool_id=props.get("tool_id"),
        use_count=props.get("use_count", 0),
    )
