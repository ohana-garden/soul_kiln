"""
Unit tests for Basin Attractor component.
"""

import numpy as np
import unittest
from virtue_basin.basin import BasinAttractor


class TestBasinAttractor(unittest.TestCase):
    """Test cases for BasinAttractor class."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.basin = BasinAttractor(
            center=np.array([1.0, 2.0, 3.0]),
            strength=1.5,
            name="test_virtue"
        )
    
    def test_initialization(self):
        """Test basin initialization."""
        self.assertEqual(self.basin.name, "test_virtue")
        self.assertEqual(self.basin.strength, 1.5)
        self.assertEqual(self.basin.dimension, 3)
        np.testing.assert_array_equal(self.basin.center, np.array([1.0, 2.0, 3.0]))
    
    def test_attraction_force(self):
        """Test attraction force calculation."""
        point = np.array([0.0, 0.0, 0.0])
        force = self.basin.attraction_force(point)
        
        # Force should point toward basin center
        self.assertEqual(force.shape, (3,))
        
        # Force should be non-zero for point away from center
        force_magnitude = np.linalg.norm(force)
        self.assertGreater(force_magnitude, 0.0)
        
        # Force at center should be zero
        force_at_center = self.basin.attraction_force(self.basin.center)
        np.testing.assert_array_almost_equal(force_at_center, np.zeros(3), decimal=5)
    
    def test_basin_potential(self):
        """Test potential energy calculation."""
        point = np.array([0.0, 0.0, 0.0])
        potential = self.basin.basin_potential(point)
        
        # Potential should be a scalar
        self.assertIsInstance(potential, (float, np.floating))
        
        # Potential should be negative (attractive)
        self.assertLess(potential, 0.0)
    
    def test_contains(self):
        """Test basin membership check."""
        # Point at center should be contained
        self.assertTrue(self.basin.contains(self.basin.center, threshold=1.0))
        
        # Point close to center should be contained
        close_point = self.basin.center + np.array([0.1, 0.1, 0.1])
        self.assertTrue(self.basin.contains(close_point, threshold=0.5))
        
        # Point far from center should not be contained
        far_point = np.array([100.0, 100.0, 100.0])
        self.assertFalse(self.basin.contains(far_point, threshold=0.5))
    
    def test_evolve_thought(self):
        """Test thought trajectory evolution."""
        initial_point = np.array([5.0, 5.0, 5.0])
        steps = 50
        
        trajectory = self.basin.evolve_thought(initial_point, steps=steps)
        
        # Check trajectory shape
        self.assertEqual(trajectory.shape, (steps, 3))
        
        # First point should be initial point
        np.testing.assert_array_equal(trajectory[0], initial_point)
        
        # Trajectory should move toward center
        initial_distance = np.linalg.norm(trajectory[0] - self.basin.center)
        final_distance = np.linalg.norm(trajectory[-1] - self.basin.center)
        self.assertLessEqual(final_distance, initial_distance)
    
    def test_repr(self):
        """Test string representation."""
        repr_str = repr(self.basin)
        self.assertIn("test_virtue", repr_str)
        self.assertIn("1.5", repr_str)


if __name__ == '__main__':
    unittest.main()
