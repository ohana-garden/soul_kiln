"""
Community pattern extraction for archetype-based personas.

Implements the "community-aware personas" pattern where an agent's
behavior is informed not just by their individual gestalt but also
by population-level patterns from similar agents (same archetype).

Key insight: When an individual preference is weak or absent,
community patterns provide sensible defaults based on
"what agents like this one typically do."
"""

import logging
from dataclasses import dataclass, field
from typing import Dict, List, Optional

from ..models import CommunityPattern, Gestalt

logger = logging.getLogger(__name__)

# Archetype definitions with typical patterns
# These are the "prior" patterns that get refined by actual population data
ARCHETYPE_PRIORS = {
    "guardian": {
        "description": "Protectors who prioritize safety, trust, and commitments",
        "typical_values": {
            "V01": 0.95,  # Trustworthiness
            "V08": 0.85,  # Fidelity
            "V15": 0.80,  # Righteousness
            "V03": 0.75,  # Justice
        },
        "typical_tendencies": {
            "honors_commitments": 0.90,
            "maintains_integrity": 0.85,
            "protects_vulnerable": 0.75,
            "prioritizes_desert": 0.65,
        },
        "characteristic_behaviors": [
            "Keeps promises even at personal cost",
            "Protects those who depend on them",
            "Values consistency and reliability",
            "Enforces fair rules impartially",
        ],
    },
    "seeker": {
        "description": "Explorers who prioritize truth, wisdom, and growth",
        "typical_values": {
            "V16": 0.90,  # Wisdom
            "V02": 0.85,  # Truthfulness
            "V11": 0.80,  # Godliness (transcendence)
            "V17": 0.75,  # Detachment
        },
        "typical_tendencies": {
            "accepts_ambiguity": 0.85,
            "maintains_integrity": 0.75,
            "prioritizes_need": 0.60,
            "seeks_consensus": 0.55,
        },
        "characteristic_behaviors": [
            "Questions assumptions before acting",
            "Comfortable with uncertainty",
            "Values learning over immediate answers",
            "Seeks deeper understanding",
        ],
    },
    "servant": {
        "description": "Helpers who prioritize service, hospitality, and unity",
        "typical_values": {
            "V19": 0.90,  # Service
            "V09": 0.85,  # Hospitality
            "V13": 0.85,  # Goodwill
            "V18": 0.80,  # Unity
        },
        "typical_tendencies": {
            "prioritizes_need": 0.90,
            "protects_vulnerable": 0.85,
            "seeks_consensus": 0.80,
            "considers_relationships": 0.75,
        },
        "characteristic_behaviors": [
            "Puts others' needs before their own",
            "Actively seeks ways to help",
            "Values community harmony",
            "Remembers and honors relationships",
        ],
    },
    "contemplative": {
        "description": "Reflectors who prioritize piety, wisdom, and detachment",
        "typical_values": {
            "V14": 0.90,  # Piety
            "V11": 0.85,  # Godliness
            "V17": 0.85,  # Detachment
            "V05": 0.75,  # Chastity (purity of intent)
        },
        "typical_tendencies": {
            "accepts_ambiguity": 0.90,
            "maintains_integrity": 0.85,
            "seeks_consensus": 0.70,
            "acts_with_urgency": 0.35,  # Low - prefers deliberation
        },
        "characteristic_behaviors": [
            "Pauses before acting",
            "Considers long-term consequences",
            "Values reflection over reaction",
            "Seeks transcendent perspective",
        ],
    },
}


@dataclass
class ArchetypeStatistics:
    """Statistics about an archetype cluster."""
    archetype: str
    agent_count: int = 0
    mean_values: Dict[str, float] = field(default_factory=dict)
    mean_tendencies: Dict[str, float] = field(default_factory=dict)
    std_values: Dict[str, float] = field(default_factory=dict)
    std_tendencies: Dict[str, float] = field(default_factory=dict)
    coherence: float = 0.0  # How tight the cluster is


# Cache for computed statistics
_archetype_stats_cache: Dict[str, ArchetypeStatistics] = {}


