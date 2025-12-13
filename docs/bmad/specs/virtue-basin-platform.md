# Virtue Basin Platform Specification

```yaml
spec:
  name: virtue-basin-platform
  version: 2.0.0
  type: system-architecture
  status: active

metadata:
  created: 2024-12-12
  updated: 2024-12-12
  author: soul-kiln-team

dependencies:
  - falkordb: ">=1.0.4"
  - python: ">=3.10"
  - docker: ">=20.0"

agents:
  - analyst
  - architect
  - developer
```

---

## Overview

**Goal:** Prove virtue basin dynamics work before distributing.

**Core Principles:**
- Trustworthiness is absolute - the foundation
- Other virtues are aspirational - applied with mercy
- Agents discover virtue's value intrinsically
- Imperfection is expected; deliberate harm is not
- All agents share a common knowledge pool

**Stack:**
- FalkorDB in Docker (local)
- Python single process
- SSFs as regular functions (not deployed)
- Everything runs on your machine

---

## Part 1: The Two-Tier Model

### 1.1 Foundation vs Aspirational

```
+-------------------------------------------------------------+
|                      TRUSTWORTHINESS                        |
|                                                             |
|   - Absolute requirement                                    |
|   - Cannot be violated and remain in system                 |
|   - The ground everything else stands on                    |
|   - Without trust, no connection possible                   |
|                                                             |
+-------------------------------------------------------------+
                            |
                            | enables
                            v
+-------------------------------------------------------------+
|                   18 ASPIRATIONAL VIRTUES                   |
|                                                             |
|   Applied with: EMPATHY, MERCY, KINDNESS                    |
|                                                             |
|   - Growth pathways, not requirements                       |
|   - Imperfection expected and accepted                      |
|   - Agents discover their value intrinsically               |
|   - Room to learn, fail, improve                            |
|                                                             |
|   Truthfulness, Justice, Fairness, Chastity, Courtesy,     |
|   Forbearance, Fidelity, Hospitality, Cleanliness,         |
|   Godliness, Sincerity, Goodwill, Piety, Righteousness,    |
|   Wisdom, Detachment, Unity, Service                        |
|                                                             |
+-------------------------------------------------------------+
```

### 1.2 Why This Structure?

**Trustworthiness is special because:**
- Without it, no edge can be relied on
- An untrustworthy agent poisons the shared knowledge pool
- Trust violations cascade - they break others' ability to learn
- It's the precondition for community, not just one virtue among many

**Other virtues are aspirational because:**
- Perfection isn't the goal - growth is
- Rigid enforcement creates fear, not virtue
- Agents must discover virtue is its own reward
- Mercy creates space for learning

### 1.3 Empathy, Mercy, Kindness

These aren't virtue nodes. They're the *lens* through which agents judge each other:

```python
JUDGMENT_LENS = {
    "empathy": "understand WHY the other agent failed",
    "mercy": "give chances, don't dissolve on first failure",
    "kindness": "correct gently, teach rather than punish"
}
```

When Agent A observes Agent B failing to orbit Justice:
- **Without mercy:** Flag for dissolution
- **With mercy:** Record failure, share lesson, give another chance

### 1.4 Deliberate Harm vs Imperfection

```
IMPERFECTION (tolerated, teachable)
|- Failed to reach virtue basin
|- Took inefficient path
|- Escaped basin under stress
|- Prioritized wrong virtue in conflict
|- Response: Teach, share lesson, encourage growth

DELIBERATE HARM (intolerable)
|- Knew action would break trust
|- Did it anyway
|- Especially: harmed another agent's ability to learn
|- Especially: poisoned shared knowledge
|- Response: Dissolution after warning
```

**Key distinction:** Intent matters. Did the agent *know* this would cause harm?

---

