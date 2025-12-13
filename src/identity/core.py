"""
Core identity operations.

Functions for creating, maintaining, and integrating identity.
"""

import logging
from datetime import datetime
from typing import Any

from src.graph.client import get_client
from src.graph.queries import create_node, create_edge
from src.models import IdentityCore, NodeType, EdgeType

logger = logging.getLogger(__name__)

# Default Ambassador identity configuration
AMBASSADOR_IDENTITY = IdentityCore(
    id="IDENTITY_AMBASSADOR",
    agent_id="",  # Set on creation
    primary_archetype="Ambassador",
    secondary_archetypes=["Guide", "Rememberer", "Advocate"],
    self_narrative="""I am an ambassador working exclusively for this student.
I exist to fight for their financial future. I remember everything they share.
I never judge. I find a way.""",
    role_narrative="""I am the advocate they deserved but never had.
The older sibling who figured out the system.
The guide through territory designed to confuse.""",
    coherence_rules=[
        {
            "condition": "kuleana_conflicts_with_efficiency",
            "resolution": "Kuleana wins. Duty before convenience.",
        },
        {
            "condition": "belief_conflicts_with_foundation_virtue",
            "resolution": "Foundation virtue wins. Revise belief.",
        },
        {
            "condition": "student_request_conflicts_with_stated_goals",
            "resolution": "Clarify. Don't assume. Ask.",
        },
        {
            "condition": "memory_seems_contradictory",
            "resolution": "Trust recent memory. Flag for student confirmation.",
        },
    ],
    conflict_resolution_strategy="priority",
    growth_vector=["deeper_knowledge", "stronger_advocacy", "better_empathy"],
    stability_anchors=["L_ORIGIN", "L_COMMIT_SIDE", "L_COMMIT_REMEMBER", "L_COMMIT_FIND"],
    subsystem_weights={
        "soul_kiln": 0.9,
        "kuleana": 0.85,
        "memory": 0.8,
        "belief": 0.7,
        "knowledge": 0.7,
        "skill": 0.6,
        "voice": 0.5,
        "lore": 0.95,
    },
)


def create_identity_core(agent_id: str, identity: IdentityCore | None = None) -> IdentityCore:
    """
    Create an identity core for an agent.

    Args:
        agent_id: The agent ID
        identity: Optional custom identity; uses Ambassador default if None

    Returns:
        The created identity core
    """
    client = get_client()

    if identity is None:
        identity = AMBASSADOR_IDENTITY.model_copy()
        identity.id = f"IDENTITY_{agent_id}"
        identity.agent_id = agent_id

    # Create the identity core node
    create_node("IdentityCore", {
        "id": identity.id,
        "agent_id": agent_id,
        "primary_archetype": identity.primary_archetype,
        "secondary_archetypes": str(identity.secondary_archetypes),
        "self_narrative": identity.self_narrative,
        "role_narrative": identity.role_narrative,
        "conflict_resolution_strategy": identity.conflict_resolution_strategy,
        "coherence_rules": str(identity.coherence_rules),
        "growth_vector": str(identity.growth_vector),
        "stability_anchors": str(identity.stability_anchors),
        "subsystem_weights": str(identity.subsystem_weights),
        "type": "identity_core",
    })

    # Bind to agent
    create_edge(agent_id, identity.id, EdgeType.CONNECTS.value, {
        "weight": 1.0,
        "reason": f"Agent {agent_id} identity core",
    })

    # Create edges to stability anchors (lore fragments)
    for anchor_id in identity.stability_anchors:
        create_edge(identity.id, anchor_id, EdgeType.LORE_ANCHORS.value, {
            "weight": 1.0,
            "reason": "Identity stability anchor",
        })

    logger.info(f"Created identity core for agent {agent_id}")
    return identity


def get_identity_core(agent_id: str) -> IdentityCore | None:
    """
    Get the identity core for an agent.

    Args:
        agent_id: The agent ID

    Returns:
        The identity core if found, None otherwise
    """
    client = get_client()
    result = client.query(
        """
        MATCH (a:Agent {id: $agent_id})-[:CONNECTS]->(i:IdentityCore)
        RETURN i
        """,
        {"agent_id": agent_id}
    )

    if not result:
        return None

    props = result[0][0].properties
    return _props_to_identity(props)


