"""Gestalt computation - holistic character from topology."""
from .compute import compute_gestalt, get_gestalt
from .tendencies import compute_tendencies, TENDENCY_DEFINITIONS

__all__ = [
    "compute_gestalt",
    "get_gestalt",
    "compute_tendencies",
    "TENDENCY_DEFINITIONS",
]
