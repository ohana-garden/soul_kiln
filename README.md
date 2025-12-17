# Soul Kiln

A platform for creating ethical, cooperating communities of AI agents through conversation.

## What This Is

Soul Kiln births new agents by having conversations with existing agents. Each new agent inherits values, learns boundaries, and joins a community built on trust. The result: agent collectives that cooperate ethically because cooperation is encoded in their identity.

## How It Works

1. **Conversational Creation**: New agents are created through dialogue with existing agents who understand the community's values
2. **Identity Through Graph**: Each agent's moral topology is stored as a knowledge graph of virtues, beliefs, duties (kuleana), memories, and voice patterns
3. **Persona Capsules**: When an agent needs to act, their full identity compiles into an LLM-ready capsule with values, preferences, and boundaries
4. **Collective Learning**: When agents fail or succeed, those lessons propagate to the whole community

## Core Concepts

### Virtue Topology
Agents have virtue anchors that act as basins of attraction. Trustworthiness is foundational (99% threshold). Other virtues allow growth and individuality.

### Kuleana (Sacred Duty)
Hawaiian concept of responsibility that flows both ways. An agent's duties aren't just tasks—they're commitments that shape identity.

### Lore
Foundational narratives that anchor identity. Some lore is immutable (origin stories); other lore evolves with the agent.

### Persona Capsules
Compiled artifacts that condition LLM behavior. Contains:
- **Values**: What matters, weighted and ranked
- **Boundaries**: Hard limits that cannot be crossed
- **Preferences**: Soft guidelines for behavior
- **Voice**: Communication patterns and style

## Quick Start

```bash
# Start FalkorDB
docker-compose up -d

# Install dependencies
pip install -r requirements.txt

# Initialize the community
python -m src.main init

# Create the first agent
python -m src.main spawn

# Compile a persona for LLM use
python -m src.main persona <agent_id>
```

## Key Commands

```bash
# Community management
python -m src.main init              # Initialize virtue topology
python -m src.main status            # Community health
python -m src.main agents            # List all agents

# Agent lifecycle
python -m src.main spawn             # Birth new agent
python -m src.main test <agent_id>   # Test coherence
python -m src.main inspect <agent_id># Deep introspection

# Identity systems
python -m src.main persona <agent_id>      # Compile persona capsule
python -m src.main persona-for <agent_id> <context>  # Context-specific persona
python -m src.main kuleana <agent_id>      # View sacred duties
python -m src.main beliefs <agent_id>      # View belief system
python -m src.main lore <agent_id>         # View foundational narratives

# Community patterns
python -m src.main archetype-patterns      # Population behavior patterns
python -m src.main lessons                 # Collective learnings
```

## Architecture

```
Soul Kiln
├── Virtue Topology (graph)
│   ├── Virtue Anchors (19 virtues, tiered)
│   ├── Affinities (virtue relationships)
│   └── Agent bindings
│
├── Proxy Agent Subsystems
│   ├── Kuleana (duties)
│   ├── Skills (capabilities)
│   ├── Beliefs (convictions)
│   ├── Lore (narratives)
│   ├── Voice (expression)
│   ├── Memory (experience)
│   ├── Identity (integration)
│   └── Knowledge (facts + domains)
│
├── Persona System
│   ├── Capsule compilation
│   ├── Temporal facts
│   ├── Community patterns
│   └── Boundary enforcement
│
├── Dynamics
│   ├── Spread functions
│   ├── Coherence testing
│   └── Attractor basins
│
└── Mercy System
    ├── Warnings before dissolution
    ├── Growth-as-coherence
    └── Lesson preservation
```

## The Philosophy

Traditional agent systems optimize for capability. Soul Kiln optimizes for character.

An agent built here doesn't just *do* ethical things—it *is* ethical. Its identity graph makes cooperation natural, boundaries clear, and growth possible.

When agents fail, they fail with dignity. Lessons are preserved. The community learns. Trust remains foundational.

## Project Structure

```
soul_kiln/
├── src/
│   ├── virtues/       # Virtue anchors and tiers
│   ├── graph/         # FalkorDB client and queries
│   ├── kiln/          # Evolution simulation
│   ├── mercy/         # Empathetic evaluation
│   ├── persona/       # Capsule compilation
│   ├── kuleana/       # Sacred duties
│   ├── skills/        # Capabilities
│   ├── beliefs/       # Convictions
│   ├── lore/          # Narratives
│   ├── voice/         # Expression patterns
│   ├── memory/        # Episodic memory
│   ├── identity/      # Integration layer
│   ├── knowledge/     # Facts and domains
│   ├── dynamics/      # Spread and activation
│   ├── evolution/     # Topology evolution
│   ├── functions/     # Core math
│   ├── utils/         # Shared utilities
│   └── cli/           # Command interface
└── tests/
```

## Running Tests

```bash
pytest tests/
```
