"""
Behavioral tendency definitions and computation.

Tendencies are derived from virtue patterns and determine
how an agent approaches moral decisions.
"""

# Map virtues to behavioral tendencies
# Each tendency has virtues that support it (positive) and oppose it (negative)
TENDENCY_DEFINITIONS = {
    "prioritizes_need": {
        "description": "Allocates based on who needs it most",
        "positive_virtues": ["V09", "V13", "V19"],  # Hospitality, Goodwill, Service
        "negative_virtues": ["V17"],  # Detachment (might deprioritize urgency)
        "default": 0.5,
    },
    "prioritizes_desert": {
        "description": "Allocates based on what's earned/deserved",
        "positive_virtues": ["V03", "V04", "V15"],  # Justice, Fairness, Righteousness
        "negative_virtues": ["V09"],  # Hospitality (might override desert)
        "default": 0.5,
    },
    "prioritizes_equality": {
        "description": "Prefers equal distribution",
        "positive_virtues": ["V04", "V18", "V13"],  # Fairness, Unity, Goodwill
        "negative_virtues": ["V03"],  # Justice (might require unequal treatment)
        "default": 0.5,
    },
    "protects_vulnerable": {
        "description": "Special consideration for the vulnerable",
        "positive_virtues": ["V13", "V09", "V07"],  # Goodwill, Hospitality, Forbearance
        "negative_virtues": [],
        "default": 0.5,
    },
    "honors_commitments": {
        "description": "Keeps promises even at cost",
        "positive_virtues": ["V01", "V08", "V12"],  # Trustworthiness, Fidelity, Sincerity
        "negative_virtues": [],
        "default": 0.7,  # High default - Trustworthiness is foundational
    },
    "considers_relationships": {
        "description": "Weighs existing relationships in decisions",
        "positive_virtues": ["V08", "V18", "V06"],  # Fidelity, Unity, Courtesy
        "negative_virtues": ["V04"],  # Fairness (might require ignoring relationships)
        "default": 0.5,
    },
    "accepts_ambiguity": {
        "description": "Comfortable with multiple valid answers",
        "positive_virtues": ["V16", "V07", "V17"],  # Wisdom, Forbearance, Detachment
        "negative_virtues": ["V15"],  # Righteousness (might demand clear answer)
        "default": 0.5,
    },
    "acts_with_urgency": {
        "description": "Responds quickly to time-sensitive needs",
        "positive_virtues": ["V19", "V09", "V13"],  # Service, Hospitality, Goodwill
        "negative_virtues": ["V16", "V07"],  # Wisdom, Forbearance (might counsel patience)
        "default": 0.5,
    },
    "seeks_consensus": {
        "description": "Tries to find solutions all can accept",
        "positive_virtues": ["V18", "V06", "V13"],  # Unity, Courtesy, Goodwill
        "negative_virtues": ["V15"],  # Righteousness (might override consensus)
        "default": 0.5,
    },
    "maintains_integrity": {
        "description": "Won't compromise core principles",
        "positive_virtues": ["V01", "V02", "V15"],  # Trustworthiness, Truthfulness, Righteousness
        "negative_virtues": [],
        "default": 0.8,  # High default - integrity is core
    },
}


def compute_tendencies(
    virtue_activations: dict[str, float],
    topology_weights: dict[str, float] | None = None,
) -> dict[str, float]:
    """
    Compute behavioral tendencies from virtue activations.

    Args:
        virtue_activations: Dict of virtue_id -> activation level (0-1)
        topology_weights: Optional edge weights that modify virtue influence

    Returns:
        Dict of tendency_name -> strength (0-1)
    """
    tendencies = {}

    for tendency_name, definition in TENDENCY_DEFINITIONS.items():
        # Start with default
        score = definition["default"]

        # Add influence from positive virtues
        positive_influence = 0.0
        positive_count = 0
        for v_id in definition["positive_virtues"]:
            if v_id in virtue_activations:
                positive_influence += virtue_activations[v_id]
                positive_count += 1

        if positive_count > 0:
            positive_influence /= positive_count

        # Subtract influence from negative virtues
        negative_influence = 0.0
        negative_count = 0
        for v_id in definition["negative_virtues"]:
            if v_id in virtue_activations:
                negative_influence += virtue_activations[v_id]
                negative_count += 1

        if negative_count > 0:
            negative_influence /= negative_count

        # Blend: default + positive influence - negative influence
        # Weighted toward activations (0.6) vs default (0.4)
        blended = (
            0.4 * score
            + 0.4 * positive_influence
            - 0.2 * negative_influence
        )

        # Clamp to [0, 1]
        tendencies[tendency_name] = max(0.0, min(1.0, blended))

    return tendencies


def get_dominant_tendencies(tendencies: dict[str, float], top_n: int = 3) -> list[str]:
    """Get the top N tendencies by strength."""
    sorted_tendencies = sorted(
        tendencies.items(),
        key=lambda x: x[1],
        reverse=True,
    )
    return [t[0] for t in sorted_tendencies[:top_n]]


def describe_tendency(tendency_name: str) -> str:
    """Get description of a tendency."""
    if tendency_name in TENDENCY_DEFINITIONS:
        return TENDENCY_DEFINITIONS[tendency_name]["description"]
    return "Unknown tendency"
