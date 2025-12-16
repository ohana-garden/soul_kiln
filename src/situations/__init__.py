"""Situation modeling - resource allocation scenarios."""
from .builder import SituationBuilder, parse_situation
from .examples import EXAMPLE_SITUATIONS, get_example_situation, list_example_situations
from .persistence import (
    save_situation,
    load_situation,
    list_situations,
    find_similar_situations,
    delete_situation,
)

__all__ = [
    # Building
    "SituationBuilder",
    "parse_situation",
    # Examples
    "EXAMPLE_SITUATIONS",
    "get_example_situation",
    "list_example_situations",
    # Persistence
    "save_situation",
    "load_situation",
    "list_situations",
    "find_similar_situations",
    "delete_situation",
]
