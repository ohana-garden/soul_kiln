"""
Unit tests for VirtueSimulator component.
"""

import numpy as np
import unittest
from virtue_basin.simulator import VirtueSimulator
from virtue_basin.topology import SoulTemplate


class TestVirtueSimulator(unittest.TestCase):
    """Test cases for VirtueSimulator class."""
    
    def setUp(self):
        """Set up test fixtures."""
        np.random.seed(42)
        self.simulator = VirtueSimulator(
            dimension=3,
            population_size=10,
            mutation_rate=0.1,
            elite_size=2
        )
        self.virtue_names = ["compassion", "courage", "wisdom"]
    
    def test_initialization(self):
        """Test simulator initialization."""
        self.assertEqual(self.simulator.dimension, 3)
        self.assertEqual(self.simulator.population_size, 10)
        self.assertEqual(self.simulator.mutation_rate, 0.1)
        self.assertEqual(self.simulator.elite_size, 2)
        self.assertEqual(len(self.simulator.population), 0)
    
    def test_initialize_population(self):
        """Test population initialization."""
        self.simulator.initialize_population(self.virtue_names, n_virtues=3)
        
        self.assertEqual(len(self.simulator.population), 10)
        
        # Check that templates have virtues
        for template in self.simulator.population:
            self.assertGreater(len(template.topology.basins), 0)
    
    def test_fitness_function(self):
        """Test fitness evaluation."""
        self.simulator.initialize_population(self.virtue_names, n_virtues=2)
        template = self.simulator.population[0]
        
        fitness = self.simulator.fitness_function(template)
        
        # Fitness should be a non-negative number
        self.assertIsInstance(fitness, (float, np.floating))
        self.assertGreaterEqual(fitness, 0.0)
    
    def test_evaluate_population(self):
        """Test population evaluation."""
        self.simulator.initialize_population(self.virtue_names, n_virtues=2)
        
        # Initially, fitness should be 0
        self.assertEqual(self.simulator.population[0].fitness, 0.0)
        
        self.simulator.evaluate_population()
        
        # After evaluation, at least some templates should have non-zero fitness
        fitness_values = [template.fitness for template in self.simulator.population]
        self.assertGreater(max(fitness_values), 0.0)
    
    def test_select_parents(self):
        """Test parent selection."""
        self.simulator.initialize_population(self.virtue_names, n_virtues=2)
        self.simulator.evaluate_population()
        
        parent1, parent2 = self.simulator.select_parents()
        
        # Parents should be from the population
        self.assertIn(parent1, self.simulator.population)
        self.assertIn(parent2, self.simulator.population)
    
    def test_evolve_generation(self):
        """Test generation evolution."""
        self.simulator.initialize_population(self.virtue_names, n_virtues=2)
        self.simulator.evaluate_population()
        
        initial_generation = self.simulator.generation
        
        self.simulator.evolve_generation()
        
        # Generation should increment
        self.assertEqual(self.simulator.generation, initial_generation + 1)
        
        # Population size should remain constant
        self.assertEqual(len(self.simulator.population), 10)
    
    def test_run(self):
        """Test running the simulator."""
        self.simulator.initialize_population(self.virtue_names, n_virtues=2)
        
        best_template = self.simulator.run(generations=5, verbose=False)
        
        # Should return a template
        self.assertIsInstance(best_template, SoulTemplate)
        
        # Should have evolved 5 generations
        self.assertEqual(self.simulator.generation, 5)
        
        # Best template should have non-zero fitness
        self.assertGreater(best_template.fitness, 0.0)
    
    def test_get_statistics(self):
        """Test statistics retrieval."""
        self.simulator.initialize_population(self.virtue_names, n_virtues=2)
        self.simulator.evaluate_population()
        
        stats = self.simulator.get_statistics()
        
        self.assertIn('generation', stats)
        self.assertIn('best_fitness', stats)
        self.assertIn('avg_fitness', stats)
        self.assertIn('std_fitness', stats)
        self.assertIn('population_size', stats)
        
        self.assertEqual(stats['population_size'], 10)
    
    def test_repr(self):
        """Test string representation."""
        repr_str = repr(self.simulator)
        self.assertIn("VirtueSimulator", repr_str)
        self.assertIn("10", repr_str)  # population_size


if __name__ == '__main__':
    unittest.main()