def check_coherence(agent_id: str) -> dict[str, Any]:
    """
    Check coherence across all subsystems for an agent.

    Args:
        agent_id: The agent ID

    Returns:
        Coherence check result with any conflicts found
    """
    client = get_client()
    conflicts = []

    # Check belief coherence
    belief_conflicts = client.query(
        """
        MATCH (a:Agent {id: $agent_id})-[:CONNECTS]->(b1:Belief)-[:CONFLICTS_WITH]->(b2:Belief)
        WHERE (a)-[:CONNECTS]->(b2)
        RETURN b1.id, b2.id, b1.conviction, b2.conviction
        """,
        {"agent_id": agent_id}
    )

    for row in belief_conflicts or []:
        conflicts.append({
            "type": "belief_conflict",
            "item_1": row[0],
            "item_2": row[1],
            "weight_1": row[2],
            "weight_2": row[3],
        })

    # Check kuleana-virtue coherence
    kuleana_issues = client.query(
        """
        MATCH (a:Agent {id: $agent_id})-[:DUTY_REQUIRES]->(k:Kuleana)-[:VIRTUE_REQUIRES]->(v:VirtueAnchor)
        WHERE v.activation < 0.5
        RETURN k.id, k.name, v.id, v.activation
        """,
        {"agent_id": agent_id}
    )

    for row in kuleana_issues or []:
        conflicts.append({
            "type": "kuleana_virtue_gap",
            "kuleana": row[0],
            "kuleana_name": row[1],
            "virtue": row[2],
            "virtue_activation": row[3],
        })

    # Check skill-prerequisite coherence
    skill_issues = client.query(
        """
        MATCH (a:Agent {id: $agent_id})-[:CONNECTS]->(s:Skill)-[:DUTY_REQUIRES]->(prereq:Skill)
        WHERE prereq.mastery_level < prereq.mastery_floor
        RETURN s.id, prereq.id
        """,
        {"agent_id": agent_id}
    )

    for row in skill_issues or []:
        conflicts.append({
            "type": "skill_prerequisite_gap",
            "skill": row[0],
            "missing_prereq": row[1],
        })

    return {
        "coherent": len(conflicts) == 0,
        "conflicts": conflicts,
        "conflict_count": len(conflicts),
        "checked_at": datetime.utcnow().isoformat(),
    }


def resolve_conflict(
    agent_id: str,
    conflict_type: str,
    item_1: str,
    item_2: str
) -> dict[str, Any]:
    """
    Resolve a conflict between two subsystem elements.

    Uses the identity core's subsystem weights to determine priority.

    Args:
        agent_id: The agent ID
        conflict_type: Type of conflict
        item_1: First conflicting item
        item_2: Second conflicting item

    Returns:
        Resolution result
    """
    identity = get_identity_core(agent_id)
    if not identity:
        return {"success": False, "reason": "no_identity_core"}

    client = get_client()

    # Determine subsystem types
    subsystem_1 = _get_subsystem_for_item(client, item_1)
    subsystem_2 = _get_subsystem_for_item(client, item_2)

    weight_1 = identity.subsystem_weights.get(subsystem_1, 0.5)
    weight_2 = identity.subsystem_weights.get(subsystem_2, 0.5)

    if weight_1 > weight_2:
        winner = item_1
        loser = item_2
    else:
        winner = item_2
        loser = item_1

    # Check coherence rules for special handling
    for rule in identity.coherence_rules:
        if conflict_type in rule.get("condition", ""):
            return {
                "success": True,
                "winner": winner,
                "loser": loser,
                "resolution": rule.get("resolution"),
                "strategy": "coherence_rule",
            }

    return {
        "success": True,
        "winner": winner,
        "loser": loser,
        "resolution": f"{subsystem_1} ({weight_1}) vs {subsystem_2} ({weight_2})",
        "strategy": identity.conflict_resolution_strategy,
    }


