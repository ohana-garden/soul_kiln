"""
Graphiti Memory System.

Provides temporal knowledge graph memory using Graphiti with FalkorDB backend.
Replaces the placeholder SemanticMemory with real graph-based episodic memory.
"""

import asyncio
import logging
import os
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any

logger = logging.getLogger(__name__)


@dataclass
class Episode:
    """A single episodic memory entry."""

    id: str
    content: str
    agent_id: str | None = None
    virtue_id: str | None = None
    episode_type: str = "text"
    metadata: dict = field(default_factory=dict)
    created_at: datetime = field(default_factory=datetime.utcnow)

    def to_dict(self) -> dict:
        """Convert to dictionary."""
        return {
            "id": self.id,
            "content": self.content,
            "agent_id": self.agent_id,
            "virtue_id": self.virtue_id,
            "episode_type": self.episode_type,
            "metadata": self.metadata,
            "created_at": self.created_at.isoformat(),
        }


class GraphitiMemory:
    """
    Graphiti-backed temporal knowledge graph memory.

    Uses FalkorDB as the graph backend for storing and querying
    episodic memories with temporal awareness.

    Features:
    - Temporal knowledge graph storage
    - Episodic memory with timestamps
    - Semantic search via embeddings
    - Entity and relationship extraction
    - Virtue-aware memory organization
    """

    def __init__(
        self,
        host: str | None = None,
        port: int | None = None,
        database: str = "soul_kiln_memory",
    ):
        """
        Initialize Graphiti memory with FalkorDB backend.

        Args:
            host: FalkorDB host (default: FALKORDB_HOST env or localhost)
            port: FalkorDB port (default: FALKORDB_PORT env or 6379)
            database: Graph database name
        """
        self._host = host or os.getenv("FALKORDB_HOST", "localhost")
        self._port = port or int(os.getenv("FALKORDB_PORT", "6379"))
        self._database = database
        self._graphiti = None
        self._driver = None
        self._initialized = False
        self._loop = None

    async def initialize(self) -> None:
        """
        Initialize the Graphiti client and build indices.

        Must be called before using any other methods.
        """
        if self._initialized:
            return

        try:
            from graphiti_core import Graphiti
            from graphiti_core.driver.falkordb_driver import FalkorDriver

            # Create FalkorDB driver
            self._driver = FalkorDriver(
                host=self._host,
                port=self._port,
                database=self._database,
            )

            # Initialize Graphiti with the driver
            self._graphiti = Graphiti(graph_driver=self._driver)

            # Build indices and constraints (idempotent)
            await self._graphiti.build_indices_and_constraints()

            self._initialized = True
            logger.info(
                f"Graphiti initialized with FalkorDB at {self._host}:{self._port}/{self._database}"
            )

        except ImportError as e:
            logger.error(f"Failed to import Graphiti components: {e}")
            raise RuntimeError(
                "Graphiti not properly installed. Run: pip install graphiti-core[falkordb]"
            ) from e
        except Exception as e:
            logger.error(f"Failed to initialize Graphiti: {e}")
            raise

    def _ensure_initialized(self) -> None:
        """Ensure the client is initialized."""
        if not self._initialized:
            raise RuntimeError("GraphitiMemory not initialized. Call initialize() first.")

    async def add_episode(
        self,
        content: str,
        agent_id: str | None = None,
        virtue_id: str | None = None,
        episode_type: str = "text",
        metadata: dict | None = None,
        reference_time: datetime | None = None,
    ) -> str:
        """
        Add an episodic memory to the knowledge graph.

        Args:
            content: The episode content (text or JSON string)
            agent_id: Optional agent ID for attribution
            virtue_id: Optional virtue ID for categorization
            episode_type: Type of episode ("text", "json", "lesson", "pathway")
            metadata: Additional metadata
            reference_time: When the episode occurred (default: now)

        Returns:
            Episode ID
        """
        self._ensure_initialized()

        from graphiti_core.nodes import EpisodeType

        # Map our types to Graphiti types
        type_mapping = {
            "text": EpisodeType.text,
            "json": EpisodeType.json,
            "lesson": EpisodeType.text,
            "pathway": EpisodeType.text,
        }
        graphiti_type = type_mapping.get(episode_type, EpisodeType.text)

        # Build source description for provenance
        source = f"soul_kiln"
        if agent_id:
            source += f":agent:{agent_id}"
        if virtue_id:
            source += f":virtue:{virtue_id}"

        # Add metadata to content if provided
        enriched_content = content
        if metadata:
            enriched_content = f"{content}\n\nContext: {metadata}"

        ref_time = reference_time or datetime.utcnow()

        try:
            episode = await self._graphiti.add_episode(
                name=f"episode_{ref_time.isoformat()}",
                episode_body=enriched_content,
                source=source,
                source_description=f"Soul Kiln memory from {source}",
                reference_time=ref_time,
                episode_type=graphiti_type,
            )

            logger.debug(f"Added episode: {episode.uuid}")
            return episode.uuid

        except Exception as e:
            logger.error(f"Failed to add episode: {e}")
            raise

    async def search(
        self,
        query: str,
        limit: int = 10,
        agent_id: str | None = None,
        virtue_id: str | None = None,
        center_node_uuid: str | None = None,
    ) -> list[dict]:
        """
        Search the knowledge graph for relevant memories.

        Uses hybrid search combining semantic, keyword, and graph traversal.

        Args:
            query: Search query text
            limit: Maximum results to return
            agent_id: Filter by agent ID
            virtue_id: Filter by virtue ID
            center_node_uuid: Optional node to center search around

        Returns:
            List of matching memory results
        """
        self._ensure_initialized()

        try:
            # Use Graphiti's hybrid search
            results = await self._graphiti.search(
                query=query,
                num_results=limit,
                center_node_uuid=center_node_uuid,
            )

            # Transform results to our format
            memories = []
            for edge in results:
                memory = {
                    "id": edge.uuid,
                    "content": edge.fact,
                    "source": edge.source,
                    "created_at": edge.created_at.isoformat() if edge.created_at else None,
                    "valid_at": edge.valid_at.isoformat() if edge.valid_at else None,
                    "score": getattr(edge, "score", None),
                }

                # Filter by agent/virtue if specified
                if agent_id and agent_id not in (edge.source or ""):
                    continue
                if virtue_id and virtue_id not in (edge.source or ""):
                    continue

                memories.append(memory)

            return memories[:limit]

        except Exception as e:
            logger.error(f"Search failed: {e}")
            return []

    async def get_entity_context(
        self,
        entity_name: str,
        limit: int = 10,
    ) -> dict:
        """
        Get context about a specific entity from the knowledge graph.

        Args:
            entity_name: Name of the entity to look up
            limit: Maximum related facts to return

        Returns:
            Entity context with related facts and relationships
        """
        self._ensure_initialized()

        try:
            # Search for facts about this entity
            results = await self._graphiti.search(
                query=entity_name,
                num_results=limit,
            )

            facts = []
            for edge in results:
                facts.append({
                    "fact": edge.fact,
                    "source": edge.source,
                    "created_at": edge.created_at.isoformat() if edge.created_at else None,
                })

            return {
                "entity": entity_name,
                "facts": facts,
                "fact_count": len(facts),
            }

        except Exception as e:
            logger.error(f"Failed to get entity context: {e}")
            return {"entity": entity_name, "facts": [], "fact_count": 0}

    async def remember_lesson(
        self,
        agent_id: str,
        lesson_type: str,
        content: str,
        virtue_id: str | None = None,
        outcome: str | None = None,
    ) -> str:
        """
        Store a lesson learned by an agent.

        Args:
            agent_id: Agent who learned the lesson
            lesson_type: Type of lesson (success, failure, warning, insight)
            content: Lesson content
            virtue_id: Related virtue
            outcome: Outcome description

        Returns:
            Lesson episode ID
        """
        metadata = {
            "lesson_type": lesson_type,
            "outcome": outcome,
        }

        enriched_content = f"[Lesson:{lesson_type}] {content}"
        if outcome:
            enriched_content += f"\nOutcome: {outcome}"

        return await self.add_episode(
            content=enriched_content,
            agent_id=agent_id,
            virtue_id=virtue_id,
            episode_type="lesson",
            metadata=metadata,
        )

    async def recall_lessons(
        self,
        query: str,
        agent_id: str | None = None,
        virtue_id: str | None = None,
        limit: int = 10,
    ) -> list[dict]:
        """
        Recall relevant lessons from the knowledge graph.

        Args:
            query: Search query
            agent_id: Filter by agent
            virtue_id: Filter by virtue
            limit: Maximum results

        Returns:
            List of relevant lessons
        """
        # Enhance query for lesson search
        lesson_query = f"lesson {query}"

        return await self.search(
            query=lesson_query,
            limit=limit,
            agent_id=agent_id,
            virtue_id=virtue_id,
        )

    async def record_pathway(
        self,
        agent_id: str,
        virtue_id: str,
        path: list[str],
        capture_time: int,
        success: bool = True,
    ) -> str:
        """
        Record a pathway to a virtue.

        Args:
            agent_id: Agent who discovered the pathway
            virtue_id: Target virtue
            path: Sequence of nodes traversed
            capture_time: Steps to capture
            success: Whether pathway was successful

        Returns:
            Pathway episode ID
        """
        content = f"Pathway to {virtue_id}: {' -> '.join(path)}"
        metadata = {
            "path_length": len(path),
            "capture_time": capture_time,
            "success": success,
        }

        return await self.add_episode(
            content=content,
            agent_id=agent_id,
            virtue_id=virtue_id,
            episode_type="pathway",
            metadata=metadata,
        )

    async def get_stats(self) -> dict:
        """Get memory system statistics."""
        if not self._initialized:
            return {
                "initialized": False,
                "host": self._host,
                "port": self._port,
                "database": self._database,
            }

        try:
            # Get basic stats from the graph
            return {
                "initialized": True,
                "host": self._host,
                "port": self._port,
                "database": self._database,
                "connected": True,
            }
        except Exception as e:
            return {
                "initialized": True,
                "connected": False,
                "error": str(e),
            }

    async def close(self) -> None:
        """Close the Graphiti connection."""
        if self._graphiti:
            try:
                await self._graphiti.close()
            except Exception as e:
                logger.warning(f"Error closing Graphiti: {e}")
            finally:
                self._graphiti = None
                self._driver = None
                self._initialized = False

    def __del__(self):
        """Cleanup on deletion."""
        if self._initialized and self._loop:
            try:
                self._loop.run_until_complete(self.close())
            except Exception:
                pass


