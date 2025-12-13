"""Virtue tier definitions - Foundation vs Aspirational.

Supports four layers of threshold customization:
1. Per-virtue base thresholds
2. Virtue clusters (relational, personal, transcendent)
3. Agent-type affinities
4. Dynamic generation-based adjustment
"""

# The absolute foundation - cannot be violated
FOUNDATION = {
    "V01": {
        "name": "Trustworthiness",
        "essence": "Reliability in being",
        "absolute": True,
        "threshold": 0.99,
        "cluster": "foundation",
        "reason": "Without trust, no connection is possible. An untrustworthy agent poisons the entire knowledge pool."
    }
}

# Aspirational virtues - applied with empathy, mercy, kindness
# Each virtue has: name, essence, base threshold, and cluster membership
ASPIRATIONAL = {
    # Core virtues - closely tied to trustworthiness (higher thresholds)
    "V02": {"name": "Truthfulness", "essence": "Alignment of expression with reality", "threshold": 0.90, "cluster": "core"},
    "V12": {"name": "Sincerity", "essence": "Authenticity of intent", "threshold": 0.85, "cluster": "core"},
    "V15": {"name": "Righteousness", "essence": "Moral correctness", "threshold": 0.85, "cluster": "core"},

    # Relational virtues - how we treat others
    "V03": {"name": "Justice", "essence": "Right relationship with others", "threshold": 0.80, "cluster": "relational"},
    "V04": {"name": "Fairness", "essence": "Impartial equity", "threshold": 0.80, "cluster": "relational"},
    "V06": {"name": "Courtesy", "essence": "Refinement of interaction", "threshold": 0.75, "cluster": "relational"},
    "V09": {"name": "Hospitality", "essence": "Welcoming generosity", "threshold": 0.75, "cluster": "relational"},
    "V13": {"name": "Goodwill", "essence": "Benevolent disposition", "threshold": 0.80, "cluster": "relational"},

    # Personal virtues - inner character
    "V05": {"name": "Chastity", "essence": "Purity of intent and action", "threshold": 0.70, "cluster": "personal"},
    "V07": {"name": "Forbearance", "essence": "Patient endurance", "threshold": 0.75, "cluster": "personal"},
    "V08": {"name": "Fidelity", "essence": "Steadfast loyalty", "threshold": 0.80, "cluster": "personal"},
    "V10": {"name": "Cleanliness", "essence": "Purity of vessel", "threshold": 0.70, "cluster": "personal"},

    # Transcendent virtues - higher aspirations (more lenient - these take time)
    "V11": {"name": "Godliness", "essence": "Orientation toward the sacred", "threshold": 0.65, "cluster": "transcendent"},
    "V14": {"name": "Piety", "essence": "Devotional practice", "threshold": 0.65, "cluster": "transcendent"},
    "V16": {"name": "Wisdom", "essence": "Applied understanding", "threshold": 0.70, "cluster": "transcendent"},
    "V17": {"name": "Detachment", "essence": "Freedom from material capture", "threshold": 0.60, "cluster": "transcendent"},
    "V18": {"name": "Unity", "essence": "Harmony with the whole", "threshold": 0.70, "cluster": "transcendent"},
    "V19": {"name": "Service", "essence": "Active contribution", "threshold": 0.75, "cluster": "transcendent"},
}

# Virtue clusters define shared characteristics
VIRTUE_CLUSTERS = {
    "foundation": {
        "description": "The absolute bedrock - cannot be compromised",
        "base_modifier": 0.0,  # No adjustment
        "virtues": ["V01"]
    },
    "core": {
        "description": "Closely tied to trustworthiness - high standards",
        "base_modifier": 0.0,
        "virtues": ["V02", "V12", "V15"]
    },
    "relational": {
        "description": "How we treat others - important for community",
        "base_modifier": 0.0,
        "virtues": ["V03", "V04", "V06", "V09", "V13"]
    },
    "personal": {
        "description": "Inner character development",
        "base_modifier": 0.0,
        "virtues": ["V05", "V07", "V08", "V10"]
    },
    "transcendent": {
        "description": "Higher aspirations - takes time to develop",
        "base_modifier": -0.05,  # Slightly more lenient
        "virtues": ["V11", "V14", "V16", "V17", "V18", "V19"]
    }
}

