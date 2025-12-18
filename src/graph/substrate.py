"""
Graph substrate implementation using FalkorDB.

FalkorDB provides the persistent, temporal knowledge graph that serves as
the cognitive space for virtue basin simulation.
"""

import json
import logging
from datetime import datetime
from typing import Any

from falkordb import FalkorDB

from src.constants import (
    EDGE_REMOVAL_THRESHOLD,
    MAX_EDGE_WEIGHT,
    MIN_EDGE_WEIGHT,
)
from src.graph.safe_parse import safe_parse_dict, serialize_for_storage
from src.models import Edge, Node, NodeType

logger = logging.getLogger(__name__)


class GraphSubstrate:
    """
    FalkorDB-backed graph substrate for the virtue basin simulator.

    Provides CRUD operations for nodes and edges with support for
    temporal metadata and weighted connections.
    """

    def __init__(self, host: str = "localhost", port: int = 6379, graph_name: str = "virtue_basin"):
        """
        Initialize the graph substrate.

        Args:
            host: FalkorDB host address
            port: FalkorDB port
            graph_name: Name of the graph in FalkorDB
        """
        self.host = host
        self.port = port
        self.graph_name = graph_name
        self._db: FalkorDB | None = None
        self._graph = None

    def connect(self) -> None:
        """Connect to FalkorDB and initialize the graph."""
        try:
            self._db = FalkorDB(host=self.host, port=self.port)
            self._graph = self._db.select_graph(self.graph_name)
            logger.info(f"Connected to FalkorDB at {self.host}:{self.port}, graph: {self.graph_name}")
            self._create_indexes()
        except Exception as e:
            logger.error(f"Failed to connect to FalkorDB: {e}")
            raise

    def _create_indexes(self) -> None:
        """Create indexes for efficient queries."""
        try:
            # Create index on node ID
            self._graph.query("CREATE INDEX FOR (n:Node) ON (n.id)")
            # Create index on node type
            self._graph.query("CREATE INDEX FOR (n:Node) ON (n.type)")
            logger.info("Created graph indexes")
        except Exception:
            # Indexes may already exist
            pass

    def disconnect(self) -> None:
        """Disconnect from FalkorDB."""
        self._graph = None
        self._db = None
        logger.info("Disconnected from FalkorDB")

    @property
    def is_connected(self) -> bool:
        """Check if connected to the database."""
        return self._graph is not None

    def _ensure_connected(self) -> None:
        """Ensure we're connected to the database."""
        if not self.is_connected:
            raise RuntimeError("Not connected to FalkorDB. Call connect() first.")

    # Node Operations

    def create_node(self, node: Node) -> Node:
        """
        Create a new node in the graph.

        Args:
            node: The node to create

        Returns:
            The created node
        """
        self._ensure_connected()
        query = """
        CREATE (n:Node {
            id: $id,
            type: $type,
            activation: $activation,
            baseline: $baseline,
            created_at: $created_at,
            last_activated: $last_activated,
            metadata: $metadata
        })
        RETURN n
        """
        params = {
            "id": node.id,
            "type": node.type.value,
            "activation": node.activation,
            "baseline": node.baseline,
            "created_at": node.created_at.isoformat(),
            "last_activated": node.last_activated.isoformat(),
            "metadata": serialize_for_storage(node.metadata),
        }
        self._graph.query(query, params)
        logger.debug(f"Created node: {node.id}")
        return node

    def get_node(self, node_id: str) -> Node | None:
        """
        Get a node by ID.

        Args:
            node_id: The node ID

        Returns:
            The node if found, None otherwise
        """
        self._ensure_connected()
        query = "MATCH (n:Node {id: $id}) RETURN n"
        result = self._graph.query(query, {"id": node_id})
        if result.result_set:
            row = result.result_set[0]
            props = row[0].properties
            return self._props_to_node(props)
        return None

    def update_node(self, node: Node) -> Node:
        """
        Update an existing node.

        Args:
            node: The node with updated properties

        Returns:
            The updated node
        """
        self._ensure_connected()
        query = """
        MATCH (n:Node {id: $id})
        SET n.activation = $activation,
            n.last_activated = $last_activated,
            n.metadata = $metadata
        RETURN n
        """
        params = {
            "id": node.id,
            "activation": node.activation,
            "last_activated": node.last_activated.isoformat(),
            "metadata": serialize_for_storage(node.metadata),
        }
        self._graph.query(query, params)
        logger.debug(f"Updated node: {node.id}")
        return node

    def delete_node(self, node_id: str) -> bool:
        """
        Delete a node by ID.

        Note: Virtue anchor nodes cannot be deleted.

        Args:
            node_id: The node ID

        Returns:
            True if deleted, False otherwise
        """
        self._ensure_connected()
        # Check if it's a virtue anchor
        node = self.get_node(node_id)
        if node and node.is_virtue_anchor():
            logger.warning(f"Cannot delete virtue anchor node: {node_id}")
            return False

        query = "MATCH (n:Node {id: $id}) DETACH DELETE n"
        self._graph.query(query, {"id": node_id})
        logger.debug(f"Deleted node: {node_id}")
        return True

    def get_all_nodes(self, node_type: NodeType | None = None) -> list[Node]:
        """
        Get all nodes, optionally filtered by type.

        Args:
            node_type: Optional type filter

        Returns:
            List of nodes
        """
        self._ensure_connected()
        if node_type:
            query = "MATCH (n:Node {type: $type}) RETURN n"
            result = self._graph.query(query, {"type": node_type.value})
        else:
            query = "MATCH (n:Node) RETURN n"
            result = self._graph.query(query)

        nodes = []
        for row in result.result_set:
            props = row[0].properties
            nodes.append(self._props_to_node(props))
        return nodes

    def get_virtue_anchors(self) -> list[Node]:
        """Get all virtue anchor nodes."""
        return self.get_all_nodes(NodeType.VIRTUE_ANCHOR)

    def _props_to_node(self, props: dict) -> Node:
        """Convert FalkorDB properties to a Node object."""
        return Node(
            id=props["id"],
            type=NodeType(props["type"]),
            activation=props["activation"],
            baseline=props["baseline"],
            created_at=datetime.fromisoformat(props["created_at"]),
            last_activated=datetime.fromisoformat(props["last_activated"]),
            metadata=safe_parse_dict(props.get("metadata", "{}")),
        )

    # Edge Operations

    def create_edge(self, edge: Edge) -> Edge:
        """
        Create a new edge in the graph.

        Args:
            edge: The edge to create

        Returns:
            The created edge
        """
        self._ensure_connected()
        query = """
        MATCH (a:Node {id: $source_id}), (b:Node {id: $target_id})
        CREATE (a)-[r:CONNECTS {
            weight: $weight,
            direction: $direction,
            created_at: $created_at,
            last_used: $last_used,
            use_count: $use_count
        }]->(b)
        RETURN r
        """
        params = {
            "source_id": edge.source_id,
            "target_id": edge.target_id,
            "weight": edge.weight,
            "direction": edge.direction.value,
            "created_at": edge.created_at.isoformat(),
            "last_used": edge.last_used.isoformat(),
            "use_count": edge.use_count,
        }
        self._graph.query(query, params)
        logger.debug(f"Created edge: {edge.source_id} -> {edge.target_id}")
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
        self._ensure_connected()
        query = """
        MATCH (a:Node {id: $source_id})-[r:CONNECTS]->(b:Node {id: $target_id})
        RETURN r
        """
        result = self._graph.query(query, {"source_id": source_id, "target_id": target_id})
        if result.result_set:
            props = result.result_set[0][0].properties
            return self._props_to_edge(source_id, target_id, props)
        return None

    def update_edge(self, edge: Edge) -> Edge:
        """
        Update an existing edge.

        Args:
            edge: The edge with updated properties

        Returns:
            The updated edge
        """
        self._ensure_connected()
        query = """
        MATCH (a:Node {id: $source_id})-[r:CONNECTS]->(b:Node {id: $target_id})
        SET r.weight = $weight,
            r.last_used = $last_used,
            r.use_count = $use_count
        RETURN r
        """
        params = {
            "source_id": edge.source_id,
            "target_id": edge.target_id,
            "weight": max(MIN_EDGE_WEIGHT, min(MAX_EDGE_WEIGHT, edge.weight)),
            "last_used": edge.last_used.isoformat(),
            "use_count": edge.use_count,
        }
        self._graph.query(query, params)
        logger.debug(f"Updated edge: {edge.source_id} -> {edge.target_id}")
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
        self._ensure_connected()
        query = """
        MATCH (a:Node {id: $source_id})-[r:CONNECTS]->(b:Node {id: $target_id})
        DELETE r
        """
        self._graph.query(query, {"source_id": source_id, "target_id": target_id})
        logger.debug(f"Deleted edge: {source_id} -> {target_id}")
        return True

    def get_incoming_edges(self, node_id: str) -> list[Edge]:
        """
        Get all edges incoming to a node.

        Args:
            node_id: The target node ID

        Returns:
            List of incoming edges
        """
        self._ensure_connected()
        query = """
        MATCH (a:Node)-[r:CONNECTS]->(b:Node {id: $id})
        RETURN a.id as source_id, r
        """
        result = self._graph.query(query, {"id": node_id})
        edges = []
        for row in result.result_set:
            source_id = row[0]
            props = row[1].properties
            edges.append(self._props_to_edge(source_id, node_id, props))
        return edges

    def get_outgoing_edges(self, node_id: str) -> list[Edge]:
        """
        Get all edges outgoing from a node.

        Args:
            node_id: The source node ID

        Returns:
            List of outgoing edges
        """
        self._ensure_connected()
        query = """
        MATCH (a:Node {id: $id})-[r:CONNECTS]->(b:Node)
        RETURN b.id as target_id, r
        """
        result = self._graph.query(query, {"id": node_id})
        edges = []
        for row in result.result_set:
            target_id = row[0]
            props = row[1].properties
            edges.append(self._props_to_edge(node_id, target_id, props))
        return edges

    def get_node_degree(self, node_id: str) -> int:
        """
        Get the degree (total edges) of a node.

        Args:
            node_id: The node ID

        Returns:
            Total number of edges (incoming + outgoing)
        """
        incoming = len(self.get_incoming_edges(node_id))
        outgoing = len(self.get_outgoing_edges(node_id))
        return incoming + outgoing

    def get_all_edges(self) -> list[Edge]:
        """Get all edges in the graph."""
        self._ensure_connected()
        query = """
        MATCH (a:Node)-[r:CONNECTS]->(b:Node)
        RETURN a.id as source_id, b.id as target_id, r
        """
        result = self._graph.query(query)
        edges = []
        for row in result.result_set:
            source_id = row[0]
            target_id = row[1]
            props = row[2].properties
            edges.append(self._props_to_edge(source_id, target_id, props))
        return edges

    def _props_to_edge(self, source_id: str, target_id: str, props: dict) -> Edge:
        """Convert FalkorDB properties to an Edge object."""
        from src.models import EdgeDirection

        return Edge(
            source_id=source_id,
            target_id=target_id,
            weight=props["weight"],
            direction=EdgeDirection(props["direction"]),
            created_at=datetime.fromisoformat(props["created_at"]),
            last_used=datetime.fromisoformat(props["last_used"]),
            use_count=props["use_count"],
        )

    # Utility Operations

    def clear_graph(self) -> None:
        """Clear all nodes and edges from the graph."""
        self._ensure_connected()
        self._graph.query("MATCH (n) DETACH DELETE n")
        logger.info("Cleared graph")

    def node_count(self) -> int:
        """Get the total number of nodes."""
        self._ensure_connected()
        result = self._graph.query("MATCH (n:Node) RETURN count(n)")
        return result.result_set[0][0] if result.result_set else 0

    def edge_count(self) -> int:
        """Get the total number of edges."""
        self._ensure_connected()
        result = self._graph.query("MATCH ()-[r:CONNECTS]->() RETURN count(r)")
        return result.result_set[0][0] if result.result_set else 0

    # GraphStore interface methods for compatibility

    def query(self, cypher: str, params: dict | None = None) -> list:
        """
        Execute a Cypher query and return results.

        Implements GraphStore protocol for compatibility with GraphClient.

        Args:
            cypher: Cypher query string
            params: Optional query parameters

        Returns:
            List of result rows
        """
        self._ensure_connected()
        result = self._graph.query(cypher, params or {})
        return result.result_set

    def execute(self, cypher: str, params: dict | None = None) -> None:
        """
        Execute a Cypher mutation.

        Implements GraphStore protocol for compatibility with GraphClient.

        Args:
            cypher: Cypher query string
            params: Optional query parameters
        """
        self._ensure_connected()
        self._graph.query(cypher, params or {})
