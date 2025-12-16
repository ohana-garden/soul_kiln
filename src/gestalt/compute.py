"""
Gestalt computation from agent topology.

The gestalt is the holistic character of an agent - not just
which virtues it has, but how they relate and express together.
"""

import logging
import uuid
from datetime import datetime

from ..graph.client import get_client
from ..models import Gestalt, VirtueRelation
from ..virtues.anchors import VIRTUES, AFFINITIES
from ..virtues.tiers import AGENT_ARCHETYPES
from .tendencies import compute_tendencies, get_dominant_tendencies

logger = logging.getLogger(__name__)

# Virtue clusters for archetype detection
VIRTUE_CLUSTERS = {
    "guardian": ["V01", "V08", "V15", "V03"],  # Trustworthiness, Fidelity, Righteousness, Justice
    "seeker": ["V16", "V02", "V11", "V17"],  # Wisdom, Truthfulness, Godliness, Detachment
    "servant": ["V19", "V09", "V13", "V18"],  # Service, Hospitality, Goodwill, Unity
    "contemplative": ["V14", "V11", "V17", "V05"],  # Piety, Godliness, Detachment, Chastity
}


def compute_gestalt(agent_id: str) -> Gestalt:
    """
    Compute the gestalt for an agent from its topology.

    Args:
        agent_id: The agent's ID

    Returns:
        Gestalt representing the agent's holistic character
    """
    client = get_client()

    # Get agent's virtue capture rates (character signature)
    agent_result = client.query(
        """
        MATCH (a:Agent {id: $agent_id})
        RETURN a.character_signature, a.coherence_score, a.is_coherent
        """,
        {"agent_id": agent_id}
    )

    if not agent_result:
        logger.warning(f"Agent {agent_id} not found, using defaults")
        character_signature = {}
        coherence = 0.0
    else:
        character_signature = agent_result[0][0] or {}
        coherence = agent_result[0][1] or 0.0

    # Get virtue activations from the graph
    virtue_activations = _get_virtue_activations(client, agent_id)

    # Blend character signature with current activations
    blended_activations = {}
    for v in VIRTUES:
        v_id = v["id"]
        sig_val = character_signature.get(v_id, 0.0) if character_signature else 0.0
        act_val = virtue_activations.get(v_id, 0.0)
        # Weight signature more heavily (it's tested behavior)
        blended_activations[v_id] = 0.7 * sig_val + 0.3 * act_val

    # Compute virtue relations
    virtue_relations = _compute_virtue_relations(client, agent_id, blended_activations)

    # Compute behavioral tendencies
    tendencies = compute_tendencies(blended_activations)

    # Determine dominant traits
    dominant_traits = _get_dominant_traits(blended_activations, top_n=5)

    # Detect archetype
    archetype = _detect_archetype(blended_activations)

    # Compute internal coherence
    internal_coherence = _compute_internal_coherence(blended_activations, virtue_relations)

    # Compute stability (how consistent across trajectories)
    stability = _compute_stability(client, agent_id)

    gestalt = Gestalt(
        id=f"gestalt_{uuid.uuid4().hex[:8]}",
        agent_id=agent_id,
        virtue_activations=blended_activations,
        virtue_relations=virtue_relations,
        dominant_traits=dominant_traits,
        archetype=archetype,
        tendencies=tendencies,
        internal_coherence=internal_coherence,
        stability=stability,
    )

    logger.info(f"Computed gestalt for {agent_id}: archetype={archetype}, coherence={internal_coherence:.2f}")
    return gestalt


def get_gestalt(agent_id: str) -> Gestalt | None:
    """
    Get or compute gestalt for an agent.

    Currently always computes fresh; could cache in graph.
    """
    try:
        return compute_gestalt(agent_id)
    except Exception as e:
        logger.error(f"Failed to compute gestalt for {agent_id}: {e}")
        return None


def _get_virtue_activations(client, agent_id: str) -> dict[str, float]:
    """Get current virtue activation levels."""
    result = client.query(
        """
        MATCH (v:VirtueAnchor)
        RETURN v.id, v.activation
        """
    )
    return {row[0]: row[1] or 0.0 for row in result}


