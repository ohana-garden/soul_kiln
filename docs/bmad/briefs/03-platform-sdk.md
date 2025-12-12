# Phase 3: Platform / SDK Design

> **Status:** Waiting for Phase 1 + Phase 2 completion

## Purpose

Transform soul_kiln from "one implementation" into "infrastructure for many implementations." Extract patterns, create APIs, enable others to build.

---

## Platform Vision

```
┌─────────────────────────────────────────────────────────────────────┐
│                     APPLICATIONS (many)                             │
│                                                                     │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐              │
│  │   Student    │  │   Health     │  │   Career     │              │
│  │  Ambassador  │  │   Coach      │  │   Mentor     │              │
│  └──────┬───────┘  └──────┬───────┘  └──────┬───────┘              │
│         └─────────────────┴─────────────────┘                       │
│                           │                                         │
│                   ┌───────▼───────┐                                 │
│                   │  Soul Kiln    │                                 │
│                   │     SDK       │                                 │
│                   └───────────────┘                                 │
└─────────────────────────────────────────────────────────────────────┘
```

---

## SDK Components (Anticipated)

### Graph Primitives
- `VirtueBasin` - Create and configure virtue attractors
- `Agent` - Spawn, bind, evolve, dissolve
- `Concept` - Domain ideas that connect to virtues
- `Pathway` - Learning routes between concepts

### Dynamics API
- `spread(source, energy)` - Activation propagation
- `decay(rate)` - Temporal forgetting
- `heal()` - Dead zone repair
- `perturb()` - Exploration injection

### Evolution API
- `Kiln.run(population, generations)` - Full evolution
- `Kiln.step(candidates)` - Single generation
- `Kiln.test(agent)` - Coherence check

### Mercy API
- `judge(agent, failure)` - Empathetic evaluation
- `warn(agent, reason)` - Issue warning
- `forgive(agent, warning)` - Remove warning
- `teach(agent, lesson)` - Apply learning

### Memory API
- `remember(agent, episode)` - Store conversation
- `recall(agent, query)` - Retrieve relevant memory
- `fact(subject, predicate, object)` - Temporal fact

### Event API
- `on(event_type, condition, action)` - Register trigger
- `emit(event)` - Fire event
- `schedule(event, time)` - Future event

---

## Multi-Tenancy Model

### Isolation Levels
1. **Full isolation** - Separate graph per tenant
2. **Shared virtues** - Common virtue anchors, separate agents
3. **Shared commons** - Common learnings, private agents

### Data Boundaries
- Personal data: never shared
- Agent data: shared only if anonymized
- Commons data: shared across tenants
- Virtue data: global (the 19 virtues)

---

## Developer Experience

### Quick Start
```python
from soul_kiln import Kiln, Agent, VirtueBasin

# Initialize with defaults
kiln = Kiln.connect()

# Create application-specific agent
ambassador = Agent.create(
    type="bound",
    virtues=["trustworthiness", "service", "wisdom"],
    tools=[scholarship_search, deadline_check]
)

# Bind to user
ambassador.bind(user_id="student_123")

# Handle conversation
response = ambassador.converse("Find me scholarships for engineering")
```

### Configuration
```yaml
# soul-kiln.yaml
virtues:
  use: default  # or custom list
  weights:
    trustworthiness: 1.0  # non-negotiable
    service: 0.8
    wisdom: 0.7

evolution:
  enabled: false  # bound agents don't evolve

mercy:
  max_warnings: 3
  grace_period_generations: 3

memory:
  backend: graphiti
  retention_days: 365
```

---

## Inputs Required (from Phase 1 + 2)

- [ ] API surface used by Student Ambassador
- [ ] Pain points in current implementation
- [ ] Patterns that emerged across stories
- [ ] Performance characteristics at scale
- [ ] Security/privacy patterns validated

---

## Timeline

Begins after Phase 2, when:
- Student Ambassador is deployed and stable
- Core evolution changes are merged
- Patterns are validated through real use
