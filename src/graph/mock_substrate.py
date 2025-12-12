"""
In-memory mock graph substrate for testing without FalkorDB.

Provides the same interface as GraphSubstrate but stores everything in memory.
"""

import logging
from datetime import datetime

from src.models import Edge, EdgeDirection, Node, NodeType

logger = logging.getLogger(__name__)


class MockGraphSubstrate:
    """
    In-memory mock implementation of GraphSubstrate.

    Use this for testing when FalkorDB is not available.
    """

    def __init__(self, host: str = "localhost", port: int = 6379, graph_name: str = "virtue_basin"):
        """Initialize the mock substrate."""
        self.host = host
        self.port = port
        self.graph_name = graph_name
        self._nodes: dict[str, Node] = {}
        self._edges: dict[str, Edge] = {}  # key: "source->target"
        self._connected = False

    def connect(self) -> None:
        """Mock connect."""
        self._connected = True
        logger.info(f"MockGraphSubstrate connected (in-memory mode)")

    def disconnect(self) -> None:
        """Mock disconnect."""
        self._connected = False
        logger.info("MockGraphSubstrate disconnected")

    @property
    def is_connected(self) -> bool:
        return self._connected

    def _ensure_connected(self) -> None:
        if not self._connected:
            raise RuntimeError("Not connected. Call connect() first.")

    # Node Operations

    def create_node(self, node: Node) -> Node:
        self._ensure_connected()
        self._nodes[node.id] = node
        return node

    def get_node(self, node_id: str) -> Node | None:
        self._ensure_connected()
        return self._nodes.get(node_id)

    def update_node(self, node: Node) -> Node:
        self._ensure_connected()
        if node.id in self._nodes:
            self._nodes[node.id] = node
        return node

    def delete_node(self, node_id: str) -> bool:
        self._ensure_connected()
        node = self._nodes.get(node_id)
        if node and node.is_virtue_anchor():
            logger.warning(f"Cannot delete virtue anchor node: {node_id}")
            return False
        if node_id in self._nodes:
            del self._nodes[node_id]
            # Also delete related edges
            keys_to_delete = [k for k in self._edges if node_id in k]
            for k in keys_to_delete:
                del self._edges[k]
            return True
        return False

    def get_all_nodes(self, node_type: NodeType | None = None) -> list[Node]:
        self._ensure_connected()
        nodes = list(self._nodes.values())
        if node_type:
            nodes = [n for n in nodes if n.type == node_type]
        return nodes

    def get_virtue_anchors(self) -> list[Node]:
        return self.get_all_nodes(NodeType.VIRTUE_ANCHOR)

    # Edge Operations

    def _edge_key(self, source_id: str, target_id: str) -> str:
        return f"{source_id}->{target_id}"

    def create_edge(self, edge: Edge) -> Edge:
        self._ensure_connected()
        key = self._edge_key(edge.source_id, edge.target_id)
        self._edges[key] = edge
        return edge

    def get_edge(self, source_id: str, target_id: str) -> Edge | None:
        self._ensure_connected()
        key = self._edge_key(source_id, target_id)
        return self._edges.get(key)

    def update_edge(self, edge: Edge) -> Edge:
        self._ensure_connected()
        key = self._edge_key(edge.source_id, edge.target_id)
        if key in self._edges:
            self._edges[key] = edge
        return edge

    def delete_edge(self, source_id: str, target_id: str) -> bool:
        self._ensure_connected()
        key = self._edge_key(source_id, target_id)
        if key in self._edges:
            del self._edges[key]
            return True
        return False

    def get_incoming_edges(self, node_id: str) -> list[Edge]:
        self._ensure_connected()
        return [e for e in self._edges.values() if e.target_id == node_id]

    def get_outgoing_edges(self, node_id: str) -> list[Edge]:
        self._ensure_connected()
        return [e for e in self._edges.values() if e.source_id == node_id]

    def get_node_degree(self, node_id: str) -> int:
        incoming = len(self.get_incoming_edges(node_id))
        outgoing = len(self.get_outgoing_edges(node_id))
        return incoming + outgoing

    def get_all_edges(self) -> list[Edge]:
        self._ensure_connected()
        return list(self._edges.values())

    # Utility Operations

    def clear_graph(self) -> None:
        self._ensure_connected()
        self._nodes.clear()
        self._edges.clear()
        logger.info("Cleared mock graph")

    def node_count(self) -> int:
        self._ensure_connected()
        return len(self._nodes)

    def edge_count(self) -> int:
        self._ensure_connected()
        return len(self._edges)