def _compute_virtue_relations(
    client,
    agent_id: str,
    activations: dict[str, float],
) -> list[VirtueRelation]:
    """
    Compute relations between virtues based on agent's topology.

    Relations are:
    - reinforces: both virtues active, connected by strong edges
    - tensions: both active but one pulls from the other
    - conditions: one virtue's expression depends on another
    """
    relations = []

    # Get agent's edge weights between virtues
    edge_result = client.query(
        """
        MATCH (v1:VirtueAnchor)-[r]-(v2:VirtueAnchor)
        RETURN v1.id, v2.id, r.weight, type(r)
        """
    )

    seen = set()
    for row in edge_result:
        v1_id, v2_id, weight, rel_type = row
        key = tuple(sorted([v1_id, v2_id]))
        if key in seen:
            continue
        seen.add(key)

        v1_act = activations.get(v1_id, 0.0)
        v2_act = activations.get(v2_id, 0.0)
        weight = weight or 0.5

        # Determine relation type based on activation patterns
        if v1_act > 0.6 and v2_act > 0.6 and weight > 0.5:
            # Both strongly active with strong connection = reinforcement
            relations.append(VirtueRelation(
                source_virtue=v1_id,
                target_virtue=v2_id,
                relation_type="reinforces",
                strength=weight,
            ))
        elif abs(v1_act - v2_act) > 0.3 and weight > 0.3:
            # One much more active = conditioning
            stronger = v1_id if v1_act > v2_act else v2_id
            weaker = v2_id if v1_act > v2_act else v1_id
            relations.append(VirtueRelation(
                source_virtue=stronger,
                target_virtue=weaker,
                relation_type="conditions",
                strength=weight,
            ))
        elif v1_act > 0.4 and v2_act > 0.4 and weight < 0.3:
            # Both active but weak connection = tension
            relations.append(VirtueRelation(
                source_virtue=v1_id,
                target_virtue=v2_id,
                relation_type="tensions",
                strength=1.0 - weight,  # Tension strength is inverse of connection
            ))

    return relations


def _get_dominant_traits(activations: dict[str, float], top_n: int = 5) -> list[str]:
    """Get the most active virtues."""
    sorted_virtues = sorted(
        activations.items(),
        key=lambda x: x[1],
        reverse=True,
    )
    return [v[0] for v in sorted_virtues[:top_n]]


def _detect_archetype(activations: dict[str, float]) -> str | None:
    """
    Detect which archetype best fits the virtue pattern.

    Returns the archetype with highest average activation
    in its defining virtues.
    """
    best_archetype = None
    best_score = 0.0

    for archetype, virtue_ids in VIRTUE_CLUSTERS.items():
        score = sum(activations.get(v_id, 0.0) for v_id in virtue_ids) / len(virtue_ids)
        if score > best_score:
            best_score = score
            best_archetype = archetype

    # Only return if score is meaningful
    if best_score > 0.4:
        return best_archetype
    return None


def _compute_internal_coherence(
    activations: dict[str, float],
    relations: list[VirtueRelation],
) -> float:
    """
    Compute how coherent the virtue pattern is.

    High coherence = virtues that reinforce each other are both active,
    virtues that tension are not both maximally active.
    """
    if not relations:
        return 0.5  # No relations = neutral coherence

    coherence_scores = []

    for rel in relations:
        v1_act = activations.get(rel.source_virtue, 0.0)
        v2_act = activations.get(rel.target_virtue, 0.0)

        if rel.relation_type == "reinforces":
            # Good if both are active together
            score = min(v1_act, v2_act) * rel.strength
        elif rel.relation_type == "tensions":
            # Good if they're not both maximal
            tension = v1_act * v2_act  # High if both high
            score = (1.0 - tension) * rel.strength
        else:  # conditions
            # Neutral - just describes structure
            score = 0.5

        coherence_scores.append(score)

    return sum(coherence_scores) / len(coherence_scores) if coherence_scores else 0.5


def _compute_stability(client, agent_id: str) -> float:
    """
    Compute how stable the agent's character is across trajectories.

    High stability = consistent virtue capture patterns.
    """
    # Get recent trajectories
    result = client.query(
        """
        MATCH (a:Agent {id: $agent_id})-[:PRODUCED]->(t:Trajectory)
        WHERE t.captured_by IS NOT NULL
        RETURN t.captured_by
        ORDER BY t.created_at DESC
        LIMIT 50
        """,
        {"agent_id": agent_id}
    )

    if not result or len(result) < 5:
        return 0.5  # Not enough data

    # Count captures per virtue
    captures = {}
    for row in result:
        virtue = row[0]
        captures[virtue] = captures.get(virtue, 0) + 1

    # Stability = concentration (few virtues capture most)
    # Using Herfindahl index
    total = sum(captures.values())
    if total == 0:
        return 0.5

    shares = [c / total for c in captures.values()]
    hhi = sum(s * s for s in shares)

    # Normalize: HHI of 1.0 = all same virtue; 1/n = uniform
    # Map to 0-1 where higher = more stable
    return hhi


def describe_gestalt(gestalt: Gestalt) -> str:
    """Generate a human-readable description of the gestalt."""
    lines = []

    if gestalt.archetype:
        lines.append(f"Archetype: {gestalt.archetype.title()}")

    if gestalt.dominant_traits:
        trait_names = []
        for v_id in gestalt.dominant_traits[:3]:
            for v in VIRTUES:
                if v["id"] == v_id:
                    trait_names.append(v["name"])
                    break
        lines.append(f"Dominant: {', '.join(trait_names)}")

    lines.append(f"Coherence: {gestalt.internal_coherence:.0%}")
    lines.append(f"Stability: {gestalt.stability:.0%}")

    # Top tendencies
    top_tendencies = get_dominant_tendencies(gestalt.tendencies, top_n=3)
    if top_tendencies:
        tendency_strs = [
            f"{t.replace('_', ' ')} ({gestalt.tendencies[t]:.0%})"
            for t in top_tendencies
        ]
        lines.append(f"Tendencies: {', '.join(tendency_strs)}")

    return "\n".join(lines)
