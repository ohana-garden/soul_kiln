# BMAD Refactor: Agent Zero Paradigm

## Current Problem

The current implementation **wraps** Agent Zero instead of **being** Agent Zero.

```
WRONG (Current):
┌─────────────────────────────────────┐
│  Python Code (Soul Kiln)            │  ← Control lives here
│  └── Wraps Agent Zero               │
│      └── Uses FalkorDB              │
└─────────────────────────────────────┘

RIGHT (Target):
┌─────────────────────────────────────┐
│  Agent Zero (Prompts + Tools)       │  ← Control lives here
│  └── Graphiti (Knowledge Flow)      │
│      └── FalkorDB (Persistence)     │
└─────────────────────────────────────┘
```

## The Three Pillars

| Layer | Technology | Role |
|-------|------------|------|
| **Operations** | Agent Zero | All agent behavior defined in prompts. Tools are capabilities. Extensions hook lifecycle. |
| **Flow** | Graphiti | Temporal knowledge graph. Bi-temporal edges. Incremental updates. Semantic search. |
| **Persistence** | FalkorDB | Graph storage. Node/edge persistence. Query execution. |

## BMAD Phases

### BUILD: Agent Zero Native Architecture

**B1: Agent Definitions as Prompts**

Current: Python dataclasses define agents
Target: Prompts define agents

```
vendor/agent-zero/prompts/
├── default/                    # Agent Zero defaults
└── ambassador/                 # Soul Kiln Ambassador
    ├── agent.system.md         # Core identity, taboos, commitments
    ├── agent.system.tools.md   # Available tools
    ├── agent.system.kuleana.md # Duty definitions
    ├── agent.system.lore.md    # Origin story, lineage
    └── agent.system.voice.md   # Communication patterns
```

**B2: Subsystems as Instruments**

Current: Python modules (src/kuleana/, src/beliefs/, etc.)
Target: Agent Zero instruments

```
vendor/agent-zero/instruments/
├── default/
└── soul_kiln/
    ├── virtue_basin/
    │   ├── check_alignment.md    # Instrument definition
    │   └── check_alignment.py    # Implementation
    ├── kuleana/
    │   ├── activate_duty.md
    │   └── activate_duty.py
    ├── taboo/
    │   ├── enforce.md
    │   └── enforce.py
    └── memory/
        ├── save_sacred.md
        └── save_sacred.py
```

**B3: State in Graphiti**

Current: In-memory Python dicts
Target: Graphiti temporal knowledge graph

```python
# Every agent state change → Graphiti episode
graphiti.add_episode(
    name="virtue_check",
    episode_body=f"Agent {agent_id} checked virtue {virtue_id}: {'passed' if passed else 'failed'}",
    source=EpisodeType.agent_action,
    reference_time=datetime.now(),
)

# Graphiti maintains temporal edges
# (Agent)--[HAS_VIRTUE {t_valid: T1, t_invalid: None}]-->(V01)
# When virtue changes:
# (Agent)--[HAS_VIRTUE {t_valid: T1, t_invalid: T2}]-->(V01)  # Old invalidated
# (Agent)--[HAS_VIRTUE {t_valid: T2, t_invalid: None}]-->(V01_new)  # New created
```

---

### MAP: Data Flow Architecture

**M1: Agent Lifecycle**

