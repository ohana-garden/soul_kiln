# Knowledge-Graph Personas for Agents

**Research Notes — December 2024**

*A practical synthesis with soul_kiln relevance mapping*

---

## Sources

| Ref | Source | Type |
|-----|--------|------|
| [1] | [arXiv:2511.17467](https://arxiv.org/abs/2511.17467) | PersonaAgent with GraphRAG |
| [2] | [arXiv:2511.17467v1 (HTML)](https://arxiv.org/html/2511.17467v1) | Same, formatted |
| [3] | [Ragas Persona Generator](https://docs.ragas.io/en/stable/howtos/customizations/testgenerator/_persona_generator/) | Test tooling |
| [4] | [Graphiti](https://github.com/getzep/graphiti) | Temporal KG framework |
| [5] | [Zep](https://github.com/getzep/zep) | Memory layer |
| [6] | [ACL Findings 2025](https://aclanthology.org/2025.findings-acl.5/) | Persona KG + GNN |
| [7] | [ACL Findings 2025 (PDF)](https://aclanthology.org/2025.findings-acl.5.pdf) | Same |

---

## Abstract

"Agent persona" is usually implemented as a static prompt. That works until the agent needs (a) long-term consistency, (b) explainability, (c) controlled updates, or (d) multiple personas that share partial traits (organization, product, role, household member, etc.). A knowledge graph (KG) persona treats persona as **structured, queryable state** rather than prose: traits, values, preferences, style rules, roles, relationships, and time.

Recent work demonstrates two converging lines:
1. **GraphRAG-style systems** that build prompts from persona subgraphs and community summaries [1, 2]
2. **Persona-aware generation** that explicitly uses persona knowledge graphs during inference [6, 7]

Meanwhile, production-minded memory layers (temporal KGs) provide the mechanics to store "who someone is" as evolving facts [4, 5].

---

## 1. What Counts as "Defining Personas Using Knowledge Graphs"?

A KG-persona system is any agent architecture where persona is represented primarily as a **graph of entities + relations** and the agent's runtime behavior is conditioned by **graph retrieval**, not just by a fixed persona paragraph.

### Three Patterns in the Wild

| Pattern | Description | Example |
|---------|-------------|---------|
| **Persona-as-Runtime-Retrieval** | Persona reconstructed on demand from graph (often as compact prompt "capsule") | PersonaAgent with GraphRAG [1] |
| **Persona-as-Graph-Feature** | Persona KG used as structured signal (sometimes via GNNs) to improve consistency | ACL Findings 2025 framework [6] |
| **Persona-as-Memory-Subgraph** | Persona treated as durable memory with timestamps, validity windows, updates | Graphiti/Zep temporal facts [4, 5] |

Separately, tooling exists to **generate personas from a KG**—often for testing rather than direct production inference. Ragas documents `generate_personas_from_kg` for automatic persona generation [3].

---

## 2. Why Do This?

A KG persona is not "better" by default—it's heavier. Teams adopt it when they need at least one of:

| Need | Description |
|------|-------------|
| **Consistency under growth** | Static persona prompts become unmaintainable as traits/preferences/relationships pile up |
| **Composable personas** | "base persona" + "role persona" + "situation persona" without rewriting everything |
| **Auditability** | Point to exact graph facts that caused behavior |
| **Safe updating** | Modify one edge ("prefers vegetarian meals") without rewriting a prompt wall |
| **Temporal truth** | Preferences shift; relationships end; roles change—temporal graphs make this first-class [4] |

---

## 3. Core Design: The Persona Graph

Represent persona as a **subgraph** rooted at an `AgentIdentity` (or `UserIdentity` if the agent embodies someone).

### 3.1 Minimal Schema (Property Graph)

**Node Labels:**
- `Identity` — agent/user/org/product
- `Trait` — e.g., "curious", "direct"
- `Value` — e.g., "fairness", "privacy"
- `Preference` — likes/dislikes; can be domain-specific
- `StyleRule` — tone, formatting constraints, taboo phrases
- `Role` — e.g., "kitchen manager", "grant advisor"
- `Relationship` — links to other identities
- `Evidence` — where a fact came from: interaction/doc/event
- `Boundary` — hard constraints: "never do X"
- `Goal` — stable or session-bound

**Edge Types:**
- `HAS_TRAIT`, `VALUES`, `PREFERS`, `AVOIDS`, `SPEAKS_WITH_STYLE`
- `PLAYS_ROLE`, `RELATED_TO`
- `SUPPORTED_BY` — fact → evidence
- `SUPERSEDES` — new fact supersedes old
- `VALID_DURING` — or properties `valid_at`, `invalid_at`

**Temporal Properties (critical):**
- `valid_at`, `invalid_at` for facts that can expire/change [5]

### 3.2 What "Persona" Looks Like Operationally

Persona is not one thing; it's a compiled artifact:

| Component | Description |
|-----------|-------------|
| **Persona Facts** | Small set of stable truths (values, boundaries, core preferences) |
| **Persona Style** | Formatting/tone constraints |
| **Persona Context** | Situationally relevant preferences and relationships pulled by query |
| **Persona Provenance** | Evidence pointers for audit/debug |

---

## 4. Runtime Architecture (GraphRAG Persona Loop)

### 4.1 Components

```
┌─────────────┐    ┌─────────────┐    ┌───────────────┐
│  Ingestor   │───>│ Graph Store │───>│ Temporal Layer│
└─────────────┘    └─────────────┘    └───────────────┘
                          │
                          v
                   ┌─────────────┐
                   │  Retriever  │ <── current task
                   └─────────────┘
                          │
                          v
                   ┌─────────────┐
                   │  Compiler   │ ──> persona capsule
                   └─────────────┘
                          │
                          v
                   ┌─────────────┐
                   │ Policy Gate │ ──> enforce boundaries
                   └─────────────┘
                          │
                          v
                   ┌─────────────┐
                   │LLM Generator│ ──> actions/responses
                   └─────────────┘
```

| Component | Function |
|-----------|----------|
| **Ingestor** | Turns interactions/docs/events into candidate triples |
| **Graph Store** | Property graph or RDF store |
| **Temporal Layer** | Stores state changes over time (Graphiti-style) [4] |
| **Retriever** | Fetches persona subgraph given current task |
| **Compiler** | Converts subgraph → compact "persona capsule" + controls |
| **Policy Gate** | Enforces boundaries (hard constraints) before generation |
| **LLM Generator** | Uses capsule + task context to produce output |

### 4.2 Persona Capsule Format

The capsule should be:
- Short (token-efficient)
- Deterministic-ish (stable ordering)
- Explicit about priorities
- Split into **Hard Boundaries** vs **Soft Preferences**

**Example Template:**
```
Identity: ...
Values (ranked): ...
Hard boundaries: ...
Style rules: ...
Current role(s): ...
Active preferences relevant to: <task> ...
Key relationships relevant to: <task> ...
Uncertainties / conflicts: ...
```

PersonaAgent with GraphRAG generates personalized prompts by combining user-history summaries from the KG with "community" interaction patterns via graph community detection [1].

---

## 5. Community-Aware Personas

A KG persona doesn't have to be only individual-specific. The "community-aware" idea: persona is shaped by personal data **and** by patterns in a cohort graph (people like them, similar histories, similar tastes).

**Implementation:**
- Maintain two graphs (or partitions):
  - `G_user`: user-specific persona/memory graph
  - `G_cohort`: anonymized aggregate graph communities
- Retrieval returns: `subgraph_user + subgraph_community`
- Compiler tags community facts as "population hint" (lower priority than explicit user facts)

---

## 6. Persona Learning and Updates

### 6.1 Fact Lifecycle

| Stage | Description |
|-------|-------------|
| **Propose** | Extract candidate facts from interactions (with confidence) |
| **Ground** | Attach evidence nodes (turn id, doc id, timestamp) |
| **Commit** | Write to graph with validity time |
| **Decay/Supersede** | Older preferences can be invalidated |
| **Conflict handling** | Keep both facts but mark conflict; let compiler surface it |

Temporal validity is first-class in Graphiti/Zep ("facts include `valid_at` and `invalid_at`") [5].

---

## 7. Using the KG to Generate Personas (Testing + Simulation)

Even if production personas are human-defined, generating personas from a KG is useful for:
- Stress testing (does the agent stay in character?)
- Dataset generation (persona-driven queries)
- Synthetic user simulation

Ragas documents `generate_personas_from_kg` [3].

---

## 8. Persona Consistency as Algorithmic Feature

Some research goes beyond retrieval and uses persona KGs as model-side structure. The ACL Findings 2025 paper uses a "persona commonsense knowledge graph" and a query-driven graph neural network [6].

**Engineering takeaway:**
- You don't need a GNN to get most of the value
- But you *do* need: (a) stable schema, (b) retrieval discipline, (c) compiler that produces consistent capsules, (d) temporal updates

---

## 9. Evaluation (What "Good" Looks Like)

| Axis | Question |
|------|----------|
| **Persona consistency** | Does output contradict hard persona facts? |
| **Preference satisfaction** | Does it honor ranked preferences when feasible? |
| **Stability under updates** | Do small graph edits cause bounded behavioral changes? |
| **Explainability** | Can you cite which nodes/edges drove the answer? |
| **Drift control** | Do outdated facts properly expire? |

PersonaAgent with GraphRAG reports benchmark gains (improved F1/MAE on LaMP tasks) [1].

---

## 10. Security, Privacy, and "Don't Be Creepy"

A KG persona can become invasive fast. Non-negotiables:

- Separate **identity** from **private evidence**; keep sensitive evidence out of retrieval path unless strictly needed
- Store *preferences as abstractions*, not raw transcripts, when possible
- Make every persona fact traceable to evidence (or mark as "assumed/default")
- Partition graphs by tenant/user; enforce retrieval ACLs at query time, not in prompts

---

## 11. Implementation Blueprint

**Core Interfaces:**

```python
# 1. Fact management
persona_graph.upsert_fact(
    subject, predicate, object,
    valid_at, invalid_at,
    evidence, confidence
)

# 2. Retrieval
subgraph = persona_graph.query(context)

# 3. Compilation
capsule = persona_compiler.compile(
    subgraph, task_context
)  # -> {capsule_text, hard_constraints, ranked_prefs, citations}

# 4. Generation
output = agent.generate(task, capsule_text, tool_context)

# 5. Learning
proposed_facts = agent.posthoc_extract(output, interaction)
```

Graph storage can be any KG backend; Graphiti is explicitly positioned as a temporally-aware KG for agents [4].

---

## Conclusion

People are already defining personas with knowledge graphs in two serious ways:
1. GraphRAG persona systems that compile prompts from persona subgraphs and community structure [1, 2]
2. Persona-aware generation pipelines that incorporate persona KGs as structured signals [6, 7]

Tooling like temporal KG memory (Graphiti/Zep) makes "persona as evolving facts" implementable [4, 5], and utilities like Ragas show KG→persona generation as a practical building block for testing [3].

**The durable idea: treat persona as data first, prose second.**

---

# Soul Kiln Relevance Mapping

## Direct Architectural Parallels

| KG-Persona Concept | Soul Kiln Equivalent | Notes |
|--------------------|---------------------|-------|
| `Identity` node | `agent` node type | Already in graph substrate |
| `Trait`, `Value` | Virtue connections via `RESONATES_WITH` | Values are virtues; traits map to virtue affinities |
| `Boundary` (hard constraints) | Foundation tier (V01 Trustworthiness) | 99% threshold = hard boundary |
| `Preference` | Edge weights to concepts | Hebbian learning adjusts preferences |
| `Evidence` | `memory` nodes + knowledge pool lessons | Provenance already tracked |
| `valid_at`/`invalid_at` | Temporal decay + `SUPERSEDES` edges | Partial—could strengthen |
| Persona Capsule | Not explicit | **Gap to fill** |
| Compiler | Not explicit | **Gap to fill** |

## What Soul Kiln Already Has

1. **Graph-native identity**: Agents are nodes with typed edges to concepts and virtues
2. **Value structure**: The 19 virtues provide a principled value schema
3. **Two-tier boundaries**: Foundation (absolute) vs Aspirational (merciful) mirrors Hard vs Soft
4. **Learning over time**: Hebbian learning + decay = evolving preferences
5. **Evidence tracking**: Knowledge pool stores lessons with provenance
6. **Community structure**: Communities with `VirtueEmphasis` modifiers = community-aware personas

## What Soul Kiln Could Add

### 1. Persona Capsule Compiler

The retriever exists (graph queries), but there's no explicit **compiler** that produces a standardized capsule format for LLM consumption.

**Proposed location:** `src/vessels/persona.py`

```python
@dataclass
class PersonaCapsule:
    identity: str
    values_ranked: list[tuple[str, float]]  # virtue_id, strength
    hard_boundaries: list[str]              # from V01 + explicit Boundary nodes
    style_rules: list[str]                  # from StyleRule nodes
    active_roles: list[str]                 # from community membership
    relevant_preferences: list[str]         # query-specific
    relevant_relationships: list[str]       # from RELATED_TO edges
    conflicts: list[str]                    # unresolved tensions
    citations: list[str]                    # evidence node IDs

def compile_persona(agent_id: str, task_context: str) -> PersonaCapsule:
    """Retrieve and compile persona subgraph into capsule."""
    ...
```

### 2. Explicit Temporal Validity

Current decay is implicit (use-based). Could add explicit `valid_at`/`invalid_at` properties to preference edges.

**Why:** Preferences set during onboarding might explicitly expire; role-based preferences should end when roles change.

### 3. StyleRule Nodes

Add a `StyleRule` node type to the graph schema. Currently, style lives in community `system_prompt_additions` but isn't queryable.

**Schema extension:**
```
(agent)-[:SPEAKS_WITH_STYLE]->(style:StyleRule {id, constraint, priority})
```

### 4. Persona Testing via Generated Personas

Ragas-style persona generation could create synthetic agents for stress-testing virtue dynamics.

**Use case:** Generate 100 synthetic personas with different trait distributions, run coherence tests, identify edge cases.

## Architectural Tensions to Resolve

### Retrieval Selectivity vs Capsule Stability

If the retrieved subgraph varies significantly per-query, agent behavior becomes unpredictable.

**Recommendation:** Two-tier retrieval:
- **Stable core**: Always include agent's direct virtue connections + community roles
- **Situational augmentation**: Query-specific concept relationships

### Conflict Handling

The research doc says "keep both facts but mark conflict; let compiler surface it." Soul Kiln needs a policy.

**Recommendation:**
- If conflicts are between aspirational virtues: surface both, let mercy system weight them
- If conflict involves V01 (Trustworthiness): foundation wins, always
- If temporal conflict (old vs new): newer wins unless confidence is lower

### Community Facts vs Personal Facts

Community patterns (from `G_cohort`) have different epistemic status than personal facts.

**Recommendation:** Tag community-derived facts with lower confidence. The persona compiler should distinguish:
```
[personal] Prefers morning watering (confidence: 0.9)
[community] Users in grant-getter community often need budget templates (confidence: 0.6)
```

---

## Implementation Priority

| Priority | Item | Complexity | Impact | Status |
|----------|------|------------|--------|--------|
| 1 | PersonaCapsule compiler | Medium | Enables consistent persona conditioning | **DONE** |
| 2 | StyleRule nodes | Low | Makes tone/format queryable | **DONE** |
| 3 | Explicit temporal validity | Medium | Better preference lifecycle | Partial |
| 4 | Two-tier retrieval | Medium | Stability + relevance balance | Pending |
| 5 | Persona generation for testing | Low | Better test coverage | Pending |
| 6 | DiffusionDefiner | Medium | Generate definitions via diffusion | **DONE** |

---

## Implementation Status

### Completed Components

1. **PersonaCapsule** (`src/vessels/persona.py`)
   - `PersonaCapsule` dataclass with full structure
   - `PersonaCompiler` for compiling gestalts to capsules
   - `to_prompt_text()` for LLM-ready output
   - `to_structured_dict()` for programmatic access

2. **Persona Graph Node Types**
   - `Trait` - personality traits derived from virtues
   - `StyleRule` - communication style constraints
   - `Boundary` - hard constraints (absolute/strong/moderate)
   - `Preference` - soft preferences with strength and domain
   - `Role` - community/context roles
   - `Conflict` - unresolved tensions between facts

3. **DiffusionDefiner** (`src/vessels/diffusion.py`)
   - `DiffusionDefiner` class for iterative denoising
   - Persona definition generation conditioned on gestalt
   - Virtue definition generation with context
   - Trait/preference generation from virtue patterns
   - LLM decoder integration (optional)
   - Definition refinement via re-noising

4. **Graph Schema Updates** (`src/graph/schema.py`)
   - Indexes for all new node types
   - `NodeType` enum extended in `src/models.py`

### Usage Example

```python
from src.vessels import (
    compile_persona,
    capsule_to_prompt,
    define_persona_with_diffusion,
    define_virtue_with_diffusion,
    DiffusionDefiner,
)
from src.models import Gestalt

# Compile persona from gestalt
gestalt = ...  # existing gestalt
capsule = compile_persona(gestalt, task_context="grant application")
prompt_text = capsule_to_prompt(capsule)

# Generate persona definition via diffusion
definition = define_persona_with_diffusion(gestalt)
print(definition.essence)
print(definition.definition)

# Generate virtue definitions
virtue_def = define_virtue_with_diffusion("V01", context_gestalt=gestalt)

# Use definer directly for more control
definer = DiffusionDefiner(num_steps=15, noise_schedule="cosine")
definitions = definer.define_virtue("V16", related_virtues=["V03", "V07"])
```

---

## Commentary and Critique

### What the Research Gets Right

- **Capsule concept is pragmatic.** Compiling a subgraph into token-efficient text acknowledges that LLMs still need prose, but the source of truth is the graph.
- **Temporal validity is correctly emphasized.** `valid_at`/`invalid_at` semantics are non-negotiable for real systems.
- **"Don't be creepy" section is appropriately blunt.** "Store preferences as abstractions, not raw transcripts" is good advice teams routinely ignore.

### What the Research Underspecifies

- **Conflict handling is hand-waved.** "Let compiler surface it" pushes complexity to runtime without a real policy.
- **Community-aware personas are risky.** Inferring traits from cohort patterns can introduce bias or feel invasive. Epistemic status of cohort-derived facts needs explicit handling.
- **Schema drift.** The "minimal" schema has ~10 node types and ~10 edge types. Real systems will extend it; schema evolution in production KGs is painful.
- **Persona bootstrapping.** How do you initialize for a new user? Cold-start is glossed over.
- **Latency costs.** Graph retrieval + compilation adds latency. Caching strategies not discussed.

### What's Missing

- **Failure modes.** What happens when retrieval returns nothing? When the graph is contradictory beyond resolution?
- **Multi-agent persona overlap.** If two agents share an organization, how do you model inheritance? Subgraph unions? Layered graphs?

---

*End of research notes*
