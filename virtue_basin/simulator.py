"""
Virtue Simulator

Self-optimizing evolutionary system that discovers valid moral topologies.
Generates and evolves soul templates through fitness-based selection.
"""

import numpy as np
from typing import List, Callable, Optional, Tuple
from .topology import VirtueTopology, SoulTemplate
from .basin import BasinAttractor
from .forces import GravitationalForce


class VirtueSimulator:
    """
    Evolutionary simulator for discovering optimal virtue topologies.
    
    The simulator evolves a population of soul templates through
    mutation, crossover, and fitness-based selection.
    """
    
    def __init__(
        self,
        dimension: int = 3,
        population_size: int = 50,
        mutation_rate: float = 0.1,
        elite_size: int = 5
    ):
        """
        Initialize the virtue simulator.
        
        Args:
            dimension: Dimensionality of the state space
            population_size: Number of soul templates in population
            mutation_rate: Probability of mutations
            elite_size: Number of top templates to preserve each generation
        """
        self.dimension = dimension
        self.population_size = population_size
        self.mutation_rate = mutation_rate
        self.elite_size = elite_size
        self.population: List[SoulTemplate] = []
        self.generation = 0
        self.gravitational_force = GravitationalForce()
        self.best_template: Optional[SoulTemplate] = None
    
    def initialize_population(
        self, 
        virtue_names: List[str],
        n_virtues: Optional[int] = None
    ) -> None:
        """
        Initialize population with random soul templates.
        
        Args:
            virtue_names: List of virtue names to use
            n_virtues: Number of virtues per template (None = use all names)
        """
        self.population = []
        
        if n_virtues is None:
            n_virtues = len(virtue_names)
        
        for _ in range(self.population_size):
            topology = VirtueTopology(self.dimension)
            
            # Randomly sample virtues
            selected_virtues = np.random.choice(
                virtue_names, 
                size=min(n_virtues, len(virtue_names)),
                replace=False
            )
            
            # Add virtues at random positions
            for name in selected_virtues:
                center = np.random.randn(self.dimension)
                strength = np.random.uniform(0.5, 2.0)
                topology.add_virtue(name, center, strength)
            
            # Add random relationships
            virtue_list = list(selected_virtues)
            n_relationships = np.random.randint(len(virtue_list), len(virtue_list) * 2)
            
            for _ in range(n_relationships):
                if len(virtue_list) >= 2:
                    from_v, to_v = np.random.choice(virtue_list, size=2, replace=False)
                    constraint_type = np.random.choice(
                        ['supports', 'requires', 'opposes'],
                        p=[0.6, 0.3, 0.1]
                    )
                    weight = np.random.uniform(0.5, 1.5)
                    
                    try:
                        topology.add_relationship(from_v, to_v, weight, constraint_type)
                    except:
                        pass  # Skip if relationship already exists
            
            template = SoulTemplate(topology)
            self.population.append(template)
    
    def fitness_function(self, template: SoulTemplate) -> float:
        """
        Evaluate the fitness of a soul template.
        
        Fitness is based on:
        - Constraint satisfaction
        - Basin separation (virtues should be distinct)
        - Stability of attractor landscape
        - Alignment quality
        
        Args:
            template: Soul template to evaluate
            
        Returns:
            Fitness score (higher is better)
        """
        topology = template.topology
        
        # Check constraint validity
        if not topology.validate_constraints():
            return 0.0
        
        fitness = 1.0
        basins = topology.get_basin_list()
        
        if len(basins) == 0:
            return 0.0
        
        # Reward basin separation (virtues should be distinct)
        separation_score = 0.0
        for i, basin1 in enumerate(basins):
            for basin2 in basins[i+1:]:
                distance = np.linalg.norm(basin1.center - basin2.center)
                separation_score += np.tanh(distance)  # Saturates at large distances
        
        if len(basins) > 1:
            separation_score /= (len(basins) * (len(basins) - 1) / 2)
        else:
            separation_score = 1.0
        
        fitness += separation_score
        
        # Reward balanced basin strengths
        strengths = [b.strength for b in basins]
        strength_variance = np.var(strengths)
        balance_score = 1.0 / (1.0 + strength_variance)
        fitness += balance_score * 0.5
        
        # Test alignment with sample points
        n_samples = 20
        alignment_scores = []
        for _ in range(n_samples):
            test_point = np.random.randn(self.dimension) * 2.0
            
            # Evolve point and check convergence
            equilibrium = self.gravitational_force.find_equilibrium(
                test_point, basins, max_iterations=100
            )
            
            # Check if it converges to a basin
            converged = False
            for basin in basins:
                if basin.contains(equilibrium, threshold=1.0):
                    converged = True
                    break
            
            if converged:
                alignment_scores.append(1.0)
            else:
                alignment_scores.append(0.0)
        
        convergence_rate = np.mean(alignment_scores)
        fitness += convergence_rate * 2.0
        
        # Reward number of relationships (connectivity)
        n_relationships = topology.graph.number_of_edges()
        n_virtues = len(basins)
        if n_virtues > 1:
            connectivity = n_relationships / (n_virtues * (n_virtues - 1))
            fitness += connectivity * 0.5
        
        return fitness
    
    def evaluate_population(self) -> None:
        """Evaluate fitness for all templates in population."""
        for template in self.population:
            template.fitness = self.fitness_function(template)
            template.generation = self.generation
    
    def select_parents(self) -> Tuple[SoulTemplate, SoulTemplate]:
        """
        Select two parents using tournament selection.
        
        Returns:
            Tuple of two parent templates
        """
        tournament_size = 5
        
        def tournament():
            competitors = np.random.choice(
                self.population, 
                size=min(tournament_size, len(self.population)),
                replace=False
            )
            return max(competitors, key=lambda t: t.fitness)
        
        parent1 = tournament()
        parent2 = tournament()
        
        return parent1, parent2
    
    def evolve_generation(self) -> None:
        """
        Evolve one generation of soul templates.
        
        Uses elitism, crossover, and mutation to create new generation.
        """
        # Sort by fitness
        self.population.sort(key=lambda t: t.fitness, reverse=True)
        
        # Track best template
        if self.best_template is None or self.population[0].fitness > self.best_template.fitness:
            self.best_template = self.population[0]
        
        # Create new population
        new_population = []
        
        # Elitism: Keep best templates
        new_population.extend(self.population[:self.elite_size])
        
        # Generate offspring
        while len(new_population) < self.population_size:
            parent1, parent2 = self.select_parents()
            
            # Crossover
            if np.random.random() < 0.7:
                child = parent1.crossover(parent2)
            else:
                child = parent1.mutate(self.mutation_rate) if np.random.random() < 0.5 else parent2.mutate(self.mutation_rate)
            
            # Mutation
            if np.random.random() < self.mutation_rate:
                child = child.mutate(self.mutation_rate)
            
            new_population.append(child)
        
        self.population = new_population[:self.population_size]
        self.generation += 1
    
    def run(
        self, 
        generations: int = 100,
        verbose: bool = True
    ) -> SoulTemplate:
        """
        Run the evolutionary simulator.
        
        Args:
            generations: Number of generations to evolve
            verbose: Whether to print progress
            
        Returns:
            Best soul template found
        """
        if not self.population:
            raise ValueError("Population not initialized. Call initialize_population() first.")
        
        # Initial evaluation
        self.evaluate_population()
        
        if verbose:
            print(f"Generation 0: Best fitness = {max(t.fitness for t in self.population):.4f}")
        
        # Evolution loop
        for gen in range(generations):
            self.evolve_generation()
            self.evaluate_population()
            
            best_fitness = max(t.fitness for t in self.population)
            avg_fitness = np.mean([t.fitness for t in self.population])
            
            if verbose and (gen + 1) % 10 == 0:
                print(f"Generation {gen + 1}: "
                      f"Best = {best_fitness:.4f}, "
                      f"Avg = {avg_fitness:.4f}")
        
        # Return best template
        self.population.sort(key=lambda t: t.fitness, reverse=True)
        return self.population[0]
    
    def get_statistics(self) -> dict:
        """
        Get statistics about the current population.
        
        Returns:
            Dictionary of statistics
        """
        if not self.population:
            return {}
        
        fitnesses = [t.fitness for t in self.population]
        
        return {
            'generation': self.generation,
            'best_fitness': max(fitnesses),
            'avg_fitness': np.mean(fitnesses),
            'std_fitness': np.std(fitnesses),
            'population_size': len(self.population),
        }
    
    def __repr__(self) -> str:
        return (f"VirtueSimulator(generation={self.generation}, "
                f"population_size={self.population_size}, "
                f"dimension={self.dimension})")
