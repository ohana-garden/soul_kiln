"""
API module for the Virtue Basin Simulator.

Provides:
- Configuration management
- Metrics export
- Soul template API
"""

from src.api.config import Config, load_config
from src.api.metrics import MetricsCollector
from src.api.templates import TemplateManager

__all__ = [
    "Config",
    "load_config",
    "MetricsCollector",
    "TemplateManager",
]
