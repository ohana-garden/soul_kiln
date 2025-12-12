"""
Node management for the Virtue Basin Simulator.

Provides high-level node operations and utilities.
"""

import logging
import uuid
from datetime import datetime
from typing import Any

from src.constants import ACTIVATION_THRESHOLD, MAX_ACTIVATION, MIN_ACTIVATION
from src.models import Node, NodeType

logger = logging.getLogger(__name__)


class NodeManager:
    """
    Manages nodes in the virtue graph.

    Provides high-level operations for creating, updating, and querying nodes.
    """

    def __init__(self, substrate):
        """
        Initialize the node manager.

        Args:
            substrate: The GraphSubstrate instance
        """
        self.substrate = substrate
        self._node_cache: dict[str, Node] = {}

    def create_concept_node(
        self,
        name: str,
        metadata: dict | None = None,
        activation: float = 0.0,
    ) -> Node:
        """
        Create a new concept node.

        Args:
            name: Name/identifier for the concept
            metadata: Optional metadata dictionary
            activation: Initial activation level

        Returns:
            The created node
        """
        node_id = f"concept_{uuid.uuid4().hex[:8]}"
        node = Node(
            id=node_id,
            type=NodeType.CONCEPT,
            activation=activation,
            baseline=0.0,
            metadata={"name": name, **(metadata or {})},
        )
        self.substrate.create_node(node)
        self._node_cache[node_id] = node
        return node

    def create_memory_node(
        self,
        content: str,
        metadata: dict | None = None,
    ) -> Node:
        """
        Create a new memory node.

        Args:
            content: The memory content
            metadata: Optional metadata dictionary

        Returns:
            The created node
        """
        node_id = f"memory_{uuid.uuid4().hex[:8]}"
        node = Node(
            id=node_id,
            type=NodeType.MEMORY,
            activation=0.0,
            baseline=0.0,
            metadata={"content": content, **(metadata or {})},
        )
        self.substrate.create_node(node)
        self._node_cache[node_id] = node
        return node

    def create_agent_node(
        self,
        agent_id: str,
        metadata: dict | None = None,
    ) -> Node:
        """
        Create a new agent reference node.

        Args:
            agent_id: Unique identifier for the agent
            metadata: Optional metadata dictionary

        Returns:
            The created node
        """
        node_id = f"agent_{agent_id}"
        node = Node(
            id=node_id,
            type=NodeType.AGENT,
            activation=0.0,
            baseline=0.0,
            metadata=metadata or {},
        )
        self.substrate.create_node(node)
        self._node_cache[node_id] = node
        return node

    def get_node(self, node_id: str) -> Node | None:
        """
        Get a node by ID.

        Args:
            node_id: The node ID

        Returns:
            The node if found, None otherwise
        """
        if node_id in self._node_cache:
            return self._node_cache[node_id]
        node = self.substrate.get_node(node_id)
        if node:
            self._node_cache[node_id] = node
        return node

    def update_activation(self, node_id: str, activation: float) -> Node | None:
        """
        Update a node's activation level.

        Args:
            node_id: The node ID
            activation: New activation level

        Returns:
            The updated node, or None if not found
        """
        node = self.get_node(node_id)
        if not node:
            return None

        # Clamp activation to valid range
        activation = max(MIN_ACTIVATION, min(MAX_ACTIVATION, activation))

        # Update the node
        node.activation = activation
        node.last_activated = datetime.utcnow()
        self.substrate.update_node(node)
        self._node_cache[node_id] = node
        return node

    def activate_node(self, node_id: str, strength: float = 1.0) -> Node | None:
        """
        Activate a node with a given strength.

        Args:
            node_id: The node ID
            strength: Activation strength (0.0 to 1.0)

        Returns:
            The updated node, or None if not found
        """
        node = self.get_node(node_id)
        if not node:
            return None

        # Add activation strength, clamped to max
        new_activation = min(MAX_ACTIVATION, node.activation + strength)
        return self.update_activation(node_id, new_activation)

    def decay_activation(self, node_id: str, decay_factor: float = 0.95) -> Node | None:
        """
        Decay a node's activation.

        Args:
            node_id: The node ID
            decay_factor: Multiplier for decay (0.0 to 1.0)

        Returns:
            The updated node, or None if not found
        """
        node = self.get_node(node_id)
        if not node:
            return None

        # Decay activation, respecting baseline
        new_activation = max(node.baseline, node.activation * decay_factor)
        return self.update_activation(node_id, new_activation)

    def is_active(self, node_id: str) -> bool:
        """
        Check if a node is currently active (above threshold).

        Args:
            node_id: The node ID

        Returns:
            True if active, False otherwise
        """
        node = self.get_node(node_id)
        return node is not None and node.activation > ACTIVATION_THRESHOLD

    def get_active_nodes(self) -> list[Node]:
        """
        Get all currently active nodes.

        Returns:
            List of active nodes
        """
        all_nodes = self.substrate.get_all_nodes()
        return [n for n in all_nodes if n.activation > ACTIVATION_THRESHOLD]

    def get_nodes_by_type(self, node_type: NodeType) -> list[Node]:
        """
        Get all nodes of a specific type.

        Args:
            node_type: The node type to filter by

        Returns:
            List of nodes
        """
        return self.substrate.get_all_nodes(node_type)

    def clear_cache(self) -> None:
        """Clear the node cache."""
        self._node_cache.clear()

    def delete_node(self, node_id: str) -> bool:
        """
        Delete a node.

        Note: Virtue anchor nodes cannot be deleted.

        Args:
            node_id: The node ID

        Returns:
            True if deleted, False otherwise
        """
        if node_id in self._node_cache:
            del self._node_cache[node_id]
        return self.substrate.delete_node(node_id)
