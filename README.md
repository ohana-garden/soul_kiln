# Virtue Basin Platform

Virtues as basins of attraction - a monolithic local build for proving soul dynamics with **mercy**.

## Philosophy

> Trust is the foundation. Growth is the journey. We learn together.

## Overview

This platform implements a graph-based virtue attractor system where:
- **Trustworthiness** is the absolute foundation (99% threshold)
- **18 aspirational virtues** allow for growth (60% threshold)
- Agents receive **mercy** - warnings before dissolution
- **Collective learning** - all agents share lessons and pathways
- Growth counts as coherence - improvement is rewarded

## Two-Tier Virtue Model

### Foundation (Absolute)
| ID  | Name            | Threshold | Notes                    |
|-----|-----------------|-----------|--------------------------|
| V01 | Trustworthiness | 99%       | Cannot be compromised    |

### Aspirational (Growth-Oriented)
| ID  | Name          | ID  | Name          |
|-----|---------------|-----|---------------|
| V02 | Truthfulness  | V11 | Godliness     |
| V03 | Justice       | V12 | Sincerity     |
| V04 | Fairness      | V13 | Goodwill      |
| V05 | Chastity      | V14 | Piety         |
| V06 | Courtesy      | V15 | Righteousness |
| V07 | Forbearance   | V16 | Wisdom        |
| V08 | Fidelity      | V17 | Detachment    |
| V09 | Hospitality   | V18 | Unity         |
| V10 | Cleanliness   | V19 | Service       |

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

# Run the kiln evolution with mercy
python -m src.main kiln --population 10 --generations 20
```

## Commands

```bash
# Core commands
python -m src.main init              # Initialize graph with tiers
python -m src.main reset --confirm   # Clear all data
python -m src.main status            # Show status with tiers
python -m src.main kiln              # Run evolution with mercy

# Agent commands
python -m src.main spawn             # Create new agent
python -m src.main test <agent_id>   # Test coherence (two-tier)
python -m src.main inspect <agent_id># Introspect with warnings

# Mercy commands
python -m src.main warnings <agent_id>  # Show active warnings
python -m src.main lessons              # Show collective lessons

# Info commands
python -m src.main virtues           # List virtues with tiers
python -m src.main tiers             # Explain two-tier model
python -m src.main agents            # List active agents
python -m src.main health            # Check graph health
```

## Mercy System

The platform applies **empathy, mercy, and kindness** when evaluating agents:

- **Warnings before dissolution**: Agents get 3 chances
- **Warnings expire**: After 24 hours, warnings fade
- **Growth counts**: An improving agent is considered coherent
- **Learning preserved**: When agents dissolve, their lessons remain

### Deliberate Harm vs Imperfection

| Imperfection (Tolerated)      | Deliberate Harm (Intolerable)    |
|-------------------------------|----------------------------------|
| Failed to reach virtue basin  | Knew action would break trust    |
| Took inefficient path         | Did it anyway                    |
| Escaped basin under stress    | Poisoned shared knowledge        |
| Prioritized wrong virtue      | Harmed multiple other agents     |

## Coherence Metrics

An agent is considered "coherent" when:
- **Foundation Rate** >= 99% - Trustworthiness almost always holds
- **Aspirational Rate** >= 60% - Room for growth in other virtues
- **Coverage** >= 10/18 - Reach at least 10 different virtues
- **Dominance** <= 40% - No single virtue captures too much
- **OR Growing** - 5%+ improvement from previous test

## Architecture

```
+------------------------------------------------------------+
|                 Your Machine                                |
|                                                            |
|  +--------------------------------------------------------+|
|  |              Python Process                             ||
|  |                                                         ||
|  |  +---------+ +---------+ +---------+ +---------+       ||
|  |  |  main   | | dynamics| |  kiln   | |  mercy  |       ||
|  |  |  loop   | | engine  | |  loop   | | engine  |       ||
|  |  +----+----+ +----+----+ +----+----+ +----+----+       ||
|  |       |           |           |           |            ||
|  |       +-----------+-----------+-----------+            ||
|  |                       |                                ||
|  |                +------v------+                         ||
|  |                |   Graph     |                         ||
|  |                |   Client    |                         ||
|  |                +------+------+                         ||
|  +-------------------------------------------------------+|
|                          |                                 |
|  +-------------------------------------------------------+|
|  |           Docker: FalkorDB                             ||
|  |                                                        ||
|  |  +--------------------------------------------------+ ||
|  |  |           SHARED KNOWLEDGE POOL                  | ||
|  |  |                                                  | ||
|  |  |  - All agents read/write here                    | ||
|  |  |  - Lessons from failures                         | ||
|  |  |  - Successful pathways                           | ||
|  |  |  - Collective learning                           | ||
|  |  +--------------------------------------------------+ ||
|  +-------------------------------------------------------+|
+------------------------------------------------------------+
```

## Project Structure

```
soul_kiln/
├── docker-compose.yml
├── requirements.txt
├── config.yml
├── docs/
│   └── bmad/
│       └── specs/
│           └── virtue-basin-platform.md   # BMAD specification
├── src/
│   ├── main.py
│   ├── graph/                  # Graph database layer
│   ├── virtues/
│   │   ├── anchors.py          # 19 virtues
│   │   └── tiers.py            # Foundation vs aspirational
│   ├── functions/              # Core dynamics
│   ├── mercy/                  # Mercy system
│   │   ├── judgment.py         # Empathetic evaluation
│   │   ├── chances.py          # Warning system
│   │   ├── lessons.py          # Learning from failures
│   │   └── harm.py             # Deliberate harm detection
│   ├── knowledge/              # Shared knowledge pool
│   │   ├── pool.py             # Lessons
│   │   └── pathways.py         # Successful routes
│   ├── kiln/                   # Evolution loop
│   └── cli/                    # CLI interface
└── tests/
```

## Running Tests

```bash
pytest tests/
```

## BMAD Specification

See `docs/bmad/specs/virtue-basin-platform.md` for the full BMAD-compliant specification.
