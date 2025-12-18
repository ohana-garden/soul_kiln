"""
Tests for GraphStore interface.

Uses MockGraphStore to test without database connection.
"""

import pytest

from src.graph.store import GraphStore, MockGraphStore


class TestMockGraphStore:
    """Tests for MockGraphStore implementation."""

    def test_implements_protocol(self):
        """MockGraphStore satisfies GraphStore protocol."""
        mock = MockGraphStore()
        assert isinstance(mock, GraphStore)

    def test_query_returns_empty_by_default(self):
        """Query returns empty list by default."""
        mock = MockGraphStore()
        result = mock.query("MATCH (n) RETURN n")
        assert result == []

    def test_query_records_call(self):
        """Query calls are recorded."""
        mock = MockGraphStore()
        mock.query("MATCH (n:Test) RETURN n", {"param": "value"})

        assert len(mock.queries) == 1
        assert mock.queries[0] == ("MATCH (n:Test) RETURN n", {"param": "value"})

    def test_execute_records_call(self):
        """Execute calls are recorded."""
        mock = MockGraphStore()
        mock.execute("CREATE (n:Test)", {"param": "value"})

        assert len(mock.executions) == 1
        assert mock.executions[0] == ("CREATE (n:Test)", {"param": "value"})

    def test_mock_result(self):
        """Can configure mock results."""
        mock = MockGraphStore()
        mock.set_mock_result("VirtueAnchor", [["V01", "Trustworthiness"]])

        result = mock.query("MATCH (v:VirtueAnchor) RETURN v.id, v.name")
        assert result == [["V01", "Trustworthiness"]]

    def test_mock_result_pattern_matching(self):
        """Mock results match on pattern."""
        mock = MockGraphStore()
        mock.set_mock_result("Agent", [["agent_001"]])
        mock.set_mock_result("Virtue", [["V01"]])

        # Query for Agent matches Agent pattern
        result1 = mock.query("MATCH (a:Agent) RETURN a.id")
        assert result1 == [["agent_001"]]

        # Query for Virtue matches Virtue pattern
        result2 = mock.query("MATCH (v:VirtueAnchor) RETURN v.id")
        assert result2 == [["V01"]]

    def test_clear_resets_state(self):
        """Clear removes all recorded calls and mock results."""
        mock = MockGraphStore()
        mock.query("SELECT 1")
        mock.execute("CREATE ...")
        mock.set_mock_result("Test", [[1]])

        mock.clear()

        assert mock.queries == []
        assert mock.executions == []
        assert mock.query("MATCH (n:Test) RETURN n") == []

    def test_multiple_queries(self):
        """Multiple queries are all recorded."""
        mock = MockGraphStore()
        mock.query("Q1")
        mock.query("Q2", {"p": 1})
        mock.query("Q3")

        assert len(mock.queries) == 3
        assert mock.queries[1] == ("Q2", {"p": 1})


class TestGraphStoreProtocol:
    """Tests for GraphStore protocol compliance."""

    def test_protocol_is_runtime_checkable(self):
        """GraphStore can be used with isinstance."""
        mock = MockGraphStore()
        assert isinstance(mock, GraphStore)

    def test_custom_implementation(self):
        """Custom class implementing methods satisfies protocol."""

        class CustomStore:
            def query(self, cypher: str, params: dict | None = None) -> list:
                return [["custom"]]

            def execute(self, cypher: str, params: dict | None = None) -> None:
                pass

        custom = CustomStore()
        assert isinstance(custom, GraphStore)
        assert custom.query("...") == [["custom"]]
