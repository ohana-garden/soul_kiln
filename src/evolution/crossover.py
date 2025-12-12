"""
Crossover operators for topology evolution.

Combines parent topologies to produce offspring,
inheriting edges from both parents.
"""

import logging
import random
import uuid

from src.constants import CROSSOVER_RATE
from src.evolution.population import Individual
from src.graph.virtues import VIRTUE_DEFINITIONS
from src.models import Edge

logger = logging.getLogger(__name__)


class Crossover:
    """
    Crossover operators for genetic recombination.

    Creates child topologies by combining edges from two parents.
    """

    def __init__(self, crossover_rate: float = CROSSOVER_RATE):
        """
        Initialize crossover operators.

        Args:
            crossover_rate: Probability of inheriting edges from single parent
        """
        self.crossover_rate = crossover_rate

    def crossover(
        self,
        parent1: Individual,
        parent2: Individual,
        method: str = "uniform",
    ) -> Individual:
        """
        Create a child from two parents.

        Args:
            parent1: First parent
            parent2: Second parent
            method: Crossover method ("uniform", "single_point", "virtue_based")

        Returns:
            Child individual
        """
        if method == "uniform":
            return self.uniform_crossover(parent1, parent2)
        elif method == "single_point":
            return self.single_point_crossover(parent1, parent2)
        elif method == "virtue_based":
            return self.virtue_based_crossover(parent1, parent2)
        else:
            raise ValueError(f"Unknown crossover method: {method}")

    def uniform_crossover(
        self,
        parent1: Individual,
        parent2: Individual,
    ) -> Individual:
        """
        Uniform crossover - each edge inherited probabilistically.

        Args:
            parent1: First parent
            parent2: Second parent

        Returns:
            Child individual
        """
        child = Individual(
            id=f"ind_{uuid.uuid4().hex[:8]}",
            generation=max(parent1.generation, parent2.generation) + 1,
            parent_ids=[parent1.id, parent2.id],
        )

        # Collect all edges from both parents
        all_edge_keys = set(parent1.edges.keys()) | set(parent2.edges.keys())

        for key in all_edge_keys:
            edge1 = parent1.edges.get(key)
            edge2 = parent2.edges.get(key)

            if edge1 and edge2:
                # Both parents have this edge - inherit with averaged weight
                avg_weight = (edge1.weight + edge2.weight) / 2
                child_edge = Edge(
                    source_id=edge1.source_id,
                    target_id=edge1.target_id,
                    weight=avg_weight,
                )
                child.set_edge(child_edge)
            elif random.random() < self.crossover_rate:
                # Only one parent has the edge - inherit probabilistically
                source_edge = edge1 or edge2
                child_edge = Edge(
                    source_id=source_edge.source_id,
                    target_id=source_edge.target_id,
                    weight=source_edge.weight,
                )
                child.set_edge(child_edge)

        return child

    def single_point_crossover(
        self,
        parent1: Individual,
        parent2: Individual,
    ) -> Individual:
        """
        Single point crossover - take first half from parent1, second from parent2.

        Args:
            parent1: First parent
            parent2: Second parent

        Returns:
            Child individual
        """
        child = Individual(
            id=f"ind_{uuid.uuid4().hex[:8]}",
            generation=max(parent1.generation, parent2.generation) + 1,
            parent_ids=[parent1.id, parent2.id],
        )

        # Sort edges by source node
        edges1 = sorted(parent1.edges.values(), key=lambda e: e.source_id)
        edges2 = sorted(parent2.edges.values(), key=lambda e: e.source_id)

        # Find crossover point
        max_len = max(len(edges1), len(edges2))
        crossover_point = random.randint(1, max(1, max_len - 1))

        # Take first portion from parent1
        for edge in edges1[:crossover_point]:
            child.set_edge(Edge(
                source_id=edge.source_id,
                target_id=edge.target_id,
                weight=edge.weight,
            ))

        # Take second portion from parent2
        for edge in edges2[crossover_point:]:
            key = f"{edge.source_id}->{edge.target_id}"
            if key not in child.edges:  # Don't overwrite
                child.set_edge(Edge(
                    source_id=edge.source_id,
                    target_id=edge.target_id,
                    weight=edge.weight,
                ))

        return child

    def virtue_based_crossover(
        self,
        parent1: Individual,
        parent2: Individual,
    ) -> Individual:
        """
        Virtue-based crossover - inherit virtue neighborhoods intact.

        For each virtue, inherit its edges from one parent or the other.

        Args:
            parent1: First parent
            parent2: Second parent

        Returns:
            Child individual
        """
        child = Individual(
            id=f"ind_{uuid.uuid4().hex[:8]}",
            generation=max(parent1.generation, parent2.generation) + 1,
            parent_ids=[parent1.id, parent2.id],
        )

        # For each virtue, choose which parent to inherit from
        for virtue_def in VIRTUE_DEFINITIONS:
            virtue_id = virtue_def.id
            parent = random.choice([parent1, parent2])

            # Inherit all edges involving this virtue
            for key, edge in parent.edges.items():
                if edge.source_id == virtue_id or edge.target_id == virtue_id:
                    # Check if already have this edge from another virtue
                    if key not in child.edges:
                        child.set_edge(Edge(
                            source_id=edge.source_id,
                            target_id=edge.target_id,
                            weight=edge.weight,
                        ))

        # Inherit concept-concept edges with uniform crossover
        for parent in [parent1, parent2]:
            for edge in parent.edges.values():
                is_virtue_edge = any(
                    edge.source_id == v.id or edge.target_id == v.id
                    for v in VIRTUE_DEFINITIONS
                )
                if not is_virtue_edge:
                    key = f"{edge.source_id}->{edge.target_id}"
                    if key not in child.edges and random.random() < self.crossover_rate:
                        child.set_edge(Edge(
                            source_id=edge.source_id,
                            target_id=edge.target_id,
                            weight=edge.weight,
                        ))

        return child

    def multi_parent_crossover(
        self,
        parents: list[Individual],
    ) -> Individual:
        """
        Create a child from multiple parents.

        Each edge inherited from the parent with highest fitness that has it.

        Args:
            parents: List of parent individuals

        Returns:
            Child individual
        """
        if len(parents) < 2:
            raise ValueError("Need at least 2 parents")

        # Sort parents by fitness
        sorted_parents = sorted(parents, key=lambda x: x.fitness, reverse=True)

        child = Individual(
            id=f"ind_{uuid.uuid4().hex[:8]}",
            generation=max(p.generation for p in parents) + 1,
            parent_ids=[p.id for p in parents[:2]],  # Record top 2 as parents
        )

        # Collect all edge keys
        all_keys = set()
        for parent in parents:
            all_keys.update(parent.edges.keys())

        # For each edge, inherit from highest-fitness parent that has it
        for key in all_keys:
            for parent in sorted_parents:
                if key in parent.edges:
                    edge = parent.edges[key]
                    child.set_edge(Edge(
                        source_id=edge.source_id,
                        target_id=edge.target_id,
                        weight=edge.weight,
                    ))
                    break

        return child

    def batch_crossover(
        self,
        parent_pairs: list[tuple[Individual, Individual]],
        method: str = "uniform",
    ) -> list[Individual]:
        """
        Perform crossover on multiple parent pairs.

        Args:
            parent_pairs: List of (parent1, parent2) tuples
            method: Crossover method

        Returns:
            List of offspring
        """
        offspring = []
        for parent1, parent2 in parent_pairs:
            child = self.crossover(parent1, parent2, method)
            offspring.append(child)
        return offspring
