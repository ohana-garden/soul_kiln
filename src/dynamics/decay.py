"""
Temporal decay for the Virtue Basin Simulator.

Implements edge weight decay over time. Unused connections weaken,
allowing the system to forget and escape local minima.

The decay formula:
    W_ij(t+1) = W_ij(t) · λ   (if edge unused)

Where:
    λ = decay constant (0.95-0.99)
"""

import logging
from datetime import datetime, timedelta

from src.constants import (
    DECAY_CONSTANT,
    DECAY_INTERVAL_SECONDS,
    EDGE_REMOVAL_THRESHOLD,
    TARGET_CONNECTIVITY,
)

logger = logging.getLogger(__name__)


class TemporalDecay:
    """
    Implements temporal decay of edge weights.

    Edges that are not used decay over time. This allows the system to:
    - Forget unused associations
    - Escape local minima
    - Maintain plasticity
    """

    def __init__(
        self,
        edge_manager,
        virtue_manager,
        decay_constant: float = DECAY_CONSTANT,
        decay_interval_seconds: int = DECAY_INTERVAL_SECONDS,
    ):
        """
        Initialize the temporal decay system.

        Args:
            edge_manager: The EdgeManager instance
            virtue_manager: The VirtueManager instance
            decay_constant: Decay multiplier (default 0.97)
            decay_interval_seconds: Interval for one decay period
        """
        self.edge_manager = edge_manager
        self.virtue_manager = virtue_manager
        self.decay_constant = decay_constant
        self.decay_interval_seconds = decay_interval_seconds
        self._last_decay_time = datetime.utcnow()
        self._edges_decayed = 0
        self._edges_removed = 0

    def apply_decay(self) -> dict:
        """
        Apply temporal decay to all edges.

        Edges decay based on time since last use.
        Protected edges (maintaining virtue min degree) are not removed.

        Returns:
            Statistics about the decay operation
        """
        current_time = datetime.utcnow()
        edges = self.edge_manager.get_all_edges()

        decayed = 0
        removed = 0
        protected = 0

        for edge in edges:
            # Calculate decay periods since last use
            time_since_use = current_time - edge.last_used
            decay_periods = time_since_use.total_seconds() / self.decay_interval_seconds

            if decay_periods < 1:
                continue  # Not enough time passed

            # Calculate new weight
            decay_factor = self.decay_constant ** decay_periods
            new_weight = edge.weight * decay_factor

            if new_weight < EDGE_REMOVAL_THRESHOLD:
                # Check if removal would violate min degree constraint
                if self._would_violate_min_degree(edge):
                    protected += 1
                    # Set to minimum instead of removing
                    self.edge_manager.decay_edge(
                        edge.source_id,
                        edge.target_id,
                        EDGE_REMOVAL_THRESHOLD / edge.weight,
                    )
                else:
                    self.edge_manager.delete_edge(edge.source_id, edge.target_id)
                    removed += 1
            else:
                self.edge_manager.decay_edge(
                    edge.source_id,
                    edge.target_id,
                    decay_factor,
                )
                decayed += 1

        self._last_decay_time = current_time
        self._edges_decayed += decayed
        self._edges_removed += removed

        logger.info(f"Decay: {decayed} edges decayed, {removed} removed, {protected} protected")

        return {
            "edges_decayed": decayed,
            "edges_removed": removed,
            "edges_protected": protected,
            "total_edges_remaining": len(edges) - removed,
        }

    def _would_violate_min_degree(self, edge) -> bool:
        """
        Check if removing an edge would violate minimum degree constraint.

        Virtue anchors must maintain at least TARGET_CONNECTIVITY edges.

        Args:
            edge: The edge to check

        Returns:
            True if removal would violate constraint, False otherwise
        """
        # Check source node
        if self.virtue_manager.is_virtue_anchor(edge.source_id):
            current_degree = self.edge_manager.get_node_degree(edge.source_id)
            if current_degree <= TARGET_CONNECTIVITY:
                return True

        # Check target node
        if self.virtue_manager.is_virtue_anchor(edge.target_id):
            current_degree = self.edge_manager.get_node_degree(edge.target_id)
            if current_degree <= TARGET_CONNECTIVITY:
                return True

        return False

    def decay_region(
        self,
        node_ids: list[str],
        multiplier: float = 2.0,
    ) -> int:
        """
        Apply accelerated decay to a specific region.

        Used for self-healing when false basins are detected.

        Args:
            node_ids: List of node IDs in the region
            multiplier: Decay acceleration factor

        Returns:
            Number of edges affected
        """
        affected = 0
        accelerated_factor = self.decay_constant ** multiplier

        for node_id in node_ids:
            # Decay outgoing edges
            for edge in self.edge_manager.get_outgoing_edges(node_id):
                if edge.target_id in node_ids:  # Only internal edges
                    self.edge_manager.decay_edge(
                        edge.source_id,
                        edge.target_id,
                        accelerated_factor,
                    )
                    affected += 1

        logger.debug(f"Accelerated decay in region: {affected} edges affected")
        return affected

    def get_decay_stats(self) -> dict:
        """
        Get statistics about decay operations.

        Returns:
            Dict with decay statistics
        """
        return {
            "decay_constant": self.decay_constant,
            "decay_interval_seconds": self.decay_interval_seconds,
            "last_decay_time": self._last_decay_time.isoformat(),
            "total_edges_decayed": self._edges_decayed,
            "total_edges_removed": self._edges_removed,
        }

    def reset_stats(self) -> None:
        """Reset decay statistics."""
        self._edges_decayed = 0
        self._edges_removed = 0


class AdaptiveDecay(TemporalDecay):
    """
    Adaptive decay that adjusts based on system state.

    Increases decay when system is stuck, decreases when exploring.
    """

    def __init__(
        self,
        edge_manager,
        virtue_manager,
        min_decay: float = 0.90,
        max_decay: float = 0.99,
        **kwargs,
    ):
        """
        Initialize adaptive decay.

        Args:
            edge_manager: The EdgeManager instance
            virtue_manager: The VirtueManager instance
            min_decay: Minimum decay constant (fastest decay)
            max_decay: Maximum decay constant (slowest decay)
        """
        super().__init__(edge_manager, virtue_manager, **kwargs)
        self.min_decay = min_decay
        self.max_decay = max_decay
        self._stuck_count = 0

    def report_stuck(self) -> None:
        """Report that the system appears stuck."""
        self._stuck_count += 1
        # Decrease decay constant (faster decay) when stuck
        self.decay_constant = max(
            self.min_decay,
            self.decay_constant - 0.01,
        )
        logger.debug(f"System stuck, decay constant now: {self.decay_constant}")

    def report_exploring(self) -> None:
        """Report that the system is exploring new regions."""
        self._stuck_count = max(0, self._stuck_count - 1)
        # Increase decay constant (slower decay) when exploring
        self.decay_constant = min(
            self.max_decay,
            self.decay_constant + 0.005,
        )
        logger.debug(f"System exploring, decay constant now: {self.decay_constant}")
