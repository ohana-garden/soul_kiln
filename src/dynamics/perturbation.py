"""
Perturbation system for the Virtue Basin Simulator.

Implements random activation injection to help the system:
- Escape local minima
- Explore neglected regions
- Maintain creativity ("dreams")

Perturbation formula:
    Every P timesteps:
        Select random node n
        Set x_n = random(0.5, 1.0)
"""

import logging
import random
from datetime import datetime

from src.constants import (
    PERTURBATION_INTERVAL,
    PERTURBATION_STRENGTH,
)

logger = logging.getLogger(__name__)


class Perturbator:
    """
    Implements perturbation (random activation injection).

    Perturbation helps the system escape local minima and explore
    neglected regions of the cognitive space. It's the system's
    capacity for "dreams" and creativity.
    """

    def __init__(
        self,
        node_manager,
        virtue_manager,
        perturbation_interval: int = PERTURBATION_INTERVAL,
        perturbation_strength: float = PERTURBATION_STRENGTH,
    ):
        """
        Initialize the perturbator.

        Args:
            node_manager: The NodeManager instance
            virtue_manager: The VirtueManager instance
            perturbation_interval: Steps between perturbations
            perturbation_strength: Base activation strength for perturbation
        """
        self.node_manager = node_manager
        self.virtue_manager = virtue_manager
        self.perturbation_interval = perturbation_interval
        self.perturbation_strength = perturbation_strength
        self._step_count = 0
        self._perturbations_applied = 0
        self._last_perturbation_time = None
        self._blind_spot_bias = True  # Bias toward low-activation nodes

    def step(self) -> str | None:
        """
        Advance one timestep, possibly triggering perturbation.

        Returns:
            ID of perturbed node if perturbation occurred, None otherwise
        """
        self._step_count += 1

        if self._step_count % self.perturbation_interval == 0:
            return self.perturb()

        return None

    def perturb(self) -> str:
        """
        Apply a perturbation to a random node.

        Returns:
            ID of the perturbed node
        """
        # Get all non-virtue nodes
        from src.models import NodeType
        all_nodes = self.node_manager.substrate.get_all_nodes()
        candidate_nodes = [
            n for n in all_nodes
            if n.type != NodeType.VIRTUE_ANCHOR
        ]

        if not candidate_nodes:
            # If no concept nodes, perturb a virtue anchor
            candidate_nodes = self.virtue_manager.get_all_virtues()

        if not candidate_nodes:
            logger.warning("No nodes available for perturbation")
            return ""

        # Select node (optionally biased toward low activation)
        if self._blind_spot_bias:
            node = self._select_blind_spot(candidate_nodes)
        else:
            node = random.choice(candidate_nodes)

        # Calculate perturbation strength (randomized)
        strength = random.uniform(
            self.perturbation_strength * 0.7,
            self.perturbation_strength * 1.3,
        )

        # Apply perturbation
        self.node_manager.activate_node(node.id, strength)

        self._perturbations_applied += 1
        self._last_perturbation_time = datetime.utcnow()

        logger.debug(f"Perturbation: activated {node.id} with strength {strength:.3f}")
        return node.id

    def _select_blind_spot(self, nodes: list) -> any:
        """
        Select a node biased toward low recent activation (blind spots).

        Args:
            nodes: List of candidate nodes

        Returns:
            Selected node
        """
        if not nodes:
            return None

        # Calculate weights inversely proportional to activation
        weights = []
        for node in nodes:
            # Inverse weight: lower activation = higher chance of selection
            weight = 1.0 - node.activation + 0.1  # +0.1 to avoid zero weights
            weights.append(weight)

        # Normalize weights
        total_weight = sum(weights)
        normalized = [w / total_weight for w in weights]

        # Weighted random selection
        return random.choices(nodes, weights=normalized, k=1)[0]

    def perturb_region(self, node_ids: list[str], strength: float | None = None) -> int:
        """
        Apply perturbation to multiple nodes in a region.

        Args:
            node_ids: List of node IDs to perturb
            strength: Optional strength (default: perturbation_strength)

        Returns:
            Number of nodes perturbed
        """
        strength = strength or self.perturbation_strength
        perturbed = 0

        for node_id in node_ids:
            # Randomize strength slightly for each node
            node_strength = strength * random.uniform(0.8, 1.2)
            self.node_manager.activate_node(node_id, node_strength)
            perturbed += 1

        self._perturbations_applied += perturbed
        logger.debug(f"Regional perturbation: activated {perturbed} nodes")
        return perturbed

    def perturb_blind_spots(self, threshold_seconds: int = 86400) -> int:
        """
        Perturb all nodes that haven't been activated recently.

        Args:
            threshold_seconds: Time threshold for "blind spot" (default: 24 hours)

        Returns:
            Number of nodes perturbed
        """
        current_time = datetime.utcnow()
        from datetime import timedelta
        threshold = current_time - timedelta(seconds=threshold_seconds)

        all_nodes = self.node_manager.substrate.get_all_nodes()
        blind_spots = [
            n for n in all_nodes
            if n.last_activated < threshold
        ]

        if not blind_spots:
            return 0

        node_ids = [n.id for n in blind_spots]
        return self.perturb_region(node_ids, strength=self.perturbation_strength * 0.5)

    def get_stats(self) -> dict:
        """
        Get perturbation statistics.

        Returns:
            Dict with perturbation statistics
        """
        return {
            "step_count": self._step_count,
            "perturbations_applied": self._perturbations_applied,
            "perturbation_interval": self.perturbation_interval,
            "perturbation_strength": self.perturbation_strength,
            "last_perturbation": (
                self._last_perturbation_time.isoformat()
                if self._last_perturbation_time
                else None
            ),
            "blind_spot_bias": self._blind_spot_bias,
        }

    def set_blind_spot_bias(self, enabled: bool) -> None:
        """Enable or disable blind spot bias."""
        self._blind_spot_bias = enabled

    def reset_stats(self) -> None:
        """Reset perturbation statistics."""
        self._step_count = 0
        self._perturbations_applied = 0
        self._last_perturbation_time = None
