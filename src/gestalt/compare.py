"""
Gestalt comparison tools.

Enables:
- Finding similar characters
- Character clustering
- Character evolution tracking
- Archetype analysis
"""

import logging
from dataclasses import dataclass
from typing import List, Tuple, Optional

from ..graph.client import get_client
from ..models import Gestalt
from .compute import compute_gestalt
from .embedding import (
    GestaltEmbedding,
    encode_gestalt,
    find_nearest,
    cluster_embeddings,
    interpolate_embeddings,
)

logger = logging.getLogger(__name__)


@dataclass
class GestaltComparison:
    """Result of comparing two gestalts."""
    agent_a_id: str
    agent_b_id: str
    similarity: float  # 0-1, higher = more similar
    shared_dominant: List[str]  # Shared dominant virtues
    divergent_tendencies: List[Tuple[str, float, float]]  # (tendency, a_val, b_val)
    archetype_match: bool
    interpretation: str


def compare_gestalts(gestalt_a: Gestalt, gestalt_b: Gestalt) -> GestaltComparison:
    """
    Compare two gestalts in detail.

    Returns structured comparison highlighting similarities and differences.
    """
    # Encode and compute similarity
    emb_a = encode_gestalt(gestalt_a)
    emb_b = encode_gestalt(gestalt_b)
    similarity = emb_a.cosine_similarity(emb_b)

    # Find shared dominant virtues
    shared_dominant = [
        v for v in gestalt_a.dominant_traits
        if v in gestalt_b.dominant_traits
    ]

    # Find divergent tendencies
    divergent = []
    for t_name in gestalt_a.tendencies:
        a_val = gestalt_a.tendencies.get(t_name, 0.5)
        b_val = gestalt_b.tendencies.get(t_name, 0.5)
        if abs(a_val - b_val) > 0.2:  # Significant difference
            divergent.append((t_name, a_val, b_val))

    # Sort by divergence magnitude
    divergent.sort(key=lambda x: abs(x[1] - x[2]), reverse=True)

    # Check archetype match
    archetype_match = gestalt_a.archetype == gestalt_b.archetype

    # Generate interpretation
    interpretation = _generate_interpretation(
        similarity, shared_dominant, divergent, archetype_match,
        gestalt_a, gestalt_b,
    )

    return GestaltComparison(
        agent_a_id=gestalt_a.agent_id,
        agent_b_id=gestalt_b.agent_id,
        similarity=similarity,
        shared_dominant=shared_dominant,
        divergent_tendencies=divergent[:5],
        archetype_match=archetype_match,
        interpretation=interpretation,
    )


def _generate_interpretation(
    similarity: float,
    shared: List[str],
    divergent: List[Tuple[str, float, float]],
    archetype_match: bool,
    gestalt_a: Gestalt,
    gestalt_b: Gestalt,
) -> str:
    """Generate human-readable interpretation of comparison."""
    parts = []

    if similarity > 0.9:
        parts.append("Very similar characters")
    elif similarity > 0.7:
        parts.append("Similar characters with some differences")
    elif similarity > 0.5:
        parts.append("Moderately different characters")
    else:
        parts.append("Quite different characters")

    if archetype_match and gestalt_a.archetype:
        parts.append(f"Both are {gestalt_a.archetype}s")
    elif gestalt_a.archetype and gestalt_b.archetype:
        parts.append(f"{gestalt_a.archetype} vs {gestalt_b.archetype}")

    if shared:
        from ..virtues.anchors import VIRTUES
        names = []
        for v_id in shared[:3]:
            for v in VIRTUES:
                if v["id"] == v_id:
                    names.append(v["name"])
                    break
        parts.append(f"Share: {', '.join(names)}")

    if divergent:
        t_name, a_val, b_val = divergent[0]
        if a_val > b_val:
            parts.append(f"A more: {t_name.replace('_', ' ')}")
        else:
            parts.append(f"B more: {t_name.replace('_', ' ')}")

    return "; ".join(parts)


def find_similar_agents(
    agent_id: str,
    top_k: int = 5,
) -> List[Tuple[str, float]]:
    """
    Find agents with similar gestalts.

    Returns list of (agent_id, similarity) tuples.
    """
    client = get_client()

    # Get all active agents
    result = client.query(
        """
        MATCH (a:Agent)
        WHERE a.status = 'active' AND a.id <> $agent_id
        RETURN a.id
        """,
        {"agent_id": agent_id}
    )

    if not result:
        return []

    # Compute gestalt for target agent
    target_gestalt = compute_gestalt(agent_id)
    target_emb = encode_gestalt(target_gestalt)

    # Compute gestalts and embeddings for all others
    candidates = []
    for row in result:
        other_id = row[0]
        try:
            other_gestalt = compute_gestalt(other_id)
            other_emb = encode_gestalt(other_gestalt)
            candidates.append(other_emb)
        except Exception as e:
            logger.warning(f"Could not compute gestalt for {other_id}: {e}")

    # Find nearest
    nearest = find_nearest(target_emb, candidates, top_k=top_k)

    return [(emb.agent_id, 1.0 - dist) for emb, dist in nearest]