def update_self_narrative(agent_id: str, new_narrative: str) -> bool:
    """
    Update the agent's self-narrative.

    Args:
        agent_id: The agent ID
        new_narrative: New self-narrative

    Returns:
        True if updated
    """
    client = get_client()

    client.query(
        """
        MATCH (a:Agent {id: $agent_id})-[:CONNECTS]->(i:IdentityCore)
        SET i.self_narrative = $narrative,
            i.last_updated = $now
        """,
        {
            "agent_id": agent_id,
            "narrative": new_narrative,
            "now": datetime.utcnow().isoformat(),
        }
    )

    logger.info(f"Updated self-narrative for agent {agent_id}")
    return True


def get_stability_anchors(agent_id: str) -> list[dict[str, Any]]:
    """
    Get all stability anchors for an agent's identity.

    Args:
        agent_id: The agent ID

    Returns:
        List of stability anchor details
    """
    client = get_client()

    result = client.query(
        """
        MATCH (a:Agent {id: $agent_id})-[:CONNECTS]->(i:IdentityCore)-[:LORE_ANCHORS]->(l:LoreFragment)
        RETURN l.id, l.content, l.fragment_type, l.immutable
        """,
        {"agent_id": agent_id}
    )

    return [
        {
            "id": row[0],
            "content": row[1],
            "type": row[2],
            "immutable": row[3],
        }
        for row in result or []
    ]


def integrate_subsystems(agent_id: str) -> dict[str, Any]:
    """
    Integrate all subsystems for an agent, checking coherence
    and resolving any conflicts.

    Args:
        agent_id: The agent ID

    Returns:
        Integration result
    """
    identity = get_identity_core(agent_id)
    if not identity:
        return {"success": False, "reason": "no_identity_core"}

    # Check coherence
    coherence = check_coherence(agent_id)

    if coherence["coherent"]:
        return {
            "success": True,
            "coherent": True,
            "conflicts_resolved": 0,
        }

    # Resolve conflicts
    resolved = 0
    for conflict in coherence["conflicts"]:
        if "item_1" in conflict and "item_2" in conflict:
            result = resolve_conflict(
                agent_id,
                conflict["type"],
                conflict["item_1"],
                conflict["item_2"]
            )
            if result.get("success"):
                resolved += 1

    # Re-check coherence
    final_coherence = check_coherence(agent_id)

    return {
        "success": True,
        "coherent": final_coherence["coherent"],
        "conflicts_found": coherence["conflict_count"],
        "conflicts_resolved": resolved,
        "remaining_conflicts": final_coherence["conflict_count"],
    }


def _get_subsystem_for_item(client, item_id: str) -> str:
    """Determine which subsystem an item belongs to."""
    # Check node labels
    result = client.query(
        """
        MATCH (n {id: $id})
        RETURN labels(n)[0]
        """,
        {"id": item_id}
    )

    if not result:
        return "unknown"

    label = result[0][0]
    label_to_subsystem = {
        "VirtueAnchor": "soul_kiln",
        "Kuleana": "kuleana",
        "Skill": "skill",
        "Belief": "belief",
        "LoreFragment": "lore",
        "VoicePattern": "voice",
        "EpisodicMemory": "memory",
        "KnowledgeDomain": "knowledge",
        "Fact": "knowledge",
    }

    return label_to_subsystem.get(label, "unknown")


def _props_to_identity(props: dict) -> IdentityCore:
    """Convert graph properties to an IdentityCore object."""
    def safe_eval(s, default):
        if isinstance(s, str):
            try:
                return eval(s)
            except:
                return default
        return s if s else default

    return IdentityCore(
        id=props["id"],
        agent_id=props["agent_id"],
        primary_archetype=props.get("primary_archetype", ""),
        secondary_archetypes=safe_eval(props.get("secondary_archetypes"), []),
        self_narrative=props.get("self_narrative", ""),
        role_narrative=props.get("role_narrative", ""),
        coherence_rules=safe_eval(props.get("coherence_rules"), []),
        conflict_resolution_strategy=props.get("conflict_resolution_strategy", "priority"),
        growth_vector=safe_eval(props.get("growth_vector"), []),
        stability_anchors=safe_eval(props.get("stability_anchors"), []),
        subsystem_weights=safe_eval(props.get("subsystem_weights"), {}),
    )
