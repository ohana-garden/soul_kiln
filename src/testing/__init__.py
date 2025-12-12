"""
Alignment testing module for the Virtue Basin Simulator.

Provides:
- Stimulus generation
- Trajectory tracking
- Alignment scoring
- Character profiling
"""

from src.testing.stimuli import StimulusGenerator
from src.testing.trajectory import TrajectoryTracker
from src.testing.alignment import AlignmentTester
from src.testing.character import CharacterProfiler

__all__ = [
    "StimulusGenerator",
    "TrajectoryTracker",
    "AlignmentTester",
    "CharacterProfiler",
]