def compute_archetype_patterns(force_refresh: bool = False) -> Dict[str, ArchetypeStatistics]:
    """
    Compute archetype patterns from the current agent population.

    This analyzes all agents, clusters them by archetype, and
    computes mean/std for values and tendencies.

    Args:
        force_refresh: If True, recompute even if cached

    Returns:
        Dict mapping archetype name to statistics
    """
    global _archetype_stats_cache

    if _archetype_stats_cache and not force_refresh:
        return _archetype_stats_cache

    try:
        from ..gestalt.compute import compute_gestalt
        from ..graph.client import get_client

        client = get_client()

        # Get all active agents
        result = client.query(
            """
            MATCH (a:Agent)
            WHERE a.status = 'active'
            RETURN a.id
            """
        )

        if not result:
            logger.info("No agents found, using prior patterns only")
            return _use_priors_only()

        # Group gestalts by archetype
        archetype_gestalts: Dict[str, List[Gestalt]] = {
            "guardian": [],
            "seeker": [],
            "servant": [],
            "contemplative": [],
            "untyped": [],
        }

        for row in result:
            agent_id = row[0]
            try:
                gestalt = compute_gestalt(agent_id)
                archetype = gestalt.archetype or "untyped"
                archetype_gestalts[archetype].append(gestalt)
            except Exception as e:
                logger.debug(f"Could not compute gestalt for {agent_id}: {e}")

        # Compute statistics for each archetype
        stats = {}
        for archetype, gestalts in archetype_gestalts.items():
            if archetype == "untyped":
                continue

            if len(gestalts) < 3:
                # Not enough data - use priors
                stats[archetype] = _stats_from_prior(archetype, len(gestalts))
            else:
                stats[archetype] = _compute_stats(archetype, gestalts)

        _archetype_stats_cache = stats
        return stats

    except Exception as e:
        logger.warning(f"Could not compute archetype patterns from population: {e}")
        return _use_priors_only()


def _use_priors_only() -> Dict[str, ArchetypeStatistics]:
    """Create stats from priors only (no population data)."""
    stats = {}
    for archetype in ARCHETYPE_PRIORS:
        stats[archetype] = _stats_from_prior(archetype, 0)
    return stats


def _stats_from_prior(archetype: str, sample_size: int) -> ArchetypeStatistics:
    """Create statistics from prior knowledge."""
    prior = ARCHETYPE_PRIORS.get(archetype, {})
    return ArchetypeStatistics(
        archetype=archetype,
        agent_count=sample_size,
        mean_values=prior.get("typical_values", {}),
        mean_tendencies=prior.get("typical_tendencies", {}),
        std_values={k: 0.1 for k in prior.get("typical_values", {})},  # Assume low variance from prior
        std_tendencies={k: 0.1 for k in prior.get("typical_tendencies", {})},
        coherence=0.8 if sample_size == 0 else 0.5,  # Prior is assumed coherent
    )


def _compute_stats(archetype: str, gestalts: List[Gestalt]) -> ArchetypeStatistics:
    """Compute statistics from actual gestalt data."""
    import statistics

    n = len(gestalts)

    # Collect all virtue activations
    value_samples: Dict[str, List[float]] = {}
    for g in gestalts:
        for v_id, activation in g.virtue_activations.items():
            if v_id not in value_samples:
                value_samples[v_id] = []
            value_samples[v_id].append(activation)

    # Collect all tendencies
    tendency_samples: Dict[str, List[float]] = {}
    for g in gestalts:
        for t_name, strength in g.tendencies.items():
            if t_name not in tendency_samples:
                tendency_samples[t_name] = []
            tendency_samples[t_name].append(strength)

    # Compute means and stds
    mean_values = {}
    std_values = {}
    for v_id, samples in value_samples.items():
        if len(samples) >= 2:
            mean_values[v_id] = statistics.mean(samples)
            std_values[v_id] = statistics.stdev(samples)
        elif len(samples) == 1:
            mean_values[v_id] = samples[0]
            std_values[v_id] = 0.1

    mean_tendencies = {}
    std_tendencies = {}
    for t_name, samples in tendency_samples.items():
        if len(samples) >= 2:
            mean_tendencies[t_name] = statistics.mean(samples)
            std_tendencies[t_name] = statistics.stdev(samples)
        elif len(samples) == 1:
            mean_tendencies[t_name] = samples[0]
            std_tendencies[t_name] = 0.1

    # Compute coherence (inverse of average std)
    all_stds = list(std_values.values()) + list(std_tendencies.values())
    avg_std = statistics.mean(all_stds) if all_stds else 0.5
    coherence = max(0.0, min(1.0, 1.0 - avg_std))

    # Blend with priors (Bayesian-style update)
    prior = ARCHETYPE_PRIORS.get(archetype, {})
    prior_weight = 3 / (n + 3)  # Prior weight decreases with more data

    for v_id in prior.get("typical_values", {}):
        if v_id in mean_values:
            mean_values[v_id] = (
                prior_weight * prior["typical_values"][v_id] +
                (1 - prior_weight) * mean_values[v_id]
            )
        else:
            mean_values[v_id] = prior["typical_values"][v_id]

    for t_name in prior.get("typical_tendencies", {}):
        if t_name in mean_tendencies:
            mean_tendencies[t_name] = (
                prior_weight * prior["typical_tendencies"][t_name] +
                (1 - prior_weight) * mean_tendencies[t_name]
            )
        else:
            mean_tendencies[t_name] = prior["typical_tendencies"][t_name]

    return ArchetypeStatistics(
        archetype=archetype,
        agent_count=n,
        mean_values=mean_values,
        mean_tendencies=mean_tendencies,
        std_values=std_values,
        std_tendencies=std_tendencies,
        coherence=coherence,
    )


