"""FalkorDB connection client with mock fallback."""
from typing import Any, Optional
import logging

# Try to import FalkorDB, fall back to mock if unavailable
try:
    from falkordb import FalkorDB
    FALKORDB_AVAILABLE = True
except ImportError:
    FALKORDB_AVAILABLE = False

from .mock_client import MockGraphClient, get_mock_client
from src.settings import settings

logger = logging.getLogger(__name__)

# Track if we're using mock mode
_using_mock = False


class GraphClient:
    """Client for FalkorDB graph database with mock fallback."""

    def __init__(self):
        global _using_mock

        self._mock = None
        self.graph = None
        self.db = None

        db_settings = settings.database

        if FALKORDB_AVAILABLE:
            try:
                self.db = FalkorDB(
                    host=db_settings.host,
                    port=db_settings.port
                )
                self.graph = self.db.select_graph(db_settings.graph)
                # Test the connection with a simple query
                self.graph.query("RETURN 1")
                _using_mock = False
                logger.info(f"Connected to FalkorDB at {db_settings.host}:{db_settings.port}")
            except Exception as e:
                logger.warning(f"FalkorDB not available ({e}), using mock graph client")
                self._mock = get_mock_client(db_settings.graph)
                _using_mock = True
        else:
            logger.warning("FalkorDB package not installed, using mock graph client")
            self._mock = get_mock_client(db_settings.graph)
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


def get_client() -> GraphClient:
    """Get or create singleton GraphClient instance."""
    global _client
    if _client is None:
        _client = GraphClient()
    return _client


def reset_client():
    """Reset the singleton client (for testing)."""
    global _client
    _client = None


def is_using_mock() -> bool:
    """Check if the current client is using mock mode."""
    return _using_mock
