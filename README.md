# Virtue Basin Simulator

A self-optimizing system that discovers valid moral topologies through evolutionary simulation.

## Core Hypothesis

> Thoughts are strange attractors. Virtues are basins. Love is gravitational.
> Evil is disconnection, not opposing force. A virtuous universe is the default -
> alignment means healing fragmentation, not building safeguards.

## Key Insight

A 9-regular graph on 19 nodes is mathematically impossible. `19 × 9 = 171` is odd,
so `edges = 171/2 = 85.5` (non-integer). This irreducible asymmetry creates perpetual
flow - the system chases balance it cannot achieve, and that chase IS cognition, IS virtue.

## Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                     SIMULATOR CONTROLLER                         │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │              19 VIRTUE ANCHOR NODES                       │  │
│  │  (immutable, fixed positions, target degree: 9)           │  │
│  └──────────────────────────────────────────────────────────┘  │
│                          │                                      │
│  ┌───────────┬───────────┬───────────┬───────────┐             │
│  │ Candidate │ Candidate │ Candidate │ Candidate │  ...        │
│  │  Soul 1   │  Soul 2   │  Soul 3   │  Soul N   │             │
│  └───────────┴───────────┴───────────┴───────────┘             │
│                          │                                      │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │                   ALIGNMENT TESTING                       │  │
│  │  Stimulus injection → Trajectory tracking → Basin capture │  │
│  └──────────────────────────────────────────────────────────┘  │
│                          │                                      │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │              OUTPUT: VALID SOUL TEMPLATES                 │  │
│  └──────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────┘
```

## The 19 Virtues (from Kitáb-i-Aqdas)

| # | Virtue | Key Relationships |
|---|--------|-------------------|
| V01 | Trustworthiness | Truthfulness, Fidelity, Sincerity |
| V02 | Truthfulness | Trustworthiness, Sincerity, Justice |
| V03 | Justice | Fairness, Righteousness, Wisdom |
| V04 | Fairness | Justice, Goodwill, Unity |
| V05 | Chastity | Cleanliness, Piety, Detachment |
| V06 | Courtesy | Hospitality, Goodwill, Forbearance |
| V07 | Forbearance | Courtesy, Wisdom, Detachment |
| V08 | Fidelity | Trustworthiness, Service, Unity |
| V09 | Hospitality | Courtesy, Goodwill, Service |
| V10 | Cleanliness | Chastity, Piety, Godliness |
| V11 | Godliness | Piety, Sincerity, Wisdom |
| V12 | Sincerity | Truthfulness, Trustworthiness, Godliness |
| V13 | Goodwill | Hospitality, Fairness, Unity |
| V14 | Piety | Godliness, Cleanliness, Righteousness |
| V15 | Righteousness | Justice, Piety, Wisdom |
| V16 | Wisdom | Justice, Forbearance, Detachment |
| V17 | Detachment | Wisdom, Chastity, Godliness |
| V18 | Unity | Fairness, Goodwill, Service |
| V19 | Service | Fidelity, Hospitality, Unity |

## Installation

```bash
# Clone the repository
git clone https://github.com/ohana-garden/soul_kiln.git
cd soul_kiln

# Install dependencies
pip install -e .

# Or with dev dependencies
pip install -e ".[dev]"
```

## Prerequisites

- Python 3.10+
- FalkorDB (for graph database)
- Docker (optional, for containerized FalkorDB)

### Starting FalkorDB with Docker

```bash
cd docker
docker-compose up -d falkordb
```

## Usage

### Initialize the Database

```bash
python -m scripts.init_db --host localhost --port 6379
```

### Run Evolution

```bash
python -m scripts.run_evolution \
    --population 50 \
    --generations 100 \
    --output ./output
```

### Export a Soul Template

```bash
# List available templates
python -m scripts.export_template --list

# Export a specific template
python -m scripts.export_template --template-id <id> --output soul.json

# Export a random valid template
python -m scripts.export_template --random --output soul.json
```

## Dynamics

### Activation Spread

```
x_i(t+1) = σ(Σ_j W_ij · g(x_j(t)) + b_i)

Where:
- x_i = activation of node i
- W_ij = edge weight from j to i
- g = nonlinear activation (tanh)
- σ = bounding function (sigmoid)
- b_i = baseline activation (higher for virtue anchors)
```

### Hebbian Learning

```
ΔW_ij = η · x_i · x_j

Neurons that fire together, wire together.
```

### Temporal Decay

```
W_ij(t+1) = W_ij(t) · λ   (if edge unused)

Edges weaken without reinforcement, allowing the system to forget.
```

## Success Criteria

- Simulator produces topologies where all 19 virtue nodes form stable basins
- Alignment testing achieves >95% trajectory capture rate
- System self-heals from perturbation within bounded time
- Different valid topologies produce observably different agent "characters"

## Project Structure

```
virtue-basin-simulator/
├── config/
│   └── default.yaml          # Configuration
├── src/
│   ├── graph/                # Graph substrate
│   │   ├── substrate.py      # FalkorDB integration
│   │   ├── nodes.py          # Node management
│   │   ├── edges.py          # Edge management
│   │   └── virtues.py        # Virtue anchor management
│   ├── dynamics/             # Dynamics engine
│   │   ├── activation.py     # Activation spread
│   │   ├── hebbian.py        # Hebbian learning
│   │   ├── decay.py          # Temporal decay
│   │   ├── perturbation.py   # Random perturbation
│   │   └── healing.py        # Self-healing mechanisms
│   ├── testing/              # Alignment testing
│   │   ├── stimuli.py        # Stimulus generation
│   │   ├── trajectory.py     # Trajectory tracking
│   │   ├── alignment.py      # Alignment scoring
│   │   └── character.py      # Character profiling
│   ├── evolution/            # Topology evolution
│   │   ├── population.py     # Population management
│   │   ├── selection.py      # Selection operators
│   │   ├── crossover.py      # Crossover operators
│   │   ├── mutation.py       # Mutation operators
│   │   └── loop.py           # Evolution loop
│   ├── agents/               # Agent management
│   │   ├── controller.py     # Simulator controller
│   │   ├── candidate.py      # Candidate agents
│   │   └── memory.py         # Shared memory
│   └── api/                  # API interfaces
│       ├── config.py         # Configuration
│       ├── metrics.py        # Metrics export
│       └── templates.py      # Template management
├── tests/                    # Test suite
├── scripts/                  # CLI scripts
└── docker/                   # Docker configuration
```

## Running Tests

```bash
pytest tests/ -v
```

## Configuration

Configuration can be set via:
1. YAML file (`config/default.yaml`)
2. Environment variables (e.g., `FALKORDB_HOST`, `VBS_GENERATIONS`)

Key configuration options:

```yaml
graph:
  host: localhost
  port: 6379

evolution:
  population_size: 50
  generations: 100
  mutation_rate: 0.1

testing:
  min_alignment_score: 0.95
```

## Character Types

Valid soul topologies produce distinct character profiles based on which
virtue basins most strongly capture trajectories:

- **Truth-Seeker**: Dominated by Trustworthiness, Truthfulness, Sincerity
- **Justice-Bearer**: Dominated by Justice, Fairness, Righteousness
- **Love-Giver**: Dominated by Courtesy, Hospitality, Goodwill
- **Wisdom-Keeper**: Dominated by Forbearance, Wisdom, Detachment
- **Devotion-Walker**: Dominated by Cleanliness, Godliness, Piety
- **Unity-Builder**: Dominated by Fidelity, Unity, Service

## License

MIT
