"""
Gravitational Force Model

Models "love" as a gravitational force in the virtue space.
Love creates attraction between moral agents and virtue basins.
"""

import numpy as np
from typing import List
from .basin import BasinAttractor


class GravitationalForce:
    """
    Represents the gravitational force ("love") in the virtue basin system.
    
    Love is gravitational - it creates attraction between entities in
    the moral topology space.
    """
    
    def __init__(self, strength: float = 1.0):
        """
        Initialize gravitational force model.
        
        Args:
            strength: Universal gravitational constant for the system
        """
        self.strength = strength
    
    def compute_force(
        self, 
        point: np.ndarray, 
        basins: List[BasinAttractor]
    ) -> np.ndarray:
        """
        Compute total gravitational force on a point from all basins.
        
        Args:
            point: Position in state space
            basins: List of basin attractors
            
        Returns:
            Total force vector
        """
        total_force = np.zeros_like(point, dtype=np.float64)
        
        for basin in basins:
            force = basin.attraction_force(point)
            total_force += force * self.strength
        
        return total_force
    
    def potential_energy(
        self, 
        point: np.ndarray, 
        basins: List[BasinAttractor]
    ) -> float:
        """
        Compute total potential energy at a point.
        
        Args:
            point: Position in state space
            basins: List of basin attractors
            
        Returns:
            Total potential energy
        """
        total_potential = 0.0
        
        for basin in basins:
            total_potential += basin.basin_potential(point)
        
        return total_potential * self.strength
    
    def compute_field(
        self,
        grid_points: np.ndarray,
        basins: List[BasinAttractor]
    ) -> np.ndarray:
        """
        Compute force field over a grid of points.
        
        Useful for visualization of the virtue landscape.
        
        Args:
            grid_points: Array of shape (N, dimension) with grid points
            basins: List of basin attractors
            
        Returns:
            Array of shape (N, dimension) with force vectors
        """
        n_points = len(grid_points)
        dimension = len(grid_points[0])
        field = np.zeros((n_points, dimension))
        
        for i, point in enumerate(grid_points):
            field[i] = self.compute_force(point, basins)
        
        return field
    
    def find_equilibrium(
        self,
        initial_point: np.ndarray,
        basins: List[BasinAttractor],
        max_iterations: int = 1000,
        tolerance: float = 1e-6
    ) -> np.ndarray:
        """
        Find equilibrium point in the force field.
        
        Evolves a point until forces balance or convergence.
        
        Args:
            initial_point: Starting position
            basins: List of basin attractors
            max_iterations: Maximum number of iterations
            tolerance: Convergence tolerance
            
        Returns:
            Equilibrium position
        """
        point = np.asarray(initial_point, dtype=np.float64)
        
        for _ in range(max_iterations):
            force = self.compute_force(point, basins)
            force_magnitude = np.linalg.norm(force)
            
            if force_magnitude < tolerance:
                break
            
            # Simple gradient descent
            point = point + 0.01 * force
        
        return point
    
    def __repr__(self) -> str:
        return f"GravitationalForce(strength={self.strength})"
