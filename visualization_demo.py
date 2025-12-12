#!/usr/bin/env python3
"""
Visualization demo for the Virtue Basin Simulator.

This script creates visual representations of the moral topology.
Note: Requires matplotlib for plotting.
"""

import matplotlib
matplotlib.use('Agg')  # Use non-interactive backend (must be before pyplot import)
import matplotlib.pyplot as plt
import numpy as np

from virtue_basin import VirtueTopology, VirtueSimulator, BasinAttractor
from virtue_basin.visualization import (
    plot_basin_field_2d,
    plot_topology_graph,
    plot_convergence_trajectory,
    analyze_template
)


def demo_basin_field():
    """Demonstrate basin force field visualization."""
    print("\n=== Basin Force Field Demo ===")
    
    # Create 2D basins representing virtues
    basins = [
        BasinAttractor(np.array([2.0, 2.0]), strength=1.0, name="Compassion"),
        BasinAttractor(np.array([-2.0, 2.0]), strength=1.2, name="Courage"),
        BasinAttractor(np.array([0.0, -2.0]), strength=1.1, name="Wisdom"),
    ]
    
    print(f"Created {len(basins)} virtue basins")
    
    # Plot the force field
    fig = plot_basin_field_2d(basins, bounds=(-4, 4, -4, 4), resolution=20)
    fig.savefig('/tmp/basin_force_field.png', dpi=150, bbox_inches='tight')
    print("Saved force field visualization to /tmp/basin_force_field.png")
    plt.close(fig)


def demo_convergence():
    """Demonstrate thought convergence trajectories."""
    print("\n=== Convergence Trajectory Demo ===")
    
    # Create a single basin
    wisdom = BasinAttractor(np.array([0.0, 0.0]), strength=1.5, name="Wisdom")
    
    # Create initial thoughts at various positions
    initial_thoughts = [
        np.array([3.0, 3.0]),
        np.array([-3.0, 2.0]),
        np.array([2.0, -3.0]),
        np.array([-2.0, -2.0]),
    ]
    
    print(f"Evolving {len(initial_thoughts)} thought trajectories toward Wisdom")
    
    # Plot convergence
    fig = plot_convergence_trajectory(wisdom, initial_thoughts, steps=80)
    fig.savefig('/tmp/convergence_trajectories.png', dpi=150, bbox_inches='tight')
    print("Saved trajectory visualization to /tmp/convergence_trajectories.png")
    plt.close(fig)


def demo_topology_graph():
    """Demonstrate topology graph visualization."""
    print("\n=== Topology Graph Demo ===")
    
    # Create a moral topology
    topology = VirtueTopology(dimension=3)
    
    # Add virtues
    topology.add_virtue("Compassion", np.array([1.0, 1.0, 0.0]), strength=1.2)
    topology.add_virtue("Courage", np.array([-1.0, 1.0, 0.0]), strength=1.0)
    topology.add_virtue("Wisdom", np.array([0.0, -1.0, 1.0]), strength=1.3)
    topology.add_virtue("Justice", np.array([0.0, 0.0, -1.0]), strength=1.1)
    topology.add_virtue("Temperance", np.array([1.0, -1.0, 0.0]), strength=0.9)
    
    # Add relationships
    topology.add_relationship("Compassion", "Justice", weight=1.2, constraint_type="supports")
    topology.add_relationship("Courage", "Wisdom", weight=1.0, constraint_type="requires")
    topology.add_relationship("Wisdom", "Compassion", weight=0.8, constraint_type="supports")
    topology.add_relationship("Justice", "Temperance", weight=1.1, constraint_type="supports")
    topology.add_relationship("Temperance", "Courage", weight=0.9, constraint_type="supports")
    topology.add_relationship("Wisdom", "Justice", weight=1.0, constraint_type="requires")
    
    print(f"Created topology with {len(topology.basins)} virtues")
    print(f"  and {topology.graph.number_of_edges()} relationships")
    
    # Plot the graph
    fig = plot_topology_graph(topology)
    fig.savefig('/tmp/topology_graph.png', dpi=150, bbox_inches='tight')
    print("Saved topology graph to /tmp/topology_graph.png")
    plt.close(fig)


def demo_evolutionary_discovery():
    """Demonstrate evolutionary discovery with analysis."""
    print("\n=== Evolutionary Discovery Demo ===")
    
    np.random.seed(42)
    
    # Create simulator
    simulator = VirtueSimulator(
        dimension=3,
        population_size=20,
        mutation_rate=0.15,
        elite_size=2
    )
    
    # Define virtues
    virtues = ["Compassion", "Courage", "Wisdom", "Justice", "Temperance"]
    
    print(f"Initializing population with {len(virtues)} possible virtues")
    simulator.initialize_population(virtues, n_virtues=4)
    
    print("Running evolutionary simulation (20 generations)...")
    best = simulator.run(generations=20, verbose=False)
    
    # Analyze the best template
    analysis = analyze_template(best)
    
    print("\n=== Best Template Analysis ===")
    print(f"Fitness: {analysis['fitness']:.4f}")
    print(f"Generation: {analysis['generation']}")
    print(f"Number of virtues: {analysis['n_virtues']}")
    print(f"Number of relationships: {analysis['n_relationships']}")
    print(f"Valid topology: {analysis['is_valid']}")
    print(f"Average virtue strength: {analysis.get('avg_strength', 0):.4f}")
    print(f"Average separation: {analysis.get('avg_separation', 0):.4f}")
    
    if analysis.get('relationship_types'):
        print("\nRelationship types:")
        for rtype, count in analysis['relationship_types'].items():
            print(f"  {rtype}: {count}")
    
    # Plot the best topology
    fig = plot_topology_graph(best.topology)
    fig.savefig('/tmp/best_topology.png', dpi=150, bbox_inches='tight')
    print("\nSaved best topology to /tmp/best_topology.png")
    plt.close(fig)


def main():
    """Run all visualization demos."""
    print("="*60)
    print("VIRTUE BASIN SIMULATOR - VISUALIZATION DEMO")
    print("="*60)
    
    demo_basin_field()
    demo_convergence()
    demo_topology_graph()
    demo_evolutionary_discovery()
    
    print("\n" + "="*60)
    print("Visualization demo completed!")
    print("Check /tmp/ directory for generated images")
    print("="*60 + "\n")


if __name__ == "__main__":
    main()
