"""
Soul Kiln - Main Entry Point.

Supports both CLI and FastAPI server modes for Railway deployment.
"""

import sys
import os
import logging

# Add src directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    level=os.getenv("LOG_LEVEL", "INFO"),
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)

logger = logging.getLogger(__name__)


def create_app():
    """Create and configure the FastAPI application."""
    from fastapi import FastAPI
    from fastapi.middleware.cors import CORSMiddleware

    from transport.server import TransportServer, create_fastapi_app
    from graph.client import get_client

    # Create transport server
    server = TransportServer()

    # Create FastAPI app from transport server
    app = create_fastapi_app(server)

    # Override app metadata
    app.title = "Soul Kiln"
    app.description = "Virtue Basin Cognitive Architecture - Theatre API"
    app.version = "1.0.0"

    @app.on_event("startup")
    async def startup():
        """Initialize on startup."""
        logger.info("Starting Soul Kiln...")

        # Check FalkorDB connection
        try:
            client = get_client()
            logger.info("Connected to FalkorDB")
        except Exception as e:
            logger.warning(f"FalkorDB not available: {e}")
            logger.info("Running in limited mode without graph database")

    @app.on_event("shutdown")
    async def shutdown():
        """Cleanup on shutdown."""
        logger.info("Shutting down Soul Kiln...")

    @app.get("/")
    async def root():
        """Root endpoint."""
        return {
            "name": "Soul Kiln",
            "version": "1.0.0",
            "description": "Virtue Basin Cognitive Architecture",
            "docs": "/docs",
            "health": "/health",
        }

    @app.get("/api/virtues")
    async def list_virtues():
        """List all 19 virtues."""
        from virtues.anchors import VIRTUES
        from virtues.tiers import get_virtue_threshold, is_foundation

        return {
            "virtues": [
                {
                    "id": v["id"],
                    "name": v["name"],
                    "essence": v["essence"],
                    "tier": "foundation" if is_foundation(v["id"]) else "aspirational",
                    "threshold": get_virtue_threshold(v["id"]),
                }
                for v in VIRTUES
            ]
        }

    @app.get("/api/graph/status")
    async def graph_status():
        """Get graph database status."""
        try:
            client = get_client()
            # Simple query to check connectivity
            result = client.query("MATCH (n) RETURN count(n) as count LIMIT 1")
            count = result[0][0] if result else 0
            return {
                "status": "connected",
                "node_count": count,
            }
        except Exception as e:
            return {
                "status": "disconnected",
                "error": str(e),
            }

    return app


# Create app instance for uvicorn
app = create_app()


# CLI entry point
if __name__ == "__main__":
    from cli.commands import cli
    cli()
