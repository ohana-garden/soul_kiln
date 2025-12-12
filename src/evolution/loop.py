"""
Main evolution loop for the Virtue Basin Simulator.

Orchestrates the evolutionary process: evaluation, selection,
crossover, mutation, and survival selection.
"""

import json
import logging
import random
from datetime import datetime
from pathlib import Path

from src.constants import (
    GENERATIONS,
    MIN_ALIGNMENT_SCORE,
    POPULATION_SIZE,
)
from src.evolution.population import Individual, Population
from src.evolution.selection import Selection
from src.evolution.crossover import Crossover
from src.evolution.mutation import Mutation

logger = logging.getLogger(__name__)


class EvolutionLoop:
    """
    Main evolution loop for discovering valid soul topologies.

    Orchestrates the evolutionary process across multiple generations,
    tracking progress and extracting winning configurations.
    """

    def __init__(
        self,
        population: Population,
        selection: Selection,
        crossover: Crossover,
        mutation: Mutation,
        evaluator,  # Callable that evaluates an Individual and returns fitness
        generations: int = GENERATIONS,
        min_score: float = MIN_ALIGNMENT_SCORE,
        checkpoint_dir: str | None = None,
    ):
        """
        Initialize the evolution loop.

        Args:
            population: The population to evolve
            selection: Selection operator
            crossover: Crossover operator
            mutation: Mutation operator
            evaluator: Function to evaluate individual fitness
            generations: Maximum number of generations
            min_score: Minimum alignment score for success
            checkpoint_dir: Optional directory for checkpoints
        """
        self.population = population
        self.selection = selection
        self.crossover = crossover
        self.mutation = mutation
        self.evaluator = evaluator
        self.generations = generations
        self.min_score = min_score
        self.checkpoint_dir = Path(checkpoint_dir) if checkpoint_dir else None

        self._current_generation = 0
        self._best_ever: Individual | None = None
        self._converged = False
        self._history: list[dict] = []

    def run(self) -> Individual | None:
        """
        Run the full evolution process.

        Returns:
            The best individual found, or None if no valid topology
        """
        logger.info(f"Starting evolution: {self.generations} generations, population {len(self.population.individuals)}")

        # Initial evaluation
        self._evaluate_population()
        self._update_best()
        self._log_generation()

        for gen in range(self.generations):
            self._current_generation = gen + 1

            # Check for early convergence
            if self._best_ever and self._best_ever.fitness >= self.min_score:
                logger.info(f"Converged at generation {gen + 1}! Best fitness: {self._best_ever.fitness:.4f}")
                self._converged = True
                break

            # Evolution step
            self._evolve_generation()

            # Logging and checkpointing
            self._log_generation()
            if self.checkpoint_dir and gen % 10 == 0:
                self._save_checkpoint()

        # Final result
        if self._best_ever:
            logger.info(f"Evolution complete. Best fitness: {self._best_ever.fitness:.4f}")
            return self._best_ever
        else:
            logger.warning("Evolution complete. No valid topology found.")
            return None

    def _evolve_generation(self) -> None:
        """Execute one generation of evolution."""
        # Select parents
        num_offspring = len(self.population.individuals) - self.selection.elitism_count
        parents = self.selection.select_parents(
            self.population,
            num_parents=num_offspring * 2,  # 2 parents per offspring
            method="tournament",
        )

        # Create offspring through crossover
        offspring = []
        for i in range(0, len(parents) - 1, 2):
            child = self.crossover.crossover(parents[i], parents[i + 1])
            offspring.append(child)

        # Apply mutation
        offspring = self.mutation.batch_mutate(offspring)

        # Evaluate offspring
        for individual in offspring:
            self._evaluate_individual(individual)

        # Select survivors
        survivors = self.selection.select_survivors(
            self.population,
            offspring,
            len(self.population.individuals),
        )

        # Update population
        self.population.individuals = survivors
        self.population.advance_generation()
        self._update_best()

    def _evaluate_population(self) -> None:
        """Evaluate all individuals in the population."""
        for individual in self.population.individuals:
            self._evaluate_individual(individual)

    def _evaluate_individual(self, individual: Individual) -> None:
        """
        Evaluate a single individual.

        Args:
            individual: The individual to evaluate
        """
        result = self.evaluator(individual)
        individual.fitness = result.get("alignment_score", 0.0)
        individual.alignment_result = result

    def _update_best(self) -> None:
        """Update the best-ever individual."""
        current_best = self.population.get_best(1)
        if current_best:
            current_best = current_best[0]
            if self._best_ever is None or current_best.fitness > self._best_ever.fitness:
                self._best_ever = current_best.clone()
                self._best_ever.fitness = current_best.fitness
                self._best_ever.alignment_result = current_best.alignment_result.copy()

    def _log_generation(self) -> None:
        """Log generation statistics."""
        stats = self.population.get_fitness_stats()
        best = self.population.get_best(1)[0] if self.population.individuals else None

        entry = {
            "generation": self._current_generation,
            "best_fitness": best.fitness if best else 0.0,
            "mean_fitness": stats["mean"],
            "min_fitness": stats["min"],
            "max_fitness": stats["max"],
            "std_fitness": stats["std"],
            "best_id": best.id if best else None,
            "timestamp": datetime.utcnow().isoformat(),
        }
        self._history.append(entry)

        logger.info(
            f"Gen {self._current_generation}: "
            f"best={stats['max']:.4f}, "
            f"mean={stats['mean']:.4f}, "
            f"std={stats['std']:.4f}"
        )

    def _save_checkpoint(self) -> None:
        """Save evolution checkpoint."""
        if not self.checkpoint_dir:
            return

        self.checkpoint_dir.mkdir(parents=True, exist_ok=True)

        checkpoint = {
            "generation": self._current_generation,
            "best_ever": self.population.export_best(),
            "history": self._history,
            "converged": self._converged,
            "timestamp": datetime.utcnow().isoformat(),
        }

        checkpoint_file = self.checkpoint_dir / f"checkpoint_gen{self._current_generation}.json"
        with open(checkpoint_file, "w") as f:
            json.dump(checkpoint, f, indent=2)

        logger.debug(f"Saved checkpoint to {checkpoint_file}")

    def get_history(self) -> list[dict]:
        """Get evolution history."""
        return list(self._history)

    def get_best(self) -> Individual | None:
        """Get the best individual found so far."""
        return self._best_ever

    def is_converged(self) -> bool:
        """Check if evolution has converged."""
        return self._converged

    def export_result(self, output_path: str | Path) -> None:
        """
        Export the evolution result to a file.

        Args:
            output_path: Path for the output file
        """
        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)

        result = {
            "best_topology": self.population.export_best(),
            "generations_run": self._current_generation,
            "converged": self._converged,
            "min_score_threshold": self.min_score,
            "history": self._history,
            "timestamp": datetime.utcnow().isoformat(),
        }

        if self._best_ever:
            result["best_fitness"] = self._best_ever.fitness
            result["best_character"] = self._best_ever.alignment_result.get("character_signature", {})

        with open(output_path, "w") as f:
            json.dump(result, f, indent=2)

        logger.info(f"Exported evolution result to {output_path}")