# Synchronous wrapper for non-async contexts
class GraphitiMemorySync:
    """
    Synchronous wrapper for GraphitiMemory.

    Use this when calling from synchronous code.
    """

    def __init__(
        self,
        host: str | None = None,
        port: int | None = None,
        database: str = "soul_kiln_memory",
    ):
        self._async_memory = GraphitiMemory(host=host, port=port, database=database)
        self._loop = None

    def _get_loop(self) -> asyncio.AbstractEventLoop:
        """Get or create event loop."""
        if self._loop is None or self._loop.is_closed():
            try:
                self._loop = asyncio.get_running_loop()
            except RuntimeError:
                self._loop = asyncio.new_event_loop()
                asyncio.set_event_loop(self._loop)
        return self._loop

    def _run(self, coro):
        """Run coroutine synchronously."""
        loop = self._get_loop()
        if loop.is_running():
            # If loop is running, create a new thread
            import concurrent.futures
            with concurrent.futures.ThreadPoolExecutor() as executor:
                future = executor.submit(asyncio.run, coro)
                return future.result()
        else:
            return loop.run_until_complete(coro)

    def initialize(self) -> None:
        """Initialize the Graphiti client."""
        self._run(self._async_memory.initialize())

    def add_episode(self, content: str, **kwargs) -> str:
        """Add an episode."""
        return self._run(self._async_memory.add_episode(content, **kwargs))

    def search(self, query: str, **kwargs) -> list[dict]:
        """Search for memories."""
        return self._run(self._async_memory.search(query, **kwargs))

    def remember_lesson(self, agent_id: str, lesson_type: str, content: str, **kwargs) -> str:
        """Store a lesson."""
        return self._run(self._async_memory.remember_lesson(agent_id, lesson_type, content, **kwargs))

    def recall_lessons(self, query: str, **kwargs) -> list[dict]:
        """Recall lessons."""
        return self._run(self._async_memory.recall_lessons(query, **kwargs))

    def get_stats(self) -> dict:
        """Get statistics."""
        return self._run(self._async_memory.get_stats())

    def close(self) -> None:
        """Close the connection."""
        self._run(self._async_memory.close())
