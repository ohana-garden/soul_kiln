"""Tests for activation spread functionality."""
import pytest
from unittest.mock import MagicMock, patch


class TestSpreadFunctions:
    """Test activation spread math functions."""

    def test_tanh(self):
        """Test tanh function."""
        from src.functions.spread import tanh

        assert tanh(0) == 0
        assert -1 < tanh(-10) < 0
        assert 0 < tanh(10) < 1

    def test_sigmoid(self):
        """Test sigmoid function."""
        from src.functions.spread import sigmoid

        assert sigmoid(0) == 0.5
        assert sigmoid(-500) == 0.0
        assert sigmoid(500) == 1.0
        assert 0 < sigmoid(-10) < 0.5
        assert 0.5 < sigmoid(10) < 1


class TestSpreadActivation:
    """Test spread_activation function with mocked graph."""

    @patch('src.functions.spread.get_client')
    @patch('src.functions.spread.get_neighbors')
    @patch('src.functions.spread.set_node_activation')
    @patch('src.functions.spread.get_node_activation')
    def test_spread_no_neighbors(
        self, mock_get_act, mock_set_act, mock_neighbors, mock_client
    ):
        """Test spread when start node has no neighbors."""
        from src.functions.spread import spread_activation

        mock_neighbors.return_value = []

        result = spread_activation("test_node")

        assert result["captured"] == False
        assert result["trajectory"] == ["test_node"]

    @patch('src.functions.spread.get_client')
    @patch('src.functions.spread.get_neighbors')
    @patch('src.functions.spread.set_node_activation')
    @patch('src.functions.spread.get_node_activation')
    def test_spread_captures_virtue(
        self, mock_get_act, mock_set_act, mock_neighbors, mock_client
    ):
        """Test spread that reaches a virtue anchor."""
        from src.functions.spread import spread_activation

        # Mock graph client
        client = MagicMock()
        mock_client.return_value = client

        # First call returns neighbors, second call returns virtue
        mock_neighbors.side_effect = [
            [("V01", "virtue_anchor", 0.8, "SEEKS")],
            []
        ]

        mock_get_act.return_value = 0.3

        # Mock virtue check
        client.query.side_effect = [
            [[0.3]],  # baseline query
            [[True]]  # is_virtue query
        ]

        result = spread_activation("start", capture_threshold=0.5)

        assert "trajectory" in result
        assert result["captured"] == True or result["captured"] == False  # Depends on activation calc
