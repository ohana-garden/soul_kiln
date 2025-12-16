"""
Graph database client and operations.

Provides FalkorDB client wrapper, schema initialization, and
query utilities for node/edge operations on the virtue topology.
"""

from .client import GraphClient, get_client
from .schema import init_schema, clear_graph
from .queries import (
    create_node,
    create_edge,
    get_neighbors,
    update_edge_weight,
    get_node_activation,
    set_node_activation,
)
