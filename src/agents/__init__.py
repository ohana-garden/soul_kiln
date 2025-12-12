"""
Agent management module for the Virtue Basin Simulator.

Provides:
- Agent 0 (simulator controller)
- Candidate soul agents
- Shared memory management
"""

from src.agents.controller import SimulatorController
from src.agents.candidate import CandidateAgent
from src.agents.memory import SharedMemory

__all__ = [
    "SimulatorController",
    "CandidateAgent",
    "SharedMemory",
]
