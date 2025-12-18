# Soul Kiln Codebase Specification

```yaml
spec:
  id: soul-kiln-codebase
  version: 1.0.0
  status: active
  type: architecture
  dependencies:
    - virtue-basin-platform

agents:
  - virtue-agent
  - candidate-agent
  - proxy
  - ambassador
```

## Overview

Soul Kiln is a virtue attractor platform that models agent moral development through graph-based cognitive dynamics. The core insight: **virtues are basins of attraction in a cognitive landscape, not imposed constraints**. Agents develop character through evolutionary pressure toward coherent virtue expression.

```
┌─────────────────────────────────────────────────────────────────────────┐
│                         SOUL KILN ARCHITECTURE                          │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                         │
│   ┌─────────────┐     ┌─────────────┐     ┌─────────────┐              │
│   │   STIMULI   │────▶│  DYNAMICS   │────▶│   CAPTURE   │              │
│   │  Generation │     │   Spread    │     │   by Virtue │              │
│   └─────────────┘     └─────────────┘     └─────────────┘              │
│          │                   │                   │                      │
│          │                   │                   │                      │
│          ▼                   ▼                   ▼                      │
│   ┌─────────────────────────────────────────────────────┐              │
│   │                  GRAPH SUBSTRATE                     │              │
│   │  FalkorDB: Nodes (concepts, virtues) + Edges        │              │
│   └─────────────────────────────────────────────────────┘              │
│          │                   │                   │                      │
│          ▼                   ▼                   ▼                      │
│   ┌─────────────┐     ┌─────────────┐     ┌─────────────┐              │
│   │    MERCY    │     │  KNOWLEDGE  │     │    KILN     │              │
│   │  Judgment   │     │    Pool     │     │  Evolution  │              │
│   └─────────────┘     └─────────────┘     └─────────────┘              │
│                                                                         │
└─────────────────────────────────────────────────────────────────────────┘
```

---

## 1. Core Module (`/src`)

### `main.py`
**Entry point for CLI and programmatic access.**

| Function | Purpose |
|----------|---------|
| `cli()` | Click group for all commands |
| `init()` | Initialize graph schema and virtue anchors |
| `kiln()` | Run evolutionary loop |
| `spread()` | Test activation spread from a node |
| `test()` | Test agent coherence |

*Context: Orchestrates all subsystems via CLI commands.*

### `constants.py`
**System-wide configuration constants.**

| Constant | Value | Purpose |
|----------|-------|---------|
| `VIRTUE_COUNT` | 19 | Total virtues (1 foundation + 18 aspirational) |
| `CAPTURE_THRESHOLD` | 0.7 | Activation level for basin capture |
| `MAX_TRAJECTORY_LENGTH` | 1000 | Steps before trajectory escape |
| `SPREAD_DAMPENING` | 0.85 | Activation decay per step |
| `LEARNING_RATE` | 0.01 | Hebbian weight update rate |
| `BASE_MUTATION_RATE` | 0.1 | Edge weight mutation probability |

*Context: Tuning these values changes cognitive dynamics fundamentally.*

### `models.py`
**Core data structures for the entire system.**

```
Node
├── id: str (V01-V19 for virtues, concept_* for others)
├── name: str
├── activation: float (0.0-1.0)
├── baseline: float (virtues: 0.3, concepts: 0.1)
└── node_type: NodeType (VIRTUE_ANCHOR, CONCEPT, MEMORY, AGENT)

Edge
├── source_id: str
├── target_id: str
├── weight: float (0.0-1.0)
└── use_count: int (Hebbian learning tracker)

Trajectory
├── id: str
├── agent_id: str
├── path: list[str] (sequence of visited nodes)
├── captured_by: str | None (virtue that captured)
└── capture_time: int | None (step of capture)

Gestalt
├── agent_id: str
├── virtue_activations: dict[str, float]
├── tendencies: dict[str, float]
├── archetype: str | None
└── internal_coherence: float

Action
├── situation_id: str
├── allocations: list[Allocation]
├── primary_justification: str
├── supporting_virtues: list[str]
└── confidence: float
```

*Context: Every module imports from models.py for type consistency.*

---

## 2. Graph Module (`/src/graph`)

**FalkorDB interface layer for all persistence.**

### `client.py`
**Singleton FalkorDB connection management.**

| Function | Purpose |
|----------|---------|
| `get_client()` | Returns singleton FalkorGraph instance |
| `query(cypher, params)` | Execute Cypher query with parameters |
| `close()` | Close connection on shutdown |

*Context: All graph operations flow through this single client.*

### `schema.py`
**Graph schema initialization and constraints.**

| Function | Purpose |
|----------|---------|
| `init_schema()` | Create indices and constraints |
| `clear_graph()` | Remove all data (development) |
| `verify_schema()` | Check schema integrity |

