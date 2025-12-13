"""FalkorDB connection client with mock fallback."""
from typing import Any, Optional
import yaml
import os

# Try to import FalkorDB, fall back to mock if unavailable
try:
    from falkordb import FalkorDB
    FALKORDB_AVAILABLE = True
except ImportError:
    FALKORDB_AVAILABLE = False

from .mock_client import MockGraphClient, get_mock_client

# Track if we're using mock mode
_using_mock = False


class GraphClient:
    """Client for FalkorDB graph database with mock fallback."""

    def __init__(self, config_path: str = None):
        global _using_mock

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

        self._mock = None
        self.graph = None
        self.db = None

        if FALKORDB_AVAILABLE:
            try:
                self.db = FalkorDB(
                    host=config["graph"]["host"],
                    port=config["graph"]["port"]
                )
                self.graph = self.db.select_graph(config["graph"]["name"])
                # Test the connection with a simple query
                self.graph.query("RETURN 1")
                _using_mock = False
            except Exception as e:
                print(f"[WARN] FalkorDB not available ({e}), using mock graph client")
                self._mock = get_mock_client(config["graph"]["name"])
                _using_mock = True
        else:
            print("[WARN] FalkorDB package not installed, using mock graph client")
            self._mock = get_mock_client(config["graph"]["name"])
            _using_mock = True

    def query(self, cypher: str, params: dict = None) -> list:
        """Execute Cypher query, return results."""
        if self._mock:
            return self._mock.query(cypher, params)

        result = self.graph.query(cypher, params or {})
        return result.result_set

    def execute(self, cypher: str, params: dict = None) -> None:
        """Execute Cypher mutation."""
        if self._mock:
            self._mock.execute(cypher, params)
            return

        self.graph.query(cypher, params or {})

    def node_exists(self, node_id: str) -> bool:
        """Check if a node with given id exists."""
        if self._mock:
            return self._mock.node_exists(node_id)

        result = self.query(
            "MATCH (n {id: $id}) RETURN n LIMIT 1",
            {"id": node_id}
        )
        return len(result) > 0

    @property
    def is_mock(self) -> bool:
        """Check if using mock client."""
        return self._mock is not None


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


def is_using_mock() -> bool:
    """Check if the current client is using mock mode."""
    return _using_mock
