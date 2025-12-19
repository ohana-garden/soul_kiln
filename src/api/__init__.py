"""
Soul Kiln API Module.

Provides HTTP API for Railway deployment and external integrations.
"""

from .server import create_app

__all__ = ["create_app"]
