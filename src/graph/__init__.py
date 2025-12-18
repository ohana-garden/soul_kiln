"""
Graph module for Virtue Basin Platform.

Provides:
- GraphStore protocol for unified graph access
- GraphClient singleton for simple queries
- GraphSubstrate for connection-managed operations
- Safe parsing utilities (no eval)
"""

from .client import GraphClient, get_client, reset_client
from .store import GraphStore, MockGraphStore, get_store
from .schema import init_schema, clear_graph
from .safe_parse import safe_parse_dict, safe_parse_list, serialize_for_storage
from .queries import (
    create_node,
    create_edge,
    get_neighbors,
    update_edge_weight,
    get_node_activation,
    set_node_activation,
)
from .moral_geometry import (
    MoralGeometryAnalyzer,
    GeometrySnapshot,
    VirtueTriad,
    BridgeNode,
    BasinTopology,
    ResonancePattern,
    MoralGeodesic,
    get_geometry_analyzer,
)

__all__ = [
    # Client
    "GraphClient",
    "get_client",
    "reset_client",
    # Store interface
    "GraphStore",
    "MockGraphStore",
    "get_store",
    # Schema
    "init_schema",
    "clear_graph",
    # Safe parsing
    "safe_parse_dict",
    "safe_parse_list",
    "serialize_for_storage",
    # Queries
    "create_node",
    "create_edge",
    "get_neighbors",
    "update_edge_weight",
    "get_node_activation",
    "set_node_activation",
    # Geometry
    "MoralGeometryAnalyzer",
    "GeometrySnapshot",
    "VirtueTriad",
    "BridgeNode",
    "BasinTopology",
    "ResonancePattern",
    "MoralGeodesic",
    "get_geometry_analyzer",
]
