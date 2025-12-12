"""
Population management for topology evolution.

Manages a population of candidate soul topologies,
each represented as a set of edges with weights.
"""

import logging
import random
import uuid
from dataclasses import dataclass, field
from datetime import datetime

from src.constants import (
    NUM_VIRTUES,
    POPULATION_SIZE,
    TARGET_CONNECTIVITY,
)
from src.graph.virtues import VIRTUE_DEFINITIONS
from src.models import Edge, EdgeDirection, Topology

logger = logging.getLogger(__name__)


@dataclass
class Individual:
    """
    An individual in the evolution population.

    Represents a candidate soul topology with its edges and fitness.
    """
    id: str
    edges: dict[str, Edge] = field(default_factory=dict)  # edge_key -> Edge
    fitness: float = 0.0
    generation: int = 0
    parent_ids: list[str] = field(default_factory=list)
    alignment_result: dict = field(default_factory=dict)
    created_at: datetime = field(default_factory=datetime.utcnow)

    def get_edge(self, source_id: str, target_id: str) -> Edge | None:
        """Get an edge by source and target."""
        key = f"{source_id}->{target_id}"
        return self.edges.get(key)

    def set_edge(self, edge: Edge) -> None:
        """Add or update an edge."""
        key = f"{edge.source_id}->{edge.target_id}"
        self.edges[key] = edge

    def remove_edge(self, source_id: str, target_id: str) -> bool:
        """Remove an edge."""
        key = f"{source_id}->{target_id}"
        if key in self.edges:
            del self.edges[key]
            return True
        return False

    def get_node_degree(self, node_id: str) -> int:
        """Get the degree of a node."""
        degree = 0
        for key in self.edges:
            source, target = key.split("->")
            if source == node_id or target == node_id:
                degree += 1
        return degree

    def get_virtue_degrees(self) -> dict[str, int]:
        """Get degrees for all virtue nodes."""
        degrees = {}
        for virtue_def in VIRTUE_DEFINITIONS:
            degrees[virtue_def.id] = self.get_node_degree(virtue_def.id)
        return degrees

    def to_topology(self) -> Topology:
        """Convert to a Topology object."""
        return Topology(
            id=self.id,
            agent_id=self.id,
            virtue_degrees=self.get_virtue_degrees(),
            total_edges=len(self.edges),
            alignment_score=self.fitness,
            character_signature=self.alignment_result.get("character_signature", {}),
            generation=self.generation,
        )

    def clone(self) -> "Individual":
        """Create a deep copy of this individual."""
        new_edges = {
            k: Edge(
                source_id=e.source_id,
                target_id=e.target_id,
                weight=e.weight,
                direction=e.direction,
            )
            for k, e in self.edges.items()
        }
        return Individual(
            id=f"ind_{uuid.uuid4().hex[:8]}",
            edges=new_edges,
            fitness=0.0,  # Reset fitness
            generation=self.generation + 1,
            parent_ids=[self.id],
        )


