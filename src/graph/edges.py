"""
Edge management for the Virtue Basin Simulator.

Provides high-level edge operations including weight management,
Hebbian updates, and decay.
"""

import logging
from datetime import datetime

from src.constants import (
    EDGE_REMOVAL_THRESHOLD,
    LEARNING_RATE,
    MAX_EDGE_WEIGHT,
    MIN_EDGE_WEIGHT,
)
from src.models import Edge, EdgeDirection

logger = logging.getLogger(__name__)


class EdgeManager:
    """
    Manages edges in the virtue graph.

    Provides high-level operations for creating, updating, and querying edges,
    including support for Hebbian learning and temporal decay.
    """

    def __init__(self, substrate):
        """
        Initialize the edge manager.

        Args:
            substrate: The GraphSubstrate instance
        """
        self.substrate = substrate
        self._edge_cache: dict[str, Edge] = {}

    def _edge_key(self, source_id: str, target_id: str) -> str:
        """Create a cache key for an edge."""
        return f"{source_id}->{target_id}"

    def create_edge(
        self,
        source_id: str,
        target_id: str,
        weight: float = 0.5,
        direction: EdgeDirection = EdgeDirection.FORWARD,
    ) -> Edge:
        """
        Create a new edge between nodes.

        Args:
            source_id: Source node ID
            target_id: Target node ID
            weight: Initial edge weight
            direction: Edge direction

        Returns:
            The created edge
        """
        edge = Edge(
            source_id=source_id,
            target_id=target_id,
            weight=max(MIN_EDGE_WEIGHT, min(MAX_EDGE_WEIGHT, weight)),
            direction=direction,
        )
        self.substrate.create_edge(edge)
        self._edge_cache[self._edge_key(source_id, target_id)] = edge
        return edge

    def get_edge(self, source_id: str, target_id: str) -> Edge | None:
        """
        Get an edge by source and target IDs.

        Args:
            source_id: Source node ID
            target_id: Target node ID

        Returns:
            The edge if found, None otherwise
        """
        key = self._edge_key(source_id, target_id)
        if key in self._edge_cache:
            return self._edge_cache[key]
        edge = self.substrate.get_edge(source_id, target_id)
        if edge:
            self._edge_cache[key] = edge
        return edge

    def get_or_create_edge(
        self,
        source_id: str,
        target_id: str,
        initial_weight: float = LEARNING_RATE,
    ) -> Edge:
        """
        Get an existing edge or create a new one.

        Args:
            source_id: Source node ID
            target_id: Target node ID
            initial_weight: Weight for new edge if created

        Returns:
            The edge (existing or new)
        """
        edge = self.get_edge(source_id, target_id)
        if edge is None:
            edge = self.create_edge(source_id, target_id, weight=initial_weight)
        return edge

    def strengthen_edge(
        self,
        source_id: str,
        target_id: str,
        amount: float = LEARNING_RATE,
    ) -> Edge:
        """
        Strengthen an edge (Hebbian learning).

        If the edge doesn't exist, it will be created.

        Args:
            source_id: Source node ID
            target_id: Target node ID
            amount: Amount to strengthen by

        Returns:
            The updated edge
        """
        edge = self.get_or_create_edge(source_id, target_id, initial_weight=amount)

        # Strengthen the edge
        edge.weight = min(MAX_EDGE_WEIGHT, edge.weight + amount)
        edge.last_used = datetime.utcnow()
        edge.use_count += 1

        self.substrate.update_edge(edge)
        self._edge_cache[self._edge_key(source_id, target_id)] = edge
        return edge

    def weaken_edge(
        self,
        source_id: str,
        target_id: str,
        amount: float = LEARNING_RATE,
    ) -> Edge | None:
        """
        Weaken an edge.

        Args:
            source_id: Source node ID
            target_id: Target node ID
            amount: Amount to weaken by

        Returns:
            The updated edge, or None if edge doesn't exist
        """
        edge = self.get_edge(source_id, target_id)
        if edge is None:
            return None

        edge.weight = max(MIN_EDGE_WEIGHT, edge.weight - amount)
        self.substrate.update_edge(edge)
        self._edge_cache[self._edge_key(source_id, target_id)] = edge
        return edge

    def decay_edge(
        self,
        source_id: str,
        target_id: str,
        decay_factor: float,
    ) -> Edge | None:
        """
        Apply temporal decay to an edge.

        Args:
            source_id: Source node ID
            target_id: Target node ID
            decay_factor: Multiplier for decay (0.0 to 1.0)

        Returns:
            The updated edge, or None if edge doesn't exist or was removed
        """
        edge = self.get_edge(source_id, target_id)
        if edge is None:
            return None

        edge.weight *= decay_factor

        # Remove edge if below threshold
        if edge.weight < EDGE_REMOVAL_THRESHOLD:
            self.delete_edge(source_id, target_id)
            return None

        self.substrate.update_edge(edge)
        self._edge_cache[self._edge_key(source_id, target_id)] = edge
        return edge

    def delete_edge(self, source_id: str, target_id: str) -> bool:
        """
        Delete an edge.

        Args:
            source_id: Source node ID
            target_id: Target node ID

        Returns:
            True if deleted, False otherwise
        """
        key = self._edge_key(source_id, target_id)
        if key in self._edge_cache:
            del self._edge_cache[key]
        return self.substrate.delete_edge(source_id, target_id)

    def get_incoming_edges(self, node_id: str) -> list[Edge]:
        """
        Get all edges incoming to a node.

        Args:
            node_id: The target node ID

        Returns:
            List of incoming edges
        """
        return self.substrate.get_incoming_edges(node_id)

    def get_outgoing_edges(self, node_id: str) -> list[Edge]:
        """
        Get all edges outgoing from a node.

        Args:
            node_id: The source node ID

        Returns:
            List of outgoing edges
        """
        return self.substrate.get_outgoing_edges(node_id)

    def get_node_degree(self, node_id: str) -> int:
        """
        Get the total degree (edges) of a node.

        Args:
            node_id: The node ID

        Returns:
            Total edge count
        """
        return self.substrate.get_node_degree(node_id)

    def get_all_edges(self) -> list[Edge]:
        """Get all edges in the graph."""
        return self.substrate.get_all_edges()

    def get_edge_weight(self, source_id: str, target_id: str) -> float:
        """
        Get the weight of an edge.

        Args:
            source_id: Source node ID
            target_id: Target node ID

        Returns:
            Edge weight, or 0.0 if edge doesn't exist
        """
        edge = self.get_edge(source_id, target_id)
        return edge.weight if edge else 0.0

    def clear_cache(self) -> None:
        """Clear the edge cache."""
        self._edge_cache.clear()

    def total_weight(self) -> float:
        """Get the sum of all edge weights."""
        return sum(e.weight for e in self.get_all_edges())

    def mean_weight(self) -> float:
        """Get the mean edge weight."""
        edges = self.get_all_edges()
        if not edges:
            return 0.0
        return sum(e.weight for e in edges) / len(edges)
