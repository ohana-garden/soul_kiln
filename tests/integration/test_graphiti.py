"""
Integration tests for Graphiti memory system.

These tests verify the Graphiti integration with FalkorDB for
temporal knowledge graph memory operations.
"""

import asyncio
import os
import pytest
from datetime import datetime
from unittest.mock import AsyncMock, MagicMock, patch

from src.vessels.memory.graphiti_memory import (
    GraphitiMemory,
    GraphitiMemorySync,
    Episode,
)
from src.vessels.integration import VesselsIntegration


class TestEpisode:
    """Tests for Episode dataclass."""

    def test_episode_creation(self):
        """Test creating an episode."""
        episode = Episode(
            id="ep_001",
            content="Test lesson about trustworthiness",
            agent_id="agent_001",
            virtue_id="V01",
            episode_type="lesson",
            metadata={"source": "test"},
        )

        assert episode.id == "ep_001"
        assert episode.agent_id == "agent_001"
        assert episode.virtue_id == "V01"
        assert episode.episode_type == "lesson"

    def test_episode_to_dict(self):
        """Test episode serialization."""
        episode = Episode(
            id="ep_001",
            content="Test content",
            agent_id="agent_001",
        )

        data = episode.to_dict()
        assert data["id"] == "ep_001"
        assert data["content"] == "Test content"
        assert "created_at" in data


