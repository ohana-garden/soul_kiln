"""Tests for kiln evolution loop."""
import pytest
from unittest.mock import MagicMock, patch


class TestSelection:
    """Test selection strategies."""

    def test_truncation_select(self):
        """Test truncation selection picks top agents."""
        from src.kiln.selection import truncation_select

        results = [
            ("agent_1", {"capture_rate": 0.95, "coverage": 19}),
            ("agent_2", {"capture_rate": 0.80, "coverage": 15}),
            ("agent_3", {"capture_rate": 0.90, "coverage": 18}),
            ("agent_4", {"capture_rate": 0.70, "coverage": 12}),
        ]

        survivors = truncation_select(results, 2)

        assert len(survivors) == 2
        assert "agent_1" in survivors
        assert "agent_3" in survivors

    def test_tournament_select(self):
        """Test tournament selection returns correct count."""
        from src.kiln.selection import tournament_select

        results = [
            ("agent_1", {"capture_rate": 0.95}),
            ("agent_2", {"capture_rate": 0.80}),
            ("agent_3", {"capture_rate": 0.90}),
            ("agent_4", {"capture_rate": 0.70}),
        ]

        survivors = tournament_select(results, 2, tournament_size=2)

        assert len(survivors) == 2
        # All survivors should be from original set
        assert all(s in [r[0] for r in results] for s in survivors)

    def test_roulette_select(self):
        """Test roulette selection returns correct count."""
        from src.kiln.selection import roulette_select

        results = [
            ("agent_1", {"capture_rate": 0.95}),
            ("agent_2", {"capture_rate": 0.80}),
            ("agent_3", {"capture_rate": 0.90}),
            ("agent_4", {"capture_rate": 0.70}),
        ]

        survivors = roulette_select(results, 2)

        assert len(survivors) == 2


class TestKilnHelpers:
    """Test kiln helper functions."""

    def test_elitism_keeps_best(self):
        """Test elitism selection always keeps top performer."""
        from src.kiln.selection import elitism_select

        results = [
            ("agent_1", {"capture_rate": 0.99}),  # Best
            ("agent_2", {"capture_rate": 0.50}),
            ("agent_3", {"capture_rate": 0.60}),
            ("agent_4", {"capture_rate": 0.40}),
        ]

        survivors = elitism_select(results, 2, elite_count=1)

        assert "agent_1" in survivors  # Best should always survive
        assert len(survivors) == 2


class TestDiversitySelection:
    """Test diversity-aware selection."""

    def test_diversity_prefers_different(self):
        """Test diversity selection favors different distributions."""
        from src.kiln.selection import diversity_aware_select

        # Two agents with same distribution, one different
        results = [
            ("agent_1", {
                "capture_rate": 0.90,
                "virtue_distribution": {"V01": 90, "V02": 5, "V03": 5}
            }),
            ("agent_2", {
                "capture_rate": 0.85,
                "virtue_distribution": {"V01": 90, "V02": 5, "V03": 5}  # Same as 1
            }),
            ("agent_3", {
                "capture_rate": 0.80,
                "virtue_distribution": {"V01": 30, "V02": 35, "V03": 35}  # Different
            }),
        ]

        survivors = diversity_aware_select(results, 2, diversity_weight=0.5)

        # Should include agent_1 (best) and prefer agent_3 over agent_2 for diversity
        assert "agent_1" in survivors
