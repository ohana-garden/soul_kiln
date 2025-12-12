"""
Graph substrate module for the Virtue Basin Simulator.

Provides FalkorDB/Graphiti integration and node/edge management.
"""

from src.graph.substrate import GraphSubstrate
from src.graph.nodes import NodeManager
from src.graph.edges import EdgeManager
from src.graph.virtues import VirtueManager, VIRTUE_DEFINITIONS

__all__ = [
    "GraphSubstrate",
    "NodeManager",
    "EdgeManager",
    "VirtueManager",
    "VIRTUE_DEFINITIONS",
]
