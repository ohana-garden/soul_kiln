"""
Unit tests for VirtueTopology and SoulTemplate components.
"""

import numpy as np
import unittest
from virtue_basin.topology import VirtueTopology, SoulTemplate


class TestVirtueTopology(unittest.TestCase):
    """Test cases for VirtueTopology class."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.topology = VirtueTopology(dimension=3)
    
    def test_initialization(self):
        """Test topology initialization."""
        self.assertEqual(self.topology.dimension, 3)
        self.assertEqual(len(self.topology.basins), 0)
        self.assertEqual(self.topology.graph.number_of_nodes(), 0)
    
    def test_add_virtue(self):
        """Test adding virtues."""
        self.topology.add_virtue("compassion", np.array([1.0, 0.0, 0.0]), strength=1.2)
        
        self.assertEqual(len(self.topology.basins), 1)
        self.assertIn("compassion", self.topology.basins)
        self.assertEqual(self.topology.basins["compassion"].strength, 1.2)
    
    def test_add_relationship(self):
        """Test adding relationships between virtues."""
        self.topology.add_virtue("compassion", np.array([1.0, 0.0, 0.0]))
        self.topology.add_virtue("courage", np.array([0.0, 1.0, 0.0]))
        
        self.topology.add_relationship("compassion", "courage", weight=1.5, constraint_type="supports")
        
        self.assertEqual(self.topology.graph.number_of_edges(), 1)
        self.assertTrue(self.topology.graph.has_edge("compassion", "courage"))
    
    def test_add_relationship_invalid(self):
        """Test adding relationship with non-existent virtue."""
        self.topology.add_virtue("compassion", np.array([1.0, 0.0, 0.0]))
        
        with self.assertRaises(ValueError):
            self.topology.add_relationship("compassion", "nonexistent", weight=1.0)
    
    def test_get_basin_list(self):
        """Test getting list of basins."""
        self.topology.add_virtue("virtue1", np.array([1.0, 0.0, 0.0]))
        self.topology.add_virtue("virtue2", np.array([0.0, 1.0, 0.0]))
        
        basins = self.topology.get_basin_list()
        self.assertEqual(len(basins), 2)
    
    def test_compute_alignment_score(self):
        """Test alignment score computation."""
        self.topology.add_virtue("compassion", np.array([1.0, 0.0, 0.0]))
        self.topology.add_virtue("courage", np.array([0.0, 1.0, 0.0]))
        
        # Point close to virtues should have higher alignment
        close_point = np.array([0.5, 0.5, 0.0])
        close_score = self.topology.compute_alignment_score(close_point)
        
        # Point far from virtues should have lower alignment
        far_point = np.array([10.0, 10.0, 10.0])
        far_score = self.topology.compute_alignment_score(far_point)
        
        self.assertGreater(close_score, far_score)
    
    def test_validate_constraints(self):
        """Test constraint validation."""
        self.topology.add_virtue("virtue1", np.array([1.0, 0.0, 0.0]))
        self.topology.add_virtue("virtue2", np.array([0.0, 1.0, 0.0]))
        
        # Add non-circular relationship
        self.topology.add_relationship("virtue1", "virtue2", constraint_type="supports")
        self.assertTrue(self.topology.validate_constraints())
    
    def test_get_virtue_strengths(self):
        """Test getting virtue strengths."""
        self.topology.add_virtue("virtue1", np.array([1.0, 0.0, 0.0]), strength=1.5)
        self.topology.add_virtue("virtue2", np.array([0.0, 1.0, 0.0]), strength=2.0)
        
        strengths = self.topology.get_virtue_strengths()
        self.assertEqual(strengths["virtue1"], 1.5)
        self.assertEqual(strengths["virtue2"], 2.0)
    
    def test_repr(self):
        """Test string representation."""
        self.topology.add_virtue("virtue1", np.array([1.0, 0.0, 0.0]))
        repr_str = repr(self.topology)
        self.assertIn("VirtueTopology", repr_str)
        self.assertIn("1", repr_str)  # 1 virtue


class TestSoulTemplate(unittest.TestCase):
    """Test cases for SoulTemplate class."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.topology = VirtueTopology(dimension=2)
        self.topology.add_virtue("virtue1", np.array([1.0, 0.0]), strength=1.0)
        self.topology.add_virtue("virtue2", np.array([0.0, 1.0]), strength=1.2)
        self.template = SoulTemplate(self.topology, fitness=0.8)
    
    def test_initialization(self):
        """Test template initialization."""
        self.assertEqual(self.template.fitness, 0.8)
        self.assertEqual(self.template.generation, 0)
        self.assertEqual(len(self.template.topology.basins), 2)
    
    def test_mutate(self):
        """Test template mutation."""
        mutated = self.template.mutate(mutation_rate=0.2)
        
        # Mutated template should be a new instance
        self.assertIsNot(mutated, self.template)
        
        # Should have same virtues
        self.assertEqual(
            set(mutated.topology.basins.keys()),
            set(self.template.topology.basins.keys())
        )
    
    def test_crossover(self):
        """Test template crossover."""
        topology2 = VirtueTopology(dimension=2)
        topology2.add_virtue("virtue1", np.array([-1.0, 0.0]), strength=0.8)
        topology2.add_virtue("virtue2", np.array([0.0, -1.0]), strength=1.5)
        template2 = SoulTemplate(topology2, fitness=0.7)
        
        child = self.template.crossover(template2)
        
        # Child should be a new template
        self.assertIsNot(child, self.template)
        self.assertIsNot(child, template2)
        
        # Child should have virtues from both parents
        self.assertEqual(len(child.topology.basins), 2)
    
    def test_is_valid(self):
        """Test template validation."""
        self.assertTrue(self.template.is_valid())
    
    def test_repr(self):
        """Test string representation."""
        repr_str = repr(self.template)
        self.assertIn("SoulTemplate", repr_str)
        self.assertIn("0.800", repr_str)


if __name__ == '__main__':
    unittest.main()
