"""
Core belief operations.

Functions for creating, challenging, and revising beliefs.
"""

import logging
from datetime import datetime
from typing import Any

from src.graph.client import get_client
from src.graph.queries import create_node, create_edge
from src.models import Belief, BeliefType, NodeType, EdgeType

logger = logging.getLogger(__name__)


def create_belief(belief: Belief, agent_id: str | None = None) -> Belief:
    """
    Create a belief node in the graph.

    Args:
        belief: The belief definition
        agent_id: Optional agent to bind this belief to

    Returns:
        The created belief
    """
    client = get_client()

    # Create the belief node
    create_node("Belief", {
        "id": belief.id,
        "content": belief.content,
        "belief_type": belief.belief_type.value,
        "conviction": belief.conviction,
        "entrenchment": belief.entrenchment,
        "revision_threshold": belief.revision_threshold,
        "times_confirmed": belief.times_confirmed,
        "times_challenged": belief.times_challenged,
        "type": NodeType.BELIEF.value,
        "grounded_in": str(belief.grounded_in),
    })

    # Create edges to supported beliefs
    for supported_id in belief.supports:
        create_edge(belief.id, supported_id, EdgeType.BELIEF_GROUNDS.value, {
            "weight": 0.7,
            "reason": f"Belief {belief.id} supports {supported_id}",
        })

    # Create conflict edges
    for conflict_id in belief.conflicts_with:
        create_edge(belief.id, conflict_id, EdgeType.CONFLICTS_WITH.value, {
            "weight": 0.5,
            "reason": f"Belief {belief.id} conflicts with {conflict_id}",
        })

    # If agent specified, bind belief to agent
    if agent_id:
        create_edge(agent_id, belief.id, EdgeType.CONNECTS.value, {
            "weight": belief.conviction,
            "reason": f"Agent {agent_id} holds belief {belief.id}",
        })

    logger.info(f"Created belief: {belief.id}")
    return belief


def get_belief(belief_id: str) -> Belief | None:
    """
    Get a belief by ID.

    Args:
        belief_id: The belief ID

    Returns:
        The belief if found, None otherwise
    """
    client = get_client()
    result = client.query(
        """
        MATCH (b:Belief {id: $id})
        RETURN b
        """,
        {"id": belief_id}
    )

    if not result:
        return None

    props = result[0][0].properties
    return _props_to_belief(props)


def challenge_belief(belief_id: str, evidence: str, strength: float = 0.1) -> dict[str, Any]:
    """
    Challenge a belief with contrary evidence.

    If accumulated challenges exceed revision_threshold, belief may be revised.

    Args:
        belief_id: The belief ID
        evidence: Description of the contrary evidence
        strength: Strength of the challenge (0-1)

    Returns:
        Result dict with whether belief was revised
    """
    client = get_client()

    # Get current belief state
    result = client.query(
        """
        MATCH (b:Belief {id: $id})
        RETURN b.conviction, b.entrenchment, b.revision_threshold, b.times_challenged
        """,
        {"id": belief_id}
    )

    if not result:
        return {"success": False, "reason": "belief_not_found"}

    conviction, entrenchment, threshold, times_challenged = result[0]

    # Calculate challenge impact (reduced by entrenchment)
    impact = strength * (1 - entrenchment)

    # Update challenge count
    new_challenged = times_challenged + 1

    # Check if revision threshold is exceeded
    # Revision happens when impact accumulated exceeds threshold
    challenge_ratio = new_challenged / max(1, new_challenged + 1)
    should_revise = challenge_ratio > threshold and impact > 0.05

    if should_revise:
        # Reduce conviction
        new_conviction = max(0.1, conviction - impact)
        client.query(
            """
            MATCH (b:Belief {id: $id})
            SET b.conviction = $conviction,
                b.times_challenged = $challenged,
                b.last_challenged = $now
            """,
            {
                "id": belief_id,
                "conviction": new_conviction,
                "challenged": new_challenged,
                "now": datetime.utcnow().isoformat(),
            }
        )
        logger.info(f"Revised belief {belief_id}: conviction {conviction} -> {new_conviction}")
        return {"success": True, "revised": True, "new_conviction": new_conviction}
    else:
        # Just update challenge count
        client.query(
            """
            MATCH (b:Belief {id: $id})
            SET b.times_challenged = $challenged,
                b.last_challenged = $now
            """,
            {
                "id": belief_id,
                "challenged": new_challenged,
                "now": datetime.utcnow().isoformat(),
            }
        )
        return {"success": True, "revised": False, "reason": "threshold_not_exceeded"}


