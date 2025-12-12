"""
Agent management module for the Virtue Basin Simulator.

Provides:
- Agent 0 (simulator controller)
- Candidate soul agents
- Shared memory management
- Hawaiian garden plant agents
"""

from src.agents.controller import SimulatorController
from src.agents.candidate import CandidateAgent
from src.agents.memory import SharedMemory
from src.agents.plants import (
    PlantAgent,
    PlantGarden,
    PlantArchetype,
    PlantDefinition,
    PlantPersonality,
    ALL_PLANTS,
    PLANT_REGISTRY,
    create_plant_agent,
    create_all_plant_agents,
    create_full_garden,
)

__all__ = [
    "SimulatorController",
    "CandidateAgent",
    "SharedMemory",
    "PlantAgent",
    "PlantGarden",
    "PlantArchetype",
    "PlantDefinition",
    "PlantPersonality",
    "ALL_PLANTS",
    "PLANT_REGISTRY",
    "create_plant_agent",
    "create_all_plant_agents",
    "create_full_garden",
]
