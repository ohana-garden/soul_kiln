"""
Virtue anchor management for the Virtue Basin Simulator.

The 19 virtue anchors from the Kitáb-i-Aqdas form the fixed points
in the cognitive space around which basins of attraction form.

Key insight: A 9-regular graph on 19 nodes is mathematically impossible.
19 × 9 = 171, which is odd, so edges = 171/2 = 85.5 (non-integer).
This irreducible asymmetry creates perpetual flow.
"""

import logging
from typing import Final

from src.constants import NUM_VIRTUES, TARGET_CONNECTIVITY, VIRTUE_BASELINE_ACTIVATION
from src.models import Node, NodeType, VirtueAnchor

logger = logging.getLogger(__name__)


# The 19 virtue anchors from the Kitáb-i-Aqdas
VIRTUE_DEFINITIONS: Final[list[VirtueAnchor]] = [
    VirtueAnchor(
        id="V01",
        name="Trustworthiness",
        description="Reliability in word and deed - the goodliest vesture, fundamental purpose of creation",
        key_relationships=["V02", "V08", "V12"],  # Truthfulness, Fidelity, Sincerity
    ),
    VirtueAnchor(
        id="V02",
        name="Truthfulness",
        description="Strict, absolute honesty in speech",
        key_relationships=["V01", "V12", "V03"],  # Trustworthiness, Sincerity, Justice
    ),
    VirtueAnchor(
        id="V03",
        name="Justice",
        description="Fair treatment and judgment in all dealings",
        key_relationships=["V04", "V15", "V16"],  # Fairness, Righteousness, Wisdom
    ),
    VirtueAnchor(
        id="V04",
        name="Fairness",
        description="Impartial equity in judgment and action",
        key_relationships=["V03", "V13", "V18"],  # Justice, Goodwill, Unity
    ),
    VirtueAnchor(
        id="V05",
        name="Chastity",
        description="Purity of conduct and moral cleanliness",
        key_relationships=["V10", "V14", "V17"],  # Cleanliness, Piety, Detachment
    ),
    VirtueAnchor(
        id="V06",
        name="Courtesy",
        description="Refined, respectful behavior in all interactions",
        key_relationships=["V09", "V13", "V07"],  # Hospitality, Goodwill, Forbearance
    ),
    VirtueAnchor(
        id="V07",
        name="Forbearance",
        description="Patient endurance and tolerance",
        key_relationships=["V06", "V16", "V17"],  # Courtesy, Wisdom, Detachment
    ),
    VirtueAnchor(
        id="V08",
        name="Fidelity",
        description="Loyal steadfastness in commitments",
        key_relationships=["V01", "V19", "V18"],  # Trustworthiness, Service, Unity
    ),
    VirtueAnchor(
        id="V09",
        name="Hospitality",
        description="Generous welcome and care for others",
        key_relationships=["V06", "V13", "V19"],  # Courtesy, Goodwill, Service
    ),
    VirtueAnchor(
        id="V10",
        name="Cleanliness",
        description="Physical and spiritual purity",
        key_relationships=["V05", "V14", "V11"],  # Chastity, Piety, Godliness
    ),
    VirtueAnchor(
        id="V11",
        name="Godliness",
        description="Reverent devotion and fear of God",
        key_relationships=["V14", "V12", "V16"],  # Piety, Sincerity, Wisdom
    ),
    VirtueAnchor(
        id="V12",
        name="Sincerity",
        description="Authentic intent and genuine expression",
        key_relationships=["V02", "V01", "V11"],  # Truthfulness, Trustworthiness, Godliness
    ),
    VirtueAnchor(
        id="V13",
        name="Goodwill",
        description="Benevolent disposition toward all",
        key_relationships=["V09", "V04", "V18"],  # Hospitality, Fairness, Unity
    ),
    VirtueAnchor(
        id="V14",
        name="Piety",
        description="Devotional practice and religious observance",
        key_relationships=["V11", "V10", "V15"],  # Godliness, Cleanliness, Righteousness
    ),
    VirtueAnchor(
        id="V15",
        name="Righteousness",
        description="Moral correctness and uprightness",
        key_relationships=["V03", "V14", "V16"],  # Justice, Piety, Wisdom
    ),
    VirtueAnchor(
        id="V16",
        name="Wisdom",
        description="Applied understanding and discernment",
        key_relationships=["V03", "V07", "V17"],  # Justice, Forbearance, Detachment
    ),
    VirtueAnchor(
        id="V17",
        name="Detachment",
        description="Freedom from material excess and worldly attachment",
        key_relationships=["V16", "V05", "V11"],  # Wisdom, Chastity, Godliness
    ),
    VirtueAnchor(
        id="V18",
        name="Unity",
        description="Harmony, concord, and amity with others",
        key_relationships=["V04", "V13", "V19"],  # Fairness, Goodwill, Service
    ),
    VirtueAnchor(
        id="V19",
        name="Service",
        description="Active contribution to the well-being of others",
        key_relationships=["V08", "V09", "V18"],  # Fidelity, Hospitality, Unity
    ),
]


