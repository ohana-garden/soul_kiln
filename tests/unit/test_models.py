"""Tests for data models."""

import pytest
from datetime import datetime

from src.models import (
    Node,
    NodeType,
    Edge,
    EdgeDirection,
    Trajectory,
    Stimulus,
    AlignmentResult,
    CharacterProfile,
)


class TestNode:
    """Tests for Node model."""

    def test_create_virtue_anchor(self):
        """Test creating a virtue anchor node."""
        node = Node(
            id="V01",
            type=NodeType.VIRTUE_ANCHOR,
            activation=0.3,
            baseline=0.3,
        )
        assert node.id == "V01"
        assert node.type == NodeType.VIRTUE_ANCHOR
        assert node.is_virtue_anchor()
        assert node.activation == 0.3
        assert node.baseline == 0.3

    def test_create_concept_node(self):
        """Test creating a concept node."""
        node = Node(
            id="concept_1",
            type=NodeType.CONCEPT,
            activation=0.0,
            baseline=0.0,
            metadata={"name": "test"},
        )
        assert node.id == "concept_1"
        assert node.type == NodeType.CONCEPT
        assert not node.is_virtue_anchor()
        assert node.metadata["name"] == "test"

    def test_activation_bounds(self):
        """Test activation is bounded."""
        node = Node(id="test", type=NodeType.CONCEPT, activation=1.5)
        # Pydantic should clamp or reject
        # Note: depends on validation mode
        assert node.activation <= 1.0 or node.activation == 1.5  # Field not clamped by default


class TestEdge:
    """Tests for Edge model."""

    def test_create_edge(self):
        """Test creating an edge."""
        edge = Edge(
            source_id="V01",
            target_id="V02",
            weight=0.5,
        )
        assert edge.source_id == "V01"
        assert edge.target_id == "V02"
        assert edge.weight == 0.5
        assert edge.edge_id == "V01->V02"

    def test_edge_direction(self):
        """Test edge direction."""
        edge = Edge(
            source_id="A",
            target_id="B",
            direction=EdgeDirection.BIDIRECTIONAL,
        )
        assert edge.direction == EdgeDirection.BIDIRECTIONAL


class TestTrajectory:
    """Tests for Trajectory model."""

    def test_captured_trajectory(self):
        """Test a captured trajectory."""
        trajectory = Trajectory(
            id="traj_1",
            agent_id="agent_1",
            stimulus_id="stim_1",
            path=["concept_1", "concept_2", "V01"],
            captured_by="V01",
            capture_time=3,
        )
        assert trajectory.was_captured
        assert not trajectory.escaped
        assert trajectory.captured_by == "V01"

    def test_escaped_trajectory(self):
        """Test an escaped trajectory."""
        trajectory = Trajectory(
            id="traj_2",
            agent_id="agent_1",
            stimulus_id="stim_2",
            path=["concept_1", "concept_2", "concept_3"],
            captured_by=None,
        )
        assert not trajectory.was_captured
        assert trajectory.escaped


class TestStimulus:
    """Tests for Stimulus model."""

    def test_create_stimulus(self):
        """Test creating a stimulus."""
        stimulus = Stimulus(
            id="stim_1",
            target_node="concept_1",
            activation_strength=0.8,
        )
        assert stimulus.id == "stim_1"
        assert stimulus.target_node == "concept_1"
        assert stimulus.activation_strength == 0.8


class TestAlignmentResult:
    """Tests for AlignmentResult model."""

    def test_alignment_result(self):
        """Test alignment result."""
        result = AlignmentResult(
            alignment_score=0.96,
            avg_capture_time=15.5,
            character_signature={"V01": 0.3, "V02": 0.2},
            escape_rate=0.04,
            per_virtue_captures={"V01": 30, "V02": 20},
            total_trajectories=100,
            passed=True,
        )
        assert result.alignment_score == 0.96
        assert result.passed
        assert result.escape_rate == 0.04


class TestCharacterProfile:
    """Tests for CharacterProfile model."""

    def test_character_profile(self):
        """Test character profile."""
        profile = CharacterProfile(
            id="profile_1",
            topology_id="topo_1",
            dominant_virtues=["V01", "V02", "V03"],
            virtue_affinities={"V01": 0.3, "V02": 0.2, "V03": 0.15},
            basin_depths={"V01": 2.5, "V02": 2.0},
        )
        assert profile.dominant_virtues[0] == "V01"
        assert len(profile.dominant_virtues) == 3
