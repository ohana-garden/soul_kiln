"""
Shared utilities for Soul Kiln.

Contains canonical implementations of commonly used functions
to avoid duplication across modules.
"""

from .activation import sigmoid, tanh
from .config import get_config, load_config

__all__ = ["sigmoid", "tanh", "get_config", "load_config"]