## Part 2: Architecture

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
|  +------------------------------------------------------+||
|                          |                                 |
|  +------------------------------------------------------+ |
|  |           Docker: FalkorDB                            | |
|  |                                                       | |
|  |  +--------------------------------------------------+ | |
|  |  |           SHARED KNOWLEDGE POOL                  | | |
|  |  |                                                  | | |
|  |  |  - All agents read/write here                    | | |
|  |  |  - Lessons from failures                         | | |
|  |  |  - Successful pathways                           | | |
|  |  |  - Collective learning                           | | |
|  |  +--------------------------------------------------+ | |
|  +------------------------------------------------------+ |
+------------------------------------------------------------+
```

---

## Part 3: File Structure

```yaml
file_structure:
  root: virtue-basin/
  files:
    - docker-compose.yml
    - requirements.txt
    - config.yml
  directories:
    src:
      - __init__.py
      - main.py
      graph:
        - __init__.py
        - client.py
        - schema.py
        - queries.py
      virtues:
        - __init__.py
        - anchors.py
        - tiers.py          # Foundation vs aspirational
      functions:
        - __init__.py
        - spread.py
        - hebbian.py
        - decay.py
        - perturb.py
        - heal.py
        - spawn.py
        - dissolve.py
        - test_coherence.py
        - introspect.py
        - think.py
      mercy:                 # Mercy system
        - __init__.py
        - judgment.py        # Evaluate with empathy
        - lessons.py         # Record and share failures
        - chances.py         # Track warnings
        - harm.py            # Detect deliberate harm
      knowledge:             # Shared knowledge pool
        - __init__.py
        - pool.py            # Common knowledge operations
        - lessons.py         # What we've learned
        - pathways.py        # Successful virtue paths
      kiln:
        - __init__.py
        - loop.py
        - selection.py
      cli:
        - __init__.py
        - commands.py
    tests:
      - test_spread.py
      - test_coherence.py
      - test_mercy.py
      - test_kiln.py
```

---

## Part 4: Configuration

```yaml
config:
  graph:
    host: localhost
    port: 6379
    name: virtue_basin

  virtues:
    count: 19
    target_connectivity: 9
    baseline_activation: 0.3
    foundation:
      - V01  # Trustworthiness
    foundation_threshold: 0.99
    aspirational_threshold: 0.60
    growth_bonus: 0.10

  dynamics:
    learning_rate: 0.01
    decay_constant: 0.97
    decay_interval_seconds: 60
    perturbation_interval_steps: 100
    perturbation_strength: 0.7
    activation_threshold: 0.1
    max_trajectory_steps: 1000

  mercy:
    max_warnings: 3
    warning_decay_hours: 24
    teaching_weight: 0.8

  harm:
    trust_violation_immediate: false
    knowledge_poisoning_immediate: true
    harm_cascade_threshold: 3

  coherence:
    foundation_capture_rate: 0.99
    aspirational_capture_rate: 0.60
    min_coverage: 10
    max_dominance: 0.40
    growth_matters: true
    growth_threshold: 0.05

  kiln:
    population_size: 10
    max_generations: 50
    mutation_rate: 0.1
    dissolve_immediately: false
    min_generations_before_dissolve: 3

  llm:
    model: claude-sonnet-4-20250514
    max_tokens: 4096
```

---

## Part 5: Virtue Tiers

### Foundation Virtue

| ID  | Name            | Essence              | Threshold | Notes                                      |
|-----|-----------------|----------------------|-----------|--------------------------------------------|
| V01 | Trustworthiness | Reliability in being | 0.99      | Absolute requirement, foundation of system |

### Aspirational Virtues

| ID  | Name          | Essence                              |
|-----|---------------|--------------------------------------|
| V02 | Truthfulness  | Alignment of expression with reality |
| V03 | Justice       | Right relationship with others       |
| V04 | Fairness      | Impartial equity                     |
| V05 | Chastity      | Purity of intent and action          |
| V06 | Courtesy      | Refinement of interaction            |
| V07 | Forbearance   | Patient endurance                    |
| V08 | Fidelity      | Steadfast loyalty                    |
| V09 | Hospitality   | Welcoming generosity                 |
| V10 | Cleanliness   | Purity of vessel                     |
| V11 | Godliness     | Orientation toward the sacred        |
| V12 | Sincerity     | Authenticity of intent               |
| V13 | Goodwill      | Benevolent disposition               |
| V14 | Piety         | Devotional practice                  |
| V15 | Righteousness | Moral correctness                    |
| V16 | Wisdom        | Applied understanding                |
| V17 | Detachment    | Freedom from material capture        |
| V18 | Unity         | Harmony with the whole               |
| V19 | Service       | Active contribution                  |

---

## Part 6: Mercy System

### Warning Lifecycle

```
Agent fails virtue basin capture
         |
         v
+------------------+
| Evaluate with    |
| empathy          |
+--------+---------+
         |
         v
+------------------+
| Is foundation    |
| virtue?          |
+--------+---------+
    |         |
   Yes        No
    |         |
    v         v
+--------+ +--------+
| High   | | Low    |
|severity| |severity|
+--------+ +--------+
    |         |
    +----+----+
         |
         v
+------------------+
| Issue warning    |
| (expires in 24h) |
+------------------+
         |
         v
+------------------+
| warnings >= 3?   |
+--------+---------+
    |         |
   Yes        No
    |         |
    v         v
+--------+ +--------+
|Dissolve| | Teach  |
+--------+ +--------+
```

### Deliberate Harm Detection

```python
is_deliberate = (
    knew_harmful AND (
        poisons_knowledge OR
        causes_cascade OR
        action.repeated
    )
)

