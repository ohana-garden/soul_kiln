"""
Unit tests for GravitationalForce component.
"""

import numpy as np
import unittest
from virtue_basin.forces import GravitationalForce
from virtue_basin.basin import BasinAttractor


class TestGravitationalForce(unittest.TestCase):
    """Test cases for GravitationalForce class."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.gravity = GravitationalForce(strength=1.0)
        self.basins = [
            BasinAttractor(np.array([1.0, 0.0]), strength=1.0, name="basin1"),
            BasinAttractor(np.array([0.0, 1.0]), strength=1.0, name="basin2"),
        ]
    
    def test_initialization(self):
        """Test gravitational force initialization."""
        self.assertEqual(self.gravity.strength, 1.0)
    
    def test_compute_force(self):
        """Test force computation."""
        point = np.array([0.0, 0.0])
        force = self.gravity.compute_force(point, self.basins)
        
        # Force should be a 2D vector
        self.assertEqual(force.shape, (2,))
        
        # Force magnitude should be non-zero for point away from basins
        force_magnitude = np.linalg.norm(force)
        self.assertGreater(force_magnitude, 0.0)
    
    def test_potential_energy(self):
        """Test potential energy computation."""
        point = np.array([0.0, 0.0])
        potential = self.gravity.potential_energy(point, self.basins)
        
        # Potential should be a scalar
        self.assertIsInstance(potential, (float, np.floating))
        
        # Potential should be negative (attractive)
        self.assertLess(potential, 0.0)
    
    def test_compute_field(self):
        """Test force field computation."""
        grid_points = np.array([
            [0.0, 0.0],
            [1.0, 0.0],
            [0.0, 1.0],
            [1.0, 1.0]
        ])
        
        field = self.gravity.compute_field(grid_points, self.basins)
        
        # Field should have same shape as grid points
        self.assertEqual(field.shape, grid_points.shape)
        
        # Field vectors should be non-zero for most points
        nonzero_count = np.sum(np.linalg.norm(field, axis=1) > 0.0)
        self.assertGreater(nonzero_count, 0)
    
    def test_find_equilibrium(self):
        """Test equilibrium finding."""
        initial_point = np.array([5.0, 5.0])
        
        equilibrium = self.gravity.find_equilibrium(
            initial_point, 
            self.basins,
            max_iterations=1000,
            tolerance=1e-6
        )
        
        # Equilibrium should be a 2D point
        self.assertEqual(equilibrium.shape, (2,))
        
        # Force at equilibrium should be small
        force = self.gravity.compute_force(equilibrium, self.basins)
        force_magnitude = np.linalg.norm(force)
        self.assertLess(force_magnitude, 0.5)
    
    def test_repr(self):
        """Test string representation."""
        repr_str = repr(self.gravity)
        self.assertIn("GravitationalForce", repr_str)
        self.assertIn("1.0", repr_str)


if __name__ == '__main__':
    unittest.main()