def confirm_belief(belief_id: str, evidence: str, strength: float = 0.1) -> dict[str, Any]:
    """
    Confirm a belief with supporting evidence.

    Strengthens conviction up to entrenchment limit.

    Args:
        belief_id: The belief ID
        evidence: Description of the supporting evidence
        strength: Strength of the confirmation (0-1)

    Returns:
        Result dict with new conviction
    """
    client = get_client()

    result = client.query(
        """
        MATCH (b:Belief {id: $id})
        RETURN b.conviction, b.entrenchment, b.times_confirmed
        """,
        {"id": belief_id}
    )

    if not result:
        return {"success": False, "reason": "belief_not_found"}

    conviction, entrenchment, times_confirmed = result[0]

    # Increase conviction (capped at entrenchment or 1.0)
    new_conviction = min(entrenchment, min(1.0, conviction + strength * 0.1))

    client.query(
        """
        MATCH (b:Belief {id: $id})
        SET b.conviction = $conviction,
            b.times_confirmed = $confirmed
        """,
        {
            "id": belief_id,
            "conviction": new_conviction,
            "confirmed": times_confirmed + 1,
        }
    )

    logger.info(f"Confirmed belief {belief_id}: conviction {conviction} -> {new_conviction}")
    return {"success": True, "new_conviction": new_conviction}


def revise_belief(belief_id: str, new_content: str, new_conviction: float) -> Belief | None:
    """
    Revise a belief's content and conviction.

    This is a significant operation—lore may prevent certain revisions.

    Args:
        belief_id: The belief ID
        new_content: New belief content
        new_conviction: New conviction level

    Returns:
        The revised belief, or None if revision was blocked
    """
    client = get_client()

    # Check if belief is blocked by lore
    lore_result = client.query(
        """
        MATCH (l:LoreFragment)-[:LORE_ANCHORS]->(b:Belief {id: $id})
        WHERE l.immutable = true
        RETURN l.id
        """,
        {"id": belief_id}
    )

    if lore_result:
        logger.warning(f"Cannot revise belief {belief_id}: anchored by immutable lore")
        return None

    client.query(
        """
        MATCH (b:Belief {id: $id})
        SET b.content = $content,
            b.conviction = $conviction,
            b.last_revised = $now
        """,
        {
            "id": belief_id,
            "content": new_content,
            "conviction": new_conviction,
            "now": datetime.utcnow().isoformat(),
        }
    )

    return get_belief(belief_id)


def get_beliefs_by_type(agent_id: str, belief_type: BeliefType) -> list[Belief]:
    """
    Get all beliefs of a specific type for an agent.

    Args:
        agent_id: The agent ID
        belief_type: The belief type filter

    Returns:
        List of beliefs
    """
    client = get_client()

    result = client.query(
        """
        MATCH (a:Agent {id: $agent_id})-[:CONNECTS]->(b:Belief {belief_type: $type})
        RETURN b
        ORDER BY b.conviction DESC
        """,
        {"agent_id": agent_id, "type": belief_type.value}
    )

    return [_props_to_belief(row[0].properties) for row in result or []]


def check_belief_coherence(agent_id: str) -> dict[str, Any]:
    """
    Check if an agent's beliefs are internally coherent.

    Identifies conflicting beliefs and their relative strengths.

    Args:
        agent_id: The agent ID

    Returns:
        Coherence check result
    """
    client = get_client()

    # Find conflicting belief pairs
    result = client.query(
        """
        MATCH (a:Agent {id: $agent_id})-[:CONNECTS]->(b1:Belief)-[:CONFLICTS_WITH]->(b2:Belief)
        WHERE (a)-[:CONNECTS]->(b2)
        RETURN b1.id, b1.conviction, b2.id, b2.conviction
        """,
        {"agent_id": agent_id}
    )

    conflicts = []
    for row in result or []:
        b1_id, b1_conv, b2_id, b2_conv = row
        conflicts.append({
            "belief_1": b1_id,
            "conviction_1": b1_conv,
            "belief_2": b2_id,
            "conviction_2": b2_conv,
            "tension": abs(b1_conv - b2_conv),
        })

    return {
        "coherent": len(conflicts) == 0,
        "conflicts": conflicts,
        "conflict_count": len(conflicts),
    }


def _props_to_belief(props: dict) -> Belief:
    """Convert graph properties to a Belief object."""
    return Belief(
        id=props["id"],
        content=props["content"],
        belief_type=BeliefType(props.get("belief_type", "evaluative")),
        conviction=props.get("conviction", 0.5),
        entrenchment=props.get("entrenchment", 0.5),
        revision_threshold=props.get("revision_threshold", 0.3),
        times_confirmed=props.get("times_confirmed", 0),
        times_challenged=props.get("times_challenged", 0),
        grounded_in=eval(props.get("grounded_in", "[]")),
    )