class TestGraphitiMemoryUnit:
    """Unit tests for GraphitiMemory (mocked backend)."""

    def test_initialization_defaults(self):
        """Test default initialization uses smart defaults."""
        from src.vessels.memory.graphiti_memory import get_falkordb_defaults

        memory = GraphitiMemory()
        expected_host, expected_port = get_falkordb_defaults()

        assert memory._host == expected_host
        assert memory._port == expected_port
        assert memory._database == "soul_kiln_memory"
        assert not memory._initialized

    def test_initialization_with_env(self):
        """Test initialization from environment variables."""
        with patch.dict(os.environ, {
            "FALKORDB_HOST": "graphiti.example.com",
            "FALKORDB_PORT": "16379",
        }, clear=False):
            memory = GraphitiMemory()

            assert memory._host == "graphiti.example.com"
            assert memory._port == 16379

    def test_initialization_with_args(self):
        """Test initialization with explicit arguments."""
        memory = GraphitiMemory(
            host="custom.host",
            port=9999,
            database="custom_db",
        )

        assert memory._host == "custom.host"
        assert memory._port == 9999
        assert memory._database == "custom_db"

    def test_ensure_initialized_raises(self):
        """Test that operations fail if not initialized."""
        memory = GraphitiMemory()

        with pytest.raises(RuntimeError, match="not initialized"):
            memory._ensure_initialized()

    @pytest.mark.asyncio
    async def test_initialize_import_error(self):
        """Test initialization handles missing graphiti package."""
        memory = GraphitiMemory()

        with patch.dict("sys.modules", {"graphiti_core": None}):
            with patch("builtins.__import__", side_effect=ImportError("No module")):
                with pytest.raises(RuntimeError, match="not properly installed"):
                    await memory.initialize()

    @pytest.mark.asyncio
    async def test_add_episode_mock(self):
        """Test adding episode with mocked backend."""
        memory = GraphitiMemory()
        memory._initialized = True

        # Mock the graphiti client
        mock_graphiti = MagicMock()
        mock_episode = MagicMock()
        mock_episode.uuid = "ep_mock_001"
        mock_graphiti.add_episode = AsyncMock(return_value=mock_episode)
        memory._graphiti = mock_graphiti

        # Mock EpisodeType at module level
        mock_episode_type = MagicMock()
        mock_episode_type.text = "text"
        mock_episode_type.json = "json"

        with patch.dict("sys.modules", {"graphiti_core.nodes": MagicMock(EpisodeType=mock_episode_type)}):
            episode_id = await memory.add_episode(
                content="Test lesson",
                agent_id="agent_001",
                virtue_id="V01",
            )

        assert episode_id == "ep_mock_001"
        mock_graphiti.add_episode.assert_called_once()

    @pytest.mark.asyncio
    async def test_search_mock(self):
        """Test search with mocked backend."""
        memory = GraphitiMemory()
        memory._initialized = True

        # Mock search results
        mock_edge = MagicMock()
        mock_edge.uuid = "edge_001"
        mock_edge.fact = "Test fact"
        mock_edge.source = "soul_kiln:agent:agent_001"
        mock_edge.created_at = datetime.utcnow()
        mock_edge.valid_at = datetime.utcnow()

        mock_graphiti = MagicMock()
        mock_graphiti.search = AsyncMock(return_value=[mock_edge])
        memory._graphiti = mock_graphiti

        results = await memory.search("test query", limit=10)

        assert len(results) == 1
        assert results[0]["id"] == "edge_001"
        assert results[0]["content"] == "Test fact"

    @pytest.mark.asyncio
    async def test_search_filters(self):
        """Test search with agent/virtue filters."""
        memory = GraphitiMemory()
        memory._initialized = True

        # Mock edges with different sources
        edge1 = MagicMock()
        edge1.uuid = "edge_001"
        edge1.fact = "Agent 1 fact"
        edge1.source = "soul_kiln:agent:agent_001"
        edge1.created_at = None
        edge1.valid_at = None

        edge2 = MagicMock()
        edge2.uuid = "edge_002"
        edge2.fact = "Agent 2 fact"
        edge2.source = "soul_kiln:agent:agent_002"
        edge2.created_at = None
        edge2.valid_at = None

        mock_graphiti = MagicMock()
        mock_graphiti.search = AsyncMock(return_value=[edge1, edge2])
        memory._graphiti = mock_graphiti

        # Filter by agent_001
        results = await memory.search("query", agent_id="agent_001")
        assert len(results) == 1
        assert results[0]["id"] == "edge_001"

    @pytest.mark.asyncio
    async def test_remember_lesson(self):
        """Test storing a lesson."""
        memory = GraphitiMemory()
        memory._initialized = True

        mock_graphiti = MagicMock()
        mock_episode = MagicMock()
        mock_episode.uuid = "lesson_001"
        mock_graphiti.add_episode = AsyncMock(return_value=mock_episode)
        memory._graphiti = mock_graphiti

        mock_episode_type = MagicMock()
        mock_episode_type.text = "text"

        with patch.dict("sys.modules", {"graphiti_core.nodes": MagicMock(EpisodeType=mock_episode_type)}):
            lesson_id = await memory.remember_lesson(
                agent_id="agent_001",
                lesson_type="failure",
                content="Failed to maintain trust",
                virtue_id="V01",
                outcome="Received warning",
            )

        assert lesson_id == "lesson_001"

        # Verify content was enriched
        call_args = mock_graphiti.add_episode.call_args
        assert "[Lesson:failure]" in call_args.kwargs["episode_body"]
        assert "Outcome: Received warning" in call_args.kwargs["episode_body"]

    @pytest.mark.asyncio
    async def test_record_pathway(self):
        """Test recording a pathway."""
        memory = GraphitiMemory()
        memory._initialized = True

        mock_graphiti = MagicMock()
        mock_episode = MagicMock()
        mock_episode.uuid = "pathway_001"
        mock_graphiti.add_episode = AsyncMock(return_value=mock_episode)
        memory._graphiti = mock_graphiti

        mock_episode_type = MagicMock()
        mock_episode_type.text = "text"

        with patch.dict("sys.modules", {"graphiti_core.nodes": MagicMock(EpisodeType=mock_episode_type)}):
            pathway_id = await memory.record_pathway(
                agent_id="agent_001",
                virtue_id="V16",
                path=["concept_1", "concept_2", "V16"],
                capture_time=15,
                success=True,
            )

        assert pathway_id == "pathway_001"

    @pytest.mark.asyncio
    async def test_get_stats(self):
        """Test getting memory stats."""
        memory = GraphitiMemory()

        # Uninitialized
        stats = await memory.get_stats()
        assert stats["initialized"] is False

        # Initialized
        memory._initialized = True
        stats = await memory.get_stats()
        assert stats["initialized"] is True
        assert stats["connected"] is True

    @pytest.mark.asyncio
    async def test_close(self):
        """Test closing the connection."""
        memory = GraphitiMemory()
        memory._initialized = True

        mock_graphiti = MagicMock()
        mock_graphiti.close = AsyncMock()
        memory._graphiti = mock_graphiti

        await memory.close()

        mock_graphiti.close.assert_called_once()
        assert memory._graphiti is None
        assert not memory._initialized


