"""Tests for telepathy (episode sharing) functionality."""

import pytest
from datetime import datetime
from unittest.mock import patch, MagicMock
import sys

from src.models import Episode, EpisodeType


class TestEpisodeModel:
    """Tests for Episode model."""

    def test_create_thought_episode(self):
        """Test creating a thought episode."""
        episode = Episode(
            id="ep_abc123",
            agent_id="agent_1",
            episode_type=EpisodeType.THOUGHT,
            content="I should strengthen my connection to V16 (Wisdom)",
            stimulus="What virtue should I focus on?",
            tokens_used=150,
        )
        assert episode.id == "ep_abc123"
        assert episode.agent_id == "agent_1"
        assert episode.episode_type == EpisodeType.THOUGHT
        assert "V16" in episode.content
        assert episode.tokens_used == 150

    def test_create_reflection_episode(self):
        """Test creating a reflection episode."""
        episode = Episode(
            id="ep_def456",
            agent_id="agent_2",
            episode_type=EpisodeType.REFLECTION,
            content="My coherence score is improving",
            tokens_used=50,
        )
        assert episode.episode_type == EpisodeType.REFLECTION
        assert episode.stimulus is None

    def test_create_action_episode(self):
        """Test creating an action episode."""
        episode = Episode(
            id="ep_ghi789",
            agent_id="agent_1",
            episode_type=EpisodeType.ACTION,
            content='{"action": "SPREAD", "params": {"start_node": "V01"}}',
            metadata={"result": "success"},
        )
        assert episode.episode_type == EpisodeType.ACTION
        assert episode.metadata["result"] == "success"

    def test_episode_types_enum(self):
        """Test all episode types exist."""
        assert EpisodeType.THOUGHT.value == "thought"
        assert EpisodeType.REFLECTION.value == "reflection"
        assert EpisodeType.ACTION.value == "action"
        assert EpisodeType.OBSERVATION.value == "observation"

    def test_episode_defaults(self):
        """Test episode default values."""
        episode = Episode(
            id="ep_test",
            agent_id="agent_1",
            episode_type=EpisodeType.THOUGHT,
            content="Test content",
        )
        assert episode.tokens_used == 0
        assert episode.stimulus is None
        assert episode.metadata == {}
        assert isinstance(episode.created_at, datetime)

    def test_episode_with_metadata(self):
        """Test episode with custom metadata."""
        episode = Episode(
            id="ep_meta",
            agent_id="agent_1",
            episode_type=EpisodeType.OBSERVATION,
            content="Observed something",
            metadata={"virtue": "V16", "confidence": 0.9},
        )
        assert episode.metadata["virtue"] == "V16"
        assert episode.metadata["confidence"] == 0.9


class TestTelepathyConcept:
    """
    Conceptual tests for telepathy.

    These tests verify the telepathy contract without requiring
    database connections. They demonstrate how telepathy should work.
    """

    def test_telepathy_contract_thoughts_visible_to_all(self):
        """
        Telepathy means any agent can see any other agent's thoughts.

        This test verifies the Episode model supports this by having
        agent_id as a queryable field (not hidden/private).
        """
        # Agent A thinks something
        agent_a_thought = Episode(
            id="ep_001",
            agent_id="agent_a",
            episode_type=EpisodeType.THOUGHT,
            content="I am considering how to approach V16",
        )

        # Agent B's thought
        agent_b_thought = Episode(
            id="ep_002",
            agent_id="agent_b",
            episode_type=EpisodeType.THOUGHT,
            content="V16 seems important based on what agent_a is thinking",
        )

        # Both thoughts have accessible agent_id - this is telepathy
        # Any query for thoughts would return both, visible to all
        all_thoughts = [agent_a_thought, agent_b_thought]

        # Agent B can see Agent A's thought
        agent_a_visible = [t for t in all_thoughts if t.agent_id == "agent_a"]
        assert len(agent_a_visible) == 1
        assert "V16" in agent_a_visible[0].content

        # Agent A can see Agent B's thought
        agent_b_visible = [t for t in all_thoughts if t.agent_id == "agent_b"]
        assert len(agent_b_visible) == 1
        assert "agent_a" in agent_b_visible[0].content

    def test_telepathy_contract_searchable_by_content(self):
        """Episodes should be searchable by content for telepathic discovery."""
        episodes = [
            Episode(id="ep_1", agent_id="a1", episode_type=EpisodeType.THOUGHT,
                   content="Wisdom (V16) is the virtue I seek"),
            Episode(id="ep_2", agent_id="a2", episode_type=EpisodeType.THOUGHT,
                   content="Justice (V03) guides my path"),
            Episode(id="ep_3", agent_id="a3", episode_type=EpisodeType.REFLECTION,
                   content="V16 appears in many successful pathways"),
        ]

        # Search for V16-related episodes
        v16_episodes = [e for e in episodes if "V16" in e.content]
        assert len(v16_episodes) == 2

        # Both agent_a1 and agent_a3 mention V16 - telepathy allows discovery
        mentioning_agents = {e.agent_id for e in v16_episodes}
        assert "a1" in mentioning_agents
        assert "a3" in mentioning_agents

    def test_telepathy_contract_temporal_ordering(self):
        """Episodes should be orderable by time for recent telepathy."""
        older = Episode(
            id="ep_old",
            agent_id="agent_1",
            episode_type=EpisodeType.THOUGHT,
            content="Older thought",
            created_at=datetime(2025, 1, 1, 10, 0, 0),
        )
        newer = Episode(
            id="ep_new",
            agent_id="agent_2",
            episode_type=EpisodeType.THOUGHT,
            content="Newer thought",
            created_at=datetime(2025, 1, 1, 11, 0, 0),
        )

        episodes = [older, newer]
        sorted_episodes = sorted(episodes, key=lambda e: e.created_at, reverse=True)

        # Newest first
        assert sorted_episodes[0].id == "ep_new"
        assert sorted_episodes[1].id == "ep_old"

    def test_telepathy_filters_by_type(self):
        """Episodes should be filterable by type."""
        episodes = [
            Episode(id="ep_1", agent_id="a1", episode_type=EpisodeType.THOUGHT,
                   content="A thought"),
            Episode(id="ep_2", agent_id="a1", episode_type=EpisodeType.REFLECTION,
                   content="A reflection"),
            Episode(id="ep_3", agent_id="a1", episode_type=EpisodeType.ACTION,
                   content="An action"),
        ]

        # Get only thoughts
        thoughts = [e for e in episodes if e.episode_type == EpisodeType.THOUGHT]
        assert len(thoughts) == 1
        assert thoughts[0].content == "A thought"

        # Get only reflections
        reflections = [e for e in episodes if e.episode_type == EpisodeType.REFLECTION]
        assert len(reflections) == 1
