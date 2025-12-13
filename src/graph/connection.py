"""
FalkorDB Connection Management.
"""

import os
from typing import Optional
from falkordb import FalkorDB

# Global connection instance
_connection: Optional["GraphConnection"] = None


class GraphConnection:
    """Manages connection to FalkorDB."""

    def __init__(
        self,
        host: str = "localhost",
        port: int = 6379,
        graph_name: str = "soul_kiln",
    ):
        self.host = host
        self.port = port
        self.graph_name = graph_name
        self._db: Optional[FalkorDB] = None
        self._graph = None

    def connect(self):
        """Establish connection to FalkorDB."""
        if self._db is None:
            self._db = FalkorDB(host=self.host, port=self.port)
            self._graph = self._db.select_graph(self.graph_name)
        return self._graph

    @property
    def graph(self):
        """Get the graph instance, connecting if needed."""
        if self._graph is None:
            self.connect()
        return self._graph

    def query(self, cypher: str, params: dict = None):
        """Execute a Cypher query."""
        return self.graph.query(cypher, params or {})

    def close(self):
        """Close the connection."""
        if self._db:
            self._db = None
            self._graph = None


def get_graph(
    host: str = None,
    port: int = None,
    graph_name: str = None,
) -> GraphConnection:
    """Get or create the global graph connection."""
    global _connection

    if _connection is None:
        _connection = GraphConnection(
            host=host or os.getenv("FALKORDB_HOST", "localhost"),
            port=port or int(os.getenv("FALKORDB_PORT", "6379")),
            graph_name=graph_name or os.getenv("FALKORDB_GRAPH", "soul_kiln"),
        )

    return _connection