class Population:
    """
    Manages a population of candidate soul topologies.

    Handles initialization, evaluation, and access to individuals.
    """

    def __init__(
        self,
        size: int = POPULATION_SIZE,
        concept_nodes: list[str] | None = None,
    ):
        """
        Initialize the population.

        Args:
            size: Population size
            concept_nodes: List of concept node IDs (optional)
        """
        self.size = size
        self.concept_nodes = concept_nodes or []
        self.individuals: list[Individual] = []
        self.generation = 0
        self._best_fitness_history: list[float] = []

    def initialize_random(self) -> None:
        """
        Initialize population with random topologies.

        Each topology has virtue anchors connected randomly.
        """
        self.individuals.clear()
        virtue_ids = [v.id for v in VIRTUE_DEFINITIONS]
        all_nodes = virtue_ids + self.concept_nodes

        for i in range(self.size):
            individual = self._create_random_individual(virtue_ids, all_nodes)
            individual.generation = 0
            self.individuals.append(individual)

        logger.info(f"Initialized population with {self.size} random individuals")

    def _create_random_individual(
        self,
        virtue_ids: list[str],
        all_nodes: list[str],
    ) -> Individual:
        """
        Create a random individual.

        Args:
            virtue_ids: List of virtue node IDs
            all_nodes: List of all node IDs

        Returns:
            Random Individual
        """
        individual = Individual(id=f"ind_{uuid.uuid4().hex[:8]}")

        # Create edges to ensure minimum connectivity for virtues
        for virtue_id in virtue_ids:
            # Connect to related virtues (from definitions)
            virtue_def = next(v for v in VIRTUE_DEFINITIONS if v.id == virtue_id)
            for related_id in virtue_def.key_relationships:
                edge = Edge(
                    source_id=virtue_id,
                    target_id=related_id,
                    weight=random.uniform(0.3, 0.7),
                )
                individual.set_edge(edge)

            # Add random additional edges
            num_extra = random.randint(1, 4)
            candidates = [n for n in all_nodes if n != virtue_id]
            for _ in range(num_extra):
                if candidates:
                    target = random.choice(candidates)
                    edge = Edge(
                        source_id=virtue_id,
                        target_id=target,
                        weight=random.uniform(0.2, 0.8),
                    )
                    individual.set_edge(edge)

        # Add some random concept-to-concept or concept-to-virtue edges
        if self.concept_nodes:
            num_concept_edges = random.randint(10, 30)
            for _ in range(num_concept_edges):
                source = random.choice(self.concept_nodes)
                target = random.choice(all_nodes)
                if source != target:
                    edge = Edge(
                        source_id=source,
                        target_id=target,
                        weight=random.uniform(0.1, 0.6),
                    )
                    individual.set_edge(edge)

        return individual

    def add_individual(self, individual: Individual) -> None:
        """Add an individual to the population."""
        self.individuals.append(individual)

    def get_best(self, n: int = 1) -> list[Individual]:
        """
        Get the n best individuals by fitness.

        Args:
            n: Number of individuals to return

        Returns:
            List of best individuals
        """
        sorted_inds = sorted(self.individuals, key=lambda x: x.fitness, reverse=True)
        return sorted_inds[:n]

    def get_worst(self, n: int = 1) -> list[Individual]:
        """
        Get the n worst individuals by fitness.

        Args:
            n: Number of individuals to return

        Returns:
            List of worst individuals
        """
        sorted_inds = sorted(self.individuals, key=lambda x: x.fitness)
        return sorted_inds[:n]

    def get_by_id(self, individual_id: str) -> Individual | None:
        """Get an individual by ID."""
        for ind in self.individuals:
            if ind.id == individual_id:
                return ind
        return None

    def replace(self, old_individuals: list[Individual], new_individuals: list[Individual]) -> None:
        """
        Replace old individuals with new ones.

        Args:
            old_individuals: Individuals to remove
            new_individuals: Individuals to add
        """
        old_ids = {ind.id for ind in old_individuals}
        self.individuals = [ind for ind in self.individuals if ind.id not in old_ids]
        self.individuals.extend(new_individuals)

    def advance_generation(self) -> None:
        """Advance to the next generation."""
        self.generation += 1
        best = self.get_best(1)
        if best:
            self._best_fitness_history.append(best[0].fitness)

    def get_fitness_stats(self) -> dict:
        """
        Get population fitness statistics.

        Returns:
            Dict with fitness statistics
        """
        if not self.individuals:
            return {"min": 0.0, "max": 0.0, "mean": 0.0, "std": 0.0}

        fitnesses = [ind.fitness for ind in self.individuals]
        mean = sum(fitnesses) / len(fitnesses)
        variance = sum((f - mean) ** 2 for f in fitnesses) / len(fitnesses)

        return {
            "min": min(fitnesses),
            "max": max(fitnesses),
            "mean": mean,
            "std": variance ** 0.5,
            "generation": self.generation,
        }

    def get_best_fitness_history(self) -> list[float]:
        """Get history of best fitness per generation."""
        return list(self._best_fitness_history)

    def export_best(self) -> dict:
        """
        Export the best individual as a dictionary.

        Returns:
            Dict with topology specification
        """
        best = self.get_best(1)
        if not best:
            return {}

        ind = best[0]
        return {
            "id": ind.id,
            "edges": [
                {
                    "source": e.source_id,
                    "target": e.target_id,
                    "weight": e.weight,
                }
                for e in ind.edges.values()
            ],
            "fitness": ind.fitness,
            "generation": ind.generation,
            "virtue_degrees": ind.get_virtue_degrees(),
            "alignment_result": ind.alignment_result,
        }
