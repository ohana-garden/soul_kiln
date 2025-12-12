"""
Hebbian learning for the Virtue Basin Simulator.

Implements the principle: "Neurons that fire together, wire together."
Co-activated nodes strengthen their connections.

The Hebbian update formula:
    ΔW_ij = η · x_i · x_j

Where:
    η = learning rate
    x_i, x_j = activations of connected nodes
"""

import logging
from datetime import datetime

from src.constants import LEARNING_RATE, MAX_EDGE_WEIGHT
from src.models import Edge, Trajectory

logger = logging.getLogger(__name__)


class HebbianLearner:
    """
    Implements Hebbian learning for edge strengthening.

    When nodes are co-activated (fire together), their connection
    is strengthened (wire together). This creates associative patterns
    in the virtue graph.
    """

    def __init__(self, edge_manager, node_manager, learning_rate: float = LEARNING_RATE):
        """
        Initialize the Hebbian learner.

        Args:
            edge_manager: The EdgeManager instance
            node_manager: The NodeManager instance
            learning_rate: Rate of learning (default from constants)
        """
        self.edge_manager = edge_manager
        self.node_manager = node_manager
        self.learning_rate = learning_rate
        self._updates_this_session = 0

    def learn_from_trajectory(self, trajectory: Trajectory) -> int:
        """
        Apply Hebbian learning from a trajectory.

        Strengthens edges between consecutive nodes in the trajectory path.

        Args:
            trajectory: The trajectory to learn from

        Returns:
            Number of edges strengthened/created
        """
        if len(trajectory.path) < 2:
            return 0

        edges_updated = 0
        for i in range(len(trajectory.path) - 1):
            source_id = trajectory.path[i]
            target_id = trajectory.path[i + 1]

            # Get node activations for weighted learning
            source_node = self.node_manager.get_node(source_id)
            target_node = self.node_manager.get_node(target_id)

            if source_node and target_node:
                # Weighted Hebbian: ΔW = η · x_source · x_target
                delta = self.learning_rate * source_node.activation * target_node.activation
                self.edge_manager.strengthen_edge(source_id, target_id, amount=delta)
                edges_updated += 1

        self._updates_this_session += edges_updated
        logger.debug(f"Hebbian learning: updated {edges_updated} edges from trajectory")
        return edges_updated

    def learn_from_coactivation(
        self,
        node_ids: list[str],
        strength: float | None = None,
    ) -> int:
        """
        Apply Hebbian learning from a set of co-activated nodes.

        Creates/strengthens edges between all pairs of co-activated nodes.

        Args:
            node_ids: List of co-activated node IDs
            strength: Optional learning strength (default: learning_rate)

        Returns:
            Number of edges strengthened/created
        """
        if len(node_ids) < 2:
            return 0

        strength = strength or self.learning_rate
        edges_updated = 0

        # Create edges between all pairs
        for i, source_id in enumerate(node_ids):
            for target_id in node_ids[i + 1:]:
                # Get activations
                source = self.node_manager.get_node(source_id)
                target = self.node_manager.get_node(target_id)

                if source and target:
                    # Bidirectional strengthening
                    delta = strength * source.activation * target.activation
                    self.edge_manager.strengthen_edge(source_id, target_id, amount=delta)
                    self.edge_manager.strengthen_edge(target_id, source_id, amount=delta)
                    edges_updated += 2

        self._updates_this_session += edges_updated
        logger.debug(f"Hebbian learning: updated {edges_updated} edges from coactivation")
        return edges_updated

    def anti_hebbian_learning(
        self,
        source_id: str,
        target_id: str,
        amount: float | None = None,
    ) -> bool:
        """
        Apply anti-Hebbian learning (weakening).

        Used to weaken connections that lead to undesirable outcomes.

        Args:
            source_id: Source node ID
            target_id: Target node ID
            amount: Amount to weaken by (default: learning_rate)

        Returns:
            True if edge was weakened, False otherwise
        """
        amount = amount or self.learning_rate
        edge = self.edge_manager.weaken_edge(source_id, target_id, amount)
        if edge:
            logger.debug(f"Anti-Hebbian: weakened edge {source_id} -> {target_id}")
            return True
        return False

    def batch_learn(self, trajectories: list[Trajectory]) -> dict:
        """
        Apply Hebbian learning from multiple trajectories.

        Args:
            trajectories: List of trajectories to learn from

        Returns:
            Statistics about the learning
        """
        total_edges = 0
        captured_learning = 0
        escaped_learning = 0

        for trajectory in trajectories:
            edges = self.learn_from_trajectory(trajectory)
            total_edges += edges

            if trajectory.was_captured:
                captured_learning += edges
            else:
                escaped_learning += edges

        return {
            "total_edges_updated": total_edges,
            "captured_trajectory_edges": captured_learning,
            "escaped_trajectory_edges": escaped_learning,
            "trajectories_processed": len(trajectories),
        }

    def get_session_stats(self) -> dict:
        """
        Get statistics for this learning session.

        Returns:
            Dict with session statistics
        """
        return {
            "updates_this_session": self._updates_this_session,
            "learning_rate": self.learning_rate,
        }

    def reset_session_stats(self) -> None:
        """Reset session statistics."""
        self._updates_this_session = 0
