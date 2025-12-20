"""
Soul Kiln API Server.

FastAPI server for Railway deployment with health checks
and integration with Graphiti memory system.
"""

import logging
import os
from contextlib import asynccontextmanager
from datetime import datetime

from fastapi import FastAPI, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from ..graph.client import get_client
from ..vessels.integration import VesselsIntegration

logger = logging.getLogger(__name__)

# Global integration instance
_integration: VesselsIntegration | None = None


class HealthResponse(BaseModel):
    """Health check response."""

    status: str
    timestamp: str
    version: str
    components: dict


class StatusResponse(BaseModel):
    """Status response with detailed info."""

    status: str
    graph: dict
    memory: dict
    vessels: dict


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan handler."""
    global _integration

    logger.info("Starting Soul Kiln API server...")

    # Initialize vessels integration
    _integration = VesselsIntegration()
    _integration.initialize()

    logger.info("Soul Kiln API server initialized")
    yield

    # Shutdown
    if _integration:
        _integration.shutdown()
        _integration = None

    logger.info("Soul Kiln API server shutdown")


def create_app() -> FastAPI:
    """Create and configure the FastAPI application."""
    app = FastAPI(
        title="Soul Kiln API",
        description="Virtue Basin Platform API for agent evolution and moral development",
        version="1.0.0",
        lifespan=lifespan,
    )

    # CORS middleware
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    @app.get("/health", response_model=HealthResponse)
    async def health_check():
        """
        Health check endpoint for Railway.

        Returns overall health status and component health.
        """
        components = {}

        # Check FalkorDB/graph connection
        try:
            client = get_client()
            client.query("RETURN 1")
            components["graph"] = {"status": "healthy"}
        except Exception as e:
            components["graph"] = {"status": "unhealthy", "error": str(e)}

        # Check Graphiti (required component)
        if _integration and _integration._graphiti_initialized:
            components["graphiti"] = {"status": "healthy"}
        else:
            components["graphiti"] = {"status": "unhealthy", "error": "Graphiti not initialized"}

        # Check vessels integration
        if _integration and _integration._initialized:
            components["vessels"] = {"status": "healthy"}
        else:
            components["vessels"] = {"status": "initializing"}

        # Overall status
        unhealthy = any(
            c.get("status") == "unhealthy"
            for c in components.values()
        )
        overall_status = "unhealthy" if unhealthy else "healthy"

        return HealthResponse(
            status=overall_status,
            timestamp=datetime.utcnow().isoformat(),
            version="1.0.0",
            components=components,
        )

    @app.get("/status", response_model=StatusResponse)
    async def get_status():
        """Get detailed status information."""
        # Graph stats
        try:
            client = get_client()
            nodes = client.query("MATCH (n) RETURN labels(n), count(*)")
            edges = client.query("MATCH ()-[r]->() RETURN type(r), count(*)")

            graph_stats = {
                "connected": True,
                "nodes": {str(row[0]): row[1] for row in nodes},
                "edges": {str(row[0]): row[1] for row in edges},
            }
        except Exception as e:
            graph_stats = {"connected": False, "error": str(e)}

        # Memory stats
        if _integration:
            memory_stats = _integration.get_status().get("memory", {})
        else:
            memory_stats = {"mode": "not_initialized"}

        # Vessels stats
        if _integration:
            vessels_stats = {
                "initialized": _integration._initialized,
                "graphiti_initialized": _integration._graphiti_initialized,
            }
        else:
            vessels_stats = {"initialized": False}

        return StatusResponse(
            status="running",
            graph=graph_stats,
            memory=memory_stats,
            vessels=vessels_stats,
        )

    @app.get("/")
    async def root():
        """Root endpoint with API info."""
        return {
            "name": "Soul Kiln API",
            "version": "1.0.0",
            "description": "Virtue Basin Platform for agent moral development",
            "docs": "/docs",
            "health": "/health",
            "status": "/status",
        }

    @app.get("/virtues")
    async def list_virtues():
        """List all virtue anchors."""
        try:
            client = get_client()
            result = client.query(
                """
                MATCH (v:VirtueAnchor)
                RETURN v.id, v.name, v.tier, v.activation, v.threshold
                ORDER BY v.tier DESC, v.id
                """
            )

            virtues = []
            for row in result:
                virtues.append({
                    "id": row[0],
                    "name": row[1],
                    "tier": row[2] or "aspirational",
                    "activation": row[3] or 0.0,
                    "threshold": row[4] or 0.80,
                })

            return {"virtues": virtues, "count": len(virtues)}

        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to fetch virtues: {str(e)}",
            )

    @app.get("/agents")
    async def list_agents():
        """List all active agents."""
        try:
            client = get_client()
            result = client.query(
                """
                MATCH (a:Agent)
                WHERE a.status = 'active'
                RETURN a.id, a.type, a.generation, a.coherence_score,
                       a.is_coherent, a.is_growing
                ORDER BY a.coherence_score DESC
                LIMIT 100
                """
            )

            agents = []
            for row in result:
                agents.append({
                    "id": row[0],
                    "type": row[1],
                    "generation": row[2],
                    "coherence_score": row[3],
                    "is_coherent": row[4],
                    "is_growing": row[5],
                })

            return {"agents": agents, "count": len(agents)}

        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to fetch agents: {str(e)}",
            )

    @app.post("/lessons")
    async def store_lesson(
        agent_id: str,
        lesson_type: str,
        content: str,
        virtue_id: str | None = None,
    ):
        """Store a lesson in memory."""
        if not _integration:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Vessels integration not initialized",
            )

        try:
            lesson_id = _integration.remember_lesson(
                agent_id=agent_id,
                lesson_type=lesson_type,
                content=content,
                virtue_id=virtue_id,
            )
            return {"lesson_id": lesson_id, "success": True}
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to store lesson: {str(e)}",
            )

    @app.get("/lessons")
    async def recall_lessons(
        query: str,
        agent_id: str | None = None,
        virtue_id: str | None = None,
        limit: int = 10,
    ):
        """Recall lessons from memory."""
        if not _integration:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Vessels integration not initialized",
            )

        try:
            lessons = _integration.recall_lessons(
                query=query,
                agent_id=agent_id,
                virtue_id=virtue_id,
                limit=limit,
            )
            return {"lessons": lessons, "count": len(lessons)}
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to recall lessons: {str(e)}",
            )

    return app