```
┌─────────────────────────────────────────────────────────────────┐
│                        Agent Zero                                │
│                                                                  │
│  1. User Message Arrives                                        │
│     │                                                           │
│     ▼                                                           │
│  2. Load Agent Context from Graphiti                            │
│     │  - Retrieve temporal subgraph                             │
│     │  - Get current virtue states                              │
│     │  - Get active kuleanas                                    │
│     │  - Get relevant memories                                  │
│     │                                                           │
│     ▼                                                           │
│  3. Agent Zero Monologue                                        │
│     │  - Reads prompts (identity, tools, kuleanas)              │
│     │  - Makes decisions                                        │
│     │  - Calls tools (instruments)                              │
│     │                                                           │
│     ▼                                                           │
│  4. Tool Execution (Instruments)                                │
│     │  - Each tool writes to Graphiti                           │
│     │  - Virtue checks → episodes                               │
│     │  - Memory saves → nodes                                   │
│     │                                                           │
│     ▼                                                           │
│  5. Response Generation                                         │
│     │  - Voice modulation from prompts                          │
│     │  - Emotion detection → Graphiti episode                   │
│     │                                                           │
│     ▼                                                           │
│  6. State Persisted                                             │
│     └── Graphiti → FalkorDB                                     │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

**M2: Knowledge Flow (Graphiti)**

```
┌─────────────────────────────────────────────────────────────────┐
│                         Graphiti                                 │
│                                                                  │
│  Episode Types:                                                  │
│  ├── conversation    - User/agent dialog                        │
│  ├── agent_action    - Tool executions                          │
│  ├── state_change    - Virtue/kuleana updates                   │
│  ├── memory_save     - Sacred memory creation                   │
│  └── external_data   - Scholarship info, deadlines              │
│                                                                  │
│  Node Types:                                                     │
│  ├── Agent           - Ambassador instances                     │
│  ├── Student         - Human users                              │
│  ├── Virtue          - V01-V19 anchors                          │
│  ├── Kuleana         - K01-K06 duties                           │
│  ├── Memory          - Episodic memories (with decay class)     │
│  ├── Belief          - Agent beliefs                            │
│  ├── Fact            - Domain knowledge                         │
│  └── Deadline        - Time-sensitive items                     │
│                                                                  │
│  Temporal Edges (bi-temporal):                                   │
│  ├── HAS_VIRTUE      - (Agent)-[{t_valid, t_invalid}]->(Virtue) │
│  ├── ACTIVATED       - (Agent)-[{t_valid, t_invalid}]->(Kuleana)│
│  ├── REMEMBERS       - (Agent)-[{t_valid, t_invalid}]->(Memory) │
│  ├── BELIEVES        - (Agent)-[{t_valid, t_invalid}]->(Belief) │
│  └── SERVES          - (Agent)-[{t_valid, t_invalid}]->(Student)│
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

**M3: Persistence Layer (FalkorDB)**

```
┌─────────────────────────────────────────────────────────────────┐
│                         FalkorDB                                 │
│                                                                  │
│  Graphs:                                                         │
│  ├── soul_kiln_virtues     - Virtue anchors (immutable)         │
│  ├── soul_kiln_definitions - Kuleanas, beliefs, lore            │
│  ├── agent_states          - Live agent state                   │
│  └── temporal_edges        - Graphiti edge storage              │
│                                                                  │
│  Indexes:                                                        │
│  ├── agent_id              - Fast agent lookup                  │
│  ├── t_valid               - Temporal range queries             │
│  ├── embedding             - Vector similarity (Graphiti)       │
│  └── decay_class           - Memory decay queries               │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

---

### ADAPT: Soul Kiln → Agent Zero Native

**A1: Virtue Basin → Agent Zero Extension**

```python
# vendor/agent-zero/python/extensions/soul_kiln/virtue_basin.py

async def check_virtue_alignment(agent: Agent, action: str) -> dict:
    """
    Extension hook that runs before every tool execution.
    Queries Graphiti for current virtue states.
    """
    graphiti = agent.get_data("graphiti")

    # Query current virtue states from temporal graph
    virtue_states = await graphiti.search(
        query=f"virtue states for agent {agent.agent_name}",
        center_node_uuid=agent.get_data("agent_uuid"),
    )

    # Check alignment
    for virtue in virtue_states:
        if virtue.score < virtue.threshold:
            return {"allowed": False, "reason": f"Virtue {virtue.id} below threshold"}

    return {"allowed": True}
```

**A2: Kuleanas → Instruments**

```markdown
# vendor/agent-zero/instruments/soul_kiln/kuleana/activate_duty.md

## Kuleana Activation Instrument

Determines which duties (kuleanas) are relevant to the current context.

### Usage
When you need to understand what duties apply, call this instrument
with the current context.

### Implementation
The instrument queries Graphiti for kuleana definitions and matches
against the context using semantic search.
```

```python
# vendor/agent-zero/instruments/soul_kiln/kuleana/activate_duty.py

async def run(context: str, graphiti: Graphiti) -> str:
    """Find relevant kuleanas for context."""
    results = await graphiti.search(
        query=f"duties that apply when: {context}",
        group_ids=["kuleana_definitions"],
    )

    activated = []
    for edge in results.edges:
        if edge.fact_type == "kuleana_trigger":
            activated.append({
                "id": edge.target_node.name,
                "priority": edge.metadata.get("priority"),
                "trigger": edge.fact,
            })

    return json.dumps(sorted(activated, key=lambda k: k["priority"]))
