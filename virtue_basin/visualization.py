"""
Visualization tools for virtue basin simulator.

Provides plotting and analysis functions for understanding
the moral topology landscape.
"""

import matplotlib
matplotlib.use('Agg')  # Use non-interactive backend for headless environments
import matplotlib.pyplot as plt
from matplotlib import cm

import numpy as np
from typing import List, Optional
import networkx as nx

from .topology import VirtueTopology, SoulTemplate
from .basin import BasinAttractor
from .forces import GravitationalForce


def plot_basin_field_2d(
    basins: List[BasinAttractor],
    bounds: tuple = (-5, 5, -5, 5),
    resolution: int = 30,
    figsize: tuple = (10, 8)
) -> plt.Figure:
    """
    Plot the force field created by virtue basins in 2D.
    
    Args:
        basins: List of basin attractors
        bounds: (xmin, xmax, ymin, ymax)
        resolution: Grid resolution
        figsize: Figure size
        
    Returns:
        Matplotlib figure
    """
    if not basins or basins[0].dimension < 2:
        raise ValueError("Need at least 2D basins for 2D visualization")
    
    xmin, xmax, ymin, ymax = bounds
    
    # Create grid
    x = np.linspace(xmin, xmax, resolution)
    y = np.linspace(ymin, ymax, resolution)
    X, Y = np.meshgrid(x, y)
    
    # Compute potential field
    U = np.zeros_like(X)
    V = np.zeros_like(Y)
    
    grav = GravitationalForce()
    
    for i in range(resolution):
        for j in range(resolution):
            point = np.array([X[i, j], Y[i, j]])
            force = grav.compute_force(point, basins)
            U[i, j] = force[0]
            V[i, j] = force[1]
    
    # Create figure
    fig, ax = plt.subplots(figsize=figsize)
    
    # Plot vector field
    magnitude = np.sqrt(U**2 + V**2)
    ax.streamplot(X, Y, U, V, color=magnitude, cmap='viridis', density=1.5)
    
    # Plot basin centers
    for basin in basins:
        ax.plot(basin.center[0], basin.center[1], 'ro', markersize=10)
        ax.text(basin.center[0], basin.center[1] + 0.3, basin.name,
                ha='center', fontsize=9, fontweight='bold')
    
    ax.set_xlabel('Dimension 1')
    ax.set_ylabel('Dimension 2')
    ax.set_title('Virtue Basin Force Field')
    ax.grid(True, alpha=0.3)
    
    return fig


def plot_topology_graph(
    topology: VirtueTopology,
    figsize: tuple = (12, 8)
) -> plt.Figure:
    """
    Visualize the virtue topology as a graph.
    
    Args:
        topology: Virtue topology to visualize
        figsize: Figure size
        
    Returns:
        Matplotlib figure
    """
    fig, ax = plt.subplots(figsize=figsize)
    
    # Use spring layout for positioning
    pos = nx.spring_layout(topology.graph, k=2, iterations=50)
    
    # Draw nodes
    node_sizes = [topology.basins[node].strength * 500 for node in topology.graph.nodes()]
    nx.draw_networkx_nodes(
        topology.graph, pos, 
        node_size=node_sizes,
        node_color='lightblue',
        alpha=0.7,
        ax=ax
    )
    
    # Draw edges with different styles for different constraint types
    edge_colors = []
    edge_styles = []
    for u, v, data in topology.graph.edges(data=True):
        constraint = data.get('constraint_type', 'supports')
        if constraint == 'supports':
            edge_colors.append('green')
            edge_styles.append('solid')
        elif constraint == 'requires':
            edge_colors.append('blue')
            edge_styles.append('dashed')
        else:  # opposes
            edge_colors.append('red')
            edge_styles.append('dotted')
    
    nx.draw_networkx_edges(
        topology.graph, pos,
        edge_color=edge_colors,
        style=edge_styles,
        width=2,
        alpha=0.6,
        ax=ax,
        arrows=True,
        arrowsize=20
    )
    
    # Draw labels
    nx.draw_networkx_labels(
        topology.graph, pos,
        font_size=10,
        font_weight='bold',
        ax=ax
    )
    
    ax.set_title(f'Virtue Topology Graph\n{len(topology.basins)} virtues, '
                 f'{topology.graph.number_of_edges()} relationships')
    ax.axis('off')
    
    # Add legend
    from matplotlib.lines import Line2D
    legend_elements = [
        Line2D([0], [0], color='green', linewidth=2, label='Supports'),
        Line2D([0], [0], color='blue', linewidth=2, linestyle='--', label='Requires'),
        Line2D([0], [0], color='red', linewidth=2, linestyle=':', label='Opposes')
    ]
    ax.legend(handles=legend_elements, loc='upper right')
    
    return fig


