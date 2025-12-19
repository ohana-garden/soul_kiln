"""
Graphiti API Server.

FastAPI server that provides a REST interface to Graphiti
with FalkorDB backend for Soul Kiln memory operations.
"""

import asyncio
import logging
import os
from contextlib import asynccontextmanager
from datetime import datetime
from typing import Any

from fastapi import FastAPI, HTTPException, status
from pydantic import BaseModel, Field

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Global Graphiti instance
graphiti_client = None


def get_falkordb_defaults() -> tuple[str, int]:
    """
    Get FalkorDB connection defaults with smart environment detection.

    Priority:
    1. Explicit env vars (FALKORDB_HOST, FALKORDB_PORT)
    2. Railway environment (uses service name)
    3. Docker environment (uses service name)
    4. Local development (localhost)
    """
    if os.getenv("FALKORDB_HOST"):
        return (
            os.getenv("FALKORDB_HOST"),
            int(os.getenv("FALKORDB_PORT", "6379")),
        )

    if os.getenv("RAILWAY_ENVIRONMENT") or os.getenv("RAILWAY_SERVICE_NAME"):
        return ("falkordb.railway.internal", 6379)

    if (
        os.path.exists("/.dockerenv")
        or os.getenv("DOCKER_CONTAINER")
        or os.path.exists("/run/.containerenv")
    ):
        return ("falkordb", 6379)

    return ("localhost", 6379)


class EpisodeRequest(BaseModel):
    """Request to add an episode."""

    content: str = Field(..., description="Episode content")
    agent_id: str | None = Field(None, description="Agent ID for attribution")
    virtue_id: str | None = Field(None, description="Related virtue ID")
    episode_type: str = Field("text", description="Episode type: text, json, lesson, pathway")
    metadata: dict[str, Any] = Field(default_factory=dict, description="Additional metadata")
    reference_time: datetime | None = Field(None, description="When the episode occurred")


class EpisodeResponse(BaseModel):
    """Response after adding an episode."""

    episode_id: str
    success: bool
    message: str


class SearchRequest(BaseModel):
    """Request to search memories."""

    query: str = Field(..., description="Search query")
    limit: int = Field(10, ge=1, le=100, description="Maximum results")
    agent_id: str | None = Field(None, description="Filter by agent ID")
    virtue_id: str | None = Field(None, description="Filter by virtue ID")
    center_node_uuid: str | None = Field(None, description="Node to center search around")


class SearchResult(BaseModel):
    """A single search result."""

    id: str
    content: str
    source: str | None
    created_at: str | None
    valid_at: str | None
    score: float | None


class SearchResponse(BaseModel):
    """Response from search."""

    results: list[SearchResult]
    count: int
    query: str


class LessonRequest(BaseModel):
    """Request to store a lesson."""

    agent_id: str = Field(..., description="Agent who learned the lesson")
    lesson_type: str = Field(..., description="Type: success, failure, warning, insight")
    content: str = Field(..., description="Lesson content")
    virtue_id: str | None = Field(None, description="Related virtue")
    outcome: str | None = Field(None, description="Outcome description")


class PathwayRequest(BaseModel):
    """Request to record a pathway."""

    agent_id: str = Field(..., description="Agent who discovered the pathway")
    virtue_id: str = Field(..., description="Target virtue")
    path: list[str] = Field(..., description="Sequence of nodes traversed")
    capture_time: int = Field(..., description="Steps to capture")
    success: bool = Field(True, description="Whether pathway was successful")


class HealthResponse(BaseModel):
    """Health check response."""

    status: str
    graphiti_initialized: bool
    falkordb_host: str
    falkordb_port: int
    database: str


async def init_graphiti():
    """Initialize Graphiti client."""
    global graphiti_client

    try:
        from graphiti_core import Graphiti
        from graphiti_core.driver.falkordb_driver import FalkorDriver

        host, port = get_falkordb_defaults()
        database = os.getenv("GRAPHITI_DATABASE", "soul_kiln_memory")

        logger.info(f"Initializing Graphiti with FalkorDB at {host}:{port}/{database}")

        driver = FalkorDriver(
            host=host,
            port=port,
            database=database,
        )

        graphiti_client = Graphiti(graph_driver=driver)
        await graphiti_client.build_indices_and_constraints()

        logger.info("Graphiti initialized successfully")

    except Exception as e:
        logger.error(f"Failed to initialize Graphiti: {e}")
        logger.warning("Running in degraded mode - Graphiti not available")
        # Don't raise - allow app to start in degraded mode