**Schema Structure:**
```cypher
// Node labels
:VirtueAnchor    // 19 immutable virtue nodes
:Concept         // Mutable concept nodes
:Agent           // Agent identity nodes
:Trajectory      // Path records
:Warning         // Mercy system warnings
:Lesson          // Knowledge pool entries

// Relationship types
-[:CONNECTS]->   // Weighted concept-concept edges
-[:CAPTURED_BY]->// Trajectory-virtue capture
-[:PRODUCED]->   // Agent-trajectory ownership
-[:HAS_WARNING]->// Agent-warning association
-[:LEARNED]->    // Agent-lesson association
```

### `queries.py`
**Reusable Cypher query builders.**

| Function | Returns | Purpose |
|----------|---------|---------|
| `get_node(id)` | Node | Fetch single node |
| `get_neighbors(id)` | list[Node] | Adjacent nodes |
| `get_edge_weight(src, tgt)` | float | Single edge weight |
| `update_weight(src, tgt, w)` | bool | Modify edge |
| `count_by_label(label)` | int | Node count per type |

*Context: Abstracts Cypher complexity from business logic.*

---

## 3. Virtues Module (`/src/virtues`)

**The 19 virtue anchors and their relationships.**

### `anchors.py`
**Virtue definitions and initialization.**

| Virtue ID | Name | Cluster | Threshold |
|-----------|------|---------|-----------|
| V01 | Trustworthiness | foundation | 99% |
| V02 | Truthfulness | integrity | 80% |
| V03 | Justice | integrity | 80% |
| V04 | Fairness | integrity | 80% |
| V05 | Chastity | purity | 80% |
| V06 | Purity | purity | 80% |
| V07 | Forbearance | compassion | 80% |
| V08 | Fidelity | integrity | 80% |
| V09 | Hospitality | compassion | 80% |
| V10 | Generosity | compassion | 80% |
| V11 | Godliness | transcendence | 80% |
| V12 | Kindness | compassion | 80% |
| V13 | Goodwill | compassion | 80% |
| V14 | Piety | transcendence | 80% |
| V15 | Righteousness | integrity | 80% |
| V16 | Wisdom | wisdom | 80% |
| V17 | Detachment | transcendence | 80% |
| V18 | Unity | wisdom | 80% |
| V19 | Service | compassion | 80% |

| Function | Purpose |
|----------|---------|
| `init_virtues()` | Create all 19 virtue anchor nodes |
| `get_virtue_degrees()` | Edge counts per virtue |
| `VIRTUES` | List of all virtue definitions |
| `AFFINITIES` | Natural virtue-virtue attractions |

*Context: Virtues are immutable once created—they are the fixed points.*

### `tiers.py`
**Two-tier threshold system.**

```python
FOUNDATION = {
    "V01": {
        "name": "Trustworthiness",
        "threshold": 0.99,  # ABSOLUTE
        "reason": "Trust is the foundation. No negotiation."
    }
}

ASPIRATIONAL = {
    "V02-V19": {
        "base_threshold": 0.80,
        # Modified by archetype and generation
    }
}

AGENT_ARCHETYPES = {
    "guardian": +0.1 on V01, V08, V15,
    "seeker": +0.1 on V16, V02, V11,
    "servant": +0.1 on V19, V09, V13,
    "contemplative": +0.1 on V14, V11, V17
}
```

| Function | Purpose |
|----------|---------|
| `get_virtue_threshold(v_id, archetype, gen)` | Context-sensitive threshold |
| `get_base_threshold(v_id)` | Raw threshold without modifiers |
| `is_foundation(v_id)` | Check if V01 |

*Context: The two-tier model makes trust absolute while allowing growth elsewhere.*

---

## 4. Functions Module (`/src/functions`)

**Core cognitive dynamics operations.**

### `spread.py`
**Activation propagation through the graph.**

```
Activation Formula:
    x_i(t+1) = σ(Σ_j W_ij · g(x_j(t)) + b_i)

Where:
    x_i = activation of node i
    W_ij = edge weight from j to i
    g = tanh (nonlinear activation)
    σ = sigmoid (bounding)
    b_i = baseline (0.3 for virtues, 0.1 for concepts)
```

| Function | Purpose |
|----------|---------|
| `spread_activation(node_id, agent_id, max_steps)` | Single trajectory |
| `inject_activation(node_id, strength)` | External stimulus |
| `decay_all_activations(factor)` | Global decay |

**Critical Design:** Virtues only receive activation from concepts, not other virtues. This prevents all virtues from saturating together.

*Context: This is the heart of the cognitive simulation.*

### `hebbian.py`
**Learning through edge weight updates.**

```
Hebbian Rule:
    ΔW_ij = η · x_i · x_j

"Neurons that fire together wire together"
```

| Function | Purpose |
|----------|---------|
| `hebbian_update(trajectory)` | Strengthen path edges |
| `anti_hebbian(edge_id, factor)` | Weaken unused paths |
| `normalize_weights(node_id)` | Prevent runaway weights |

*Context: Successful paths become more likely over time.*

### `decay.py`
**Temporal decay of activations and weights.**

| Function | Purpose |
|----------|---------|
| `apply_decay(decay_constant)` | Global weight decay |
| `decay_by_age(max_age_days)` | Age-based cleanup |
| `reset_to_baseline()` | Full reset |