class VirtueManager:
    """
    Manages virtue anchor nodes in the virtue graph.

    Virtue anchors are immutable, fixed points in the cognitive space.
    They cannot be deleted or moved, and have elevated baseline activation.
    """

    def __init__(self, substrate):
        """
        Initialize the virtue manager.

        Args:
            substrate: The GraphSubstrate instance
        """
        self.substrate = substrate
        self._virtue_nodes: dict[str, Node] = {}

    def initialize_virtues(self) -> list[Node]:
        """
        Initialize all 19 virtue anchor nodes.

        Creates virtue anchor nodes if they don't exist.
        Virtue anchors are immutable once created.

        Returns:
            List of virtue anchor nodes
        """
        nodes = []
        for virtue_def in VIRTUE_DEFINITIONS:
            node = self._create_or_get_virtue(virtue_def)
            nodes.append(node)
        logger.info(f"Initialized {len(nodes)} virtue anchor nodes")
        return nodes

    def _create_or_get_virtue(self, virtue_def: VirtueAnchor) -> Node:
        """
        Create or retrieve a virtue anchor node.

        Args:
            virtue_def: The virtue definition

        Returns:
            The virtue anchor node
        """
        existing = self.substrate.get_node(virtue_def.id)
        if existing:
            self._virtue_nodes[virtue_def.id] = existing
            return existing

        node = Node(
            id=virtue_def.id,
            type=NodeType.VIRTUE_ANCHOR,
            activation=VIRTUE_BASELINE_ACTIVATION,
            baseline=VIRTUE_BASELINE_ACTIVATION,
            metadata={
                "name": virtue_def.name,
                "description": virtue_def.description,
                "key_relationships": virtue_def.key_relationships,
            },
        )
        self.substrate.create_node(node)
        self._virtue_nodes[virtue_def.id] = node
        logger.debug(f"Created virtue anchor: {virtue_def.name} ({virtue_def.id})")
        return node

    def get_virtue(self, virtue_id: str) -> Node | None:
        """
        Get a virtue anchor node by ID.

        Args:
            virtue_id: The virtue ID (e.g., "V01")

        Returns:
            The virtue node if found, None otherwise
        """
        if virtue_id in self._virtue_nodes:
            return self._virtue_nodes[virtue_id]
        node = self.substrate.get_node(virtue_id)
        if node and node.is_virtue_anchor():
            self._virtue_nodes[virtue_id] = node
            return node
        return None

    def get_all_virtues(self) -> list[Node]:
        """
        Get all virtue anchor nodes.

        Returns:
            List of all virtue anchor nodes
        """
        return self.substrate.get_virtue_anchors()

    def get_virtue_by_name(self, name: str) -> Node | None:
        """
        Get a virtue anchor by name.

        Args:
            name: The virtue name (e.g., "Trustworthiness")

        Returns:
            The virtue node if found, None otherwise
        """
        for virtue_def in VIRTUE_DEFINITIONS:
            if virtue_def.name.lower() == name.lower():
                return self.get_virtue(virtue_def.id)
        return None

    def get_virtue_definition(self, virtue_id: str) -> VirtueAnchor | None:
        """
        Get the virtue definition by ID.

        Args:
            virtue_id: The virtue ID

        Returns:
            The virtue definition if found, None otherwise
        """
        for virtue_def in VIRTUE_DEFINITIONS:
            if virtue_def.id == virtue_id:
                return virtue_def
        return None

    def is_virtue_anchor(self, node_id: str) -> bool:
        """
        Check if a node ID refers to a virtue anchor.

        Args:
            node_id: The node ID to check

        Returns:
            True if it's a virtue anchor, False otherwise
        """
        return any(v.id == node_id for v in VIRTUE_DEFINITIONS)

    def get_related_virtues(self, virtue_id: str) -> list[Node]:
        """
        Get the related virtues for a given virtue.

        Args:
            virtue_id: The virtue ID

        Returns:
            List of related virtue nodes
        """
        virtue_def = self.get_virtue_definition(virtue_id)
        if not virtue_def:
            return []
        return [self.get_virtue(rel_id) for rel_id in virtue_def.key_relationships if self.get_virtue(rel_id)]

    def get_virtue_degree(self, virtue_id: str) -> int:
        """
        Get the current degree (edge count) of a virtue anchor.

        Args:
            virtue_id: The virtue ID

        Returns:
            Number of edges connected to this virtue
        """
        return self.substrate.get_node_degree(virtue_id)

    def get_degree_deficit(self, virtue_id: str) -> int:
        """
        Get the deficit from target connectivity for a virtue.

        Args:
            virtue_id: The virtue ID

        Returns:
            Number of edges needed to reach target (can be negative if over)
        """
        current = self.get_virtue_degree(virtue_id)
        return TARGET_CONNECTIVITY - current

    def get_all_degree_deficits(self) -> dict[str, int]:
        """
        Get degree deficits for all virtues.

        Returns:
            Dict mapping virtue ID to deficit
        """
        return {v.id: self.get_degree_deficit(v.id) for v in VIRTUE_DEFINITIONS}

    def initialize_virtue_relationships(self, edge_manager) -> int:
        """
        Initialize edges between related virtues.

        Creates initial edges based on the key_relationships defined
        for each virtue.

        Args:
            edge_manager: The EdgeManager instance

        Returns:
            Number of edges created
        """
        edges_created = 0
        for virtue_def in VIRTUE_DEFINITIONS:
            for related_id in virtue_def.key_relationships:
                # Create bidirectional edges
                existing = edge_manager.get_edge(virtue_def.id, related_id)
                if not existing:
                    edge_manager.create_edge(virtue_def.id, related_id, weight=0.5)
                    edges_created += 1
                existing = edge_manager.get_edge(related_id, virtue_def.id)
                if not existing:
                    edge_manager.create_edge(related_id, virtue_def.id, weight=0.5)
                    edges_created += 1

        logger.info(f"Initialized {edges_created} virtue relationship edges")
        return edges_created