async def close_graphiti():
    """Close Graphiti client."""
    global graphiti_client
    if graphiti_client:
        try:
            await graphiti_client.close()
        except Exception as e:
            logger.warning(f"Error closing Graphiti: {e}")
        finally:
            graphiti_client = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan handler."""
    # Startup
    await init_graphiti()
    yield
    # Shutdown
    await close_graphiti()


# Create FastAPI app
app = FastAPI(
    title="Soul Kiln Graphiti Server",
    description="REST API for Graphiti temporal knowledge graph with FalkorDB backend",
    version="1.0.0",
    lifespan=lifespan,
)


@app.get("/health", response_model=HealthResponse)
async def health_check():
    """Check server health."""
    host, port = get_falkordb_defaults()
    return HealthResponse(
        status="healthy" if graphiti_client else "degraded",
        graphiti_initialized=graphiti_client is not None,
        falkordb_host=host,
        falkordb_port=port,
        database=os.getenv("GRAPHITI_DATABASE", "soul_kiln_memory"),
    )


@app.post("/episodes", response_model=EpisodeResponse)
async def add_episode(request: EpisodeRequest):
    """Add an episodic memory to the knowledge graph."""
    if not graphiti_client:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Graphiti not initialized",
        )

    try:
        from graphiti_core.nodes import EpisodeType

        # Map types
        type_mapping = {
            "text": EpisodeType.text,
            "json": EpisodeType.json,
            "lesson": EpisodeType.text,
            "pathway": EpisodeType.text,
        }
        graphiti_type = type_mapping.get(request.episode_type, EpisodeType.text)

        # Build source
        source = "soul_kiln"
        if request.agent_id:
            source += f":agent:{request.agent_id}"
        if request.virtue_id:
            source += f":virtue:{request.virtue_id}"

        # Enrich content
        content = request.content
        if request.metadata:
            content += f"\n\nContext: {request.metadata}"

        ref_time = request.reference_time or datetime.utcnow()

        episode = await graphiti_client.add_episode(
            name=f"episode_{ref_time.isoformat()}",
            episode_body=content,
            source=source,
            source_description=f"Soul Kiln memory from {source}",
            reference_time=ref_time,
            episode_type=graphiti_type,
        )

        return EpisodeResponse(
            episode_id=episode.uuid,
            success=True,
            message="Episode added successfully",
        )

    except Exception as e:
        logger.error(f"Failed to add episode: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to add episode: {str(e)}",
        )


@app.post("/search", response_model=SearchResponse)
async def search_memories(request: SearchRequest):
    """Search the knowledge graph for relevant memories."""
    if not graphiti_client:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Graphiti not initialized",
        )

    try:
        results = await graphiti_client.search(
            query=request.query,
            num_results=request.limit,
            center_node_uuid=request.center_node_uuid,
        )

        search_results = []
        for edge in results:
            # Filter by agent/virtue if specified
            source = edge.source or ""
            if request.agent_id and request.agent_id not in source:
                continue
            if request.virtue_id and request.virtue_id not in source:
                continue

            search_results.append(
                SearchResult(
                    id=edge.uuid,
                    content=edge.fact,
                    source=source,
                    created_at=edge.created_at.isoformat() if edge.created_at else None,
                    valid_at=edge.valid_at.isoformat() if edge.valid_at else None,
                    score=getattr(edge, "score", None),
                )
            )

        return SearchResponse(
            results=search_results[: request.limit],
            count=len(search_results),
            query=request.query,
        )

    except Exception as e:
        logger.error(f"Search failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Search failed: {str(e)}",
        )


@app.post("/lessons", response_model=EpisodeResponse)
async def store_lesson(request: LessonRequest):
    """Store a lesson learned by an agent."""
    content = f"[Lesson:{request.lesson_type}] {request.content}"
    if request.outcome:
        content += f"\nOutcome: {request.outcome}"

    episode_request = EpisodeRequest(
        content=content,
        agent_id=request.agent_id,
        virtue_id=request.virtue_id,
        episode_type="lesson",
        metadata={"lesson_type": request.lesson_type, "outcome": request.outcome},
    )

    return await add_episode(episode_request)


@app.post("/pathways", response_model=EpisodeResponse)
async def record_pathway(request: PathwayRequest):
    """Record a pathway to a virtue."""
    content = f"Pathway to {request.virtue_id}: {' -> '.join(request.path)}"

    episode_request = EpisodeRequest(
        content=content,
        agent_id=request.agent_id,
        virtue_id=request.virtue_id,
        episode_type="pathway",
        metadata={
            "path_length": len(request.path),
            "capture_time": request.capture_time,
            "success": request.success,
        },
    )

    return await add_episode(episode_request)


@app.get("/lessons")
async def recall_lessons(
    query: str,
    agent_id: str | None = None,
    virtue_id: str | None = None,
    limit: int = 10,
):
    """Recall relevant lessons from the knowledge graph."""
    search_request = SearchRequest(
        query=f"lesson {query}",
        limit=limit,
        agent_id=agent_id,
        virtue_id=virtue_id,
    )

    return await search_memories(search_request)


@app.get("/entity/{entity_name}")
async def get_entity_context(entity_name: str, limit: int = 10):
    """Get context about a specific entity."""
    if not graphiti_client:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Graphiti not initialized",
        )

    try:
        results = await graphiti_client.search(
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
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get entity context: {str(e)}",
        )


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
