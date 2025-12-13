"""
Graph module - Single source of truth for the platform.

All agent definitions, prompts, tools, and behavioral configurations
are stored in and loaded from the FalkorDB graph.
"""
from .client import GraphClient, get_client, reset_client, is_using_mock
from .schema import init_schema, clear_graph, get_schema_version, SCHEMA_VERSION
from .connection import GraphConnection, get_graph
from .queries import (
    create_node,
    create_edge,
    get_neighbors,
    update_edge_weight,
    get_node_activation,
    set_node_activation,
)

__all__ = [
    # Client
    "GraphClient",
    "get_client",
    "reset_client",
    "is_using_mock",
    # Connection
    "GraphConnection",
    "get_graph",
    # Schema
    "init_schema",
    "clear_graph",
    "get_schema_version",
    "SCHEMA_VERSION",
    # Queries
    "create_node",
    "create_edge",
    "get_neighbors",
    "update_edge_weight",
    "get_node_activation",
    "set_node_activation",
]
