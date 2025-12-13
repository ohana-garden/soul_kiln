"""
Seed Data Module.

Contains scripts to populate the graph with initial data
including agent types, virtues, kuleanas, beliefs, taboos,
voice patterns, prompts, and tools.
"""
from .ambassador import seed_ambassador
from .core import seed_core_data

__all__ = [
    "seed_ambassador",
    "seed_core_data",
]