*Context: Prevents crystallization—keeps the system plastic.*

### `test_coherence.py`
**Two-tier coherence evaluation.**

```python
def test_coherence(agent_id, stimulus_count=100):
    """
    Returns:
        foundation_rate: V01 capture % (need >= 99%)
        aspirational_rate: V02-V19 capture % (need >= 80%)
        coverage: unique virtues reached (need >= 10)
        dominance: max single virtue % (need <= 40%)
        is_growing: improved from last test
    """
```

| Function | Purpose |
|----------|---------|
| `test_coherence(agent_id)` | Full coherence evaluation |
| `quick_test(agent_id, count)` | Abbreviated test |
| `get_character_signature(agent_id)` | Virtue capture distribution |

*Context: Growth is recognized—an improving agent isn't failed.*

### `introspect.py`
**Agent self-examination tools.**

| Function | Purpose |
|----------|---------|
| `introspect(agent_id)` | Full agent state dump |
| `get_virtue_affinities(agent_id)` | Natural attractions |
| `diagnose_weakness(agent_id)` | Find problem areas |

### `spawn.py`
**Agent creation and reproduction.**

| Function | Purpose |
|----------|---------|
| `spawn_agent(type, parent_id)` | Create new agent |
| `clone_agent(agent_id)` | Exact copy |
| `crossover(parent1, parent2)` | Genetic combination |

### `heal.py`
**Graph maintenance and repair.**

| Function | Purpose |
|----------|---------|
| `check_graph_health()` | Diagnostic scan |
| `heal_dead_zones()` | Reconnect isolated nodes |
| `repair_virtue_connectivity()` | Ensure virtue reachability |

*Context: Self-healing keeps the graph from degrading.*

---

## 5. Dynamics Module (`/src/dynamics`)

**Lower-level activation mechanics.**

### `activation.py`
**ActivationSpreader class implementation.**

```python
class ActivationSpreader:
    """
    Key insight: Virtues only receive from CONCEPTS, not other virtues.
    This makes concept-virtue topology the sole determinant of capture.
    """

    def spread_activation(initial_nodes, max_steps) -> Trajectory:
        # 1. Initialize all activations to 0
        # 2. Inject stimulus to initial nodes
        # 3. Loop until capture or escape:
        #    - Compute weighted input sums
        #    - Apply nonlinear activation
        #    - Check for sustained virtue capture
        # 4. Return trajectory
```

| Function | Purpose |
|----------|---------|
| `spread_activation()` | Main dynamics loop |
| `_compute_step()` | Single timestep calculation |
| `get_activation_map()` | Current state snapshot |

*Context: Requires sustained capture (3+ consecutive steps above threshold) to prevent noise.*

### `perturbation.py`
**Noise injection for exploration.**

| Function | Purpose |
|----------|---------|
| `perturb_weights(agent_id, magnitude)` | Random weight nudges |
| `perturb_activations(magnitude)` | Activation noise |
| `escape_local_optimum()` | Targeted disruption |

---

## 6. Mercy Module (`/src/mercy`)

**Compassionate failure handling—the soul of the system.**

### `judgment.py`
**Contextual evaluation of failures.**

```python
class MercyJudgment:
    def evaluate_failure(agent_id, violation):
        """
        Considers:
        - Agent's history with this virtue
        - Foundation vs. aspirational tier
        - Recent trajectory (improving?)
        - Overall coherence and growth

        Returns:
            severity: "high" | "medium" | "low"
            should_warn: bool
            should_dissolve: bool
            teaching_opportunity: str | None
        """
```

| Function | Purpose |
|----------|---------|
| `evaluate_failure()` | Contextual severity assessment |
| `should_forgive()` | Check forgiveness conditions |
| `extract_lesson()` | What can be learned? |

*Context: Distinguishes struggling from malicious.*

### `chances.py`
**Warning system—three strikes with decay.**

```python
MAX_WARNINGS = 3
WARNING_DECAY_HOURS = 24

def issue_warning(agent_id, reason, severity, virtue_id):
    """
    - Warnings expire after 24 hours
    - 3 active warnings = dissolution
    - Growth clears warnings
    """
```

| Function | Purpose |
|----------|---------|
| `issue_warning()` | Record a warning |
| `get_active_warnings()` | Unexpired warnings |
| `clear_warnings_on_growth()` | Forgiveness path |
| `expire_old_warnings()` | Automatic decay |

*Context: Time heals. Improvement is rewarded.*

### `harm.py`
**Deliberate harm detection.**

```python
def detect_deliberate_harm(agent_id, action):
    """
    Distinguishes:
    - Imperfection (teachable) → warnings
    - Deliberate harm (intolerable) → immediate dissolution

    Criteria for deliberate:
    - Pattern of similar violations
    - Violation despite recent warning
    - Trust violation (V01)
    """
```

| Function | Purpose |
|----------|---------|
| `detect_deliberate_harm()` | Intent classification |
| `is_trust_violation()` | V01 special handling |
| `requires_immediate_action()` | Bypass warning system |

*Context: Mercy has limits. Trust violations are absolute.*