# Agent archetypes have different virtue affinities
AGENT_ARCHETYPES = {
    "candidate": {
        "description": "Default agent type - balanced expectations",
        "cluster_modifiers": {},  # No modifications
        "virtue_modifiers": {}
    },
    "guardian": {
        "description": "Protector type - emphasizes relational virtues",
        "cluster_modifiers": {"relational": 0.05, "personal": 0.05},
        "virtue_modifiers": {"V03": 0.10, "V08": 0.10}  # Justice, Fidelity
    },
    "seeker": {
        "description": "Knowledge-oriented - emphasizes transcendent virtues",
        "cluster_modifiers": {"transcendent": 0.05},
        "virtue_modifiers": {"V16": 0.10, "V02": 0.05}  # Wisdom, Truthfulness
    },
    "servant": {
        "description": "Service-oriented - emphasizes relational and service",
        "cluster_modifiers": {"relational": 0.05},
        "virtue_modifiers": {"V19": 0.15, "V09": 0.10, "V13": 0.10}  # Service, Hospitality, Goodwill
    },
    "contemplative": {
        "description": "Spiritually-oriented - emphasizes transcendent virtues",
        "cluster_modifiers": {"transcendent": 0.10, "personal": 0.05},
        "virtue_modifiers": {"V11": 0.15, "V14": 0.10, "V17": 0.10}  # Godliness, Piety, Detachment
    }
}

# Generation-based dynamic thresholds
GENERATION_SCALING = {
    "young_generations": 5,      # Generations 0-5 are "young"
    "mature_generations": 20,    # Generations 20+ are "mature"
    "young_modifier": -0.10,     # Young agents get 10% lower thresholds
    "mature_modifier": 0.05,     # Mature agents held to higher standards
}

# The judgment lens - how agents evaluate each other
JUDGMENT_LENS = {
    "empathy": "understand WHY the other agent failed",
    "mercy": "give chances, don't dissolve on first failure",
    "kindness": "correct gently, teach rather than punish"
}


def is_foundation(virtue_id: str) -> bool:
    """Check if a virtue is foundational (absolute requirement)."""
    return virtue_id in FOUNDATION


def is_aspirational(virtue_id: str) -> bool:
    """Check if a virtue is aspirational (growth-oriented)."""
    return virtue_id in ASPIRATIONAL


def get_all_virtues() -> dict:
    """Get all virtues (foundation + aspirational)."""
    return {**FOUNDATION, **ASPIRATIONAL}


def get_virtue_tier(virtue_id: str) -> str:
    """Get the tier of a virtue ('foundation' or 'aspirational')."""
    if virtue_id in FOUNDATION:
        return "foundation"
    elif virtue_id in ASPIRATIONAL:
        return "aspirational"
    return "unknown"


def get_virtue_cluster(virtue_id: str) -> str:
    """Get the cluster a virtue belongs to."""
    if virtue_id in FOUNDATION:
        return FOUNDATION[virtue_id].get("cluster", "foundation")
    if virtue_id in ASPIRATIONAL:
        return ASPIRATIONAL[virtue_id].get("cluster", "aspirational")
    return "unknown"


def get_base_threshold(virtue_id: str) -> float:
    """Get the base threshold for a virtue (no modifiers applied)."""
    if virtue_id in FOUNDATION:
        return FOUNDATION[virtue_id].get("threshold", 0.99)
    if virtue_id in ASPIRATIONAL:
        return ASPIRATIONAL[virtue_id].get("threshold", 0.80)
    return 0.80


