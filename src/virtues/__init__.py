"""
Virtue anchor definitions and management.

Provides virtue topology with foundation and aspirational tiers,
affinity relationships between virtues, and initialization utilities.
"""

from .anchors import VIRTUES, AFFINITIES, init_virtues, get_virtue_degrees
from .tiers import (
    FOUNDATION, ASPIRATIONAL, is_foundation, is_aspirational,
    get_all_virtues, get_virtue_tier, get_tier_threshold
)
