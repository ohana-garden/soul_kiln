"""
Virtue Topology and Soul Templates

Graph structures representing moral topologies and agent alignment patterns.
Soul templates are geometric constraint systems that guarantee alignment.
"""

import numpy as np
import networkx as nx
from typing import Dict, List, Tuple, Optional, Set
from .basin import BasinAttractor


class VirtueTopology:
    """
    Represents a moral topology as a graph structure.
    
    Nodes represent virtues (basin attractors), edges represent
    relationships and constraints between virtues.
    """
    
    def __init__(self, dimension: int = 3):
        """
        Initialize an empty virtue topology.
        
        Args:
            dimension: Dimensionality of the state space
        """
        self.graph = nx.DiGraph()
        self.dimension = dimension
        self.basins: Dict[str, BasinAttractor] = {}
    
    def add_virtue(
        self, 
        name: str, 
        center: np.ndarray, 
        strength: float = 1.0
    ) -> None:
        """
        Add a virtue basin to the topology.
        
        Args:
            name: Unique identifier for the virtue
            center: Position of basin center
            strength: Attraction strength
        """
        basin = BasinAttractor(center, strength, name)
        self.basins[name] = basin
        self.graph.add_node(name, basin=basin)
    
    def add_relationship(
        self, 
        from_virtue: str, 
        to_virtue: str, 
        weight: float = 1.0,
        constraint_type: str = "supports"
    ) -> None:
        """
        Add a relationship between two virtues.
        
        Args:
            from_virtue: Source virtue name
            to_virtue: Target virtue name
            weight: Strength of the relationship
            constraint_type: Type of constraint ('supports', 'opposes', 'requires')
        """
        if from_virtue not in self.basins or to_virtue not in self.basins:
            raise ValueError("Both virtues must exist in the topology")
        
        self.graph.add_edge(
            from_virtue, 
            to_virtue, 
            weight=weight,
            constraint_type=constraint_type
        )
    
    def get_basin_list(self) -> List[BasinAttractor]:
        """Get list of all basin attractors."""
        return list(self.basins.values())
    
    def compute_alignment_score(self, point: np.ndarray) -> float:
        """
        Compute how well a point aligns with the topology.
        
        Higher scores indicate better alignment with the virtue structure.
        
        Args:
            point: Position in state space
            
        Returns:
            Alignment score
        """
        if not self.basins:
            return 0.0
        
        # Score based on proximity to virtue basins
        min_distances = []
        for basin in self.basins.values():
            distance = np.linalg.norm(basin.center - point)
            min_distances.append(distance)
        
        # Lower average distance = higher alignment
        avg_distance = np.mean(min_distances)
        return 1.0 / (1.0 + avg_distance)
    
    def validate_constraints(self) -> bool:
        """
        Validate that all geometric constraints are satisfied.
        
        Returns:
            True if topology is valid
        """
        # Check for cycles in required relationships
        try:
            cycles = list(nx.simple_cycles(self.graph))
            
            # Check if any cycles involve 'requires' constraints
            for cycle in cycles:
                for i in range(len(cycle)):
                    from_node = cycle[i]
                    to_node = cycle[(i + 1) % len(cycle)]
                    if self.graph[from_node][to_node].get('constraint_type') == 'requires':
                        return False  # Circular requirements are invalid
            
            return True
        except (nx.NetworkXError, KeyError) as e:
            # If there's an error analyzing the graph, consider it invalid
            return False
    
    def get_virtue_strengths(self) -> Dict[str, float]:
        """Get the strength of each virtue basin."""
        return {name: basin.strength for name, basin in self.basins.items()}
    
    def __repr__(self) -> str:
        n_virtues = len(self.basins)
        n_relationships = self.graph.number_of_edges()
        return (f"VirtueTopology(virtues={n_virtues}, "
                f"relationships={n_relationships}, dimension={self.dimension})")


class SoulTemplate:
    """
    A soul template is a validated topology that guarantees agent alignment.
    
    Soul templates are discovered through evolutionary simulation and
    represent stable configurations in the virtue space.
    """
    
    def __init__(self, topology: VirtueTopology, fitness: float = 0.0):
        """
        Initialize a soul template.
        
        Args:
            topology: The virtue topology structure
            fitness: Fitness score from evolutionary simulation
        """
        self.topology = topology
        self.fitness = fitness
        self.generation = 0
    
    def mutate(self, mutation_rate: float = 0.1) -> 'SoulTemplate':
        """
        Create a mutated copy of this soul template.
        
        Args:
            mutation_rate: Probability and magnitude of mutations
            
        Returns:
            New mutated soul template
        """
        # Create a copy of the topology
        new_topology = VirtueTopology(self.topology.dimension)
        
        # Copy virtues with potential mutations
        for name, basin in self.topology.basins.items():
            # Mutate center position
            if np.random.random() < mutation_rate:
                noise = np.random.randn(self.topology.dimension) * mutation_rate
                new_center = basin.center + noise
            else:
                new_center = basin.center.copy()
            
            # Mutate strength
            if np.random.random() < mutation_rate:
                new_strength = basin.strength * (1.0 + np.random.randn() * mutation_rate)
                new_strength = max(0.1, new_strength)  # Keep positive
            else:
                new_strength = basin.strength
            
            new_topology.add_virtue(name, new_center, new_strength)
        
        # Copy relationships
        for from_v, to_v, data in self.topology.graph.edges(data=True):
            new_topology.add_relationship(
                from_v, to_v, 
                data.get('weight', 1.0),
                data.get('constraint_type', 'supports')
            )
        
        return SoulTemplate(new_topology, fitness=0.0)
    
    def crossover(self, other: 'SoulTemplate') -> 'SoulTemplate':
        """
        Create offspring by combining two soul templates.
        
        Args:
            other: Another soul template to combine with
            
        Returns:
            New soul template combining features of both parents
        """
        new_topology = VirtueTopology(self.topology.dimension)
        
        # Combine virtues from both parents
        all_virtues = set(self.topology.basins.keys()) | set(other.topology.basins.keys())
        
        for name in all_virtues:
            if name in self.topology.basins and name in other.topology.basins:
                # Average the centers from both parents
                center1 = self.topology.basins[name].center
                center2 = other.topology.basins[name].center
                new_center = (center1 + center2) / 2.0
                
                strength1 = self.topology.basins[name].strength
                strength2 = other.topology.basins[name].strength
                new_strength = (strength1 + strength2) / 2.0
            elif name in self.topology.basins:
                basin = self.topology.basins[name]
                new_center = basin.center
                new_strength = basin.strength
            else:
                basin = other.topology.basins[name]
                new_center = basin.center
                new_strength = basin.strength
            
            new_topology.add_virtue(name, new_center, new_strength)
        
        return SoulTemplate(new_topology, fitness=0.0)
    
    def is_valid(self) -> bool:
        """Check if this soul template satisfies all constraints."""
        return self.topology.validate_constraints()
    
    def __repr__(self) -> str:
        return (f"SoulTemplate(fitness={self.fitness:.3f}, "
                f"generation={self.generation}, "
                f"topology={self.topology})")
