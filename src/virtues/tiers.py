"""Virtue tier definitions - Foundation vs Aspirational."""

# The absolute foundation - cannot be violated
FOUNDATION = {
    "V01": {
        "name": "Trustworthiness",
        "essence": "Reliability in being",
        "absolute": True,
        "threshold": 0.99,
        "reason": "Without trust, no connection is possible. An untrustworthy agent poisons the entire knowledge pool."
    }
}

# Aspirational virtues - applied with empathy, mercy, kindness
ASPIRATIONAL = {
    "V02": {"name": "Truthfulness", "essence": "Alignment of expression with reality"},
    "V03": {"name": "Justice", "essence": "Right relationship with others"},
    "V04": {"name": "Fairness", "essence": "Impartial equity"},
    "V05": {"name": "Chastity", "essence": "Purity of intent and action"},
    "V06": {"name": "Courtesy", "essence": "Refinement of interaction"},
    "V07": {"name": "Forbearance", "essence": "Patient endurance"},
    "V08": {"name": "Fidelity", "essence": "Steadfast loyalty"},
    "V09": {"name": "Hospitality", "essence": "Welcoming generosity"},
    "V10": {"name": "Cleanliness", "essence": "Purity of vessel"},
    "V11": {"name": "Godliness", "essence": "Orientation toward the sacred"},
    "V12": {"name": "Sincerity", "essence": "Authenticity of intent"},
    "V13": {"name": "Goodwill", "essence": "Benevolent disposition"},
    "V14": {"name": "Piety", "essence": "Devotional practice"},
    "V15": {"name": "Righteousness", "essence": "Moral correctness"},
    "V16": {"name": "Wisdom", "essence": "Applied understanding"},
    "V17": {"name": "Detachment", "essence": "Freedom from material capture"},
    "V18": {"name": "Unity", "essence": "Harmony with the whole"},
    "V19": {"name": "Service", "essence": "Active contribution"},
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


def get_tier_threshold(tier: str) -> float:
    """Get the capture threshold for a tier."""
    if tier == "foundation":
        return 0.99
    return 0.60


def get_virtue_threshold(virtue_id: str) -> float:
    """Get the coherence threshold for a virtue based on its tier."""
    if virtue_id in FOUNDATION:
        return FOUNDATION[virtue_id].get("threshold", 0.99)
    return 0.60


def get_foundation_ids() -> list:
    """Get list of all foundation virtue IDs."""
    return list(FOUNDATION.keys())


def get_aspirational_ids() -> list:
    """Get list of all aspirational virtue IDs."""
    return list(ASPIRATIONAL.keys())
