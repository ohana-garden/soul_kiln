#!/usr/bin/env python3
"""
Run all seed scripts to populate the graph database.

Usage:
    python -m src.seed.run_seed
"""
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from src.graph import init_schema
from src.seed.core import seed_core_data
from src.seed.ambassador import seed_ambassador


def run_all_seeds():
    """Run all seed scripts in order."""
    print("=" * 50)
    print("Soul Kiln - Graph Seed Runner")
    print("=" * 50)

    print("\n1. Initializing schema...")
    init_schema()
    print("   Schema initialized.")

    print("\n2. Seeding core data...")
    seed_core_data()

    print("\n3. Seeding Ambassador agent...")
    seed_ambassador()

    print("\n" + "=" * 50)
    print("Seeding complete!")
    print("=" * 50)


if __name__ == "__main__":
    run_all_seeds()
