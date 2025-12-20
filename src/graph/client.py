"""FalkorDB connection client."""
from falkordb import FalkorDB
from typing import Any, Optional
import yaml
import os

class GraphClient:
    """Client for FalkorDB graph database."""

    def __init__(self, config_path: str = None):
        # Try environment variables first (for Railway/Docker deployment)
        host = os.getenv("FALKORDB_HOST") or os.getenv("REDIS_HOST")
        port = os.getenv("FALKORDB_PORT") or os.getenv("REDIS_PORT")
        graph_name = os.getenv("FALKORDB_GRAPH", "soul_kiln")

        if host and port:
            # Use environment variables
            self.db = FalkorDB(host=host, port=int(port))
            self.graph = self.db.select_graph(graph_name)
        else:
            # Fall back to config file
            if config_path is None:
                # Look for config.yml relative to this file or in working directory
                possible_paths = [
                    "config.yml",
                    os.path.join(os.path.dirname(__file__), "..", "..", "config.yml"),
                ]
                for path in possible_paths:
                    if os.path.exists(path):
                        config_path = path
                        break
                else:
                    config_path = "config.yml"

            with open(config_path) as f:
                config = yaml.safe_load(f)

            self.db = FalkorDB(
                host=config["graph"]["host"],
                port=config["graph"]["port"]
            )
            self.graph = self.db.select_graph(config["graph"]["name"])

    def query(self, cypher: str, params: dict = None) -> list:
        """Execute Cypher query, return results."""
        result = self.graph.query(cypher, params or {})
        return result.result_set

    def execute(self, cypher: str, params: dict = None) -> None:
        """Execute Cypher mutation."""
        self.graph.query(cypher, params or {})

    def node_exists(self, node_id: str) -> bool:
        """Check if a node with given id exists."""
        result = self.query(
            "MATCH (n {id: $id}) RETURN n LIMIT 1",
            {"id": node_id}
        )
        return len(result) > 0


# Singleton client instance
_client: Optional[GraphClient] = None


def get_client(config_path: str = None) -> GraphClient:
    """Get or create singleton GraphClient instance."""
    global _client
    if _client is None:
        _client = GraphClient(config_path)
    return _client


def reset_client():
    """Reset the singleton client (for testing)."""
    global _client
    _client = None