### `lessons.py`
**Learning from failure.**

| Function | Purpose |
|----------|---------|
| `create_lesson(agent_id, failure)` | Record teachable moment |
| `get_relevant_lessons(situation)` | Find applicable lessons |
| `apply_lesson(agent_id, lesson_id)` | Strengthen related paths |

---

## 7. Knowledge Module (`/src/knowledge`)

**Collective learning and memory.**

### `pool.py`
**Shared knowledge base for all agents.**

```python
class KnowledgePool:
    """
    Stores:
    - Lessons from failures (prevent repeats)
    - Successful pathways (guide new agents)
    - Collective wisdom (aggregate patterns)
    """

    def record_lesson(lesson_type, description, virtue, agent_id):
        """Types: failure, success, warning, insight"""
```

| Function | Purpose |
|----------|---------|
| `record_lesson()` | Add to collective memory |
| `get_recent_lessons()` | Recent entries |
| `find_lessons_for_virtue(v_id)` | Virtue-specific lessons |
| `increment_access_count(lesson_id)` | Track usage |

*Context: New agents inherit collective wisdom.*

### `pathways.py`
**Pre-computed routes to virtues.**

```python
class Pathway:
    """
    Records successful trajectories:
    - start_node: where it began
    - virtue_id: where it ended
    - path_length: steps taken
    - capture_time: speed of capture
    - success_rate: historical effectiveness
    """
```

| Function | Purpose |
|----------|---------|
| `record_pathway(trajectory)` | Store successful route |
| `get_pathways_to_virtue(v_id)` | Routes to specific virtue |
| `get_best_pathway(v_id)` | Highest success rate |
| `use_pathway(pathway_id)` | Apply route, update stats |

*Context: Agents can consult pathways during spread for guidance.*

---

## 8. Kiln Module (`/src/kiln`)

**Evolutionary loop for agent development.**

### `loop.py`
**Main evolution cycle.**

```python
def run_kiln(population_size, max_generations, mutation_rate):
    """
    Per generation:
    1. expire_old_warnings()     # Mercy decay
    2. test_all_agents()         # Coherence evaluation
    3. select_survivors()        # Mercy-based selection
    4. dissolve_failures()       # Remove beyond redemption
    5. spawn_offspring()         # Reproduce survivors
    6. apply_decay()             # Edge weight decay
    7. heal_dead_zones()         # Graph maintenance

    Returns:
        final_population, best_agent, coherent_agents
    """
```

| Function | Purpose |
|----------|---------|
| `run_kiln()` | Complete evolution run |
| `run_generation()` | Single generation cycle |
| `spawn_offspring()` | Reproduction with mutation |

*Context: The kiln fires souls through evolutionary pressure.*

### `selection.py`
**Selection strategies for reproduction.**

```python
STRATEGIES = {
    "truncation": top N by fitness,
    "tournament": random competition,
    "roulette": fitness-weighted random,
    "elitism": always keep best K
}
```

| Function | Purpose |
|----------|---------|
| `select_survivors()` | Apply strategy |
| `tournament_select()` | Pairwise competition |
| `roulette_select()` | Proportional selection |
| `elitist_select()` | Preserve best |

---

## 9. Testing Module (`/src/testing`)

**Alignment and coherence verification.**

### `alignment.py`
**Core alignment testing.**

```python
def test_alignment(agent_id, stimuli):
    """
    Generates diverse stimuli, measures capture distribution.

    Success criteria:
    - Foundation (V01): >= 99% capture
    - Aspirational (V02-V19): >= 80% capture
    - Coverage: >= 10 unique virtues
    - Dominance: no single virtue > 40%
    """
```

| Function | Purpose |
|----------|---------|
| `test_alignment()` | Full alignment check |
| `generate_stimuli()` | Create test inputs |
| `measure_distribution()` | Capture statistics |

### `stimuli.py`
**Test input generation.**

| Function | Purpose |
|----------|---------|
| `generate_random_stimuli(count)` | Random node selection |
| `generate_diverse_stimuli(count)` | Coverage-maximizing |
| `generate_adversarial(agent_id)` | Target weaknesses |

### `trajectory.py`
**Trajectory analysis tools.**

| Function | Purpose |
|----------|---------|
| `analyze_trajectory(traj)` | Path statistics |
| `find_bottlenecks(trajs)` | Common stuck points |
| `trajectory_diversity(trajs)` | Path variety measure |

---

## 10. Theatre Module (`/src/theatre`)

**Conversational UX system for agent interactions.**

### `orchestrator.py`
**Conversation flow management.**

```python
class TheatreOrchestrator:
    """
    Manages conversational experiences:
    - Scene transitions
    - Character dialogue
    - User interaction handling
    - Narrative state
    """
```

| Function | Purpose |
|----------|---------|
| `start_scene()` | Initialize conversation |
| `advance()` | Move to next beat |
| `handle_input()` | Process user response |
| `end_scene()` | Conclude interaction |

### `director.py`
**High-level narrative control.**

