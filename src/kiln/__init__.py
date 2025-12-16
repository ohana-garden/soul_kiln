"""
Kiln simulation loop.

Core simulation engine that runs virtue basin dynamics, applying
spread functions and selection mechanisms over topology states.
"""

from .loop import run_kiln
from .selection import select_survivors