```

**A3: Memory → Graphiti Episodes**

```python
# All memory operations become Graphiti episodes

# Sacred memory save
await graphiti.add_episode(
    name="sacred_memory",
    episode_body=f"SACRED: {content}",
    source=EpisodeType.memory_save,
    reference_time=datetime.now(),
    metadata={
        "decay_class": "SACRED",
        "category": category,
        "importance": 10,
    }
)

# Memory retrieval with temporal awareness
memories = await graphiti.search(
    query="student's main goal",
    center_node_uuid=student_uuid,
    # Only get memories valid at current time
    reference_time=datetime.now(),
)
```

---

### DEPLOY: Directory Structure

```
soul_kiln/
├── vendor/
│   └── agent-zero/                    # Agent Zero (submodule)
│       ├── prompts/
│       │   ├── default/               # Agent Zero defaults
│       │   └── ambassador/            # Soul Kiln Ambassador profile
│       │       ├── agent.system.md
│       │       ├── agent.system.kuleana.md
│       │       ├── agent.system.lore.md
│       │       └── agent.system.voice.md
│       ├── instruments/
│       │   ├── default/
│       │   └── soul_kiln/             # Soul Kiln instruments
│       │       ├── virtue_basin/
│       │       ├── kuleana/
│       │       ├── taboo/
│       │       ├── memory/
│       │       └── voice/
│       └── python/
│           └── extensions/
│               └── soul_kiln/         # Soul Kiln extensions
│                   ├── virtue_guard.py
│                   ├── graphiti_state.py
│                   └── kuleana_tracker.py
│
├── src/
│   ├── graph/                         # FalkorDB operations
│   │   ├── connection.py
│   │   ├── schema.py                  # Graph schema definitions
│   │   └── queries.py
│   │
│   ├── graphiti/                      # Graphiti integration
│   │   ├── client.py                  # Graphiti client setup
│   │   ├── episodes.py                # Episode type definitions
│   │   ├── nodes.py                   # Node type definitions
│   │   └── search.py                  # Search utilities
│   │
│   └── definitions/                   # Static definitions (loaded into Graphiti)
│       ├── virtues.yaml               # Virtue anchors
│       ├── kuleanas.yaml              # Duty definitions
│       ├── beliefs.yaml               # Belief definitions
│       └── lore.yaml                  # Lore fragments
│
├── scripts/
│   ├── init_graphiti.py               # Initialize Graphiti with definitions
│   └── seed_virtues.py                # Seed virtue anchors
│
└── docs/
    └── bmad-agent-zero-refactor.md    # This document
```

---

## Implementation Order

### Phase 1: Graphiti Foundation
1. Install Graphiti with FalkorDB driver
2. Create graph schema
3. Seed virtue anchors (immutable)
4. Load kuleana/belief/lore definitions into Graphiti

### Phase 2: Agent Zero Native Prompts
1. Move Ambassador identity to prompts/ambassador/
2. Convert kuleanas to prompt format
3. Convert voice patterns to prompt format
4. Test agent without Python wrappers

### Phase 3: Instruments
1. Create virtue_basin instrument
2. Create kuleana instrument
3. Create taboo instrument
4. Create memory instrument

### Phase 4: Extensions
1. virtue_guard extension (pre-action hook)
2. graphiti_state extension (state persistence)
3. kuleana_tracker extension (duty lifecycle)

### Phase 5: Cleanup
1. Remove src/agent_zero/ wrapper code
2. Remove src/kuleana/, src/beliefs/, etc. Python modules
3. All definitions live in YAML → loaded into Graphiti
4. All behavior lives in prompts/instruments

---

## Key Paradigm Shifts

| From (Current) | To (Target) |
|----------------|-------------|
| Python classes define agents | Prompts define agents |
| Python dicts store state | Graphiti stores state |
| Code enforces taboos | Prompts + instruments enforce taboos |
| In-memory factory | Graphiti hydrates agents |
| Static definitions | Temporal knowledge graph |
| Synchronous checks | Episode-driven updates |
| Session-only memory | Bi-temporal persistent memory |

---

## Sources

- [Graphiti GitHub](https://github.com/getzep/graphiti)
- [Graphiti + FalkorDB Integration](https://www.falkordb.com/blog/building-temporal-knowledge-graphs-graphiti/)
- [Zep Temporal Knowledge Graph Paper](https://arxiv.org/abs/2501.13956)
- [Agent Zero GitHub](https://github.com/agent0ai/agent-zero)
