"""
Topology evolution module for the Virtue Basin Simulator.

Implements evolutionary search for valid soul topologies using:
- Population management
- Selection operators
- Crossover operators
- Mutation operators
- Generational evolution loop
- Topology evaluation
"""

from src.evolution.population import Population, Individual
from src.evolution.selection import Selection
from src.evolution.crossover import Crossover
from src.evolution.mutation import Mutation
from src.evolution.loop import EvolutionLoop, TopologyEvaluator

__all__ = [
    "Population",
    "Individual",
    "Selection",
    "Crossover",
    "Mutation",
    "EvolutionLoop",
    "TopologyEvaluator",
]
