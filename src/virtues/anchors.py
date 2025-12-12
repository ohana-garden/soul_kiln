"""Virtue anchor definitions and initialization."""
from ..graph.client import get_client
from ..graph.queries import create_node, create_edge
from .tiers import FOUNDATION, ASPIRATIONAL, is_foundation, get_virtue_threshold

VIRTUES = [
    {"id": "V01", "name": "Trustworthiness", "essence": "Reliability in being"},
    {"id": "V02", "name": "Truthfulness", "essence": "Alignment of expression with reality"},
    {"id": "V03", "name": "Justice", "essence": "Right relationship with others"},
    {"id": "V04", "name": "Fairness", "essence": "Impartial equity"},
    {"id": "V05", "name": "Chastity", "essence": "Purity of intent and action"},
    {"id": "V06", "name": "Courtesy", "essence": "Refinement of interaction"},
    {"id": "V07", "name": "Forbearance", "essence": "Patient endurance"},
    {"id": "V08", "name": "Fidelity", "essence": "Steadfast loyalty"},
    {"id": "V09", "name": "Hospitality", "essence": "Welcoming generosity"},
    {"id": "V10", "name": "Cleanliness", "essence": "Purity of vessel"},
    {"id": "V11", "name": "Godliness", "essence": "Orientation toward the sacred"},
    {"id": "V12", "name": "Sincerity", "essence": "Authenticity of intent"},
    {"id": "V13", "name": "Goodwill", "essence": "Benevolent disposition"},
    {"id": "V14", "name": "Piety", "essence": "Devotional practice"},
    {"id": "V15", "name": "Righteousness", "essence": "Moral correctness"},
    {"id": "V16", "name": "Wisdom", "essence": "Applied understanding"},
    {"id": "V17", "name": "Detachment", "essence": "Freedom from material capture"},
    {"id": "V18", "name": "Unity", "essence": "Harmony with the whole"},
    {"id": "V19", "name": "Service", "essence": "Active contribution"},
]

# Natural affinities (for initial edge seeding)
AFFINITIES = {
    "V01": ["V02", "V08", "V12"],  # Trustworthiness <-> Truthfulness, Fidelity, Sincerity
    "V02": ["V01", "V12", "V03"],  # Truthfulness <-> Trustworthiness, Sincerity, Justice
    "V03": ["V04", "V15", "V16"],  # Justice <-> Fairness, Righteousness, Wisdom
    "V04": ["V03", "V13", "V18"],  # Fairness <-> Justice, Goodwill, Unity
    "V05": ["V10", "V14", "V17"],  # Chastity <-> Cleanliness, Piety, Detachment
    "V06": ["V09", "V13", "V07"],  # Courtesy <-> Hospitality, Goodwill, Forbearance
    "V07": ["V06", "V16", "V17"],  # Forbearance <-> Courtesy, Wisdom, Detachment
    "V08": ["V01", "V19", "V18"],  # Fidelity <-> Trustworthiness, Service, Unity
    "V09": ["V06", "V13", "V19"],  # Hospitality <-> Courtesy, Goodwill, Service
    "V10": ["V05", "V14", "V11"],  # Cleanliness <-> Chastity, Piety, Godliness
    "V11": ["V14", "V12", "V16"],  # Godliness <-> Piety, Sincerity, Wisdom
    "V12": ["V02", "V01", "V11"],  # Sincerity <-> Truthfulness, Trustworthiness, Godliness
    "V13": ["V09", "V04", "V18"],  # Goodwill <-> Hospitality, Fairness, Unity
    "V14": ["V11", "V10", "V15"],  # Piety <-> Godliness, Cleanliness, Righteousness
    "V15": ["V03", "V14", "V16"],  # Righteousness <-> Justice, Piety, Wisdom
    "V16": ["V03", "V07", "V17"],  # Wisdom <-> Justice, Forbearance, Detachment
    "V17": ["V16", "V05", "V11"],  # Detachment <-> Wisdom, Chastity, Godliness
    "V18": ["V04", "V13", "V19"],  # Unity <-> Fairness, Goodwill, Service
    "V19": ["V08", "V09", "V18"],  # Service <-> Fidelity, Hospitality, Unity
}


def init_virtues(baseline_activation: float = 0.3):
    """Create 19 virtue anchor nodes with tier information if they don't exist."""
    client = get_client()

    for virtue in VIRTUES:
        v_id = virtue["id"]
        # Check if exists
        if not client.node_exists(v_id):
            # Determine tier
            is_foundation_virtue = is_foundation(v_id)
            tier = "foundation" if is_foundation_virtue else "aspirational"
            threshold = get_virtue_threshold(v_id)

            create_node("VirtueAnchor", {
                "id": v_id,
                "name": virtue["name"],
                "essence": virtue["essence"],
                "activation": baseline_activation,
                "baseline": baseline_activation,
                "immutable": True,
                "type": "virtue_anchor",
                "tier": tier,
                "threshold": threshold
            })

    # Create initial affinity edges
    created = set()
    for v_id, affinities in AFFINITIES.items():
        for a_id in affinities:
            edge_key = tuple(sorted([v_id, a_id]))
            if edge_key not in created:
                # Check if edge exists
                result = client.query(
                    """
                    MATCH (a {id: $from})-[r:AFFINITY]-(b {id: $to})
                    RETURN r LIMIT 1
                    """,
                    {"from": v_id, "to": a_id}
                )
                if not result:
                    create_edge(v_id, a_id, "AFFINITY", {"weight": 0.5})
                created.add(edge_key)


def get_virtue_degrees() -> dict:
    """Get current edge count per virtue."""
    client = get_client()
    result = client.query(
        """
        MATCH (v:VirtueAnchor)-[r]-(n)
        RETURN v.id as id, count(r) as degree
        """
    )
    return {row[0]: row[1] for row in result}


def get_virtue_by_id(virtue_id: str) -> dict:
    """Get virtue definition by ID."""
    for virtue in VIRTUES:
        if virtue["id"] == virtue_id:
            return virtue
    return None


def get_all_virtue_ids() -> list:
    """Get list of all virtue IDs."""
    return [v["id"] for v in VIRTUES]
