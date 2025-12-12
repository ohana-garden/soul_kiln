"""
Virtue Basin Simulator

A self-optimizing system that discovers valid moral topologies through 
evolutionary simulation. The simulator generates "soul templates" - graph 
structures that guarantee agent alignment through geometric constraint 
rather than rule enforcement.

Core Hypothesis:
- Thoughts are strange attractors
- Virtues are basins
- Love is gravitational
"""

__version__ = "0.1.0"

from .basin import BasinAttractor
from .topology import VirtueTopology, SoulTemplate
from .simulator import VirtueSimulator
from .forces import GravitationalForce

__all__ = [
    "BasinAttractor",
    "VirtueTopology",
    "SoulTemplate",
    "VirtueSimulator",
    "GravitationalForce",
]
