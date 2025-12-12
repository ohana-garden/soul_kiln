"""
Selection operators for topology evolution.

Implements various selection strategies to choose parents
for reproduction.
"""

import logging
import random

from src.constants import ELITISM_COUNT
from src.evolution.population import Individual, Population

logger = logging.getLogger(__name__)


class Selection:
    """
    Selection operators for evolutionary selection.

    Provides different strategies for selecting individuals
    for reproduction based on fitness.
    """

    def __init__(self, elitism_count: int = ELITISM_COUNT):
        """
        Initialize selection operators.

        Args:
            elitism_count: Number of best individuals to always keep
        """
        self.elitism_count = elitism_count

    def select_parents(
        self,
        population: Population,
        num_parents: int,
        method: str = "tournament",
    ) -> list[Individual]:
        """
        Select parents for reproduction.

        Args:
            population: The population to select from
            num_parents: Number of parents to select
            method: Selection method ("tournament", "roulette", "rank")

        Returns:
            List of selected parents
        """
        if method == "tournament":
            return self.tournament_selection(population, num_parents)
        elif method == "roulette":
            return self.roulette_selection(population, num_parents)
        elif method == "rank":
            return self.rank_selection(population, num_parents)
        else:
            raise ValueError(f"Unknown selection method: {method}")

    def tournament_selection(
        self,
        population: Population,
        num_parents: int,
        tournament_size: int = 3,
    ) -> list[Individual]:
        """
        Tournament selection.

        Select the best individual from random tournaments.

        Args:
            population: The population
            num_parents: Number of parents to select
            tournament_size: Size of each tournament

        Returns:
            List of selected parents
        """
        selected = []
        individuals = population.individuals

        for _ in range(num_parents):
            # Select random tournament participants
            tournament = random.sample(
                individuals,
                min(tournament_size, len(individuals)),
            )
            # Winner is the one with highest fitness
            winner = max(tournament, key=lambda x: x.fitness)
            selected.append(winner)

        return selected

    def roulette_selection(
        self,
        population: Population,
        num_parents: int,
    ) -> list[Individual]:
        """
        Roulette wheel selection (fitness proportionate).

        Selection probability proportional to fitness.

        Args:
            population: The population
            num_parents: Number of parents to select

        Returns:
            List of selected parents
        """
        individuals = population.individuals
        total_fitness = sum(ind.fitness for ind in individuals)

        if total_fitness == 0:
            # If all fitnesses are 0, select randomly
            return random.choices(individuals, k=num_parents)

        # Calculate selection probabilities
        probs = [ind.fitness / total_fitness for ind in individuals]

        # Select using weighted random choice
        return random.choices(individuals, weights=probs, k=num_parents)

    def rank_selection(
        self,
        population: Population,
        num_parents: int,
    ) -> list[Individual]:
        """
        Rank-based selection.

        Selection probability based on rank, not fitness.

        Args:
            population: The population
            num_parents: Number of parents to select

        Returns:
            List of selected parents
        """
        # Sort by fitness
        sorted_inds = sorted(population.individuals, key=lambda x: x.fitness)
        n = len(sorted_inds)

        # Assign rank-based weights (higher rank = higher weight)
        weights = [(i + 1) for i in range(n)]

        return random.choices(sorted_inds, weights=weights, k=num_parents)

    def select_survivors(
        self,
        population: Population,
        offspring: list[Individual],
        num_survivors: int,
    ) -> list[Individual]:
        """
        Select survivors for the next generation.

        Combines parents and offspring, keeping elites.

        Args:
            population: The current population
            offspring: New offspring individuals
            num_survivors: Number of survivors to select

        Returns:
            List of survivors for next generation
        """
        # Always keep the elite
        elites = population.get_best(self.elitism_count)
        elite_ids = {e.id for e in elites}

        # Combine remaining parents and offspring
        candidates = [ind for ind in population.individuals if ind.id not in elite_ids]
        candidates.extend(offspring)

        # Sort by fitness
        sorted_candidates = sorted(candidates, key=lambda x: x.fitness, reverse=True)

        # Select survivors
        remaining_slots = num_survivors - len(elites)
        survivors = elites + sorted_candidates[:remaining_slots]

        return survivors

    def get_elites(self, population: Population) -> list[Individual]:
        """
        Get the elite individuals that always survive.

        Args:
            population: The population

        Returns:
            List of elite individuals
        """
        return population.get_best(self.elitism_count)

    def diversity_aware_selection(
        self,
        population: Population,
        num_parents: int,
        diversity_weight: float = 0.3,
    ) -> list[Individual]:
        """
        Selection that balances fitness and diversity.

        Args:
            population: The population
            num_parents: Number of parents to select
            diversity_weight: Weight for diversity (0-1)

        Returns:
            List of selected parents
        """
        individuals = population.individuals
        selected = []

        # First, select some by pure fitness
        fitness_count = int(num_parents * (1 - diversity_weight))
        selected.extend(self.tournament_selection(population, fitness_count))

        # Then, select some for diversity
        remaining = [ind for ind in individuals if ind not in selected]
        diversity_count = num_parents - len(selected)

        # Select diverse individuals (different character signatures)
        for _ in range(diversity_count):
            if not remaining:
                break

            # Find most different from already selected
            best_diff = None
            best_score = -1

            for candidate in remaining:
                min_diff = float("inf")
                for sel in selected:
                    diff = self._character_difference(candidate, sel)
                    min_diff = min(min_diff, diff)
                if min_diff > best_score:
                    best_score = min_diff
                    best_diff = candidate

            if best_diff:
                selected.append(best_diff)
                remaining.remove(best_diff)

        return selected

    def _character_difference(self, ind1: Individual, ind2: Individual) -> float:
        """
        Calculate character difference between two individuals.

        Args:
            ind1: First individual
            ind2: Second individual

        Returns:
            Difference score (higher = more different)
        """
        sig1 = ind1.alignment_result.get("character_signature", {})
        sig2 = ind2.alignment_result.get("character_signature", {})

        if not sig1 or not sig2:
            return 0.5  # Unknown difference

        all_keys = set(sig1.keys()) | set(sig2.keys())
        diff = sum(abs(sig1.get(k, 0) - sig2.get(k, 0)) for k in all_keys)
        return diff / len(all_keys) if all_keys else 0.0
