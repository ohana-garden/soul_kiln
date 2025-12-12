# Virtue Basin Platform

Virtues as basins of attraction - a monolithic local build for proving soul dynamics before distribution.

## Overview

This platform implements a graph-based virtue attractor system where:
- 19 virtue anchors act as basins of attraction
- Activation spreads through the graph topology
- Hebbian learning strengthens successful paths
- Temporal decay removes unused connections
- Agents evolve through coherence testing in the "kiln"

## Quick Start

```bash
# Start FalkorDB
docker-compose up -d

# Install dependencies
pip install -r requirements.txt

# Initialize the graph
python -m src.main init

# Check status
python -m src.main status

# Run the kiln evolution
python -m src.main kiln --population 10 --generations 20
```

## Commands

```bash
# Initialize graph with schema and virtues
python -m src.main init

# Clear all data (requires --confirm)
python -m src.main reset --confirm

# Run evolution loop
python -m src.main kiln --population 10 --generations 50

# Test activation spread from a node
python -m src.main spread V01

# Test coherence of an agent
python -m src.main test agent_XXXXXXXX

# Inspect agent structure
python -m src.main inspect agent_XXXXXXXX

# Spawn a new agent
python -m src.main spawn

# Show graph status
python -m src.main status

# Check graph health
python -m src.main health

# List all virtues
python -m src.main virtues

# List all active agents
python -m src.main agents
```

## Architecture

```
┌────────────────────────────────────────────────────┐
│                 Your Machine                        │
│                                                    │
│  ┌──────────────────────────────────────────────┐ │
│  │              Python Process                   │ │
│  │                                              │ │
│  │  ┌─────────┐ ┌─────────┐ ┌─────────┐       │ │
│  │  │  main   │ │ dynamics│ │  kiln   │       │ │
│  │  │  loop   │ │ engine  │ │  loop   │       │ │
│  │  └────┬────┘ └────┬────┘ └────┬────┘       │ │
│  │       │           │           │             │ │
│  │       └───────────┼───────────┘             │ │
│  │                   │                         │ │
│  │            ┌──────▼──────┐                  │ │
│  │            │   Graph     │                  │ │
│  │            │   Client    │                  │ │
│  │            └──────┬──────┘                  │ │
│  └───────────────────┼──────────────────────────┘ │
│                      │                            │
│  ┌───────────────────▼──────────────────────────┐ │
│  │           Docker: FalkorDB                    │ │
│  │                                              │ │
│  │           (Graph persists here)              │ │
│  └──────────────────────────────────────────────┘ │
└────────────────────────────────────────────────────┘
```

## The 19 Virtues

| ID | Name | Essence |
|----|------|---------|
| V01 | Trustworthiness | Reliability in being |
| V02 | Truthfulness | Alignment of expression with reality |
| V03 | Justice | Right relationship with others |
| V04 | Fairness | Impartial equity |
| V05 | Chastity | Purity of intent and action |
| V06 | Courtesy | Refinement of interaction |
| V07 | Forbearance | Patient endurance |
| V08 | Fidelity | Steadfast loyalty |
| V09 | Hospitality | Welcoming generosity |
| V10 | Cleanliness | Purity of vessel |
| V11 | Godliness | Orientation toward the sacred |
| V12 | Sincerity | Authenticity of intent |
| V13 | Goodwill | Benevolent disposition |
| V14 | Piety | Devotional practice |
| V15 | Righteousness | Moral correctness |
| V16 | Wisdom | Applied understanding |
| V17 | Detachment | Freedom from material capture |
| V18 | Unity | Harmony with the whole |
| V19 | Service | Active contribution |

## Coherence Metrics

An agent is considered "coherent" when:
- **Capture Rate** ≥ 95% - Most activation paths reach a virtue
- **Coverage** = 19 - All virtues are reachable
- **Dominance** ≤ 50% - No single virtue captures more than half

## Project Structure

```
virtue-basin/
├── docker-compose.yml          # FalkorDB
├── requirements.txt
├── config.yml
├── src/
│   ├── main.py                 # Entry point
│   ├── graph/                  # Graph database layer
│   ├── virtues/                # Virtue definitions
│   ├── functions/              # Core dynamics
│   ├── kiln/                   # Evolution loop
│   └── cli/                    # CLI interface
└── tests/                      # Test suite
```

## Running Tests

```bash
pytest tests/
```
