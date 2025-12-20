"""FalkorDB connection client."""
from falkordb import FalkorDB
from typing import Any, Optional
import yaml
import os

class GraphClient:
    """Client for FalkorDB graph database."""

    def __init__(self, config_path: str = None):
        # Check environment variables first (for Railway/cloud deployment)
        env_host = os.environ.get("FALKORDB_HOST")
        env_port = os.environ.get("FALKORDB_PORT")

        # Default values
        host = env_host or "localhost"
        port = int(env_port) if env_port else 6379
        graph_name = os.environ.get("FALKORDB_GRAPH", "soul_kiln")

        # Fall back to config.yml if no env vars and config exists
        if not env_host:
            if config_path is None:
                possible_paths = [
                    "config.yml",
                    os.path.join(os.path.dirname(__file__), "..", "..", "config.yml"),
                ]
                for path in possible_paths:
                    if os.path.exists(path):
                        config_path = path
                        break

            if config_path and os.path.exists(config_path):
                with open(config_path) as f:
                    config = yaml.safe_load(f)
                host = config.get("graph", {}).get("host", host)
                port = config.get("graph", {}).get("port", port)
                graph_name = config.get("graph", {}).get("name", graph_name)

        self.db = FalkorDB(host=host, port=port)
        self.graph = self.db.select_graph(graph_name)

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