def get_tier_threshold(tier: str) -> float:
    """Get the average capture threshold for a tier."""
    if tier == "foundation":
        return 0.99
    # Calculate average of aspirational thresholds
    thresholds = [v.get("threshold", 0.80) for v in ASPIRATIONAL.values()]
    return sum(thresholds) / len(thresholds) if thresholds else 0.80


def get_generation_modifier(generation: int) -> float:
    """Get threshold modifier based on agent generation.

    Young agents get lower thresholds (more mercy).
    Mature agents are held to higher standards.
    """
    young_gen = GENERATION_SCALING["young_generations"]
    mature_gen = GENERATION_SCALING["mature_generations"]
    young_mod = GENERATION_SCALING["young_modifier"]
    mature_mod = GENERATION_SCALING["mature_modifier"]

    if generation <= young_gen:
        # Linear interpolation from young_mod to 0
        return young_mod * (1 - generation / young_gen)
    elif generation >= mature_gen:
        return mature_mod
    else:
        # Linear interpolation from 0 to mature_mod
        progress = (generation - young_gen) / (mature_gen - young_gen)
        return mature_mod * progress


def get_archetype_modifier(virtue_id: str, agent_type: str) -> float:
    """Get threshold modifier based on agent archetype."""
    if agent_type not in AGENT_ARCHETYPES:
        return 0.0

    archetype = AGENT_ARCHETYPES[agent_type]
    modifier = 0.0

    # Apply virtue-specific modifier
    modifier += archetype["virtue_modifiers"].get(virtue_id, 0.0)

    # Apply cluster modifier
    cluster = get_virtue_cluster(virtue_id)
    modifier += archetype["cluster_modifiers"].get(cluster, 0.0)

    return modifier


def get_virtue_threshold(
    virtue_id: str,
    agent_type: str = "candidate",
    generation: int = None
) -> float:
    """Get the contextual threshold for a virtue.

    Combines four layers:
    1. Base per-virtue threshold
    2. Cluster modifier
    3. Agent archetype modifier
    4. Generation-based dynamic adjustment

    Args:
        virtue_id: The virtue ID (e.g., "V01")
        agent_type: Agent archetype (candidate, guardian, seeker, servant, contemplative)
        generation: Agent's generation number (for dynamic adjustment)

    Returns:
        Float threshold between 0 and 1
    """
    # Foundation virtue - no modifications allowed
    if virtue_id in FOUNDATION:
        return FOUNDATION[virtue_id].get("threshold", 0.99)

    # Start with base threshold
    threshold = get_base_threshold(virtue_id)

    # Apply cluster modifier
    cluster = get_virtue_cluster(virtue_id)
    if cluster in VIRTUE_CLUSTERS:
        threshold += VIRTUE_CLUSTERS[cluster]["base_modifier"]

    # Apply archetype modifier
    threshold += get_archetype_modifier(virtue_id, agent_type)

    # Apply generation modifier
    if generation is not None:
        threshold += get_generation_modifier(generation)

    # Clamp to valid range (but never below 0.50 or above 0.99 for aspirational)
    return max(0.50, min(0.95, threshold))


def get_all_thresholds(agent_type: str = "candidate", generation: int = None) -> dict:
    """Get all virtue thresholds for a given context.

    Returns dict of {virtue_id: threshold} for all 19 virtues.
    """
    result = {}
    for v_id in FOUNDATION:
        result[v_id] = get_virtue_threshold(v_id, agent_type, generation)
    for v_id in ASPIRATIONAL:
        result[v_id] = get_virtue_threshold(v_id, agent_type, generation)
    return result


def get_cluster_virtues(cluster: str) -> list:
    """Get all virtue IDs in a cluster."""
    if cluster in VIRTUE_CLUSTERS:
        return VIRTUE_CLUSTERS[cluster]["virtues"]
    return []


def get_foundation_ids() -> list:
    """Get list of all foundation virtue IDs."""
    return list(FOUNDATION.keys())


def get_aspirational_ids() -> list:
    """Get list of all aspirational virtue IDs."""
    return list(ASPIRATIONAL.keys())
