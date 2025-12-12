#!/usr/bin/env python3
"""
Initialize the FalkorDB database with virtue anchors.

Usage:
    python -m scripts.init_db [--host HOST] [--port PORT]
"""

import argparse
import logging
import sys

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def main():
    """Initialize the database."""
    parser = argparse.ArgumentParser(description="Initialize virtue basin database")
    parser.add_argument("--host", default="localhost", help="FalkorDB host")
    parser.add_argument("--port", type=int, default=6379, help="FalkorDB port")
    parser.add_argument("--graph", default="virtue_basin", help="Graph name")
    parser.add_argument("--clear", action="store_true", help="Clear existing data")
    args = parser.parse_args()

    try:
        from src.graph.substrate import GraphSubstrate
        from src.graph.nodes import NodeManager
        from src.graph.edges import EdgeManager
        from src.graph.virtues import VirtueManager

        # Connect to database
        logger.info(f"Connecting to FalkorDB at {args.host}:{args.port}")
        substrate = GraphSubstrate(host=args.host, port=args.port, graph_name=args.graph)
        substrate.connect()

        if args.clear:
            logger.info("Clearing existing data...")
            substrate.clear_graph()

        # Initialize managers
        node_manager = NodeManager(substrate)
        edge_manager = EdgeManager(substrate)
        virtue_manager = VirtueManager(substrate)

        # Initialize virtues
        logger.info("Initializing virtue anchor nodes...")
        virtues = virtue_manager.initialize_virtues()
        logger.info(f"Created {len(virtues)} virtue anchors")

        # Initialize virtue relationships
        logger.info("Initializing virtue relationships...")
        edges = virtue_manager.initialize_virtue_relationships(edge_manager)
        logger.info(f"Created {edges} relationship edges")

        # Report status
        logger.info(f"Database initialized successfully!")
        logger.info(f"  Nodes: {substrate.node_count()}")
        logger.info(f"  Edges: {substrate.edge_count()}")

        substrate.disconnect()
        return 0

    except Exception as e:
        logger.error(f"Failed to initialize database: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