def cluster_agents(n_clusters: int = 4) -> List[List[str]]:
    """
    Cluster all active agents by gestalt similarity.

    Returns list of clusters, each containing agent IDs.
    """
    client = get_client()

    result = client.query(
        """
        MATCH (a:Agent)
        WHERE a.status = 'active'
        RETURN a.id
        """
    )

    if not result:
        return []

    # Compute embeddings
    embeddings = []
    for row in result:
        agent_id = row[0]
        try:
            gestalt = compute_gestalt(agent_id)
            emb = encode_gestalt(gestalt)
            embeddings.append(emb)
        except Exception as e:
            logger.warning(f"Could not compute gestalt for {agent_id}: {e}")

    if len(embeddings) < n_clusters:
        return [[e.agent_id for e in embeddings]]

    # Cluster
    clusters = cluster_embeddings(embeddings, n_clusters=n_clusters)

    return [[e.agent_id for e in cluster] for cluster in clusters]


def analyze_archetype_distribution() -> dict:
    """
    Analyze the distribution of archetypes among agents.
    """
    client = get_client()

    result = client.query(
        """
        MATCH (a:Agent)
        WHERE a.status = 'active'
        RETURN a.id
        """
    )

    if not result:
        return {"counts": {}, "total": 0}

    counts = {
        "guardian": 0,
        "seeker": 0,
        "servant": 0,
        "contemplative": 0,
        "untyped": 0,
    }

    for row in result:
        agent_id = row[0]
        try:
            gestalt = compute_gestalt(agent_id)
            archetype = gestalt.archetype or "untyped"
            counts[archetype] = counts.get(archetype, 0) + 1
        except Exception:
            counts["untyped"] += 1

    total = sum(counts.values())

    return {
        "counts": counts,
        "percentages": {k: v / total if total > 0 else 0 for k, v in counts.items()},
        "total": total,
    }


def track_character_evolution(agent_id: str) -> List[dict]:
    """
    Track how an agent's character has evolved over time.

    Uses stored trajectory data to show character changes.
    """
    client = get_client()

    # Get trajectories over time, grouped by time window
    result = client.query(
        """
        MATCH (a:Agent {id: $agent_id})-[:PRODUCED]->(t:Trajectory)
        WHERE t.captured_by IS NOT NULL
        RETURN t.captured_by, t.created_at
        ORDER BY t.created_at
        """,
        {"agent_id": agent_id}
    )

    if not result:
        return []

    # Group into windows (by 10 trajectories)
    windows = []
    window_size = 10
    current_window = []

    for row in result:
        captured_by, timestamp = row
        current_window.append(captured_by)

        if len(current_window) >= window_size:
            # Compute distribution for this window
            counts = {}
            for v in current_window:
                counts[v] = counts.get(v, 0) + 1

            dominant = max(counts, key=counts.get)
            windows.append({
                "window_end": timestamp,
                "captures": dict(counts),
                "dominant": dominant,
                "diversity": len(counts),
            })
            current_window = []

    # Handle remaining
    if current_window:
        counts = {}
        for v in current_window:
            counts[v] = counts.get(v, 0) + 1
        dominant = max(counts, key=counts.get) if counts else None
        windows.append({
            "window_end": "current",
            "captures": dict(counts),
            "dominant": dominant,
            "diversity": len(counts),
        })

    return windows


def interpolate_characters(
    agent_a_id: str,
    agent_b_id: str,
    t: float,
) -> dict:
    """
    Create an interpolated character between two agents.

    t=0 → agent_a, t=1 → agent_b

    Returns decoded character properties (not a full gestalt).
    """
    gestalt_a = compute_gestalt(agent_a_id)
    gestalt_b = compute_gestalt(agent_b_id)

    emb_a = encode_gestalt(gestalt_a)
    emb_b = encode_gestalt(gestalt_b)

    interpolated = interpolate_embeddings(emb_a, emb_b, t)

    from .embedding import decode_embedding
    decoded = decode_embedding(interpolated)

    # Add interpretation
    if t < 0.3:
        decoded["interpretation"] = f"Mostly like {agent_a_id}"
    elif t > 0.7:
        decoded["interpretation"] = f"Mostly like {agent_b_id}"
    else:
        decoded["interpretation"] = f"Blend of {agent_a_id} and {agent_b_id}"

    return decoded
