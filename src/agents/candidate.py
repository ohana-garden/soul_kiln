"""
Candidate soul agents for the Virtue Basin Simulator.

Each candidate has a unique topology (edge weight configuration)
while sharing access to the virtue anchors.
"""

import logging
import uuid
from datetime import datetime

from src.evolution.population import Individual
from src.models import Edge, Topology

logger = logging.getLogger(__name__)


class CandidateAgent:
    """
    A candidate soul agent in the simulation.

    Each candidate represents a potential soul topology being tested
    for alignment. Candidates share access to virtue anchors but have
    isolated edge weight configurations.
    """

    def __init__(
        self,
        topology: Individual | None = None,
        agent_id: str | None = None,
    ):
        """
        Initialize a candidate agent.

        Args:
            topology: Optional topology (Individual from evolution)
            agent_id: Optional agent ID
        """
        self.id = agent_id or f"candidate_{uuid.uuid4().hex[:8]}"
        self.topology = topology or Individual(id=self.id)
        self.created_at = datetime.utcnow()
        self.generation = self.topology.generation if topology else 0
        self._fitness: float | None = None
        self._alignment_result: dict | None = None

    @classmethod
    def from_individual(cls, individual: Individual) -> "CandidateAgent":
        """
        Create a candidate from an evolution Individual.

        Args:
            individual: The Individual from evolution

        Returns:
            CandidateAgent wrapping the individual
        """
        return cls(topology=individual, agent_id=individual.id)

    @classmethod
    def from_parents(
        cls,
        parent1: "CandidateAgent",
        parent2: "CandidateAgent",
        crossover_fn,
    ) -> "CandidateAgent":
        """
        Create a candidate through crossover of two parents.

        Args:
            parent1: First parent candidate
            parent2: Second parent candidate
            crossover_fn: Crossover function

        Returns:
            Child CandidateAgent
        """
        child_topology = crossover_fn(parent1.topology, parent2.topology)
        return cls(topology=child_topology)

    def get_edge(self, source_id: str, target_id: str) -> Edge | None:
        """Get an edge from this candidate's topology."""
        return self.topology.get_edge(source_id, target_id)

    def set_edge(self, edge: Edge) -> None:
        """Set an edge in this candidate's topology."""
        self.topology.set_edge(edge)

    def get_edge_weight(self, source_id: str, target_id: str) -> float:
        """Get the weight of an edge."""
        edge = self.get_edge(source_id, target_id)
        return edge.weight if edge else 0.0

    def set_fitness(self, fitness: float, alignment_result: dict | None = None) -> None:
        """
        Set the fitness score for this candidate.

        Args:
            fitness: Alignment fitness score
            alignment_result: Optional full alignment result
        """
        self._fitness = fitness
        self.topology.fitness = fitness
        if alignment_result:
            self._alignment_result = alignment_result
            self.topology.alignment_result = alignment_result

    @property
    def fitness(self) -> float | None:
        """Get the fitness score."""
        return self._fitness

    @property
    def alignment_result(self) -> dict | None:
        """Get the full alignment result."""
        return self._alignment_result

    def is_valid(self, min_score: float = 0.95) -> bool:
        """
        Check if this candidate meets alignment threshold.

        Args:
            min_score: Minimum alignment score

        Returns:
            True if valid (aligned), False otherwise
        """
        return self._fitness is not None and self._fitness >= min_score

    def get_virtue_degrees(self) -> dict[str, int]:
        """Get degrees for all virtue nodes."""
        return self.topology.get_virtue_degrees()

    def get_character_signature(self) -> dict[str, float]:
        """Get the character signature from alignment result."""
        if self._alignment_result:
            return self._alignment_result.get("character_signature", {})
        return {}

    def clone(self) -> "CandidateAgent":
        """Create a clone of this candidate."""
        cloned = CandidateAgent(
            topology=self.topology.clone(),
            agent_id=f"candidate_{uuid.uuid4().hex[:8]}",
        )
        cloned.generation = self.generation + 1
        return cloned

    def to_topology(self) -> Topology:
        """Convert to a Topology model object."""
        return self.topology.to_topology()

    def export(self) -> dict:
        """Export candidate state as dictionary."""
        return {
            "id": self.id,
            "generation": self.generation,
            "fitness": self._fitness,
            "edges": [
                {
                    "source": e.source_id,
                    "target": e.target_id,
                    "weight": e.weight,
                }
                for e in self.topology.edges.values()
            ],
            "virtue_degrees": self.get_virtue_degrees(),
            "character_signature": self.get_character_signature(),
            "created_at": self.created_at.isoformat(),
            "is_valid": self.is_valid(),
        }

    def __repr__(self) -> str:
        return (
            f"CandidateAgent(id={self.id}, gen={self.generation}, "
            f"fitness={self._fitness}, edges={len(self.topology.edges)})"
        )


class CandidatePool:
    """
    Pool of candidate agents for batch operations.

    Manages creation, evaluation, and lifecycle of candidates.
    """

    def __init__(self, max_size: int = 100):
        """
        Initialize the candidate pool.

        Args:
            max_size: Maximum pool size
        """
        self.max_size = max_size
        self._candidates: dict[str, CandidateAgent] = {}
        self._generation = 0

    def add(self, candidate: CandidateAgent) -> bool:
        """
        Add a candidate to the pool.

        Args:
            candidate: The candidate to add

        Returns:
            True if added, False if pool full
        """
        if len(self._candidates) >= self.max_size:
            return False
        self._candidates[candidate.id] = candidate
        return True

    def remove(self, candidate_id: str) -> bool:
        """
        Remove a candidate from the pool.

        Args:
            candidate_id: ID of candidate to remove

        Returns:
            True if removed, False if not found
        """
        if candidate_id in self._candidates:
            del self._candidates[candidate_id]
            return True
        return False

    def get(self, candidate_id: str) -> CandidateAgent | None:
        """Get a candidate by ID."""
        return self._candidates.get(candidate_id)

    def get_all(self) -> list[CandidateAgent]:
        """Get all candidates."""
        return list(self._candidates.values())

    def get_by_fitness(self, n: int = 10, ascending: bool = False) -> list[CandidateAgent]:
        """
        Get top N candidates by fitness.

        Args:
            n: Number of candidates
            ascending: Sort ascending (worst first) if True

        Returns:
            List of candidates sorted by fitness
        """
        sorted_candidates = sorted(
            self._candidates.values(),
            key=lambda c: c.fitness or 0.0,
            reverse=not ascending,
        )
        return sorted_candidates[:n]

    def get_valid(self, min_score: float = 0.95) -> list[CandidateAgent]:
        """Get all valid (aligned) candidates."""
        return [c for c in self._candidates.values() if c.is_valid(min_score)]

    def advance_generation(self) -> None:
        """Advance to the next generation."""
        self._generation += 1

    @property
    def generation(self) -> int:
        """Current generation."""
        return self._generation

    @property
    def size(self) -> int:
        """Current pool size."""
        return len(self._candidates)

    def clear(self) -> None:
        """Clear all candidates."""
        self._candidates.clear()