def plot_convergence_trajectory(
    basin: BasinAttractor,
    initial_points: List[np.ndarray],
    steps: int = 100,
    figsize: tuple = (10, 8)
) -> plt.Figure:
    """
    Plot trajectories converging to a basin.
    
    Args:
        basin: Basin attractor
        initial_points: List of starting points
        steps: Number of evolution steps
        figsize: Figure size
        
    Returns:
        Matplotlib figure
    """
    if basin.dimension < 2:
        raise ValueError("Need at least 2D for trajectory visualization")
    
    fig, ax = plt.subplots(figsize=figsize)
    
    # Plot trajectories
    for i, point in enumerate(initial_points):
        trajectory = basin.evolve_thought(point, steps=steps)
        ax.plot(trajectory[:, 0], trajectory[:, 1], 
               alpha=0.6, linewidth=2, label=f'Trajectory {i+1}')
        ax.plot(trajectory[0, 0], trajectory[0, 1], 'go', markersize=8)
        ax.plot(trajectory[-1, 0], trajectory[-1, 1], 'rx', markersize=10)
    
    # Plot basin center
    ax.plot(basin.center[0], basin.center[1], 'r*', markersize=20, 
           label=f'Basin: {basin.name}')
    
    ax.set_xlabel('Dimension 1')
    ax.set_ylabel('Dimension 2')
    ax.set_title(f'Thought Trajectories Converging to "{basin.name}" Basin')
    ax.grid(True, alpha=0.3)
    ax.legend()
    
    return fig


def plot_fitness_evolution(
    fitness_history: List[float],
    figsize: tuple = (10, 6)
) -> plt.Figure:
    """
    Plot fitness evolution over generations.
    
    Args:
        fitness_history: List of best fitness values per generation
        figsize: Figure size
        
    Returns:
        Matplotlib figure
    """
    fig, ax = plt.subplots(figsize=figsize)
    
    generations = range(len(fitness_history))
    ax.plot(generations, fitness_history, linewidth=2, color='blue')
    ax.fill_between(generations, fitness_history, alpha=0.3)
    
    ax.set_xlabel('Generation')
    ax.set_ylabel('Best Fitness')
    ax.set_title('Evolutionary Fitness Over Time')
    ax.grid(True, alpha=0.3)
    
    return fig


def analyze_template(template: SoulTemplate) -> dict:
    """
    Analyze a soul template and return statistics.
    
    Args:
        template: Soul template to analyze
        
    Returns:
        Dictionary of analysis results
    """
    topology = template.topology
    basins = topology.get_basin_list()
    
    analysis = {
        'fitness': template.fitness,
        'generation': template.generation,
        'n_virtues': len(basins),
        'n_relationships': topology.graph.number_of_edges(),
        'is_valid': template.is_valid(),
        'dimension': topology.dimension,
    }
    
    if basins:
        strengths = [b.strength for b in basins]
        analysis['avg_strength'] = np.mean(strengths)
        analysis['std_strength'] = np.std(strengths)
        
        # Compute pairwise distances
        distances = []
        for i, b1 in enumerate(basins):
            for b2 in basins[i+1:]:
                distances.append(np.linalg.norm(b1.center - b2.center))
        
        if distances:
            analysis['avg_separation'] = np.mean(distances)
            analysis['min_separation'] = np.min(distances)
        else:
            analysis['avg_separation'] = 0.0
            analysis['min_separation'] = 0.0
    
    # Analyze relationship types
    relationship_types = {}
    for _, _, data in topology.graph.edges(data=True):
        constraint_type = data.get('constraint_type', 'supports')
        relationship_types[constraint_type] = relationship_types.get(constraint_type, 0) + 1
    
    analysis['relationship_types'] = relationship_types
    
    return analysis