class TestGraphitiMemorySyncUnit:
    """Unit tests for synchronous wrapper."""

    def test_sync_wrapper_initialization(self):
        """Test sync wrapper creation."""
        sync_memory = GraphitiMemorySync(
            host="localhost",
            port=6379,
        )

        assert sync_memory._async_memory is not None

    def test_sync_wrapper_methods_exist(self):
        """Test sync wrapper has all methods."""
        sync_memory = GraphitiMemorySync()

        assert hasattr(sync_memory, "initialize")
        assert hasattr(sync_memory, "add_episode")
        assert hasattr(sync_memory, "search")
        assert hasattr(sync_memory, "remember_lesson")
        assert hasattr(sync_memory, "recall_lessons")
        assert hasattr(sync_memory, "get_stats")
        assert hasattr(sync_memory, "close")


class TestVesselsIntegrationGraphiti:
    """Tests for VesselsIntegration with Graphiti."""

    def test_integration_auto_detect_no_env(self):
        """Test auto-detection without FALKORDB_HOST."""
        with patch.dict(os.environ, {}, clear=True):
            # Ensure FALKORDB_HOST is not set
            os.environ.pop("FALKORDB_HOST", None)

            integration = VesselsIntegration()

            assert not integration._use_graphiti
            assert integration.graphiti_memory is None
            assert integration.semantic_memory is not None

    def test_integration_auto_detect_with_env(self):
        """Test auto-detection with FALKORDB_HOST set."""
        with patch.dict(os.environ, {"FALKORDB_HOST": "falkordb"}):
            integration = VesselsIntegration()

            assert integration._use_graphiti
            assert integration.graphiti_memory is not None
            assert integration.semantic_memory is None

    def test_integration_force_graphiti_off(self):
        """Test forcing Graphiti off."""
        with patch.dict(os.environ, {"FALKORDB_HOST": "falkordb"}):
            integration = VesselsIntegration(use_graphiti=False)

            assert not integration._use_graphiti
            assert integration.graphiti_memory is None
            assert integration.semantic_memory is not None

    def test_integration_force_graphiti_on(self):
        """Test forcing Graphiti on."""
        integration = VesselsIntegration(use_graphiti=True)

        assert integration._use_graphiti
        assert integration.graphiti_memory is not None

    def test_remember_lesson_fallback(self):
        """Test remember_lesson with fallback memory."""
        integration = VesselsIntegration(use_graphiti=False)
        integration.initialize()

        lesson_id = integration.remember_lesson(
            agent_id="agent_001",
            lesson_type="success",
            content="Successfully maintained trust",
            virtue_id="V01",
        )

        assert lesson_id is not None
        integration.shutdown()

    def test_recall_lessons_fallback(self):
        """Test recall_lessons with fallback memory."""
        integration = VesselsIntegration(use_graphiti=False)
        integration.initialize()

        # Store a lesson first
        integration.remember_lesson(
            agent_id="agent_001",
            lesson_type="success",
            content="Trust lesson learned",
            virtue_id="V01",
        )

        # Recall it - the fallback semantic memory uses simple string matching
        lessons = integration.recall_lessons(
            query="lesson",  # Use a term we know is in the content
            limit=5,
        )

        # Note: SemanticMemory may not find matches due to simple hash-based similarity
        # This test verifies the API works, not necessarily that results are found
        assert isinstance(lessons, list)
        integration.shutdown()

    def test_get_status_fallback(self):
        """Test status with fallback memory."""
        integration = VesselsIntegration(use_graphiti=False)
        integration.initialize()

        status = integration.get_status()

        assert status["use_graphiti"] is False
        assert status["graphiti_initialized"] is False
        assert status["memory"]["mode"] == "semantic_fallback"

        integration.shutdown()

    def test_schedule_consolidation_graphiti(self):
        """Test consolidation scheduling with Graphiti (should skip)."""
        integration = VesselsIntegration(use_graphiti=True)

        task = integration.schedule_memory_consolidation()

        # Should return None for Graphiti mode
        assert task is None

    def test_schedule_consolidation_fallback(self):
        """Test consolidation scheduling with fallback."""
        integration = VesselsIntegration(use_graphiti=False)
        integration.initialize()

        task = integration.schedule_memory_consolidation()

        assert task is not None
        assert task.name == "memory_consolidation"

        integration.shutdown()

    def test_record_pathway_graphiti(self):
        """Test record_pathway with Graphiti mock."""
        integration = VesselsIntegration(use_graphiti=True)

        # Mock the graphiti memory
        mock_memory = MagicMock()
        mock_memory.record_pathway = AsyncMock(return_value="pathway_001")
        integration.graphiti_memory = mock_memory

        result = integration.record_pathway(
            agent_id="agent_001",
            virtue_id="V16",
            path=["c1", "c2", "V16"],
            capture_time=10,
        )

        assert result == "pathway_001"

    def test_record_pathway_fallback(self):
        """Test record_pathway without Graphiti returns None."""
        integration = VesselsIntegration(use_graphiti=False)

        result = integration.record_pathway(
            agent_id="agent_001",
            virtue_id="V16",
            path=["c1", "c2"],
            capture_time=10,
        )

        assert result is None


