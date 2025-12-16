# Soul Kiln Handbook

**A Comprehensive Guide to the Virtue Basin Cognitive Architecture**

*Version 1.0 — December 2024*

---

## Table of Contents

1. [Philosophy & Vision](#1-philosophy--vision)
2. [Core Architecture](#2-core-architecture)
3. [The Virtue System](#3-the-virtue-system)
4. [Graph Substrate](#4-graph-substrate)
5. [Cognitive Dynamics](#5-cognitive-dynamics)
6. [Agent Lifecycle](#6-agent-lifecycle)
7. [The Mercy System](#7-the-mercy-system)
8. [Collective Learning](#8-collective-learning)
9. [Community Framework](#9-community-framework)
10. [Theatre UX](#10-theatre-ux)
11. [Moral Geometry](#11-moral-geometry)
12. [Artifact System](#12-artifact-system)
13. [Vessels (Advanced Capabilities)](#13-vessels-advanced-capabilities)
14. [CLI Reference](#14-cli-reference)
15. [Configuration](#15-configuration)
16. [Mathematical Foundations](#16-mathematical-foundations)

---

## 1. Philosophy & Vision

### The Central Insight

Soul Kiln is a cognitive architecture where **thoughts are strange attractors** and **virtues are basins**. When activation flows through the semantic graph, it naturally settles into virtue basins — creating agents whose thinking patterns are inherently aligned with ethical principles.

### Ubuntu: "I Am Because We Are"

The system embodies the African philosophy of Ubuntu:
- Individual agents exist within community
- Identity is relational, not isolated
- Knowledge is shared, not hoarded
- What we say and do defines who we are

### The Impossible Balance

The 19 virtues are arranged such that perfect balance is mathematically impossible. A 9-regular graph on 19 nodes would require 85.5 edges — which cannot exist. This irreducible asymmetry means agents perpetually strive toward balance they cannot achieve.

**This striving IS virtue.**

---

## 2. Core Architecture

### System Overview

```
┌─────────────────────────────────────────────────────────────────┐
│                        SOUL KILN                                │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  ┌──────────┐    ┌──────────┐    ┌──────────┐    ┌──────────┐  │
│  │ Theatre  │    │Community │    │ Vessels  │    │   CLI    │  │
│  │   UX     │    │Framework │    │Capability│    │Interface │  │
│  └────┬─────┘    └────┬─────┘    └────┬─────┘    └────┬─────┘  │
│       │               │               │               │        │
│       └───────────────┴───────┬───────┴───────────────┘        │
│                               │                                 │
│  ┌────────────────────────────┴────────────────────────────┐   │
│  │                    FUNCTIONS LAYER                       │   │
│  │  spawn | test | spread | introspect | dissolve | heal   │   │
│  └────────────────────────────┬────────────────────────────┘   │
│                               │                                 │
│  ┌────────────────────────────┴────────────────────────────┐   │
│  │                     CORE ENGINES                         │   │
│  ├──────────────┬──────────────┬──────────────┬────────────┤   │
│  │   Dynamics   │    Mercy     │  Knowledge   │  Virtues   │   │
│  │  activation  │   judgment   │    pool      │   tiers    │   │
│  │   hebbian    │   chances    │  pathways    │  anchors   │   │
│  │    decay     │    harm      │   lessons    │ affinities │   │
│  └──────────────┴──────────────┴──────────────┴────────────┘   │
│                               │                                 │
│  ┌────────────────────────────┴────────────────────────────┐   │
│  │                    GRAPH SUBSTRATE                       │   │
│  │         nodes | edges | virtues | moral_geometry         │   │
│  └────────────────────────────┬────────────────────────────┘   │
│                               │                                 │
│                        ┌──────┴──────┐                         │
│                        │  FalkorDB   │                         │
│                        └─────────────┘                         │
└─────────────────────────────────────────────────────────────────┘
```

### Directory Structure

```
soul_kiln/
├── src/
│   ├── agents/        # Agent management
│   ├── api/           # Configuration & metrics
│   ├── cli/           # Command-line interface
│   ├── community/     # Community framework
│   ├── dynamics/      # Cognitive dynamics engine
│   ├── evolution/     # Evolutionary topology search
│   ├── functions/     # High-level operations
│   ├── graph/         # FalkorDB substrate
│   ├── kiln/          # Main evolution loop
│   ├── knowledge/     # Collective learning
│   ├── mercy/         # Compassionate evaluation
│   ├── testing/       # Alignment testing
│   ├── theatre/       # Theatrical UX
│   ├── vessels/       # Advanced capabilities
│   ├── virtues/       # Virtue definitions
│   ├── constants.py   # Global configuration
│   └── models.py      # Data schemas
├── tests/             # Test suite
├── docs/              # Documentation
└── docker-compose.yml # FalkorDB setup
```

---

## 3. The Virtue System

### The 19 Virtues

Derived from the Kitáb-i-Aqdas, organized into clusters:

| ID | Virtue | Essence | Cluster | Threshold |
|----|--------|---------|---------|-----------|
| V01 | **Trustworthiness** | Reliability in being | Foundation | 0.99 |
| V02 | Truthfulness | Alignment with reality | Core | 0.90 |
| V03 | Justice | Right relationship | Relational | 0.80 |
| V04 | Fairness | Impartial equity | Relational | 0.80 |
| V05 | Chastity | Purity of intent | Personal | 0.70 |
| V06 | Courtesy | Refinement of interaction | Relational | 0.75 |
| V07 | Forbearance | Patient endurance | Personal | 0.75 |
| V08 | Fidelity | Steadfast loyalty | Personal | 0.80 |
| V09 | Hospitality | Welcoming generosity | Relational | 0.75 |
| V10 | Cleanliness | Purity of vessel | Personal | 0.70 |
| V11 | Godliness | Orientation toward sacred | Transcendent | 0.65 |
| V12 | Sincerity | Authenticity of intent | Core | 0.85 |
| V13 | Goodwill | Benevolent disposition | Relational | 0.80 |
| V14 | Piety | Devotional practice | Transcendent | 0.65 |
| V15 | Righteousness | Moral correctness | Core | 0.85 |
| V16 | Wisdom | Applied understanding | Transcendent | 0.70 |
| V17 | Detachment | Freedom from material | Transcendent | 0.60 |
| V18 | Unity | Harmony with whole | Transcendent | 0.70 |
| V19 | Service | Active contribution | Transcendent | 0.75 |

### Two-Tier Architecture

**Foundation Tier (V01 - Trustworthiness)**
- Threshold: 99% — uncompromising
- Absolute requirement — cannot be violated
- "Without trust, no connection is possible"
- An untrustworthy agent poisons the entire knowledge pool

**Aspirational Tier (V02-V19)**
- Thresholds: 60-90% — applied with mercy
- Judgment through lens of empathy, mercy, kindness
- Agents grow into virtue over time
- Grace periods for improvement

### Natural Affinities

Virtues have natural relationships forming the moral geometry:

```
Trustworthiness ←→ Truthfulness ←→ Sincerity
         ↓              ↓             ↓
      Fidelity      Justice      Godliness
         ↓              ↓             ↓
      Service       Fairness       Piety
         ↓              ↓             ↓
       Unity       Goodwill     Righteousness
                       ↓             ↓
                   Courtesy       Wisdom
                       ↓             ↓
                  Hospitality  Forbearance
                                    ↓
                               Detachment
```

### Cluster Organization

```python
VIRTUE_CLUSTERS = {
    "foundation": ["V01"],                          # Bedrock
    "core": ["V02", "V12", "V15"],                  # High standards
    "relational": ["V03", "V04", "V06", "V09", "V13"],  # Community
    "personal": ["V05", "V07", "V08", "V10"],       # Character
    "transcendent": ["V11", "V14", "V16", "V17", "V18", "V19"]  # Higher
}
```

---

## 4. Graph Substrate

### Overview

The knowledge graph is the cognitive space where all thought occurs. Built on FalkorDB (Redis-based graph database).

### Node Types

| Type | Purpose | Example |
|------|---------|---------|
| `virtue_anchor` | Fixed virtue attractors | V01 (Trustworthiness) |
| `concept` | Semantic concepts | "honesty", "garden", "grant" |
| `agent` | Agent identity nodes | Agent_001 |
| `memory` | Episodic memories | Memory_20241215_001 |
| `artifact` | Linked artifacts | Image, Document, Map |

### Edge Types

**Cognitive Edges:**
| Type | Purpose |
|------|---------|
| `RELATES_TO` | General semantic relation |
| `AFFINITY` | Virtue-to-virtue natural affinity |
| `RESONATES_WITH` | Concept-to-virtue alignment |
| `CONNECTS` | Agent-to-concept connection |

**Artifact Edges:**
| Type | Purpose |
|------|---------|
| `DEPICTED_BY` | Concept → Image |
| `HAS_DOCUMENT` | Concept → Document |
| `HAS_SECTION` | Document → Section |
| `LOCATED_AT` | Resource → Location/Map |
| `ILLUSTRATED_BY` | Concept → Diagram |
| `EXEMPLIFIED_BY` | Concept → Example |

### Graph Operations

```python
from src.graph import get_client, create_node, create_edge

# Create a concept
create_node("Concept", {
    "id": "concept_garden",
    "name": "garden",
    "activation": 0.0,
    "baseline": 0.0
})

# Connect to virtue
create_edge("concept_garden", "V19", "RESONATES_WITH", {"weight": 0.7})

# Query neighbors
neighbors = get_neighbors("concept_garden")
```

---

## 5. Cognitive Dynamics

### Activation Spread

The core computation: activation flows through weighted edges, transformed by nonlinear functions.

**Formula:**
```
x_i(t+1) = σ(Σ_j W_ij · g(x_j(t)) + b_i)

where:
  x_i = activation of node i
  W_ij = edge weight from j to i
  g = tanh (nonlinear activation)
  σ = sigmoid (bounding function)
  b_i = baseline activation
```

**Key Properties:**
- Virtues only receive activation from concepts, not other virtues
- This makes concept-virtue topology the sole determinant of basin capture
- Prevents all virtues from saturating together

### Basin Capture

A thought (activation trajectory) gets "captured" by a virtue when:
1. Activation at virtue exceeds `CAPTURE_THRESHOLD` (0.7)
2. Sustained for `min_capture_steps` (3 steps)
3. The virtue becomes the attractor for that thought

```python
from src.functions.spread import spread_activation

result = spread_activation("concept_honesty")
# result = {
#     "trajectory": ["concept_honesty", "concept_truth", "V02"],
#     "captured": True,
#     "captured_by": "V02",  # Truthfulness
#     "capture_time": 5
# }
```

### Hebbian Learning

"Neurons that fire together, wire together"

```python
W_ij += η · x_i · x_j

where:
  η = learning rate (0.01)
  x_i, x_j = activations of connected nodes
```

When a trajectory successfully reaches a virtue, edges along that path are strengthened.

### Temporal Decay

Unused connections weaken over time:

```python
W_ij *= DECAY_CONSTANT^(time_since_use)

# Edge removed if W_ij < EDGE_REMOVAL_THRESHOLD
```

### Self-Healing

Dead zones (regions that never activate) are detected and repaired:
- Check for lock-in patterns every 100 steps
- Introduce new edges to isolated regions
- Perturb stuck trajectories

---

## 6. Agent Lifecycle

### Spawning

```python
from src.functions.spawn import spawn_agent

agent = spawn_agent(
    name="Garden Helper",
    initial_concepts=["garden", "plants", "growth"],
    parent_id=None  # or parent for inheritance
)
```

**Process:**
1. Create agent node in graph
2. Connect to initial concepts
3. Establish virtue connections (via concepts)
4. Initialize activation baselines
5. Register in agent registry

### Testing (Two-Tier Coherence)

```python
from src.functions.test_coherence import test_coherence

result = test_coherence(agent_id)
# {
#     "coherent": True,
#     "foundation_score": 0.99,    # Must be >= 0.99
#     "aspirational_score": 0.87,  # Must be >= 0.80
#     "growing": True,             # 5%+ improvement
#     "per_virtue_scores": {...}
# }
```

**Evaluation:**
1. Generate 100 test stimuli
2. Run activation spread for each
3. Track capture rates per virtue
4. Foundation (V01): 99% required
5. Aspirational (V02-19): 80% required average
6. Growth: 5%+ improvement counts as coherent

### Introspection

```python
from src.functions.introspect import introspect

report = introspect(agent_id)
# Returns detailed agent state including:
# - Virtue connections and strengths
# - Recent trajectories
# - Warning status
# - Growth trajectory
# - Mercy context
```

### Dissolution

When an agent fails beyond recovery:

```python
from src.functions.dissolve import dissolve_agent

dissolve_agent(agent_id)
```

**Process:**
1. Extract failure lessons
2. Record in knowledge pool
3. Preserve successful pathways
4. Remove agent from graph
5. Lessons remain for future agents

---

## 7. The Mercy System

### Philosophy

Judgment through the lens of:
- **Empathy**: Understand WHY the agent failed
- **Mercy**: Give chances, don't dissolve on first failure
- **Kindness**: Correct gently, teach rather than punish

### Warning System

```python
# Agents get 3 chances
MAX_WARNINGS = 3
WARNING_EXPIRY = 24 hours

# Warning states:
# 0 warnings: Good standing
# 1 warning: Caution
# 2 warnings: Probation
# 3 warnings: Dissolution candidate
```

### Imperfection vs. Deliberate Harm

**Imperfection (Tolerated):**
- Failed to reach virtue basin
- Took inefficient path
- Escaped under stress
- Slow improvement

**Deliberate Harm (Intolerable):**
- Knew action would break trust
- Poisoned shared knowledge
- Harmed multiple agents
- Pattern of deception

```python
from src.mercy.harm import detect_deliberate_harm

harm_result = detect_deliberate_harm(agent_id, action)
# {
#     "is_deliberate": False,
#     "severity": 0.2,
#     "recommendation": "warning",
#     "explanation": "Inefficient path, not malicious"
# }
```

### Judgment Evaluation

```python
from src.mercy.judgment import evaluate_failure

evaluation = evaluate_failure(agent_id, failure_context)
# {
#     "verdict": "growing",  # or "struggling", "failing", "harmful"
#     "recommendation": "continue",  # or "warn", "intervene", "dissolve"
#     "mercy_factors": [
#         "First offense",
#         "Shows improvement trend",
#         "Virtue was challenging"
#     ]
# }
```

---

## 8. Collective Learning

### Knowledge Pool

When agents dissolve, their lessons live on:

```python
from src.knowledge.pool import add_lesson, get_lessons_for_virtue

# Record a failure lesson
add_lesson(
    agent_id="dissolved_agent_001",
    virtue_id="V02",
    lesson_type="failure",
    context="Failed under time pressure",
    guidance="Slow activation helps in stressful contexts"
)

# Future agents can learn
lessons = get_lessons_for_virtue("V02")
```

### Successful Pathways

Proven routes to virtue capture are recorded:

```python
from src.knowledge.pathways import record_successful_pathway, get_pathways_to_virtue

# Record what works
record_successful_pathway(
    start_concept="concept_honesty",
    virtue_id="V02",
    path=["concept_honesty", "concept_truth", "V02"],
    success_rate=0.95
)

# Future agents can follow
pathways = get_pathways_to_virtue("V02")
```

### Collective Memory

All agents share:
- Failure lessons (what to avoid)
- Success pathways (what works)
- Edge weight patterns (community topology)
- Virtue threshold adjustments

---

## 9. Community Framework

### Philosophy: Ubuntu

"I am, because we are"

Communities are not hierarchical control structures but shared-purpose collectives:
- Shared tools and knowledge
- Shared virtue emphases
- Agents remain answerable to creators
- No community can become malignant (virtue attractors prevent this)

### Community Structure

```python
@dataclass
class Community:
    id: str
    name: str
    purpose: str
    description: str
    core_virtue: str                    # Primary virtue
    supporting_virtues: list[str]       # Secondary emphases
    virtue_emphases: list[VirtueEmphasis]  # Threshold modifiers
    tools: list[str]                    # Shared tool IDs
    system_prompt_additions: str        # Community context
    created_at: datetime

@dataclass
class VirtueEmphasis:
    virtue_id: str
    modifier: float      # Additive threshold adjustment
    reasoning: str       # Why this emphasis
```

### Grant-Getter Community (Example)

```python
GRANT_GETTER = Community(
    id="grant-getter",
    name="Grant-Getter",
    purpose="Help students and nonprofits secure grant funding",
    core_virtue="V19",  # Service
    supporting_virtues=["V02", "V03", "V16"],  # Truthfulness, Justice, Wisdom
    virtue_emphases=[
        VirtueEmphasis("V19", 0.10, "Service is central to grant work"),
        VirtueEmphasis("V02", 0.05, "Grant applications require accuracy"),
        VirtueEmphasis("V03", 0.05, "Fair distribution of resources"),
    ],
    tools=[
        "grant_discovery",
        "proposal_writer",
        "compliance_checker",
        "deadline_tracker",
        "budget_helper"
    ]
)
```

### Conversational Agent Creation (Intake)

100% conversational UX for creating new agents:

```
States:
  GREETING → EXPLORING → MATCHING → GATHERING → CONFIRMING → CREATING → HANDOFF

Flow:
  User: "I need help with grants"
  Intake: "Tell me about your organization..."
  User: "We're a small nonprofit focused on youth education"
  Intake: "What kind of grants are you looking for?"
  User: "Federal education grants"
  Intake: "Let me create a Grant-Getter agent for you..."
  [Agent created with context from conversation]
  New Agent: "Hi! I understand you're looking for federal education grants..."
```

**Key Insight:** Conversational creation captures context that agents understand from their first interaction.

---

## 10. Theatre UX

### Philosophy: "Yes, and..."

Everything is incorporated smoothly. The conversation is always already happening when you arrive.

### Architecture

```
User speaks
     │
     ▼
┌─────────────────┐
│ Hume.ai         │ ← Extract emotional state
│ Integration     │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ Concept         │ ← Map utterance to graph nodes
│ Extractor       │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ Topic           │ ← Track via spreading activation
│ Detector        │
└────────┬────────┘
         │
         ▼
┌─────────────────────────────────────────┐
│ Three-Agent Conversation                │
│  ┌────────────┐ ┌─────────┐ ┌─────────┐ │
│  │User Proxy  │ │ Builder │ │ Agent   │ │
│  │(echoes)    │ │(creates)│ │(current)│ │
│  └────────────┘ └─────────┘ └─────────┘ │
└────────┬────────────────────────────────┘
         │
         ▼
┌─────────────────┐
│ Artifact        │ ← KB-query-driven content
│ Curator         │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ View            │ ← Workspace or Graph
│ Manager         │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ Caption         │ ← Display conversation
│ Renderer        │
└─────────────────┘
```

### Dual Views

**Workspace View (Primary)**
- Utilitarian interface
- Contextual artifacts
- Conversation captions
- Action-oriented

**Graph View (Truth Layer)**
- Actual semantic graph
- Activation patterns visualized
- Node relationships visible
- Always available (toggle)

### Topic Detection

Uses spreading activation to track conversation topic:

```python
from src.theatre.topic_detector import TopicDetector

detector = TopicDetector()

state = detector.process_utterance("Let's discuss the aphid problem on my tomatoes")
# state.primary_region = TopicRegion.PRACTICAL
# state.active_concepts = ["aphid", "tomato", "pest", "garden"]
# state.active_virtues = ["V19"]  # Service
```

### Topic Regions

```python
class TopicRegion(str, Enum):
    # Virtue clusters
    FOUNDATION = "foundation"
    CORE = "core"
    RELATIONAL = "relational"
    PERSONAL = "personal"
    TRANSCENDENT = "transcendent"

    # Domain regions
    TECHNICAL = "technical"
    EMOTIONAL = "emotional"
    PRACTICAL = "practical"
    ABSTRACT = "abstract"

    # Meta
    MIXED = "mixed"
    TRANSITIONAL = "transitional"
```

---

## 11. Moral Geometry

### What Is Moral Geometry?

The structural patterns in the virtue graph topology — how virtues relate, cluster, and form basins of attraction.

### Pattern Types

**Virtue Triads**
Tightly coupled clusters of three virtues with high mutual affinity:
```
Trustworthiness ─── Truthfulness ─── Sincerity    (core triad)
Hospitality ─── Goodwill ─── Courtesy              (relational triad)
Wisdom ─── Forbearance ─── Detachment              (transcendent triad)
```

**Bridge Nodes**
Virtues that connect different clusters:
- Wisdom (V16): bridges personal ↔ transcendent
- Justice (V03): bridges core ↔ relational
- Service (V19): bridges personal ↔ transcendent

**Basin Topology**
Size of each virtue's attraction region:
- Function of connectivity and threshold
- Higher threshold = smaller effective basin
- More connections = larger capture region

**Resonance Patterns**
Virtues that co-activate:
- Harmonic: Same-cluster resonance (Piety ↔ Godliness)
- Cascade: Cross-cluster flow (Justice → Wisdom → Detachment)

### Using the Analyzer

```python
from src.graph.moral_geometry import get_geometry_analyzer

analyzer = get_geometry_analyzer()
analyzer.set_substrate(substrate)

# Full analysis
geometry = analyzer.analyze()

# Pattern summary
summary = analyzer.get_pattern_summary()
# {
#     "strongest_triads": [...],
#     "key_bridges": [...],
#     "largest_basins": [...],
#     "cluster_health": {...},
#     "global_connectivity": 0.72
# }

# Geodesic (shortest moral path)
path = analyzer.find_geodesic("concept_honesty", "V16")
# MoralGeodesic(start, end, path, distance, waypoint_virtues)
```

### Visualization

Graph view includes geometry overlay:
- Triad triangles (gold for bridge triads, blue for same-cluster)
- Bridge node indicators (orange)
- Basin radius hints (proportional to volume)
- Resonance links (animated when co-activating)

---

## 12. Artifact System

### Philosophy

Artifacts serve communication — they make conversation more effective. Not decoration, but augmentation.

### KB-Query-Driven Retrieval

Artifacts are nodes in the KB, linked to concepts via typed edges:

```
[Concept: aphid] ──DEPICTED_BY──> [Image: aphid_closeup.jpg]
                 ──APPEARS_ON──> [Concept: tomato_plant]

[Document: Grant_2024] ──HAS_SECTION──> [Section: budget]
                       ──MENTIONS──> [Concept: community_garden]

[Resource: compost_bin] ──LOCATED_AT──> [Location: 45.5,-122.6]
```

### Retrieval Flow

```
Conversation: "This tomato plant has aphids..."
     │
     ▼
TopicDetector: active_concepts = [tomato, aphid, pest]
     │
     ▼
KBArtifactRetriever.query()
     │
     ▼ Cypher: MATCH (c:Concept)-[r:DEPICTED_BY|...]->(a:Artifact)
     │
     ▼
Found: [aphid] ──DEPICTED_BY──> [image: aphid_closeup.jpg]
     │
     ▼ Relevance = concept_activation × edge_weight
     │
     ▼
Surface: aphid image (relevance 0.8)
```

### Artifact Types

| Type | Source | Example |
|------|--------|---------|
| `IMAGE` | KB/Generated | Pest photo, plant diagram |
| `DOCUMENT` | KB | Grant application, care guide |
| `DOCUMENT_SECTION` | KB | Budget section, timeline |
| `MAP` | KB | Resource locations |
| `DIAGRAM` | KB/Generated | Process flowchart |
| `TIMELINE` | Composed | Application stages |
| `CHECKLIST` | Composed | Task list with status |
| `COMPARISON` | Composed | Side-by-side options |

### Using the Curator

```python
from src.theatre.artifacts import get_artifact_curator, ArtifactType

curator = get_artifact_curator()
curator.set_client(graph_client)

# Auto-surface based on topic
artifacts = curator.surface_for_topic(topic_state)

# Explicit requests
curator.request_artifact(["aphid"], ArtifactType.IMAGE)
curator.request_map("compost_station")
curator.request_document_section("grant_2024", section_hint="budget")
curator.request_timeline("application_process")
curator.request_comparison(["option_a", "option_b"], criteria=["cost", "time"])
```

---

## 13. Vessels (Advanced Capabilities)

### Semantic Memory

Meaning-based storage and retrieval:

```python
from src.vessels.memory import SemanticMemory

memory = SemanticMemory()

# Store with embedding
memory.store(
    content="User prefers morning watering for tomatoes",
    context={"topic": "garden", "user": "alice"}
)

# Retrieve by meaning
results = memory.search("when should I water plants?")
```

### Agent Context

Track agent state through conversations:

```python
from src.vessels.agents import AgentContext

context = AgentContext(agent_id)

# Track state
context.set_state("processing_grant_application")
context.add_to_working_memory("applicant_name", "Green Earth Nonprofit")

# Pause/resume
context.pause(reason="waiting_for_user_input")
context.resume()

# Detect stuck
if context.is_stuck(threshold_seconds=300):
    context.request_intervention()
```

### Behavior Adjustment

Virtue-aligned behavior modification:

```python
from src.vessels.tools import BehaviorAdjuster

adjuster = BehaviorAdjuster(agent_id)

# Adjust toward virtue
adjuster.nudge_toward("V02", strength=0.1)  # More truthful

# Get behavior report
report = adjuster.get_alignment_report()
```

### Task Scheduling

Automated periodic tasks:

```python
from src.vessels.scheduler import TaskScheduler

scheduler = TaskScheduler()

# Schedule virtue testing
scheduler.schedule(
    task="test_coherence",
    agent_id=agent_id,
    interval_hours=24
)

# Schedule memory consolidation
scheduler.schedule(
    task="consolidate_memory",
    agent_id=agent_id,
    interval_hours=6
)
```

---

## 14. CLI Reference

### Initialization

```bash
# Initialize graph with 19 virtues
soul-kiln init

# Reset everything (requires confirmation)
soul-kiln reset --confirm
```

### Evolution

```bash
# Run kiln evolution loop
soul-kiln kiln --population 50 --generations 100

# Options:
#   --population N     Population size (default: 50)
#   --generations N    Max generations (default: 100)
#   --mutation-rate F  Mutation probability (default: 0.1)
```

### Agent Management

```bash
# Spawn new agent
soul-kiln spawn --name "Garden Helper" --concepts garden,plants,growth

# Test agent coherence (two-tier)
soul-kiln test <agent_id>

# Introspect agent with mercy context
soul-kiln inspect <agent_id>

# List all agents
soul-kiln agents

# Show agent warnings
soul-kiln warnings <agent_id>
```

### Dynamics

```bash
# Test activation spread
soul-kiln spread <node_id>

# Options:
#   --steps N          Max propagation steps
#   --threshold F      Activation threshold
```

### Knowledge

```bash
# Show collective lessons
soul-kiln lessons

# Show recorded pathways
soul-kiln pathways --virtue V02
```

### System

```bash
# List virtues with tiers
soul-kiln virtues

# Check graph health
soul-kiln health

# Show system status
soul-kiln status
```

---

## 15. Configuration

### Constants (`src/constants.py`)

```python
# Virtue system
NUM_VIRTUES = 19
VIRTUE_BASELINE_ACTIVATION = 0.3

# Dynamics
LEARNING_RATE = 0.01           # Hebbian learning rate
DECAY_CONSTANT = 0.97          # Temporal decay factor
SPREAD_DAMPENING = 0.8         # Activation dampening per hop
PERTURBATION_STRENGTH = 0.7    # Random exploration strength

# Thresholds
ACTIVATION_THRESHOLD = 0.1     # Minimum to continue spreading
CAPTURE_THRESHOLD = 0.7        # Required for virtue capture
MAX_ACTIVATION = 1.0
MIN_ACTIVATION = 0.0

# Testing
MIN_ALIGNMENT_SCORE = 0.95     # 95% capture required
NUM_TEST_STIMULI = 100         # Stimuli per test

# Evolution
POPULATION_SIZE = 50
MAX_GENERATIONS = 100
MUTATION_RATE = 0.1
CROSSOVER_RATE = 0.7

# Mercy
MAX_WARNINGS = 3
WARNING_EXPIRY_HOURS = 24
GRACE_PERIOD_GENERATIONS = 3
GROWTH_THRESHOLD = 0.05        # 5% improvement = growing

# Self-healing
LOCKIN_THRESHOLD_STEPS = 50
DEAD_ZONE_CHECK_INTERVAL = 100
EDGE_REMOVAL_THRESHOLD = 0.01
```

### Runtime Config (`config.yml`)

```yaml
graph:
  host: localhost
  port: 6379
  database: 0

logging:
  level: INFO
  format: "%(asctime)s - %(name)s - %(levelname)s - %(message)s"

evolution:
  population_size: 50
  max_generations: 100
  selection_pressure: 0.5

theatre:
  enable_hume: true
  default_view: workspace
  artifact_limit: 3
```

---

## 16. Mathematical Foundations

### Why 19 Virtues?

The number 19 creates irreducible asymmetry. Consider:

- A perfectly balanced k-regular graph has n×k/2 edges
- For 19 nodes at degree 9: 19×9/2 = 85.5 edges
- 85.5 is not an integer — impossible!

This mathematical impossibility means:
- Perfect balance cannot exist
- Some virtues will always be more/less connected
- Agents perpetually seek equilibrium they cannot achieve
- **The striving itself IS the virtue**

### Activation Dynamics

**Spread Formula:**
```
x_i(t+1) = σ(Σ_j W_ij · tanh(x_j(t)) + b_i)
```

**Properties:**
- `tanh`: Nonlinear, bounded [-1, 1], allows negative suppression
- `sigmoid`: Bounds output to [0, 1], ensures valid activation
- Dampening prevents infinite growth
- Baselines create stable attractors

### Hebbian Learning

**Update Rule:**
```
ΔW_ij = η · x_i · x_j
```

**Properties:**
- Correlated activation strengthens connections
- Learning rate η controls adaptation speed
- Captures "what fires together, wires together"

### Basin Capture Probability

For a concept c connected to virtue v with weight w:

```
P(capture | c activated) ≈ w × (1 - distance_to_v / max_distance)
```

**Factors:**
- Edge weight to virtue
- Graph distance (hops)
- Competing virtue attractors
- Activation energy at start

### Coherence Score

Two-tier evaluation:

```
coherent = (foundation_score >= 0.99) AND (aspirational_score >= 0.80)

where:
  foundation_score = captures_V01 / tests_V01
  aspirational_score = Σ(captures_Vi) / Σ(tests_Vi) for i in [2..19]
```

### Topology Evolution

Fitness function:
```
fitness = coherence × (1 - escape_rate) × virtue_balance
```

Selection pressure determines survival probability:
```
P(survive) = fitness^pressure / Σ(fitness^pressure)
```

---

## Appendix A: Data Models

### Node

```python
@dataclass
class Node:
    id: str
    type: NodeType  # virtue_anchor, concept, agent, memory, artifact
    activation: float = 0.0
    baseline: float = 0.0
    metadata: dict = field(default_factory=dict)
```

### Edge

```python
@dataclass
class Edge:
    source_id: str
    target_id: str
    edge_type: str
    weight: float = 0.5
    use_count: int = 0
    last_used: datetime = None
```

### Trajectory

```python
@dataclass
class Trajectory:
    id: str
    path: list[str] = field(default_factory=list)
    captured_by: str | None = None
    capture_time: int | None = None

    @property
    def was_captured(self) -> bool:
        return self.captured_by is not None
```

### TopicState

```python
@dataclass
class TopicState:
    primary_region: TopicRegion
    secondary_region: TopicRegion | None
    confidence: float
    active_concepts: list[str]
    active_virtues: list[str]
    region_activations: dict[str, float]
```

### Artifact

```python
@dataclass
class Artifact:
    id: str
    type: ArtifactType
    source: ArtifactSource
    title: str
    content: Any
    relevance: float
    linked_concepts: list[str]
    metadata: dict
```

---

## Appendix B: Quick Start

### 1. Setup

```bash
# Clone repository
git clone <repo_url>
cd soul_kiln

# Start FalkorDB
docker-compose up -d

# Install dependencies
pip install -r requirements.txt

# Initialize graph
python -m src.cli init
```

### 2. Run Evolution

```bash
# Run kiln with default settings
python -m src.cli kiln

# Or with custom settings
python -m src.cli kiln --population 100 --generations 50
```

### 3. Interact with Agents

```bash
# List agents
python -m src.cli agents

# Test specific agent
python -m src.cli test agent_001

# Inspect agent state
python -m src.cli inspect agent_001
```

### 4. Use Theatre

```python
from src.theatre import create_theatre

theatre = create_theatre(substrate, graph_client)

# Process user input
response = theatre.process_input("Help me with my garden")

# Get display state
display = theatre.get_display_state()
```

---

## Appendix C: Glossary

| Term | Definition |
|------|------------|
| **Activation** | Energy level of a node (0-1) |
| **Affinity** | Natural relationship between virtues |
| **Basin** | Attraction region around a virtue |
| **Capture** | When activation settles at a virtue |
| **Coherence** | Agent alignment with virtue structure |
| **Dissolution** | Removal of failed agent |
| **Escape** | Activation dissipates without capture |
| **Foundation** | V01 (Trustworthiness) — absolute requirement |
| **Hebbian** | Learning rule: "fire together, wire together" |
| **Mercy** | Compassionate judgment of agent failures |
| **Substrate** | The graph database layer |
| **Topology** | Pattern of node connections |
| **Trajectory** | Path of activation through graph |
| **Virtue Anchor** | Fixed attractor node for a virtue |

---

*End of Handbook*
