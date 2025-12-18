"""
Unified Graph Store Interface.

Provides a consistent interface for graph operations regardless of the
underlying client implementation (GraphClient singleton vs GraphSubstrate).

This abstraction allows:
- Consistent query/execute interface
- Proper connection lifecycle management
- Easy testing with mock implementations
- Type safety through Protocol
"""

import logging
from abc import ABC, abstractmethod
from typing import Any, Protocol, runtime_checkable

logger = logging.getLogger(__name__)


@runtime_checkable
class GraphStore(Protocol):
    """
    Protocol for graph store implementations.

    Any class implementing these methods can be used as a GraphStore,
    enabling polymorphism between GraphClient and GraphSubstrate.
    """

    def query(self, cypher: str, params: dict | None = None) -> list:
        """
        Execute a Cypher query and return results.

        Args:
            cypher: Cypher query string
            params: Optional query parameters

        Returns:
            List of result rows
        """
        ...

    def execute(self, cypher: str, params: dict | None = None) -> None:
        """
        Execute a Cypher mutation (no return value expected).

        Args:
            cypher: Cypher query string
            params: Optional query parameters
        """
        ...


class MockGraphStore:
    """
    Mock implementation for testing.

    Does not connect to any database - returns empty results
    and tracks queries for assertion.
    """

    def __init__(self):
        self.queries: list[tuple[str, dict | None]] = []
        self.executions: list[tuple[str, dict | None]] = []
        self._mock_results: dict[str, list] = {}

    def query(self, cypher: str, params: dict | None = None) -> list:
        """Record query and return mock result."""
        self.queries.append((cypher, params))
        # Return mock result if configured, else empty list
        for pattern, result in self._mock_results.items():
            if pattern in cypher:
                return result
        return []

    def execute(self, cypher: str, params: dict | None = None) -> None:
        """Record execution."""
        self.executions.append((cypher, params))

    def set_mock_result(self, pattern: str, result: list) -> None:
        """Configure a mock result for queries containing pattern."""
        self._mock_results[pattern] = result

    def clear(self) -> None:
        """Clear recorded queries and executions."""
        self.queries.clear()
        self.executions.clear()
        self._mock_results.clear()


def get_store(use_singleton: bool = True, config_path: str | None = None) -> GraphStore:
    """
    Get a GraphStore instance.

    Args:
        use_singleton: If True, use the singleton GraphClient.
                      If False, create a new GraphSubstrate instance.
        config_path: Optional path to config file.

    Returns:
        GraphStore implementation
    """
    if use_singleton:
        from .client import get_client
        return get_client(config_path)
    else:
        from .substrate import GraphSubstrate
        import yaml
        import os

        if config_path is None:
            config_path = "config.yml"
            if not os.path.exists(config_path):
                config_path = os.path.join(
                    os.path.dirname(__file__), "..", "..", "config.yml"
                )

        with open(config_path) as f:
            config = yaml.safe_load(f)

        substrate = GraphSubstrate(
            host=config["graph"]["host"],
            port=config["graph"]["port"],
            graph_name=config["graph"]["name"],
        )
        substrate.connect()
        return substrate


# Type alias for documentation
GraphStoreType = GraphStore