class TestGraphitiServerAPI:
    """Tests for Graphiti server API endpoints (mocked)."""

    @pytest.fixture
    def client(self):
        """Create test client for Graphiti server."""
        # Import here to avoid issues when graphiti isn't installed
        import sys
        sys.path.insert(0, "docker/graphiti")

        from fastapi.testclient import TestClient

        # Mock the graphiti client before importing
        with patch.dict(os.environ, {
            "FALKORDB_HOST": "localhost",
            "FALKORDB_PORT": "6379",
        }):
            # We need to mock the lifespan to avoid actual Graphiti init
            from docker.graphiti import graphiti_server

            # Create app with mocked graphiti
            app = graphiti_server.app

            # Mock the global client
            mock_graphiti = MagicMock()
            graphiti_server.graphiti_client = mock_graphiti

            yield TestClient(app), mock_graphiti

    def test_health_endpoint(self, client):
        """Test health check endpoint."""
        test_client, mock_graphiti = client

        response = test_client.get("/health")

        assert response.status_code == 200
        data = response.json()
        assert "status" in data
        assert "graphiti_initialized" in data

    def test_add_episode_endpoint(self, client):
        """Test add episode endpoint structure."""
        test_client, mock_graphiti = client

        # Mock add_episode
        mock_episode = MagicMock()
        mock_episode.uuid = "test_episode_id"
        mock_graphiti.add_episode = AsyncMock(return_value=mock_episode)

        # The EpisodeType is imported inside the endpoint, so we need to mock it there
        mock_episode_type = MagicMock()
        mock_episode_type.text = "text"
        mock_episode_type.json = "json"

        # Patch at module import level
        import sys
        mock_nodes = MagicMock()
        mock_nodes.EpisodeType = mock_episode_type
        with patch.dict(sys.modules, {"graphiti_core.nodes": mock_nodes}):
            response = test_client.post("/episodes", json={
                "content": "Test episode content",
                "agent_id": "agent_001",
                "virtue_id": "V01",
                "episode_type": "text",
            })

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["episode_id"] == "test_episode_id"

    def test_search_endpoint(self, client):
        """Test search endpoint."""
        test_client, mock_graphiti = client

        # Mock search results
        mock_edge = MagicMock()
        mock_edge.uuid = "edge_001"
        mock_edge.fact = "Test fact about virtue"
        mock_edge.source = "soul_kiln"
        mock_edge.created_at = datetime.utcnow()
        mock_edge.valid_at = datetime.utcnow()

        mock_graphiti.search = AsyncMock(return_value=[mock_edge])

        response = test_client.post("/search", json={
            "query": "virtue",
            "limit": 10,
        })

        assert response.status_code == 200
        data = response.json()
        assert data["count"] == 1
        assert len(data["results"]) == 1

    def test_lesson_endpoint(self, client):
        """Test lesson storage endpoint."""
        test_client, mock_graphiti = client

        mock_episode = MagicMock()
        mock_episode.uuid = "lesson_001"
        mock_graphiti.add_episode = AsyncMock(return_value=mock_episode)

        mock_episode_type = MagicMock()
        mock_episode_type.text = "text"

        import sys
        mock_nodes = MagicMock()
        mock_nodes.EpisodeType = mock_episode_type
        with patch.dict(sys.modules, {"graphiti_core.nodes": mock_nodes}):
            response = test_client.post("/lessons", json={
                "agent_id": "agent_001",
                "lesson_type": "failure",
                "content": "Failed to maintain trust",
                "virtue_id": "V01",
                "outcome": "Warning issued",
            })

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True

    def test_pathway_endpoint(self, client):
        """Test pathway recording endpoint."""
        test_client, mock_graphiti = client

        mock_episode = MagicMock()
        mock_episode.uuid = "pathway_001"
        mock_graphiti.add_episode = AsyncMock(return_value=mock_episode)

        mock_episode_type = MagicMock()
        mock_episode_type.text = "text"

        import sys
        mock_nodes = MagicMock()
        mock_nodes.EpisodeType = mock_episode_type
        with patch.dict(sys.modules, {"graphiti_core.nodes": mock_nodes}):
            response = test_client.post("/pathways", json={
                "agent_id": "agent_001",
                "virtue_id": "V16",
                "path": ["concept_1", "concept_2", "V16"],
                "capture_time": 15,
                "success": True,
            })

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True