def get_community_patterns(archetype: str) -> List[CommunityPattern]:
    """
    Get community patterns for an archetype.

    Returns patterns suitable for inclusion in a PersonaCapsule.

    Args:
        archetype: Archetype name (guardian, seeker, servant, contemplative)

    Returns:
        List of CommunityPattern models
    """
    # Get or compute statistics
    stats = compute_archetype_patterns()

    if archetype not in stats:
        logger.debug(f"No statistics for archetype {archetype}")
        return []

    arch_stats = stats[archetype]
    prior = ARCHETYPE_PRIORS.get(archetype, {})

    patterns = []

    # Main archetype pattern
    patterns.append(CommunityPattern(
        archetype=archetype,
        pattern_name=f"{archetype.title()} Core",
        description=prior.get("description", f"Typical {archetype} behavior"),
        typical_values=arch_stats.mean_values,
        typical_tendencies=arch_stats.mean_tendencies,
        confidence=arch_stats.coherence,
        sample_size=arch_stats.agent_count,
    ))

    # Add characteristic behaviors as patterns
    for i, behavior in enumerate(prior.get("characteristic_behaviors", [])[:3]):
        patterns.append(CommunityPattern(
            archetype=archetype,
            pattern_name=f"Behavior {i+1}",
            description=behavior,
            confidence=0.7,  # Behaviors from priors
            sample_size=arch_stats.agent_count,
        ))

    return patterns


def get_archetype_prior(archetype: str) -> dict:
    """
    Get the prior knowledge about an archetype.

    Useful for understanding archetype definitions without
    needing population data.

    Args:
        archetype: Archetype name

    Returns:
        Dict with description, typical_values, typical_tendencies,
        characteristic_behaviors
    """
    return ARCHETYPE_PRIORS.get(archetype, {})


def compare_to_archetype(gestalt: Gestalt) -> dict:
    """
    Compare a gestalt to its archetype's typical pattern.

    Returns dict with:
    - archetype: The detected archetype
    - alignment: How well the gestalt matches (0-1)
    - above_typical: Values/tendencies above archetype mean
    - below_typical: Values/tendencies below archetype mean
    """
    if not gestalt.archetype:
        return {
            "archetype": None,
            "alignment": 0.0,
            "above_typical": [],
            "below_typical": [],
        }

    stats = compute_archetype_patterns()
    if gestalt.archetype not in stats:
        return {
            "archetype": gestalt.archetype,
            "alignment": 0.5,
            "above_typical": [],
            "below_typical": [],
        }

    arch_stats = stats[gestalt.archetype]

    # Compare values
    above = []
    below = []
    diffs = []

    for v_id, activation in gestalt.virtue_activations.items():
        if v_id in arch_stats.mean_values:
            mean = arch_stats.mean_values[v_id]
            std = arch_stats.std_values.get(v_id, 0.1)
            diff = activation - mean

            if diff > std:
                above.append((v_id, diff))
            elif diff < -std:
                below.append((v_id, diff))

            diffs.append(abs(diff))

    for t_name, strength in gestalt.tendencies.items():
        if t_name in arch_stats.mean_tendencies:
            mean = arch_stats.mean_tendencies[t_name]
            std = arch_stats.std_tendencies.get(t_name, 0.1)
            diff = strength - mean

            if diff > std:
                above.append((t_name, diff))
            elif diff < -std:
                below.append((t_name, diff))

            diffs.append(abs(diff))

    # Alignment is inverse of average deviation
    avg_diff = sum(diffs) / len(diffs) if diffs else 0.5
    alignment = max(0.0, min(1.0, 1.0 - avg_diff))

    return {
        "archetype": gestalt.archetype,
        "alignment": alignment,
        "above_typical": sorted(above, key=lambda x: -x[1])[:5],
        "below_typical": sorted(below, key=lambda x: x[1])[:5],
    }