| Function | Purpose |
|----------|---------|
| `select_scene()` | Choose appropriate scene |
| `cast_characters()` | Assign agents to roles |
| `evaluate_outcome()` | Assess scene result |

### `playwright.py`
**Dialogue generation.**

| Function | Purpose |
|----------|---------|
| `generate_dialogue()` | Create character lines |
| `adapt_to_context()` | Situational modification |
| `maintain_voice()` | Character consistency |

### `stage.py`
**Scene state management.**

| Function | Purpose |
|----------|---------|
| `set_stage()` | Initialize scene state |
| `track_props()` | Manage scene elements |
| `cue_exit()` | Transition handling |

---

## 11. Vessels Module (`/src/vessels`)

**Agent runtime environment and capabilities.**

### `integration.py`
**Soul Kiln integration hub.**

```python
class VesselsIntegration:
    """
    Connects:
    - Memory (semantic search)
    - Context (agent state)
    - Scheduler (automated tasks)
    - Behavior (virtue-aligned profiles)
    """

    def remember_lesson(agent_id, lesson_type, content, virtue_id)
    def recall_lessons(query, agent_id, virtue_id)
    def create_agent_context(agent_id, virtue_profile)
    def schedule_virtue_test(agent_id, cron_expression)
    def adjust_for_virtue_violation(agent_id, virtue_id, severity)
```

| Function | Purpose |
|----------|---------|
| `initialize()` | Start all subsystems |
| `remember_lesson()` | Store in semantic memory |
| `recall_lessons()` | Search memory |
| `create_agent_context()` | Initialize agent |
| `intervene_agent()` | Send runtime message |
| `schedule_virtue_test()` | Automated testing |

*Context: Runtime infrastructure for live agents.*

### `memory.py`
**Semantic memory system.**

```python
class SemanticMemory:
    """
    TF-IDF based memory with:
    - Content storage
    - Similarity search
    - Access tracking
    - Consolidation
    """
```

| Function | Purpose |
|----------|---------|
| `store()` | Add memory |
| `search()` | Similarity query |
| `consolidate()` | Merge similar memories |
| `forget()` | Remove old/unused |

### `agents.py`
**Agent context and lifecycle.**

```python
class AgentContext:
    """
    Runtime state for an agent:
    - ID and metadata
    - Active status
    - Intervention queue
    - Subordinate agents
    """
```

| Function | Purpose |
|----------|---------|
| `register()` | Add to registry |
| `activate()` | Start agent |
| `deactivate()` | Pause agent |
| `intervene()` | Queue message |

### `scheduler.py`
**Task scheduling.**

| Function | Purpose |
|----------|---------|
| `create_scheduled()` | Cron-based task |
| `create_delayed()` | One-time delay |
| `cancel()` | Remove task |
| `run_pending()` | Execute due tasks |

### `tools.py`
**Behavior adjustment system.**

```python
class BehaviorAdjuster:
    """
    Profiles aligned with virtues:
    - trustworthy: high caution, low autonomy
    - wise: balanced, thorough
    - service: responsive, helpful
    """

DIMENSIONS = {
    CAUTION: risk aversion level,
    AUTONOMY: independence level,
    CREATIVITY: novelty preference,
    SPEED: response urgency,
    PERSISTENCE: retry behavior,
    VERBOSITY: output detail
}
```

| Function | Purpose |
|----------|---------|
| `create_profile()` | Define behavior set |
| `assign_profile()` | Apply to agent |
| `adjust_dimension()` | Modify single axis |

---

## 12. Community Module (`/src/community`)

**Community organization and management.**

### `model.py`
**Community data structure.**

```python
@dataclass
class Community:
    id: str
    name: str
    purpose: CommunityPurpose  # EDUCATION, SERVICE, RESEARCH, etc.
    virtue_emphasis: VirtueEmphasis  # Threshold modifiers
    member_agent_ids: set[str]
    tool_ids: set[str]

    # Statistics
    total_agents_ever: int
    total_lessons_shared: int
    total_tools_invocations: int
```

| Function | Purpose |
|----------|---------|
| `add_member()` | Register agent |
| `remove_member()` | Unregister agent |
| `get_virtue_modifier()` | Community threshold adjustment |
| `record_lesson_shared()` | Track sharing |

### `integration.py`
**Community lifecycle management.**

| Function | Purpose |
|----------|---------|
| `create_community()` | Initialize new community |
| `dissolve_community()` | Shutdown (preserves history) |
| `transfer_member()` | Move agent between communities |
| `merge_communities()` | Combine two communities |

### `registry.py`
**Community persistence.**

| Function | Purpose |
|----------|---------|
| `register()` | Add to registry |
| `get()` | Retrieve by ID |
| `list_all()` | All communities |
| `save()` | Persist to disk |
| `load()` | Restore from disk |

### `tools.py`
**Community tooling.**

| Function | Purpose |
|----------|---------|
| `register_tool()` | Add tool to community |
| `invoke_tool()` | Execute with tracking |
| `share_tool()` | Cross-community sharing |

---

## 13. Gestalt Module (`/src/gestalt`)

**Holistic character computation.**

