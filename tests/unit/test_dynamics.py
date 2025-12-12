"""Tests for dynamics functions."""

import pytest
import math

from src.dynamics.activation import tanh, sigmoid


class TestActivationFunctions:
    """Tests for activation functions."""

    def test_tanh_bounds(self):
        """Test tanh is bounded between -1 and 1."""
        assert -1 <= tanh(-100) <= 1
        assert -1 <= tanh(0) <= 1
        assert -1 <= tanh(100) <= 1

    def test_tanh_zero(self):
        """Test tanh(0) = 0."""
        assert abs(tanh(0)) < 1e-10

    def test_tanh_symmetry(self):
        """Test tanh is odd function."""
        for x in [0.5, 1.0, 2.0, 5.0]:
            assert abs(tanh(-x) + tanh(x)) < 1e-10

    def test_sigmoid_bounds(self):
        """Test sigmoid is bounded between 0 and 1."""
        assert 0 <= sigmoid(-100) <= 1
        assert 0 < sigmoid(0) < 1
        assert 0 <= sigmoid(100) <= 1

    def test_sigmoid_at_zero(self):
        """Test sigmoid(0) = 0.5."""
        assert abs(sigmoid(0) - 0.5) < 1e-10

    def test_sigmoid_symmetry(self):
        """Test sigmoid symmetry around 0.5."""
        for x in [0.5, 1.0, 2.0, 5.0]:
            assert abs(sigmoid(x) + sigmoid(-x) - 1.0) < 1e-10


class TestDynamicsConstants:
    """Tests for dynamics constants."""

    def test_constants_in_valid_ranges(self):
        """Test constants are in valid ranges."""
        from src.constants import (
            LEARNING_RATE,
            DECAY_CONSTANT,
            PERTURBATION_STRENGTH,
            ACTIVATION_THRESHOLD,
            CAPTURE_THRESHOLD,
        )

        assert 0 < LEARNING_RATE < 1
        assert 0.9 < DECAY_CONSTANT < 1.0
        assert 0 < PERTURBATION_STRENGTH <= 1
        assert 0 < ACTIVATION_THRESHOLD < 1
        assert 0 < CAPTURE_THRESHOLD < 1
        assert ACTIVATION_THRESHOLD < CAPTURE_THRESHOLD
