#!/usr/bin/env python3
"""
Example usage of the Virtue Basin Simulator.

Demonstrates:
- Creating virtue basins
- Running evolutionary simulation
- Analyzing results
- Visualization
"""

import numpy as np
from virtue_basin import (
    BasinAttractor,
    VirtueTopology,
    SoulTemplate,
    VirtueSimulator,
    GravitationalForce
)


def example_basic_basin():
    """Example: Basic basin attractor."""
    print("\n" + "="*60)
    print("EXAMPLE 1: Basic Basin Attractor")
    print("="*60)
    
    # Create a virtue basin
    compassion = BasinAttractor(
        center=np.array([1.0, 2.0, 0.5]),
        strength=1.5,
        name="compassion"
    )
    
    print(f"\nCreated basin: {compassion}")
    
    # Test a thought converging to the basin
    initial_thought = np.array([5.0, -3.0, 2.0])
    print(f"\nInitial thought position: {initial_thought}")
    
    trajectory = compassion.evolve_thought(initial_thought, steps=50)
    final_position = trajectory[-1]
    
    print(f"Final position after evolution: {final_position}")
    print(f"Distance to basin center: {np.linalg.norm(final_position - compassion.center):.4f}")
    print(f"Thought converged to basin: {compassion.contains(final_position)}")


def example_topology():
    """Example: Creating a virtue topology."""
    print("\n" + "="*60)
    print("EXAMPLE 2: Virtue Topology")
    print("="*60)
    
    # Create a topology with multiple virtues
    topology = VirtueTopology(dimension=3)
    
    # Add virtues
    topology.add_virtue("compassion", np.array([1.0, 1.0, 0.0]), strength=1.2)
    topology.add_virtue("courage", np.array([-1.0, 1.0, 0.0]), strength=1.0)
    topology.add_virtue("wisdom", np.array([0.0, -1.0, 1.0]), strength=1.3)
    topology.add_virtue("justice", np.array([0.0, 0.0, -1.0]), strength=1.1)
    
    # Add relationships
    topology.add_relationship("compassion", "justice", weight=1.2, constraint_type="supports")
    topology.add_relationship("courage", "wisdom", weight=1.0, constraint_type="requires")
    topology.add_relationship("wisdom", "compassion", weight=0.8, constraint_type="supports")
    
    print(f"\nCreated topology: {topology}")
    print(f"Valid constraints: {topology.validate_constraints()}")
    
    # Test alignment
    test_point = np.array([0.5, 0.5, 0.0])
    alignment = topology.compute_alignment_score(test_point)
    print(f"\nAlignment score for test point: {alignment:.4f}")
    
    # Show virtue strengths
    print("\nVirtue strengths:")
    for name, strength in topology.get_virtue_strengths().items():
        print(f"  {name}: {strength:.2f}")


def example_gravitational_force():
    """Example: Gravitational force field."""
    print("\n" + "="*60)
    print("EXAMPLE 3: Gravitational Force (Love)")
    print("="*60)
    
    # Create basins
    basins = [
        BasinAttractor(np.array([2.0, 0.0]), strength=1.0, name="virtue_a"),
        BasinAttractor(np.array([-2.0, 0.0]), strength=1.0, name="virtue_b"),
    ]
    
    # Create gravitational force
    gravity = GravitationalForce(strength=1.0)
    
    # Find equilibrium point
    initial = np.array([0.0, 3.0])
    equilibrium = gravity.find_equilibrium(initial, basins, max_iterations=1000)
    
    print(f"\nInitial position: {initial}")
    print(f"Equilibrium position: {equilibrium}")
    print(f"Force at equilibrium: {gravity.compute_force(equilibrium, basins)}")
    print(f"Potential at equilibrium: {gravity.potential_energy(equilibrium, basins):.4f}")


def example_evolutionary_simulation():
    """Example: Full evolutionary simulation."""
    print("\n" + "="*60)
    print("EXAMPLE 4: Evolutionary Simulation")
    print("="*60)
    
    # Define virtues to explore
    virtue_names = [
        "compassion", "courage", "wisdom", "justice",
        "temperance", "humility", "integrity", "kindness"
    ]
    
    # Create simulator
    simulator = VirtueSimulator(
        dimension=3,
        population_size=30,
        mutation_rate=0.15,
        elite_size=3
    )
    
    print(f"\nCreated simulator: {simulator}")
    
    # Initialize population
    simulator.initialize_population(virtue_names, n_virtues=5)
    print(f"Initialized population with {len(simulator.population)} templates")
    
    # Run evolution
    print("\nRunning evolutionary simulation...")
    best_template = simulator.run(generations=50, verbose=True)
    
    # Analyze results
    print("\n" + "-"*60)
    print("RESULTS")
    print("-"*60)
    print(f"\nBest template found: {best_template}")
    print(f"\nTopology details:")
    print(f"  Virtues: {list(best_template.topology.basins.keys())}")
    print(f"  Relationships: {best_template.topology.graph.number_of_edges()}")
    print(f"  Valid constraints: {best_template.is_valid()}")
    
    # Get statistics
    stats = simulator.get_statistics()
    print(f"\nPopulation statistics:")
    for key, value in stats.items():
        print(f"  {key}: {value}")


def example_soul_template_operations():
    """Example: Soul template mutation and crossover."""
    print("\n" + "="*60)
    print("EXAMPLE 5: Soul Template Operations")
    print("="*60)
    
    # Create a base template
    topology = VirtueTopology(dimension=2)
    topology.add_virtue("virtue_a", np.array([1.0, 0.0]), strength=1.0)
    topology.add_virtue("virtue_b", np.array([0.0, 1.0]), strength=1.2)
    topology.add_relationship("virtue_a", "virtue_b", constraint_type="supports")
    
    template = SoulTemplate(topology, fitness=0.8)
    print(f"\nOriginal template: {template}")
    print(f"  Virtue A center: {topology.basins['virtue_a'].center}")
    print(f"  Virtue B center: {topology.basins['virtue_b'].center}")
    
    # Mutate
    mutated = template.mutate(mutation_rate=0.2)
    print(f"\nMutated template: {mutated}")
    print(f"  Virtue A center: {mutated.topology.basins['virtue_a'].center}")
    print(f"  Virtue B center: {mutated.topology.basins['virtue_b'].center}")
    
    # Create another template for crossover
    topology2 = VirtueTopology(dimension=2)
    topology2.add_virtue("virtue_a", np.array([-1.0, 0.0]), strength=0.8)
    topology2.add_virtue("virtue_b", np.array([0.0, -1.0]), strength=1.5)
    template2 = SoulTemplate(topology2, fitness=0.7)
    
    # Crossover
    child = template.crossover(template2)
    print(f"\nChild from crossover: {child}")
    print(f"  Virtue A center: {child.topology.basins['virtue_a'].center}")
    print(f"  Virtue B center: {child.topology.basins['virtue_b'].center}")


def main():
    """Run all examples."""
    print("\n" + "="*60)
    print("VIRTUE BASIN SIMULATOR - EXAMPLES")
    print("="*60)
    print("\nCore Hypothesis:")
    print("  - Thoughts are strange attractors")
    print("  - Virtues are basins")
    print("  - Love is gravitational")
    
    np.random.seed(42)  # For reproducibility
    
    # Run examples
    example_basic_basin()
    example_topology()
    example_gravitational_force()
    example_soul_template_operations()
    example_evolutionary_simulation()
    
    print("\n" + "="*60)
    print("Examples completed successfully!")
    print("="*60 + "\n")


if __name__ == "__main__":
    main()