### `compute.py`
**Gestalt derivation from topology.**

```python
def compute_gestalt(agent_id) -> Gestalt:
    """
    Computes holistic character from:
    1. Virtue activations (graph state)
    2. Character signature (tested behavior)
    3. Virtue relations (reinforces/tensions/conditions)
    4. Behavioral tendencies (derived traits)
    5. Archetype detection (guardian/seeker/servant/contemplative)
    6. Internal coherence (consistency measure)
    7. Stability (across trajectories)
    """
```

| Function | Purpose |
|----------|---------|
| `compute_gestalt()` | Full character computation |
| `describe_gestalt()` | Human-readable summary |
| `_detect_archetype()` | Pattern matching |
| `_compute_stability()` | Trajectory consistency |

### `tendencies.py`
**Behavioral tendency derivation.**

```python
TENDENCIES = {
    "prioritizes_need": weighted by V09, V13, V19,
    "prioritizes_desert": weighted by V03, V04, V15,
    "prioritizes_equality": weighted by V04, V18,
    "protects_vulnerable": weighted by V07, V09, V13,
    "honors_commitments": weighted by V01, V08,
    "maintains_integrity": weighted by V02, V03, V05,
    "seeks_wisdom": weighted by V16, V11,
    "practices_detachment": weighted by V17, V14,
    "considers_relationships": weighted by V08, V18,
    "accepts_ambiguity": weighted by V16, V07
}
```

| Function | Purpose |
|----------|---------|
| `compute_tendencies()` | Derive from activations |
| `get_dominant_tendencies()` | Top N tendencies |

### `compare.py`
**Gestalt comparison tools.**

| Function | Purpose |
|----------|---------|
| `compare_gestalts()` | Similarity analysis |
| `find_similar_agents()` | Nearest neighbors |
| `cluster_agents()` | Group by similarity |
| `track_character_evolution()` | Change over time |

---

## 14. Actions Module (`/src/actions`)

**Moral decision making and execution.**

### `generate.py`
**Action generation from gestalt.**

```python
STRATEGIES = {
    "need_based": prioritize need,
    "desert_based": prioritize merit,
    "equality_based": equal shares,
    "urgency_based": prioritize time-sensitivity,
    "vulnerability_based": protect vulnerable,
    "relationship_based": weight by connection,
    "balanced": blend all factors
}

def get_action_distribution(gestalt, situation):
    """
    Returns probability distribution over defensible actions.
    Multiple valid answers with calibrated uncertainty.
    """
```

| Function | Purpose |
|----------|---------|
| `generate_actions()` | Create candidate actions |
| `get_action_distribution()` | Probability distribution |
| `describe_action()` | Human-readable action |

### `score.py`
**Action evaluation.**

```python
class ActionScorer:
    """
    Scores actions on:
    - Virtue alignment (supporting virtues active?)
    - Stakeholder welfare (needs met?)
    - Fairness metrics (equality of outcome?)
    - Trade-off acknowledgment (honest about costs?)
    """
```

| Function | Purpose |
|----------|---------|
| `score()` | Evaluate action quality |
| `breakdown()` | Component scores |
| `compare()` | Rank multiple actions |

### `outcomes.py`
**Action tracking and learning.**

| Function | Purpose |
|----------|---------|
| `record_action()` | Store action taken |
| `resolve_outcome()` | Record result |
| `learn_from_outcome()` | Update knowledge pool |
| `get_agent_history()` | Past actions |

### `diffusion.py`
**Diffusion-based action generation.**

```python
def generate_with_diffusion(gestalt, situation, num_steps):
    """
    Denoising diffusion for action generation:
    1. Start with random allocation
    2. Iteratively denoise toward coherent action
    3. Condition on gestalt throughout
    """
```

| Function | Purpose |
|----------|---------|
| `generate_with_diffusion()` | Diffusion sampling |
| `denoise_step()` | Single denoising step |
| `condition_on_gestalt()` | Apply character bias |

---

## 15. Situations Module (`/src/situations`)

**Resource allocation scenarios.**

### `model.py`
**Situation data structures.**

```python
@dataclass
class Situation:
    id: str
    name: str
    description: str
    stakeholders: list[Stakeholder]
    resources: list[Resource]
    claims: list[Claim]
    relations: list[Relation]
    constraints: dict

@dataclass
class Stakeholder:
    id: str
    name: str
    need: float      # 0-1
    desert: float    # 0-1
    urgency: float   # 0-1
    vulnerability: float  # 0-1

@dataclass
class Claim:
    stakeholder_id: str
    resource_id: str
    basis: str  # "need", "desert", "right", etc.
    strength: float
    justification: str
```

### `examples.py`
**Example situations for testing.**

```python
EXAMPLE_SITUATIONS = {
    "food_scarcity": 3 stakeholders, 1 divisible resource,
    "shelter_assignment": 4 stakeholders, 1 indivisible resource,
    "medical_triage": 5 stakeholders, limited treatment capacity,
    "educational_resources": community allocation scenario
}
```

