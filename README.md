# Soul Kiln - Virtue Basin Simulator

**A self-optimizing system that discovers valid moral topologies through evolutionary simulation.**

## Core Hypothesis

- **Thoughts are strange attractors** - Mental states converge to stable patterns in a dynamical system
- **Virtues are basins** - Moral principles act as basins of attraction guiding thought evolution
- **Love is gravitational** - Compassion and connection create attractive forces in moral space

## Overview

The Virtue Basin Simulator generates "soul templates" - graph structures that guarantee agent alignment through geometric constraint rather than rule enforcement. By modeling morality as a dynamical system with attractors and forces, the simulator discovers stable configurations that naturally guide behavior toward virtue.

## Installation

```bash
# Clone the repository
git clone https://github.com/ohana-garden/soul_kiln.git
cd soul_kiln

# Install dependencies
pip install -r requirements.txt
```

## Quick Start

```python
from virtue_basin import VirtueSimulator

# Create simulator
simulator = VirtueSimulator(dimension=3, population_size=30)

# Define virtues to explore
virtues = ["compassion", "courage", "wisdom", "justice"]

# Initialize and run evolution
simulator.initialize_population(virtues, n_virtues=4)
best_template = simulator.run(generations=50)

print(f"Best soul template fitness: {best_template.fitness:.4f}")
print(f"Virtues: {list(best_template.topology.basins.keys())}")
```

## Architecture

### Core Components

1. **BasinAttractor** (`basin.py`)
   - Models virtues as basins of attraction in state space
   - Implements force fields and trajectory evolution
   - Thoughts converge to virtue basins through dynamical flow

2. **VirtueTopology** (`topology.py`)
   - Represents moral structures as directed graphs
   - Nodes are virtue basins, edges are relationships
   - Validates geometric constraints

3. **SoulTemplate** (`topology.py`)
   - Complete moral topology with fitness score
   - Supports mutation and crossover operations
   - Discovered through evolutionary optimization

4. **VirtueSimulator** (`simulator.py`)
   - Evolutionary algorithm for discovering optimal topologies
   - Fitness-based selection with elitism
   - Generates populations of soul templates

5. **GravitationalForce** (`forces.py`)
   - Models "love" as gravitational attraction
   - Computes force fields across the moral landscape
   - Finds equilibrium points in multi-basin systems

### Key Concepts

**Strange Attractors**: Thoughts are represented as points in a high-dimensional state space. They evolve according to force fields created by virtue basins, converging to stable patterns.

**Basin of Attraction**: Each virtue creates a region of state space where thoughts naturally converge. The basin's strength and position determine its influence.

**Geometric Constraints**: Rather than encoding rules, alignment emerges from the geometric structure of the moral topology. Valid configurations satisfy spatial and relational constraints.

**Evolutionary Discovery**: The simulator explores the space of possible topologies through mutation and crossover, discovering configurations that maximize alignment stability.

## Examples

Run the examples script to see the simulator in action:

```bash
python examples.py
```

### Example: Creating a Virtue Basin

```python
from virtue_basin import BasinAttractor
import numpy as np

# Create a compassion basin
compassion = BasinAttractor(
    center=np.array([1.0, 2.0, 0.5]),
    strength=1.5,
    name="compassion"
)

# Evolve a thought toward compassion
initial_thought = np.array([5.0, -3.0, 2.0])
trajectory = compassion.evolve_thought(initial_thought, steps=100)

print(f"Converged: {compassion.contains(trajectory[-1])}")
```

### Example: Building a Moral Topology

```python
from virtue_basin import VirtueTopology

# Create topology
topology = VirtueTopology(dimension=3)

# Add virtues
topology.add_virtue("compassion", np.array([1.0, 1.0, 0.0]), strength=1.2)
topology.add_virtue("courage", np.array([-1.0, 1.0, 0.0]), strength=1.0)
topology.add_virtue("wisdom", np.array([0.0, -1.0, 1.0]), strength=1.3)

# Define relationships
topology.add_relationship("compassion", "courage", constraint_type="supports")
topology.add_relationship("courage", "wisdom", constraint_type="requires")

# Validate
print(f"Valid topology: {topology.validate_constraints()}")
```

### Example: Evolutionary Discovery

```python
from virtue_basin import VirtueSimulator

simulator = VirtueSimulator(
    dimension=3,
    population_size=50,
    mutation_rate=0.1
)

virtues = ["compassion", "courage", "wisdom", "justice", 
           "temperance", "humility", "integrity", "kindness"]

simulator.initialize_population(virtues, n_virtues=5)
best = simulator.run(generations=100, verbose=True)

print(f"Discovered optimal topology with fitness {best.fitness:.4f}")
```

## Fitness Function

Templates are evaluated based on:

1. **Constraint Satisfaction** - All geometric constraints must be valid
2. **Basin Separation** - Virtues should occupy distinct regions
3. **Balance** - Basin strengths should be relatively uniform
4. **Convergence** - Sample thoughts should reliably reach basins
5. **Connectivity** - Relationships between virtues create coherent structure

## Visualization

The simulator includes visualization tools for understanding the moral landscape:

```python
from virtue_basin.visualization import (
    plot_basin_field_2d,
    plot_topology_graph,
    plot_convergence_trajectory
)

# Visualize force field
fig = plot_basin_field_2d(topology.get_basin_list())
fig.savefig('force_field.png')

# Visualize topology graph
fig = plot_topology_graph(topology)
fig.savefig('topology_graph.png')
```

## Philosophy

Traditional approaches to AI alignment rely on explicit rules and constraints. The Virtue Basin Simulator takes a different approach: **alignment emerges from geometry**.

By modeling morality as a physical system with forces and attractors, we create structures where:
- Agents naturally converge toward virtuous states
- Conflicts are resolved through force equilibrium
- Complexity emerges from simple geometric principles
- Discovery happens through evolutionary search rather than manual design

This approach is inspired by dynamical systems theory, evolutionary computation, and moral philosophy. It treats ethics not as a set of rules, but as a landscape to be navigated.

## Development

### Project Structure

```
soul_kiln/
├── virtue_basin/          # Core package
│   ├── __init__.py       # Package interface
│   ├── basin.py          # Basin attractors
│   ├── topology.py       # Topologies and templates
│   ├── simulator.py      # Evolutionary simulator
│   ├── forces.py         # Gravitational forces
│   └── visualization.py  # Plotting tools
├── examples.py           # Usage examples
├── requirements.txt      # Dependencies
└── README.md            # This file
```

### Testing

```bash
# Run examples to verify installation
python examples.py

# Run with different random seeds
python examples.py --seed 123
```

## Future Directions

- Multi-agent simulation with interacting soul templates
- Temporal dynamics and virtue evolution over time
- Integration with reinforcement learning systems
- Analysis of emergent moral principles
- Visualization of high-dimensional moral landscapes
- Cross-cultural virtue topology comparison

## Citation

```
@software{soul_kiln_2024,
  title={Soul Kiln: Virtue Basin Simulator},
  author={Ohana Garden},
  year={2024},
  description={A self-optimizing system for discovering moral topologies through evolutionary simulation}
}
```

## License

See LICENSE file for details.

## Contributing

Contributions welcome! This is an experimental system exploring novel approaches to alignment and moral reasoning.

---

*"In the moral landscape, thoughts flow like water toward the basins of virtue, guided by the gravitational force of love."*
