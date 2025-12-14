"""Situation modeling - resource allocation scenarios."""
from .builder import SituationBuilder
from .examples import EXAMPLE_SITUATIONS, get_example_situation

__all__ = [
    "SituationBuilder",
    "EXAMPLE_SITUATIONS",
    "get_example_situation",
]