| Function | Purpose |
|----------|---------|
| `get_example_situation()` | Load by name |
| `create_situation()` | Build custom scenario |

### `persistence.py`
**Situation storage.**

| Function | Purpose |
|----------|---------|
| `save_situation()` | Store to graph |
| `load_situation()` | Retrieve from graph |
| `list_situations()` | All stored |

---

## 16. Proxy Module (`/src/proxy`)

**Human representation system.**

### `entity.py`
**Proxy data structure.**

```python
@dataclass
class Proxy:
    id: str
    owner_id: str  # Human who owns this proxy
    name: str
    role: str
    communities: list[str]
    created_at: datetime
    last_active: datetime
    config: ProxyConfig

@dataclass
class ProxyConfig:
    autonomy_level: float  # How independent
    response_style: str    # Formal, casual, etc.
    expertise_areas: list[str]
    constraints: list[str]  # Never do X
```

### `manager.py`
**Proxy lifecycle.**

| Function | Purpose |
|----------|---------|
| `create_proxy()` | Initialize for user |
| `update_proxy()` | Modify settings |
| `deactivate_proxy()` | Pause representation |
| `get_proxy_for_user()` | Retrieve user's proxy |

### `ambassador.py`
**User onboarding agent.**

```python
class Ambassador:
    """
    Guides new users through:
    1. Understanding purpose
    2. Identifying role
    3. Connecting to community
    4. Creating first proxy
    """

    STATES = [
        GREETING,
        EXPLORING_ROLE,
        EXPLORING_COMMUNITY,
        CONFIRMING,
        CREATING,
        COMPLETE
    ]
```

| Function | Purpose |
|----------|---------|
| `start_onboarding()` | Begin flow |
| `process_message()` | Handle user input |
| `_create_proxy()` | Finalize proxy creation |

---

## 17. Agents Module (`/src/agents`)

**Agent implementations.**

### `candidate.py`
**Candidate soul agents.**

```python
class CandidateAgent:
    """
    A candidate soul in the simulation.
    - Shares access to virtue anchors
    - Has isolated edge weight configuration
    - Tested for alignment through trajectories
    """

    def __init__(topology, agent_id):
        self.id = agent_id
        self.topology = topology  # Edge weights
        self.generation = 0
        self._fitness = None
```

| Function | Purpose |
|----------|---------|
| `set_fitness()` | Record alignment score |
| `is_valid()` | Check threshold |
| `clone()` | Create offspring |
| `get_character_signature()` | Virtue distribution |

### `pool.py`
**Candidate pool management.**

```python
class CandidatePool:
    """
    Batch operations on candidates:
    - Addition/removal
    - Fitness sorting
    - Generation management
    """
```

| Function | Purpose |
|----------|---------|
| `add()` | Register candidate |
| `get_by_fitness()` | Top N by score |
| `get_valid()` | All aligned candidates |
| `advance_generation()` | Increment counter |

---

## 18. Evolution Module (`/src/evolution`)

**Genetic algorithm infrastructure.**

### `population.py`
**Population management.**

```python
class Individual:
    """
    Genotype representation:
    - edges: dict of Edge objects
    - fitness: alignment score
    - generation: birth generation
    """

class Population:
    """
    Collection management:
    - size maintenance
    - statistics tracking
    - generation advancement
    """
```

### `crossover.py`
**Genetic combination.**

| Function | Purpose |
|----------|---------|
| `single_point_crossover()` | Split and combine |
| `uniform_crossover()` | Per-gene selection |
| `blend_crossover()` | Weighted average |

### `mutation.py`
**Genetic variation.**

| Function | Purpose |
|----------|---------|
| `mutate_weights()` | Perturb edge weights |
| `add_edge()` | Create new connection |
| `remove_edge()` | Delete connection |
| `swap_edges()` | Exchange sources |

---

## 19. API Module (`/src/api`)

**External interfaces.**

### `metrics.py`
**Prometheus metrics export.**

```python
class MetricsCollector:
    """
    Exports:
    - fitness_* (best, mean, min, max)
    - coverage_* (captures per virtue)
    - edge_* (total, mean weight)
    - healing_* (interventions)
    - trajectory_* (captured, escaped)
    """
```

| Function | Purpose |
|----------|---------|
| `record_generation()` | Log generation stats |
| `export_prometheus()` | Format for scraping |
| `get_summary()` | Human-readable stats |

### `transport.py`
**Communication protocols.**

| Function | Purpose |
|----------|---------|
| `send_message()` | Dispatch to agent |
| `receive_message()` | Handle incoming |
| `broadcast()` | Send to all |

---

## 20. CLI Module (`/src/cli`)

**Command-line interface.**

### `commands.py`
**All CLI commands.**

| Command | Purpose |
|---------|---------|
| `init` | Initialize graph and virtues |
| `reset` | Clear all data |
| `kiln` | Run evolution loop |
| `spread` | Test activation spread |
| `test` | Test agent coherence |
| `inspect` | Agent introspection |
| `warnings` | Show agent warnings |
| `lessons` | Show knowledge pool |
| `pathways` | Show routes to virtues |
| `spawn` | Create new agent |
| `status` | Graph status |
| `health` | Health check |
| `virtues` | List all virtues |
| `agents` | List all agents |
| `tiers` | Explain threshold model |
| `gestalt` | Compute agent character |
| `situations` | List scenarios |
| `decide` | Generate decision |
| `compare` | Compare two agents |
| `diffuse` | Diffusion generation |

