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

### Prerequisites

- Python 3.10+
- Docker (for FalkorDB)

### Installation

```bash
# Start FalkorDB
docker-compose up -d

# Install the package (editable mode for development)
pip install -e .

# Or with optional features:
pip install -e ".[server]"  # WebSocket server support
pip install -e ".[llm]"     # LLM integration (Anthropic)
pip install -e ".[dev]"     # Development tools (pytest, etc.)
pip install -e ".[all]"     # Everything
```

### Basic Usage

```bash
# Initialize the graph
soul-kiln init

# Check status
soul-kiln status

# Run the kiln evolution with mercy
soul-kiln kiln --population 10 --generations 20
```

## Commands

The main CLI is available via the `soul-kiln` command after installation:

```bash
# Core commands
soul-kiln init              # Initialize graph with tiers
soul-kiln reset --confirm   # Clear all data
soul-kiln status            # Show status with tiers
soul-kiln kiln              # Run evolution with mercy

# Agent commands
soul-kiln spawn             # Create new agent
soul-kiln test <agent_id>   # Test coherence (two-tier)
soul-kiln inspect <agent_id># Introspect with warnings

# Mercy commands
soul-kiln warnings <agent_id>  # Show active warnings
soul-kiln lessons              # Show collective lessons

# Info commands
soul-kiln virtues           # List virtues with tiers
soul-kiln tiers             # Explain two-tier model
soul-kiln agents            # List active agents
soul-kiln health            # Check graph health

# Advanced commands
soul-kiln gestalt <agent_id>        # Holistic character analysis
soul-kiln decide <agent_id> <sit>   # Generate action distribution
soul-kiln compare <agent1> <agent2> # Compare two agents
soul-kiln situations                # List available situations
```

### Alternative: Running as module

```bash
python -m src.main <command>
```

## Configuration

Configuration is stored in `config.yml`:

```yaml
graph:
  host: localhost
  port: 6379
  name: virtue_basin

virtues:
  foundation_threshold: 0.99
  aspirational_threshold: 0.80

mercy:
  max_warnings: 3
  warning_decay_hours: 24

kiln:
  population_size: 10
  max_generations: 50
```

## Environment Variables

- `FALKORDB_HOST` - Override graph host (default: localhost)
- `FALKORDB_PORT` - Override graph port (default: 6379)
- `ANTHROPIC_API_KEY` - API key for LLM features (optional)

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
|  |                |   Store     |                         ||
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
├── pyproject.toml           # Package configuration (single source of truth)
├── requirements.txt         # Derived from pyproject.toml
├── config.yml              # Runtime configuration
├── docker-compose.yml
├── src/
│   ├── main.py             # Entry point
│   ├── models.py           # Data models
│   ├── constants.py        # System constants
│   ├── graph/              # Graph database layer
│   │   ├── client.py       # Singleton GraphClient
│   │   ├── substrate.py    # Connection-managed GraphSubstrate
│   │   ├── store.py        # Unified GraphStore interface
│   │   └── safe_parse.py   # Safe JSON/dict parsing (no eval)
│   ├── virtues/
│   │   ├── anchors.py      # 19 virtues
│   │   └── tiers.py        # Foundation vs aspirational
│   ├── functions/          # Core dynamics
│   ├── mercy/              # Mercy system
│   ├── knowledge/          # Shared knowledge pool
│   ├── kiln/               # Evolution loop
│   ├── vessels/            # Agent runtime (sessions, contexts)
│   ├── theatre/            # Conversational theatre
│   ├── transport/          # WebSocket server
│   └── cli/                # CLI interface
├── scripts/                # Utility scripts
└── tests/                  # Test suite
```

## Running Tests

```bash
# Run all tests
pytest tests/

# Run with coverage
pytest tests/ --cov=src

# Run specific test file
pytest tests/test_safe_parse.py -v
```

## Development

```bash
# Install with dev dependencies
pip install -e ".[dev]"

# Format code
black src tests

# Lint
ruff src tests

# Type check
mypy src
```

## WebSocket Server (Optional)

For real-time conversational theatre features:

```bash
# Install server dependencies
pip install -e ".[server]"

# Run the server (from Python)
python -c "
from src.transport.server import create_server, create_fastapi_app
import uvicorn
server = create_server()
app = create_fastapi_app(server)
uvicorn.run(app, host='0.0.0.0', port=8000)
"
```

## Security Notes

- No `eval()` on persisted data - uses JSON + `ast.literal_eval` for safety
- Graph data is parsed through safe_parse utilities
- See `tests/test_safe_parse.py` for security test suite

## BMAD Specification

See `docs/bmad/specs/virtue-basin-platform.md` for the full BMAD-compliant specification.
