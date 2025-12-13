"""
Core lore operations.

Functions for creating, querying, and anchoring lore fragments.
"""

import logging
from datetime import datetime
from typing import Any

from src.graph.client import get_client
from src.graph.queries import create_node, create_edge
from src.models import LoreFragment, NodeType, EdgeType

logger = logging.getLogger(__name__)


def create_lore_fragment(lore: LoreFragment, agent_id: str | None = None) -> LoreFragment:
    """
    Create a lore fragment in the graph.

    Args:
        lore: The lore fragment
        agent_id: Optional agent to bind this lore to

    Returns:
        The created lore fragment
    """
    client = get_client()

    # Create the lore node
    create_node("LoreFragment", {
        "id": lore.id,
        "content": lore.content,
        "fragment_type": lore.fragment_type,
        "salience": lore.salience,
        "immutable": lore.immutable,
        "type": NodeType.LORE_FRAGMENT.value,
    })

    # Create anchoring edges
    for anchor_id in lore.anchors:
        create_edge(lore.id, anchor_id, EdgeType.LORE_ANCHORS.value, {
            "weight": lore.salience,
            "immutable": lore.immutable,
            "reason": f"Lore {lore.id} anchors {anchor_id}",
        })

    # If agent specified, bind lore to agent
    if agent_id:
        create_edge(agent_id, lore.id, EdgeType.CONNECTS.value, {
            "weight": 1.0,
            "reason": f"Agent {agent_id} carries lore {lore.id}",
        })

    logger.info(f"Created lore fragment: {lore.id} ({lore.fragment_type})")
    return lore


def get_lore_fragment(lore_id: str) -> LoreFragment | None:
    """
    Get a lore fragment by ID.

    Args:
        lore_id: The lore ID

    Returns:
        The lore fragment if found, None otherwise
    """
    client = get_client()
    result = client.query(
        """
        MATCH (l:LoreFragment {id: $id})
        RETURN l
        """,
        {"id": lore_id}
    )

    if not result:
        return None

    props = result[0][0].properties
    return _props_to_lore(props)


def get_origin_story(agent_id: str) -> str | None:
    """
    Get the origin story for an agent.

    Args:
        agent_id: The agent ID

    Returns:
        The origin story content, or None
    """
    client = get_client()
    result = client.query(
        """
        MATCH (a:Agent {id: $agent_id})-[:CONNECTS]->(l:LoreFragment {fragment_type: 'origin'})
        RETURN l.content
        ORDER BY l.salience DESC
        LIMIT 1
        """,
        {"agent_id": agent_id}
    )

    if result:
        return result[0][0]
    return None


def get_sacred_commitments(agent_id: str) -> list[str]:
    """
    Get all sacred commitments for an agent.

    Args:
        agent_id: The agent ID

    Returns:
        List of commitment contents
    """
    client = get_client()
    result = client.query(
        """
        MATCH (a:Agent {id: $agent_id})-[:CONNECTS]->(l:LoreFragment {fragment_type: 'commitment'})
        RETURN l.content
        ORDER BY l.salience DESC
        """,
        {"agent_id": agent_id}
    )

    return [row[0] for row in result or []]


def get_taboos(agent_id: str) -> list[str]:
    """
    Get all taboos for an agent.

    Args:
        agent_id: The agent ID

    Returns:
        List of taboo contents
    """
    client = get_client()
    result = client.query(
        """
        MATCH (a:Agent {id: $agent_id})-[:CONNECTS]->(l:LoreFragment {fragment_type: 'taboo'})
        RETURN l.id, l.content
        ORDER BY l.salience DESC
        """,
        {"agent_id": agent_id}
    )

    return [{"id": row[0], "content": row[1]} for row in result or []]


def check_taboo_violation(agent_id: str, action: str) -> dict[str, Any]:
    """
    Check if an action would violate any taboos.

    This is a simple keyword-based check. In production, this would
    use more sophisticated semantic matching.

    Args:
        agent_id: The agent ID
        action: Description of the proposed action

    Returns:
        Violation check result
    """
    taboos = get_taboos(agent_id)
    violations = []

    action_lower = action.lower()

    for taboo in taboos:
        taboo_content = taboo["content"].lower()

        # Simple keyword matching (would be more sophisticated in production)
        if "recommend debt" in action_lower and "debt" in taboo_content:
            violations.append(taboo)
        elif "judge" in action_lower and "judge" in taboo_content:
            violations.append(taboo)
        elif "share" in action_lower and "private" in taboo_content:
            violations.append(taboo)
        elif "give up" in action_lower and "give up" in taboo_content:
            violations.append(taboo)

    return {
        "violated": len(violations) > 0,
        "violations": violations,
    }


def anchor_identity(agent_id: str, target_id: str, lore_id: str) -> bool:
    """
    Create an anchoring relationship between lore and a target.

    Args:
        agent_id: The agent ID
        target_id: The belief/kuleana/virtue being anchored
        lore_id: The lore fragment providing the anchor

    Returns:
        True if anchored successfully
    """
    client = get_client()

    # Verify the lore belongs to the agent
    result = client.query(
        """
        MATCH (a:Agent {id: $agent_id})-[:CONNECTS]->(l:LoreFragment {id: $lore_id})
        RETURN l
        """,
        {"agent_id": agent_id, "lore_id": lore_id}
    )

    if not result:
        logger.warning(f"Cannot anchor: lore {lore_id} not found for agent {agent_id}")
        return False

    # Create the anchoring edge
    lore = _props_to_lore(result[0][0].properties)
    create_edge(lore_id, target_id, EdgeType.LORE_ANCHORS.value, {
        "weight": lore.salience,
        "immutable": lore.immutable,
    })

    logger.info(f"Anchored {target_id} with lore {lore_id}")
    return True


def get_lore_for_agent(agent_id: str) -> list[LoreFragment]:
    """
    Get all lore fragments for an agent.

    Args:
        agent_id: The agent ID

    Returns:
        List of lore fragments ordered by salience
    """
    client = get_client()

    result = client.query(
        """
        MATCH (a:Agent {id: $agent_id})-[:CONNECTS]->(l:LoreFragment)
        RETURN l
        ORDER BY l.salience DESC
        """,
        {"agent_id": agent_id}
    )

    return [_props_to_lore(row[0].properties) for row in result or []]


def _props_to_lore(props: dict) -> LoreFragment:
    """Convert graph properties to a LoreFragment object."""
    return LoreFragment(
        id=props["id"],
        content=props["content"],
        fragment_type=props.get("fragment_type", "origin"),
        salience=props.get("salience", 0.5),
        immutable=props.get("immutable", False),
    )
