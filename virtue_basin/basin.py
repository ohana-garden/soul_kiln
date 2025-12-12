"""
Basin Attractor System

Models thoughts as strange attractors in a dynamical system.
Thoughts converge toward virtue basins through iterative evolution.
"""

import numpy as np
from typing import Tuple, Optional, Callable


class BasinAttractor:
    """
    Represents a basin of attraction in the virtue space.
    
    Thoughts (represented as points in state space) are attracted to 
    virtue basins through dynamical system evolution.
    """
    
    def __init__(
        self, 
        center: np.ndarray, 
        strength: float = 1.0,
        name: str = "unnamed_virtue"
    ):
        """
        Initialize a basin attractor.
        
        Args:
            center: The center point of the basin in state space
            strength: The strength of attraction (default: 1.0)
            name: Human-readable name for this virtue
        """
        self.center = np.asarray(center, dtype=np.float64)
        self.strength = strength
        self.name = name
        self.dimension = len(self.center)
    
    def attraction_force(self, point: np.ndarray) -> np.ndarray:
        """
        Calculate the attraction force at a given point.
        
        Uses inverse square law similar to gravitational attraction.
        
        Args:
            point: Position in state space
            
        Returns:
            Force vector pointing toward basin center
        """
        point = np.asarray(point, dtype=np.float64)
        displacement = self.center - point
        distance = np.linalg.norm(displacement)
        
        if distance < 1e-10:  # Avoid division by zero
            return np.zeros_like(displacement)
        
        # Inverse square law with strength modifier
        force_magnitude = self.strength / (distance ** 2 + 0.1)
        force_direction = displacement / distance
        
        return force_magnitude * force_direction
    
    def basin_potential(self, point: np.ndarray) -> float:
        """
        Calculate the potential energy at a point.
        
        Lower potential indicates closer to basin center.
        
        Args:
            point: Position in state space
            
        Returns:
            Potential energy value
        """
        point = np.asarray(point, dtype=np.float64)
        distance = np.linalg.norm(self.center - point)
        return -self.strength / (distance + 0.1)
    
    def contains(self, point: np.ndarray, threshold: float = 0.5) -> bool:
        """
        Check if a point is within the basin of attraction.
        
        Args:
            point: Position in state space
            threshold: Distance threshold for basin membership
            
        Returns:
            True if point is within the basin
        """
        point = np.asarray(point, dtype=np.float64)
        distance = np.linalg.norm(self.center - point)
        return distance < threshold
    
    def evolve_thought(
        self, 
        initial_point: np.ndarray, 
        steps: int = 100,
        dt: float = 0.01
    ) -> np.ndarray:
        """
        Evolve a thought trajectory toward the basin.
        
        Simulates the dynamical system evolution of a thought as it
        converges toward the virtue basin.
        
        Args:
            initial_point: Starting position in state space
            steps: Number of evolution steps
            dt: Time step size
            
        Returns:
            Trajectory as array of shape (steps, dimension)
        """
        trajectory = np.zeros((steps, self.dimension))
        point = np.asarray(initial_point, dtype=np.float64)
        trajectory[0] = point
        
        for i in range(1, steps):
            force = self.attraction_force(point)
            velocity = force * dt
            point = point + velocity
            trajectory[i] = point
        
        return trajectory
    
    def __repr__(self) -> str:
        return (f"BasinAttractor(name='{self.name}', "
                f"center={self.center}, strength={self.strength})")