class TopologyEvaluator:
    """
    Evaluator that uses the alignment tester to evaluate topologies.

    Bridges between evolution individuals and the alignment testing system.
    """

    def __init__(self, alignment_tester, substrate, num_stimuli: int = 50):
        """
        Initialize the evaluator.

        Args:
            alignment_tester: The AlignmentTester instance
            substrate: The GraphSubstrate instance
            num_stimuli: Number of stimuli for evaluation
        """
        self.alignment_tester = alignment_tester
        self.substrate = substrate
        self.num_stimuli = num_stimuli

    def __call__(self, individual: Individual) -> dict:
        """
        Evaluate an individual.

        Args:
            individual: The individual to evaluate

        Returns:
            Dict with evaluation results
        """
        # Apply individual's topology to the graph
        self._apply_topology(individual)

        # Run alignment test
        result = self.alignment_tester.test_alignment(
            agent_id=individual.id,
            num_stimuli=self.num_stimuli,
        )

        return {
            "alignment_score": result.alignment_score,
            "capture_rate": result.alignment_score,
            "escape_rate": result.escape_rate,
            "avg_capture_time": result.avg_capture_time,
            "character_signature": result.character_signature,
            "passed": result.passed,
            "per_virtue_captures": result.per_virtue_captures,
        }

    def _apply_topology(self, individual: Individual) -> None:
        """
        Apply an individual's topology to the graph substrate.

        Args:
            individual: The individual whose topology to apply
        """
        # For simplicity, we update edge weights based on the individual's edges
        # In a full implementation, this would manage isolated edge spaces per agent
        for edge in individual.edges.values():
            existing = self.substrate.get_edge(edge.source_id, edge.target_id)
            if existing:
                existing.weight = edge.weight
                self.substrate.update_edge(existing)
