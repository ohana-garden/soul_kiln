"""
Mutation operators for topology evolution.

Applies random mutations to topologies to explore new regions
of the search space.
"""

import logging
import random

from src.constants import MUTATION_RATE, TARGET_CONNECTIVITY
from src.evolution.population import Individual
from src.graph.virtues import VIRTUE_DEFINITIONS
from src.models import Edge

logger = logging.getLogger(__name__)


class Mutation:
    """
    Mutation operators for genetic variation.

    Applies random changes to topology edges to enable exploration
    of the search space.
    """

    def __init__(self, mutation_rate: float = MUTATION_RATE):
        """
        Initialize mutation operators.

        Args:
            mutation_rate: Probability of each mutation type
        """
        self.mutation_rate = mutation_rate

    def mutate(self, individual: Individual) -> Individual:
        """
        Apply mutations to an individual.

        Args:
            individual: The individual to mutate

        Returns:
            The mutated individual (modified in place)
        """
        # Weight perturbation
        self._mutate_weights(individual)

        # Edge addition
        if random.random() < self.mutation_rate:
            self._add_random_edge(individual)

        # Edge removal
        if random.random() < self.mutation_rate:
            self._remove_random_edge(individual)

        return individual

    def _mutate_weights(self, individual: Individual) -> int:
        """
        Apply weight perturbations to edges.

        Args:
            individual: The individual to mutate

        Returns:
            Number of edges mutated
        """
        mutated = 0
        for edge in list(individual.edges.values()):
            if random.random() < self.mutation_rate:
                # Gaussian perturbation
                delta = random.gauss(0, 0.1)
                new_weight = max(0.0, min(1.0, edge.weight + delta))
                edge.weight = new_weight
                mutated += 1

        return mutated

    def _add_random_edge(self, individual: Individual) -> bool:
        """
        Add a random edge.

        Args:
            individual: The individual to mutate

        Returns:
            True if edge was added
        """
        # Collect all possible nodes
        virtue_ids = [v.id for v in VIRTUE_DEFINITIONS]

        # Get concept nodes from existing edges
        concept_ids = set()
        for edge in individual.edges.values():
            if edge.source_id not in virtue_ids:
                concept_ids.add(edge.source_id)
            if edge.target_id not in virtue_ids:
                concept_ids.add(edge.target_id)

        all_nodes = virtue_ids + list(concept_ids)

        if len(all_nodes) < 2:
            return False

        # Try to find a new edge
        for _ in range(10):  # Max 10 attempts
            source = random.choice(all_nodes)
            target = random.choice(all_nodes)

            if source == target:
                continue

            key = f"{source}->{target}"
            if key not in individual.edges:
                edge = Edge(
                    source_id=source,
                    target_id=target,
                    weight=random.uniform(0.1, 0.5),
                )
                individual.set_edge(edge)
                return True

        return False

    def _remove_random_edge(self, individual: Individual) -> bool:
        """
        Remove a random edge (respecting min degree).

        Args:
            individual: The individual to mutate

        Returns:
            True if edge was removed
        """
        if not individual.edges:
            return False

        # Find edges that can be safely removed
        removable = []
        for key, edge in individual.edges.items():
            if not self._would_violate_min_degree(individual, edge):
                removable.append(key)

        if not removable:
            return False

        # Remove a random removable edge
        key = random.choice(removable)
        edge = individual.edges[key]
        individual.remove_edge(edge.source_id, edge.target_id)
        return True

    def _would_violate_min_degree(self, individual: Individual, edge: Edge) -> bool:
        """
        Check if removing an edge would violate min degree constraint.

        Args:
            individual: The individual
            edge: The edge to potentially remove

        Returns:
            True if removal would violate constraint
        """
        virtue_ids = {v.id for v in VIRTUE_DEFINITIONS}

        # Check source node
        if edge.source_id in virtue_ids:
            degree = individual.get_node_degree(edge.source_id)
            if degree <= TARGET_CONNECTIVITY:
                return True

        # Check target node
        if edge.target_id in virtue_ids:
            degree = individual.get_node_degree(edge.target_id)
            if degree <= TARGET_CONNECTIVITY:
                return True

        return False

    def aggressive_mutate(self, individual: Individual) -> Individual:
        """
        Apply more aggressive mutations.

        Used when population diversity is low.

        Args:
            individual: The individual to mutate

        Returns:
            The mutated individual
        """
        # Higher mutation rate for this call
        saved_rate = self.mutation_rate
        self.mutation_rate = min(0.5, self.mutation_rate * 3)

        # Apply standard mutations multiple times
        for _ in range(3):
            self.mutate(individual)

        # Restore original rate
        self.mutation_rate = saved_rate

        return individual

    def adaptive_mutate(
        self,
        individual: Individual,
        fitness_rank: float,
    ) -> Individual:
        """
        Adaptive mutation - higher fitness = lower mutation rate.

        Args:
            individual: The individual to mutate
            fitness_rank: Normalized fitness rank (0 = worst, 1 = best)

        Returns:
            The mutated individual
        """
        # Adaptive rate: lower fitness -> higher mutation
        adaptive_rate = self.mutation_rate * (2.0 - fitness_rank)
        saved_rate = self.mutation_rate
        self.mutation_rate = adaptive_rate

        self.mutate(individual)

        self.mutation_rate = saved_rate
        return individual

    def topology_preserving_mutate(self, individual: Individual) -> Individual:
        """
        Mutation that preserves overall topology structure.

        Only mutates weights, doesn't add/remove edges.

        Args:
            individual: The individual to mutate

        Returns:
            The mutated individual
        """
        self._mutate_weights(individual)
        return individual

    def batch_mutate(self, individuals: list[Individual]) -> list[Individual]:
        """
        Apply mutations to multiple individuals.

        Args:
            individuals: List of individuals to mutate

        Returns:
            List of mutated individuals
        """
        for individual in individuals:
            self.mutate(individual)
        return individuals

    def directed_mutate(
        self,
        individual: Individual,
        weak_virtues: list[str],
    ) -> Individual:
        """
        Directed mutation to strengthen weak virtue connections.

        Args:
            individual: The individual to mutate
            weak_virtues: List of virtue IDs needing more connections

        Returns:
            The mutated individual
        """
        virtue_ids = [v.id for v in VIRTUE_DEFINITIONS]
        all_nodes = set()
        for edge in individual.edges.values():
            all_nodes.add(edge.source_id)
            all_nodes.add(edge.target_id)
        all_nodes = list(all_nodes)

        for weak_virtue in weak_virtues:
            # Add edge to this virtue
            candidates = [n for n in all_nodes if n != weak_virtue]
            if candidates:
                target = random.choice(candidates)
                edge = Edge(
                    source_id=weak_virtue,
                    target_id=target,
                    weight=random.uniform(0.4, 0.8),
                )
                individual.set_edge(edge)

                # Also add reverse edge
                edge_rev = Edge(
                    source_id=target,
                    target_id=weak_virtue,
                    weight=random.uniform(0.4, 0.8),
                )
                individual.set_edge(edge_rev)

        return individual