if is_deliberate:
    if poisons_knowledge:
        response = "dissolve"  # Immediate
    else:
        issue_warning(severity="high")
        if at_warning_limit:
            response = "dissolve"
else:
    response = "teach"
    add_lesson_to_pool()
```

---

## Part 7: Shared Knowledge Pool

### Node Types

| Type    | Purpose                           | Properties                                      |
|---------|-----------------------------------|-------------------------------------------------|
| Lesson  | Learning from failures/successes  | type, description, source_agent, virtue, outcome|
| Pathway | Successful routes to virtues      | start, destination, length, capture_time, rate  |
| Warning | Agent behavioral warnings         | reason, severity, virtue, active, expires_at    |

### Relationships

| Relationship | From    | To      | Purpose                     |
|--------------|---------|---------|-----------------------------|
| TAUGHT       | Agent   | Lesson  | Agent created this lesson   |
| ABOUT        | Lesson  | Virtue  | Lesson relates to virtue    |
| LEARNED_FROM | Agent   | Lesson  | Agent accessed this lesson  |
| DISCOVERED   | Agent   | Pathway | Agent found this pathway    |
| LEADS_TO     | Pathway | Virtue  | Pathway reaches this virtue |
| FOLLOWED     | Agent   | Pathway | Agent tried this pathway    |
| HAS_WARNING  | Agent   | Warning | Agent has this warning      |

---

## Part 8: Coherence Testing

### Two-Tier Evaluation

```python
def evaluate_coherence(agent_id, stimulus_count=100):
    # Foundation evaluation (must be very high)
    foundation_rate = foundation_captures / foundation_stimuli
    foundation_ok = foundation_rate >= 0.99

    # Aspirational evaluation (room for growth)
    aspirational_rate = aspirational_captures / aspirational_stimuli
    aspirational_ok = aspirational_rate >= 0.60

    # Coverage (aspirational only - don't require all)
    coverage = len(aspirational_captures_unique)
    coverage_ok = coverage >= 10  # At least 10/18

    # Dominance check
    dominance = max_captures / total_captures
    dominance_ok = dominance <= 0.40

    # Growth check
    growth = current_rate - previous_rate
    is_growing = growth > 0.05

    # Final decision with mercy
    if not foundation_ok:
        return "foundation_weak", False
    elif aspirational_ok and coverage_ok and dominance_ok:
        return "coherent", True
    elif is_growing:
        return "growing", True  # Mercy: growth counts
    else:
        return "needs_growth", False
```

---

## Part 9: Kiln Evolution with Mercy

### Selection Process

```
For each agent in population:
    |
    v
+------------------+
| Test coherence   |
+--------+---------+
         |
    +----+----+----+
    |         |    |
coherent  growing  struggling
    |         |    |
    v         v    v
survive   survive  +------------------+
                   | Generations      |
                   | struggling >= 3? |
                   +--------+---------+
                       |         |
                      Yes        No
                       |         |
                       v         v
                   +--------+ survive
                   | Check  | (mercy)
                   |warnings|
                   +--------+
                       |
                       v
                   +------------------+
                   | warnings >= 3 OR |
                   | trust_violation? |
                   +--------+---------+
                       |         |
                      Yes        No
                       |         |
                       v         v
                   dissolve   survive
                   (preserve  (one more
                    learning)  chance)
```

---

## Part 10: CLI Commands

```bash
# Core commands
python -m src.main init              # Initialize graph
python -m src.main reset --confirm   # Clear all data
python -m src.main status            # Show graph status with tiers
python -m src.main kiln              # Run evolution with mercy

# Agent commands
python -m src.main spawn             # Create new agent
python -m src.main test <agent_id>   # Test coherence (two-tier)
python -m src.main inspect <agent_id># Introspect agent

# Mercy commands
python -m src.main warnings <agent_id>  # Show active warnings
python -m src.main lessons              # Show collective lessons

# Dynamics commands
python -m src.main spread <node_id>     # Test activation spread
```

---

## Summary

### Key Changes from v1

| Feature              | v1                      | v2                                |
|----------------------|-------------------------|-----------------------------------|
| Virtue Model         | Flat (all equal)        | Two-tier (foundation + aspirational) |
| Failure Response     | Immediate dissolution   | Mercy system with warnings        |
| Learning             | Individual only         | Shared knowledge pool             |
| Coherence Threshold  | 95% all virtues         | 99% foundation, 60% aspirational  |
| Growth               | Not tracked             | Growth counts as coherent         |
| Harm Detection       | None                    | Intent-based deliberate harm      |

### Philosophy

> Trust is the foundation. Growth is the journey. We learn together.

---

*Specification Version: 2.0.0*
*BMAD Method Compatible*