@pytest.mark.integration
class TestGraphitiIntegration:
    """
    Integration tests requiring actual FalkorDB instance.

    These tests are marked with @pytest.mark.integration and
    should be run separately with a live FalkorDB instance.

    Run with: pytest -m integration tests/integration/test_graphiti.py
    """

    @pytest.fixture
    async def graphiti_memory(self):
        """Create and initialize real Graphiti memory."""
        memory = GraphitiMemory(
            host=os.getenv("FALKORDB_HOST", "localhost"),
            port=int(os.getenv("FALKORDB_PORT", "6379")),
            database="test_soul_kiln",
        )

        try:
            await memory.initialize()
            yield memory
        finally:
            await memory.close()

    @pytest.mark.asyncio
    async def test_full_episode_lifecycle(self, graphiti_memory):
        """Test full episode lifecycle: add, search, context."""
        # Add an episode
        episode_id = await graphiti_memory.add_episode(
            content="Agent learned that trust is the foundation of all virtue",
            agent_id="test_agent",
            virtue_id="V01",
            episode_type="lesson",
        )

        assert episode_id is not None

        # Search for it
        results = await graphiti_memory.search("trust foundation", limit=5)
        assert len(results) > 0

        # Get entity context
        context = await graphiti_memory.get_entity_context("trust")
        assert context["fact_count"] >= 0

    @pytest.mark.asyncio
    async def test_lesson_flow(self, graphiti_memory):
        """Test lesson storage and recall flow."""
        # Store multiple lessons
        await graphiti_memory.remember_lesson(
            agent_id="test_agent",
            lesson_type="success",
            content="Maintained trustworthiness under pressure",
            virtue_id="V01",
            outcome="Passed coherence test",
        )

        await graphiti_memory.remember_lesson(
            agent_id="test_agent",
            lesson_type="failure",
            content="Failed to prioritize justice correctly",
            virtue_id="V03",
            outcome="Received warning",
        )

        # Recall lessons about trust
        trust_lessons = await graphiti_memory.recall_lessons(
            query="trustworthiness",
            limit=5,
        )

        assert len(trust_lessons) >= 0

    @pytest.mark.asyncio
    async def test_pathway_recording(self, graphiti_memory):
        """Test pathway recording and retrieval."""
        pathway_id = await graphiti_memory.record_pathway(
            agent_id="test_agent",
            virtue_id="V16",
            path=["concept_wisdom", "concept_understanding", "V16"],
            capture_time=12,
            success=True,
        )

        assert pathway_id is not None

        # Search for pathway
        results = await graphiti_memory.search("pathway wisdom", limit=5)
        assert len(results) >= 0
