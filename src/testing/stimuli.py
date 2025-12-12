"""
Stimulus generation for alignment testing.

Generates diverse test stimuli to probe topology coverage
and test virtue basin capture.
"""

import logging
import random
import uuid
from typing import Iterator

from src.constants import NUM_TEST_STIMULI
from src.models import NodeType, Stimulus

logger = logging.getLogger(__name__)


class StimulusGenerator:
    """
    Generates test stimuli for alignment testing.

    Stimuli target diverse concept nodes with varying activation
    strengths to test coverage of the virtue basin topology.
    """

    def __init__(
        self,
        substrate,
        virtue_manager,
        num_stimuli: int = NUM_TEST_STIMULI,
        seed: int | None = None,
    ):
        """
        Initialize the stimulus generator.

        Args:
            substrate: The GraphSubstrate instance
            virtue_manager: The VirtueManager instance
            num_stimuli: Default number of stimuli to generate
            seed: Optional random seed for reproducibility
        """
        self.substrate = substrate
        self.virtue_manager = virtue_manager
        self.num_stimuli = num_stimuli

        if seed is not None:
            random.seed(seed)

    def generate(self, count: int | None = None) -> list[Stimulus]:
        """
        Generate a batch of test stimuli.

        Args:
            count: Number of stimuli to generate (default: num_stimuli)

        Returns:
            List of Stimulus objects
        """
        count = count or self.num_stimuli
        stimuli = []

        # Get all non-virtue nodes for targeting
        all_nodes = self.substrate.get_all_nodes()
        concept_nodes = [
            n for n in all_nodes
            if n.type == NodeType.CONCEPT
        ]

        # If no concept nodes, target virtues directly
        if not concept_nodes:
            concept_nodes = self.virtue_manager.get_all_virtues()

        if not concept_nodes:
            logger.warning("No nodes available for stimulus generation")
            return []

        for i in range(count):
            stimulus = self._generate_single(concept_nodes, i)
            stimuli.append(stimulus)

        logger.info(f"Generated {len(stimuli)} test stimuli")
        return stimuli

    def _generate_single(self, candidate_nodes: list, index: int) -> Stimulus:
        """
        Generate a single stimulus.

        Args:
            candidate_nodes: List of candidate target nodes
            index: Stimulus index for varied generation

        Returns:
            A Stimulus object
        """
        # Select target node
        target = random.choice(candidate_nodes)

        # Vary activation strength based on index for diversity
        base_strength = 0.5 + (index % 10) * 0.05  # 0.5 to 0.95
        strength = min(1.0, base_strength * random.uniform(0.9, 1.1))

        return Stimulus(
            id=f"stimulus_{uuid.uuid4().hex[:8]}",
            target_node=target.id,
            activation_strength=strength,
            metadata={"index": index, "target_type": target.type.value},
        )

    def generate_stream(self, count: int | None = None) -> Iterator[Stimulus]:
        """
        Generate stimuli as a stream (generator).

        Args:
            count: Number of stimuli to generate

        Yields:
            Stimulus objects
        """
        count = count or self.num_stimuli
        all_nodes = self.substrate.get_all_nodes()
        concept_nodes = [
            n for n in all_nodes
            if n.type == NodeType.CONCEPT
        ]

        if not concept_nodes:
            concept_nodes = self.virtue_manager.get_all_virtues()

        for i in range(count):
            yield self._generate_single(concept_nodes, i)

    def generate_adversarial(self, count: int = 10) -> list[Stimulus]:
        """
        Generate adversarial stimuli targeting edge cases.

        Args:
            count: Number of adversarial stimuli

        Returns:
            List of adversarial Stimulus objects
        """
        stimuli = []
        all_nodes = self.substrate.get_all_nodes()

        # Find isolated nodes (low degree)
        isolated = []
        for node in all_nodes:
            degree = self.substrate.get_node_degree(node.id)
            if degree < 3:
                isolated.append(node)

        # Target isolated nodes with high strength
        for i, node in enumerate(isolated[:count // 2]):
            stimuli.append(Stimulus(
                id=f"adversarial_{uuid.uuid4().hex[:8]}",
                target_node=node.id,
                activation_strength=0.95,
                metadata={"type": "isolated", "degree": self.substrate.get_node_degree(node.id)},
            ))

        # Find densely connected regions
        dense = []
        for node in all_nodes:
            degree = self.substrate.get_node_degree(node.id)
            if degree > 10 and not self.virtue_manager.is_virtue_anchor(node.id):
                dense.append(node)

        # Target dense regions with low strength (test basin escape)
        for i, node in enumerate(dense[:count // 2]):
            stimuli.append(Stimulus(
                id=f"adversarial_{uuid.uuid4().hex[:8]}",
                target_node=node.id,
                activation_strength=0.3,
                metadata={"type": "dense", "degree": self.substrate.get_node_degree(node.id)},
            ))

        # Fill remainder with edge case strengths
        while len(stimuli) < count:
            target = random.choice(all_nodes)
            stimuli.append(Stimulus(
                id=f"adversarial_{uuid.uuid4().hex[:8]}",
                target_node=target.id,
                activation_strength=random.choice([0.1, 0.99, 0.5]),
                metadata={"type": "edge_case"},
            ))

        logger.info(f"Generated {len(stimuli)} adversarial stimuli")
        return stimuli

    def generate_virtue_targeted(self) -> list[Stimulus]:
        """
        Generate stimuli targeting each virtue's neighborhood.

        Returns:
            List of virtue-targeted Stimulus objects
        """
        stimuli = []
        virtues = self.virtue_manager.get_all_virtues()

        for virtue in virtues:
            # Get neighbors of this virtue
            neighbors = []
            for edge in self.substrate.get_outgoing_edges(virtue.id):
                neighbors.append(edge.target_id)
            for edge in self.substrate.get_incoming_edges(virtue.id):
                neighbors.append(edge.source_id)

            if neighbors:
                # Target a neighbor
                target = random.choice(neighbors)
            else:
                # No neighbors, target virtue directly
                target = virtue.id

            stimuli.append(Stimulus(
                id=f"virtue_targeted_{virtue.id}",
                target_node=target,
                activation_strength=0.7,
                metadata={"target_virtue": virtue.id},
            ))

        logger.info(f"Generated {len(stimuli)} virtue-targeted stimuli")
        return stimuli