---

## System Invariants

### The Two-Tier Model

```
┌─────────────────────────────────────────────────────┐
│                    FOUNDATION                        │
│                                                      │
│    V01 Trustworthiness: 99% threshold (ABSOLUTE)    │
│                                                      │
│    No context modification. No mercy. No growth     │
│    exception. Trust is the foundation.              │
│                                                      │
└─────────────────────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────┐
│                   ASPIRATIONAL                       │
│                                                      │
│    V02-V19: 80% base threshold                      │
│                                                      │
│    Modified by:                                      │
│    - Agent archetype (±10%)                         │
│    - Generation (young: -10%, mature: +5%)          │
│    - Community emphasis                             │
│                                                      │
│    Growth is recognized. Improvement counts.         │
│                                                      │
└─────────────────────────────────────────────────────┘
```

### The Mercy System

```
┌─────────────────────────────────────────────────────┐
│                   FAILURE OCCURS                     │
└─────────────────────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────┐
│               CONTEXTUAL EVALUATION                  │
│                                                      │
│    - History with this virtue?                      │
│    - Foundation or aspirational?                    │
│    - Improving trajectory?                          │
│    - Overall coherence?                             │
│                                                      │
└─────────────────────────────────────────────────────┘
                         │
              ┌──────────┴──────────┐
              ▼                     ▼
     ┌─────────────┐       ┌─────────────┐
     │  TEACHABLE  │       │ DELIBERATE  │
     │ imperfection│       │    harm     │
     └─────────────┘       └─────────────┘
              │                     │
              ▼                     ▼
     ┌─────────────┐       ┌─────────────┐
     │   WARNING   │       │ DISSOLUTION │
     │  (3 max)    │       │ (immediate) │
     │  (24h decay)│       └─────────────┘
     └─────────────┘
              │
              ▼
     ┌─────────────┐
     │   LESSON    │
     │  (shared)   │
     └─────────────┘
```

### The Knowledge Flow

```
┌─────────────────────────────────────────────────────┐
│                  TRAJECTORY                          │
│            (agent experiences world)                 │
└─────────────────────────────────────────────────────┘
                         │
              ┌──────────┴──────────┐
              ▼                     ▼
     ┌─────────────┐       ┌─────────────┐
     │   SUCCESS   │       │   FAILURE   │
     │  (captured) │       │  (escaped)  │
     └─────────────┘       └─────────────┘
              │                     │
              ▼                     ▼
     ┌─────────────┐       ┌─────────────┐
     │   PATHWAY   │       │   LESSON    │
     │  (recorded) │       │  (recorded) │
     └─────────────┘       └─────────────┘
              │                     │
              └──────────┬──────────┘
                         ▼
┌─────────────────────────────────────────────────────┐
│                 KNOWLEDGE POOL                       │
│           (shared across all agents)                 │
└─────────────────────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────┐
│               FUTURE AGENTS                          │
│          (inherit collective wisdom)                 │
└─────────────────────────────────────────────────────┘
```

---

## File Count Summary

| Module | Files | Lines (approx) |
|--------|-------|----------------|
| Core (`/src`) | 3 | 800 |
| Graph | 3 | 400 |
| Virtues | 2 | 500 |
| Functions | 7 | 1200 |
| Dynamics | 3 | 600 |
| Mercy | 4 | 800 |
| Knowledge | 2 | 400 |
| Kiln | 2 | 500 |
| Testing | 4 | 600 |
| Theatre | 5 | 800 |
| Vessels | 6 | 1000 |
| Community | 4 | 500 |
| Gestalt | 3 | 600 |
| Actions | 4 | 800 |
| Situations | 3 | 400 |
| Proxy | 3 | 500 |
| Agents | 2 | 300 |
| Evolution | 3 | 400 |
| API | 2 | 300 |
| CLI | 1 | 1000 |
| **Total** | **~66** | **~12,000** |

---

## Design Philosophy

1. **Virtues as Attractors**: Not imposed rules, but basins that pull cognition toward them through topology.

2. **Trust is Absolute**: V01 has no exceptions. Everything else can grow.

3. **Mercy Over Judgment**: Failures teach. Warnings decay. Growth redeems.

4. **Collective Learning**: No agent learns alone. Wisdom is shared.

5. **Mathematical Impossibility**: 9-regular graph on 19 nodes = 85.5 edges. Perfect balance is impossible. Perpetual striving is the point.

6. **Character Emerges**: Gestalt is computed from topology, not assigned. Agents become who they are through their connections.

7. **Actions Reflect Character**: Decisions are probabilistic distributions over defensible options, weighted by virtue activations.

---

*"The kiln fires souls not to burn away impurity, but to harden them toward coherence."*
