"""
Shared memory management for the Virtue Basin Simulator.

Manages the shared Graphiti memory space where all agents
can read and write, with proper conflict resolution.
"""

import logging
import threading
from datetime import datetime
from typing import Any

from src.models import Edge, Node

logger = logging.getLogger(__name__)


class SharedMemory:
    """
    Shared memory space for agent coordination.

    All agents see the same concept nodes and can write to shared edges.
    Activity is attributed to originating agents for tracking.
    """

    def __init__(self, substrate, edge_manager, node_manager):
        """
        Initialize shared memory.

        Args:
            substrate: The GraphSubstrate instance
            edge_manager: The EdgeManager instance
            node_manager: The NodeManager instance
        """
        self.substrate = substrate
        self.edge_manager = edge_manager
        self.node_manager = node_manager
        self._lock = threading.RLock()
        self._activity_log: list[dict] = []
        self._max_log_size = 10000

    def read_node(self, node_id: str) -> Node | None:
        """
        Read a node from shared memory.

        Args:
            node_id: The node ID

        Returns:
            The node, or None if not found
        """
        return self.node_manager.get_node(node_id)

    def read_edge(self, source_id: str, target_id: str) -> Edge | None:
        """
        Read an edge from shared memory.

        Args:
            source_id: Source node ID
            target_id: Target node ID

        Returns:
            The edge, or None if not found
        """
        return self.edge_manager.get_edge(source_id, target_id)

    def write_edge(
        self,
        source_id: str,
        target_id: str,
        weight: float,
        agent_id: str,
    ) -> Edge:
        """
        Write an edge to shared memory.

        Creates or updates the edge, attributing the write to the agent.

        Args:
            source_id: Source node ID
            target_id: Target node ID
            weight: Edge weight
            agent_id: ID of the writing agent

        Returns:
            The created/updated edge
        """
        with self._lock:
            existing = self.edge_manager.get_edge(source_id, target_id)

            if existing:
                # Update existing edge
                existing.weight = weight
                existing.last_used = datetime.utcnow()
                existing.use_count += 1
                self.edge_manager.substrate.update_edge(existing)
                edge = existing
            else:
                # Create new edge
                edge = self.edge_manager.create_edge(source_id, target_id, weight)

            # Log activity
            self._log_activity(
                agent_id=agent_id,
                action="write_edge",
                details={
                    "source": source_id,
                    "target": target_id,
                    "weight": weight,
                    "was_update": existing is not None,
                },
            )

            return edge

    def strengthen_edge(
        self,
        source_id: str,
        target_id: str,
        amount: float,
        agent_id: str,
    ) -> Edge:
        """
        Strengthen an edge in shared memory.

        Args:
            source_id: Source node ID
            target_id: Target node ID
            amount: Amount to strengthen
            agent_id: ID of the writing agent

        Returns:
            The strengthened edge
        """
        with self._lock:
            edge = self.edge_manager.strengthen_edge(source_id, target_id, amount)

            self._log_activity(
                agent_id=agent_id,
                action="strengthen_edge",
                details={
                    "source": source_id,
                    "target": target_id,
                    "amount": amount,
                    "new_weight": edge.weight,
                },
            )

            return edge

    def activate_node(
        self,
        node_id: str,
        strength: float,
        agent_id: str,
    ) -> Node | None:
        """
        Activate a node in shared memory.

        Args:
            node_id: The node ID
            strength: Activation strength
            agent_id: ID of the activating agent

        Returns:
            The activated node, or None if not found
        """
        with self._lock:
            node = self.node_manager.activate_node(node_id, strength)

            if node:
                self._log_activity(
                    agent_id=agent_id,
                    action="activate_node",
                    details={
                        "node_id": node_id,
                        "strength": strength,
                        "new_activation": node.activation,
                    },
                )

            return node

    def _log_activity(self, agent_id: str, action: str, details: dict) -> None:
        """Log an activity."""
        entry = {
            "timestamp": datetime.utcnow().isoformat(),
            "agent_id": agent_id,
            "action": action,
            "details": details,
        }
        self._activity_log.append(entry)

        # Trim log if too large
        if len(self._activity_log) > self._max_log_size:
            self._activity_log = self._activity_log[-self._max_log_size // 2:]

    def get_activity_log(
        self,
        agent_id: str | None = None,
        action: str | None = None,
        limit: int = 100,
    ) -> list[dict]:
        """
        Get activity log entries.

        Args:
            agent_id: Filter by agent ID
            action: Filter by action type
            limit: Maximum entries to return

        Returns:
            List of activity log entries
        """
        entries = self._activity_log

        if agent_id:
            entries = [e for e in entries if e["agent_id"] == agent_id]

        if action:
            entries = [e for e in entries if e["action"] == action]

        return entries[-limit:]

    def get_agent_contributions(self, agent_id: str) -> dict:
        """
        Get summary of an agent's contributions.

        Args:
            agent_id: The agent ID

        Returns:
            Dict with contribution summary
        """
        entries = [e for e in self._activity_log if e["agent_id"] == agent_id]

        action_counts: dict[str, int] = {}
        for entry in entries:
            action = entry["action"]
            action_counts[action] = action_counts.get(action, 0) + 1

        return {
            "agent_id": agent_id,
            "total_activities": len(entries),
            "action_counts": action_counts,
        }

    def get_shared_state(self) -> dict:
        """
        Get a summary of the shared memory state.

        Returns:
            Dict with shared state summary
        """
        return {
            "node_count": self.substrate.node_count(),
            "edge_count": self.substrate.edge_count(),
            "mean_edge_weight": self.edge_manager.mean_weight(),
            "activity_log_size": len(self._activity_log),
        }

    def clear_activity_log(self) -> None:
        """Clear the activity log."""
        self._activity_log.clear()


class MemoryTransaction:
    """
    Transaction wrapper for atomic memory operations.

    Provides rollback capability for failed operations.
    """

    def __init__(self, shared_memory: SharedMemory, agent_id: str):
        """
        Initialize a memory transaction.

        Args:
            shared_memory: The SharedMemory instance
            agent_id: The agent performing the transaction
        """
        self.memory = shared_memory
        self.agent_id = agent_id
        self._operations: list[dict] = []
        self._committed = False

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        if exc_type is not None and not self._committed:
            self.rollback()
        return False

    def write_edge(self, source_id: str, target_id: str, weight: float) -> Edge:
        """Write an edge in this transaction."""
        # Record original state for rollback
        original = self.memory.read_edge(source_id, target_id)
        self._operations.append({
            "type": "edge",
            "source": source_id,
            "target": target_id,
            "original_weight": original.weight if original else None,
            "original_existed": original is not None,
        })

        return self.memory.write_edge(source_id, target_id, weight, self.agent_id)

    def commit(self) -> None:
        """Commit the transaction."""
        self._committed = True
        self._operations.clear()

    def rollback(self) -> None:
        """Rollback all operations in this transaction."""
        for op in reversed(self._operations):
            if op["type"] == "edge":
                if op["original_existed"]:
                    # Restore original weight
                    self.memory.write_edge(
                        op["source"],
                        op["target"],
                        op["original_weight"],
                        self.agent_id,
                    )
                else:
                    # Delete the created edge
                    self.memory.edge_manager.delete_edge(op["source"], op["target"])

        self._operations.clear()
        logger.debug(f"Transaction rolled back for agent {self.agent_id}")
