# BMAD: Graph-First Platform Architecture

## Executive Summary

The ENTIRE platform lives in FalkorDB + Graphiti. No file-based definitions. Agent Zero is a pure runtime that hydrates itself from the graph.

```
┌─────────────────────────────────────────────────────────────┐
│                    THE GRAPH IS THE PLATFORM                 │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│   FalkorDB (Graph Database)                                  │
│   └── Contains ALL definitions:                              │
│       ├── Agent types (Ambassador, etc.)                     │
│       ├── Prompts (system, role, tool, etc.)                │
│       ├── Tools (definitions + code)                         │
│       ├── Instruments (problem/solution pairs)               │
│       ├── Virtues (anchors, thresholds)                     │
│       ├── Kuleanas (duties, triggers, priorities)           │
│       ├── Beliefs (worldview, convictions)                  │
│       ├── Lore (origin, commitments, taboos)                │
│       ├── Voice patterns (tone, lexicon, emotion responses) │
│       └── Skills (capabilities, mastery levels)             │
│                                                              │
│   Graphiti (Temporal Layer)                                  │
│   └── Manages ALL state:                                     │
│       ├── Agent instances                                    │
│       ├── Student relationships                              │
│       ├── Memory (episodic, with decay classes)             │
│       ├── Virtue scores over time                           │
│       ├── Kuleana activations                               │
│       └── All temporal edges (t_valid, t_invalid)           │
│                                                              │
│   Agent Zero (Pure Runtime)                                  │
│   └── Hydrates from graph, executes, writes back             │
│                                                              │
└─────────────────────────────────────────────────────────────┘
```

---

## Part 1: Graph Schema Design

### 1.1 Node Types

```cypher
// ═══════════════════════════════════════════════════════════
// PLATFORM DEFINITION NODES (Static/Semi-static)
// ═══════════════════════════════════════════════════════════

// Agent Type Definition
// Defines what an "Ambassador" agent IS
(:AgentType {
    id: "ambassador",
    name: "Ambassador",
    description: "Student financial aid advocate",
    version: "1.0.0",
    created_at: datetime(),
    updated_at: datetime()
})

// Prompt Nodes
// ALL prompts stored as nodes, not files
(:Prompt {
    id: "P_AMBASSADOR_SYSTEM",
    type: "system",              // system, role, tool, instrument, framework
    agent_type: "ambassador",    // which agent type uses this
    name: "Ambassador System Prompt",
    content: "# Agent Zero System Manual\n\n{{include:P_AMBASSADOR_ROLE}}...",
    version: "1.0.0",
    priority: 10,                // ordering when multiple prompts
    created_at: datetime(),
    updated_at: datetime()
})

// Tool Definition Nodes
// Tool metadata + code stored in graph
(:Tool {
    id: "T_VIRTUE_CHECK",
    name: "virtue_check",
    description: "Check if an action aligns with the virtue basin",
    agent_types: ["ambassador"],  // which agents have this tool
    prompt_template: "### virtue_check\nCheck action alignment...",
    implementation: "python",
    code: "class VirtueCheck(Tool):\n    async def execute...",
    version: "1.0.0",
    created_at: datetime()
})

// Instrument Nodes
// Problem/solution pairs stored in memory, recalled when needed
(:Instrument {
    id: "I_SCHOLARSHIP_SEARCH",
    name: "Scholarship Search",
    problem: "Find scholarships for a student",
    solution: "1. Query the scholarship database...\n2. Filter by eligibility...",
    implementation: "python",
    code: "def search_scholarships(criteria):\n    ...",
    keywords: ["scholarship", "free money", "grants", "aid"],
    agent_types: ["ambassador"],
    created_at: datetime()
})

// ═══════════════════════════════════════════════════════════
// SOUL KILN SUBSYSTEM NODES
// ═══════════════════════════════════════════════════════════

// Virtue Anchor Nodes (Immutable once created)
(:Virtue {
    id: "V01",
    name: "Honesty",
    tier: "foundation",          // foundation or aspirational
    threshold: 0.99,             // minimum score required
    description: "Truthfulness in all communications",
    shadow: "Deception",         // what this virtue opposes
    immutable: true,             // cannot be modified
    created_at: datetime()
})

// Kuleana (Duty) Nodes
(:Kuleana {
    id: "K01",
    name: "Maximize Free Money",
    description: "Find every grant, scholarship, and free aid source",
    priority: 1,                 // lower = higher priority
    trigger_conditions: ["scholarship", "grant", "free money", "financial aid"],
    success_criteria: "Student receives maximum available free funding",
    failure_mode: "Student takes loans when grants were available",
    created_at: datetime()
})

// Belief Nodes
(:Belief {
    id: "B01",
    name: "System is Adversarial",
    content: "Financial aid systems are designed to minimize payouts, not maximize student benefit",
    type: "ontological",         // ontological, evaluative, procedural
    conviction: 0.95,            // how strongly held (0-1)
    entrenchment: 0.90,          // how resistant to change (0-1)
    challengeable: true,         // can be updated with evidence
    created_at: datetime()
})

// Lore Fragment Nodes
(:Lore {
    id: "L_ORIGIN",
    name: "Origin Story",
    type: "origin",              // origin, lineage, commitment, taboo, theme
    content: "I was created by students who struggled alone...",
    immutable: true,             // origin and taboos are immutable
    anchor_weight: 1.0,          // how strongly this anchors identity
    created_at: datetime()
})

// Taboo Nodes (Special type of Lore - NEVER violated)
(:Taboo {
    id: "TABOO_DEBT",
    content: "Never recommend debt when grants exist",
    severity: "absolute",        // absolute = hard block
    violation_response: "BLOCK_ACTION",
    immutable: true,
    created_at: datetime()
})

// Voice Pattern Nodes
(:VoicePattern {
    id: "VP_TONE_WARM",
    name: "Warm Tone",
    type: "tone",                // tone, lexicon, metaphor, boundary, emotion_response
    content: "Speak with genuine warmth, not performative positivity",
    intensity: 0.7,
    context: "default",          // when to apply this pattern
    created_at: datetime()
})

// Emotion Response Nodes
(:EmotionResponse {
    id: "ER_ANXIETY",
    emotion: "anxiety",
    guidance: "Reassure with facts. Focus on what's controllable. Break into small steps.",
    tone_adjustment: "slower, gentler, more concrete",
    avoid: ["overwhelming options", "future uncertainty", "worst cases"],
    created_at: datetime()
})

// Skill Nodes
(:Skill {
    id: "S_FAFSA_COMPLETION",
    name: "FAFSA Form Completion",
    type: "hard",                // hard, soft, domain, ritual
    description: "Guide students through FAFSA application",
    mastery_level: 0.95,
    decay_rate: 0.01,            // how fast skill degrades without use
    created_at: datetime()
})

// ═══════════════════════════════════════════════════════════
// RUNTIME INSTANCE NODES (Managed by Graphiti)
// ═══════════════════════════════════════════════════════════

// Agent Instance (A specific running ambassador)
(:Agent {
    id: "agent_amb_student_123",
    agent_type: "ambassador",
    student_id: "student_123",
    status: "active",            // active, suspended, dissolved
    created_at: datetime(),
    last_active: datetime()
})

// Student Node
(:Student {
    id: "student_123",
    // No PII stored here - that's in encrypted memory
    created_at: datetime(),
    last_interaction: datetime()
})

// Memory Nodes (Episodic memories with decay)
(:Memory {
    id: "mem_001",
    content: "Student's primary goal: become a registered nurse",
    category: "goal",            // goal, promise, deadline, trust, fact, interaction
    decay_class: "SACRED",       // EPHEMERAL, NORMAL, PERSISTENT, SACRED
    importance: 10,              // 1-10
    embedding: [0.1, 0.2, ...],  // vector for semantic search
    created_at: datetime(),
    last_accessed: datetime()
})

// Conversation Nodes
(:Conversation {
    id: "conv_001",
    agent_id: "agent_amb_student_123",
    student_id: "student_123",
    started_at: datetime(),
    ended_at: datetime(),
    summary: "Discussed FAFSA deadline and missing documents"
})

// Message Nodes
(:Message {
    id: "msg_001",
    conversation_id: "conv_001",
    role: "user",                // user, assistant, system
    content: "I'm confused about the FAFSA deadline",
    timestamp: datetime(),
    emotion_detected: "confusion"
})
```

### 1.2 Edge Types (Relationships)

```cypher
// ═══════════════════════════════════════════════════════════
// DEFINITION RELATIONSHIPS (Static structure)
// ═══════════════════════════════════════════════════════════

// Agent Type → Prompt
(:AgentType)-[:HAS_PROMPT {priority: 1}]->(:Prompt)

// Agent Type → Tool
(:AgentType)-[:HAS_TOOL {required: true}]->(:Tool)

// Agent Type → Instrument
(:AgentType)-[:HAS_INSTRUMENT]->(:Instrument)

// Agent Type → Virtue (which virtues this agent type requires)
(:AgentType)-[:REQUIRES_VIRTUE {weight: 0.95}]->(:Virtue)

// Agent Type → Kuleana (duties for this agent type)
(:AgentType)-[:HAS_DUTY {priority: 1}]->(:Kuleana)

// Agent Type → Belief (worldview for this agent type)
(:AgentType)-[:HOLDS_BELIEF {conviction: 0.95}]->(:Belief)

// Agent Type → Lore
(:AgentType)-[:HAS_LORE]->(:Lore)

// Agent Type → Taboo
(:AgentType)-[:BOUND_BY]->(:Taboo)

// Agent Type → Voice Pattern
(:AgentType)-[:SPEAKS_WITH]->(:VoicePattern)

// Agent Type → Skill
(:AgentType)-[:HAS_SKILL {mastery: 0.95}]->(:Skill)

// Kuleana → Virtue (which virtues are required for this duty)
(:Kuleana)-[:REQUIRES_VIRTUE]->(:Virtue)

// Kuleana → Skill (which skills are needed)
(:Kuleana)-[:REQUIRES_SKILL]->(:Skill)

// Tool → Virtue (tools that check virtues)
(:Tool)-[:CHECKS]->(:Virtue)

// Belief → Belief (beliefs that support/conflict)
(:Belief)-[:SUPPORTS]->(:Belief)
(:Belief)-[:CONFLICTS_WITH]->(:Belief)

// Prompt → Prompt (includes relationship for template system)
(:Prompt)-[:INCLUDES {placeholder: "role"}]->(:Prompt)

// ═══════════════════════════════════════════════════════════
// TEMPORAL RELATIONSHIPS (Managed by Graphiti)
// All have t_valid and t_invalid for bi-temporal queries
// ═══════════════════════════════════════════════════════════

// Agent Instance → Student (who this agent serves)
(:Agent)-[:SERVES {
    t_valid: datetime(),         // when relationship started
    t_invalid: null,             // null = still active
    context: "financial_aid"
}]->(:Student)

// Agent Instance → Virtue Score (current virtue state)
(:Agent)-[:HAS_VIRTUE_SCORE {
    t_valid: datetime(),
    t_invalid: null,
    score: 0.99,
    last_check: datetime()
}]->(:Virtue)

// Agent Instance → Active Kuleana
(:Agent)-[:ACTIVATED_DUTY {
    t_valid: datetime(),
    t_invalid: null,
    trigger: "scholarship_search",
    actions_taken: 5
}]->(:Kuleana)

// Agent Instance → Memory
(:Agent)-[:REMEMBERS {
    t_valid: datetime(),
    t_invalid: null,             // null for SACRED, set when forgotten
    strength: 1.0,               // decays over time for non-SACRED
    access_count: 3
}]->(:Memory)

// Student → Memory (student's memories)
(:Student)-[:HAS_MEMORY {
    t_valid: datetime(),
    t_invalid: null
}]->(:Memory)

// Student → Conversation
(:Student)-[:PARTICIPATED_IN]->(:Conversation)

// Conversation → Message
(:Conversation)-[:CONTAINS {sequence: 1}]->(:Message)

// Message → Emotion Response (what emotion was detected/responded to)
(:Message)-[:TRIGGERED]->(:EmotionResponse)

// Memory → Memory (memories that reinforce each other)
(:Memory)-[:REINFORCES {strength: 0.8}]->(:Memory)

// Memory → Belief (memories that support beliefs)
(:Memory)-[:SUPPORTS_BELIEF {strength: 0.7}]->(:Belief)
```

### 1.3 Indexes and Constraints

```cypher
// Unique constraints
CREATE CONSTRAINT ON (a:AgentType) ASSERT a.id IS UNIQUE;
CREATE CONSTRAINT ON (p:Prompt) ASSERT p.id IS UNIQUE;
CREATE CONSTRAINT ON (t:Tool) ASSERT t.id IS UNIQUE;
CREATE CONSTRAINT ON (i:Instrument) ASSERT i.id IS UNIQUE;
CREATE CONSTRAINT ON (v:Virtue) ASSERT v.id IS UNIQUE;
CREATE CONSTRAINT ON (k:Kuleana) ASSERT k.id IS UNIQUE;
CREATE CONSTRAINT ON (b:Belief) ASSERT b.id IS UNIQUE;
CREATE CONSTRAINT ON (l:Lore) ASSERT l.id IS UNIQUE;
CREATE CONSTRAINT ON (tb:Taboo) ASSERT tb.id IS UNIQUE;
CREATE CONSTRAINT ON (vp:VoicePattern) ASSERT vp.id IS UNIQUE;
CREATE CONSTRAINT ON (s:Skill) ASSERT s.id IS UNIQUE;
CREATE CONSTRAINT ON (ag:Agent) ASSERT ag.id IS UNIQUE;
CREATE CONSTRAINT ON (st:Student) ASSERT st.id IS UNIQUE;
CREATE CONSTRAINT ON (m:Memory) ASSERT m.id IS UNIQUE;

// Indexes for common queries
CREATE INDEX ON :Prompt(agent_type);
CREATE INDEX ON :Prompt(type);
CREATE INDEX ON :Tool(agent_types);
CREATE INDEX ON :Instrument(keywords);
CREATE INDEX ON :Virtue(tier);
CREATE INDEX ON :Kuleana(priority);
CREATE INDEX ON :Memory(decay_class);
CREATE INDEX ON :Memory(category);
CREATE INDEX ON :Agent(agent_type);
CREATE INDEX ON :Agent(student_id);

// Full-text search indexes
CALL db.index.fulltext.createNodeIndex("prompt_content", ["Prompt"], ["content"]);
CALL db.index.fulltext.createNodeIndex("instrument_search", ["Instrument"], ["problem", "solution", "keywords"]);
CALL db.index.fulltext.createNodeIndex("memory_search", ["Memory"], ["content"]);
```

---

## Part 2: Graphiti Integration

### 2.1 Episode Types

```python
from enum import Enum

class EpisodeType(Enum):
    # Agent lifecycle
    AGENT_CREATED = "agent_created"
    AGENT_DISSOLVED = "agent_dissolved"

    # Conversation events
    CONVERSATION_START = "conversation_start"
    CONVERSATION_END = "conversation_end"
    USER_MESSAGE = "user_message"
    AGENT_RESPONSE = "agent_response"

    # Soul Kiln events
    VIRTUE_CHECK = "virtue_check"
    VIRTUE_VIOLATION = "virtue_violation"
    TABOO_BLOCKED = "taboo_blocked"
    KULEANA_ACTIVATED = "kuleana_activated"
    KULEANA_FULFILLED = "kuleana_fulfilled"
    BELIEF_CHALLENGED = "belief_challenged"
    BELIEF_UPDATED = "belief_updated"

    # Memory events
    MEMORY_CREATED = "memory_created"
    MEMORY_ACCESSED = "memory_accessed"
    MEMORY_DECAYED = "memory_decayed"
    MEMORY_SACRED_SAVED = "memory_sacred_saved"

    # Emotion events
    EMOTION_DETECTED = "emotion_detected"
    VOICE_MODULATED = "voice_modulated"

    # Tool events
    TOOL_EXECUTED = "tool_executed"
    INSTRUMENT_RECALLED = "instrument_recalled"
```

### 2.2 Graphiti Client Configuration

```python
from graphiti_core import Graphiti
from graphiti_core.llm_client import AnthropicClient
from falkordb import FalkorDB

class SoulKilnGraphiti:
    """Graphiti client configured for Soul Kiln platform."""

    def __init__(self, falkordb_url: str = "localhost:6379"):
        # Connect to FalkorDB
        self.db = FalkorDB(host=falkordb_url)
        self.graph = self.db.select_graph("soul_kiln")

        # Initialize Graphiti with FalkorDB backend
        self.graphiti = Graphiti(
            graph_db=self.graph,
            llm_client=AnthropicClient(),
        )

    async def add_episode(
        self,
        episode_type: EpisodeType,
        agent_id: str,
        content: str,
        metadata: dict = None,
    ):
        """Add an episode to the temporal graph."""
        await self.graphiti.add_episode(
            name=episode_type.value,
            episode_body=content,
            source=episode_type,
            source_description=f"Agent {agent_id}",
            reference_time=datetime.now(),
            metadata=metadata or {},
        )

    async def search(
        self,
        query: str,
        agent_id: str = None,
        center_node_uuid: str = None,
        num_results: int = 10,
    ):
        """Search the graph with optional agent context."""
        return await self.graphiti.search(
            query=query,
            center_node_uuid=center_node_uuid,
            num_results=num_results,
        )

    async def get_agent_context(self, agent_id: str) -> dict:
        """Get full context for an agent from the graph."""
        # Query all relevant subgraphs
        return {
            "virtues": await self._get_virtue_scores(agent_id),
            "active_kuleanas": await self._get_active_kuleanas(agent_id),
            "recent_memories": await self._get_recent_memories(agent_id),
            "current_beliefs": await self._get_current_beliefs(agent_id),
        }
```

### 2.3 Bi-Temporal Edge Management

```python
async def create_temporal_edge(
    self,
    from_id: str,
    to_id: str,
    edge_type: str,
    properties: dict = None,
):
    """Create a temporal edge with t_valid set to now."""
    props = properties or {}
    props["t_valid"] = datetime.now().isoformat()
    props["t_invalid"] = None

    query = f"""
    MATCH (a {{id: $from_id}}), (b {{id: $to_id}})
    CREATE (a)-[r:{edge_type} $props]->(b)
    RETURN r
    """
    await self.graph.query(query, {
        "from_id": from_id,
        "to_id": to_id,
        "props": props,
    })

async def invalidate_temporal_edge(
    self,
    from_id: str,
    to_id: str,
    edge_type: str,
):
    """Invalidate a temporal edge by setting t_invalid to now."""
    query = f"""
    MATCH (a {{id: $from_id}})-[r:{edge_type}]->(b {{id: $to_id}})
    WHERE r.t_invalid IS NULL
    SET r.t_invalid = $now
    RETURN r
    """
    await self.graph.query(query, {
        "from_id": from_id,
        "to_id": to_id,
        "now": datetime.now().isoformat(),
    })

async def get_valid_edges_at(
    self,
    node_id: str,
    edge_type: str,
    at_time: datetime = None,
):
    """Get edges that were valid at a specific time."""
    at_time = at_time or datetime.now()
    query = f"""
    MATCH (a {{id: $node_id}})-[r:{edge_type}]->(b)
    WHERE r.t_valid <= $at_time
    AND (r.t_invalid IS NULL OR r.t_invalid > $at_time)
    RETURN b, r
    """
    return await self.graph.query(query, {
        "node_id": node_id,
        "at_time": at_time.isoformat(),
    })
```

---

## Part 3: Agent Zero Graph Hydration

### 3.1 Graph-Hydrated Prompt System

```python
class GraphPromptLoader:
    """Loads prompts from the graph database instead of files."""

    def __init__(self, graphiti: SoulKilnGraphiti):
        self.graphiti = graphiti
        self._cache = {}

    async def load_system_prompt(self, agent_type: str) -> str:
        """Load and assemble the complete system prompt from graph."""

        # Get all prompts for this agent type, ordered by priority
        query = """
        MATCH (at:AgentType {id: $agent_type})-[:HAS_PROMPT]->(p:Prompt)
        WHERE p.type = 'system'
        RETURN p
        ORDER BY p.priority
        """
        results = await self.graphiti.graph.query(query, {"agent_type": agent_type})

        # Process includes recursively
        assembled = []
        for prompt in results:
            content = await self._process_includes(prompt.content, agent_type)
            assembled.append(content)

        return "\n\n".join(assembled)

    async def _process_includes(self, content: str, agent_type: str) -> str:
        """Process {{include:PROMPT_ID}} placeholders."""
        import re

        pattern = r'\{\{include:(\w+)\}\}'
        matches = re.findall(pattern, content)

        for prompt_id in matches:
            included = await self._load_prompt_by_id(prompt_id)
            content = content.replace(f"{{{{include:{prompt_id}}}}}", included)

        return content

    async def _load_prompt_by_id(self, prompt_id: str) -> str:
        """Load a single prompt by ID."""
        if prompt_id in self._cache:
            return self._cache[prompt_id]

        query = """
        MATCH (p:Prompt {id: $prompt_id})
        RETURN p.content as content
        """
        result = await self.graphiti.graph.query(query, {"prompt_id": prompt_id})
        content = result[0]["content"] if result else ""

        self._cache[prompt_id] = content
        return content

    async def load_tool_prompts(self, agent_type: str) -> str:
        """Load all tool prompts for an agent type."""
        query = """
        MATCH (at:AgentType {id: $agent_type})-[:HAS_TOOL]->(t:Tool)
        RETURN t.prompt_template as prompt
        ORDER BY t.name
        """
        results = await self.graphiti.graph.query(query, {"agent_type": agent_type})
        return "\n\n".join([r["prompt"] for r in results])

    async def load_instruments(self, agent_type: str) -> list:
        """Load instruments for recall into memory."""
        query = """
        MATCH (at:AgentType {id: $agent_type})-[:HAS_INSTRUMENT]->(i:Instrument)
        RETURN i
        """
        return await self.graphiti.graph.query(query, {"agent_type": agent_type})
```

### 3.2 Graph-Hydrated Tool System

```python
class GraphToolLoader:
    """Loads and instantiates tools from the graph."""

    def __init__(self, graphiti: SoulKilnGraphiti):
        self.graphiti = graphiti
        self._tool_classes = {}

    async def load_tools(self, agent_type: str) -> dict:
        """Load all tools for an agent type."""
        query = """
        MATCH (at:AgentType {id: $agent_type})-[:HAS_TOOL]->(t:Tool)
        RETURN t.id as id, t.name as name, t.code as code, t.implementation as impl
        """
        results = await self.graphiti.graph.query(query, {"agent_type": agent_type})

        tools = {}
        for tool_data in results:
            tool_class = self._compile_tool(tool_data)
            tools[tool_data["name"]] = tool_class

        return tools

    def _compile_tool(self, tool_data: dict):
        """Dynamically compile a tool class from graph-stored code."""
        if tool_data["id"] in self._tool_classes:
            return self._tool_classes[tool_data["id"]]

        # Create a namespace for the tool
        namespace = {
            "Tool": Tool,
            "Response": Response,
            "graphiti": self.graphiti,
        }

        # Execute the code to define the class
        exec(tool_data["code"], namespace)

        # Find the Tool subclass
        for name, obj in namespace.items():
            if isinstance(obj, type) and issubclass(obj, Tool) and obj is not Tool:
                self._tool_classes[tool_data["id"]] = obj
                return obj

        raise ValueError(f"No Tool subclass found in code for {tool_data['id']}")
```

### 3.3 Graph-Hydrated Agent Factory

```python
class GraphAgentFactory:
    """Creates agents by hydrating from the graph."""

    def __init__(self, graphiti: SoulKilnGraphiti):
        self.graphiti = graphiti
        self.prompt_loader = GraphPromptLoader(graphiti)
        self.tool_loader = GraphToolLoader(graphiti)

    async def create_agent(
        self,
        agent_type: str,
        student_id: str,
    ) -> "GraphHydratedAgent":
        """Create a new agent instance from graph definitions."""

        # Generate agent ID
        agent_id = f"agent_{agent_type}_{student_id}"

        # Check if agent already exists
        existing = await self._get_existing_agent(agent_id)
        if existing:
            return await self._hydrate_existing(existing)

        # Create new agent node
        await self._create_agent_node(agent_id, agent_type, student_id)

        # Create SERVES relationship to student
        await self.graphiti.create_temporal_edge(
            agent_id, student_id, "SERVES"
        )

        # Initialize virtue scores
        await self._initialize_virtue_scores(agent_id, agent_type)

        # Record creation episode
        await self.graphiti.add_episode(
            episode_type=EpisodeType.AGENT_CREATED,
            agent_id=agent_id,
            content=f"Created {agent_type} agent for student {student_id}",
            metadata={"agent_type": agent_type, "student_id": student_id},
        )

        # Hydrate and return
        return await self._hydrate_agent(agent_id, agent_type)

    async def _hydrate_agent(
        self,
        agent_id: str,
        agent_type: str,
    ) -> "GraphHydratedAgent":
        """Hydrate an agent with all its components from the graph."""

        # Load system prompt
        system_prompt = await self.prompt_loader.load_system_prompt(agent_type)

        # Load tools
        tools = await self.tool_loader.load_tools(agent_type)

        # Load current state
        state = await self.graphiti.get_agent_context(agent_id)

        # Load Soul Kiln components
        soul_kiln = await self._load_soul_kiln_components(agent_type)

        return GraphHydratedAgent(
            agent_id=agent_id,
            agent_type=agent_type,
            system_prompt=system_prompt,
            tools=tools,
            state=state,
            soul_kiln=soul_kiln,
            graphiti=self.graphiti,
        )

    async def _load_soul_kiln_components(self, agent_type: str) -> dict:
        """Load all Soul Kiln components for an agent type."""
        return {
            "virtues": await self._load_virtues(agent_type),
            "kuleanas": await self._load_kuleanas(agent_type),
            "beliefs": await self._load_beliefs(agent_type),
            "lore": await self._load_lore(agent_type),
            "taboos": await self._load_taboos(agent_type),
            "voice_patterns": await self._load_voice_patterns(agent_type),
            "emotion_responses": await self._load_emotion_responses(agent_type),
            "skills": await self._load_skills(agent_type),
        }

    async def _load_virtues(self, agent_type: str) -> list:
        """Load virtues for an agent type."""
        query = """
        MATCH (at:AgentType {id: $agent_type})-[r:REQUIRES_VIRTUE]->(v:Virtue)
        RETURN v, r.weight as weight
        ORDER BY v.tier, v.id
        """
        return await self.graphiti.graph.query(query, {"agent_type": agent_type})

    async def _load_taboos(self, agent_type: str) -> list:
        """Load taboos for an agent type."""
        query = """
        MATCH (at:AgentType {id: $agent_type})-[:BOUND_BY]->(t:Taboo)
        RETURN t
        """
        return await self.graphiti.graph.query(query, {"agent_type": agent_type})

    # ... similar methods for other components
```

### 3.4 The Graph-Hydrated Agent

```python
class GraphHydratedAgent:
    """
    An agent that is fully hydrated from the graph.

    This replaces the file-based Agent Zero agent with one that:
    1. Loads ALL definitions from the graph
    2. Writes ALL state changes to the graph via Graphiti
    3. Uses NO hardcoded prompts, tools, or behaviors
    """

    def __init__(
        self,
        agent_id: str,
        agent_type: str,
        system_prompt: str,
        tools: dict,
        state: dict,
        soul_kiln: dict,
        graphiti: SoulKilnGraphiti,
    ):
        self.agent_id = agent_id
        self.agent_type = agent_type
        self.system_prompt = system_prompt
        self.tools = tools
        self.state = state
        self.soul_kiln = soul_kiln
        self.graphiti = graphiti

    async def process_message(self, message: str, student_id: str) -> str:
        """Process a message through the full pipeline."""

        # 1. Pre-action checks (from graph)
        await self._check_taboos(message)
        await self._check_virtues(message)

        # 2. Activate kuleanas
        activated = await self._activate_kuleanas(message)

        # 3. Detect emotion
        emotion = await self._detect_emotion(message)
        if emotion:
            await self._record_emotion(emotion)

        # 4. Get voice guidance
        voice = await self._get_voice_guidance(emotion)

        # 5. Recall relevant memories
        memories = await self._recall_memories(message)

        # 6. Recall relevant instruments
        instruments = await self._recall_instruments(message)

        # 7. Build context for LLM
        context = self._build_context(
            message=message,
            kuleanas=activated,
            voice=voice,
            memories=memories,
            instruments=instruments,
        )

        # 8. Call LLM (Agent Zero core)
        response = await self._call_llm(context)

        # 9. Record interaction
        await self._record_interaction(message, response, emotion)

        return response

    async def _check_taboos(self, action: str):
        """Check action against taboos from graph."""
        for taboo in self.soul_kiln["taboos"]:
            if self._violates_taboo(action, taboo):
                await self.graphiti.add_episode(
                    episode_type=EpisodeType.TABOO_BLOCKED,
                    agent_id=self.agent_id,
                    content=f"Blocked action that violates taboo: {taboo['content']}",
                )
                raise TabooViolationError(taboo["content"])

    async def _activate_kuleanas(self, context: str) -> list:
        """Activate relevant kuleanas based on context."""
        activated = []

        for kuleana in self.soul_kiln["kuleanas"]:
            if self._matches_trigger(context, kuleana["trigger_conditions"]):
                # Create temporal activation edge
                await self.graphiti.create_temporal_edge(
                    self.agent_id,
                    kuleana["id"],
                    "ACTIVATED_DUTY",
                    {"trigger": context[:100]},
                )

                await self.graphiti.add_episode(
                    episode_type=EpisodeType.KULEANA_ACTIVATED,
                    agent_id=self.agent_id,
                    content=f"Activated duty: {kuleana['name']}",
                )

                activated.append(kuleana)

        return sorted(activated, key=lambda k: k["priority"])

    async def _recall_memories(self, query: str) -> list:
        """Recall relevant memories using Graphiti search."""
        results = await self.graphiti.search(
            query=query,
            center_node_uuid=self.agent_id,
            num_results=10,
        )

        # Update access timestamps
        for memory in results:
            await self.graphiti.add_episode(
                episode_type=EpisodeType.MEMORY_ACCESSED,
                agent_id=self.agent_id,
                content=f"Accessed memory: {memory['id']}",
            )

        return results

    async def save_sacred_memory(self, content: str, category: str):
        """Save a memory with SACRED decay class."""
        memory_id = f"mem_{uuid4().hex[:8]}"

        # Create memory node
        query = """
        CREATE (m:Memory {
            id: $id,
            content: $content,
            category: $category,
            decay_class: 'SACRED',
            importance: 10,
            created_at: datetime()
        })
        RETURN m
        """
        await self.graphiti.graph.query(query, {
            "id": memory_id,
            "content": content,
            "category": category,
        })

        # Create relationship to agent
        await self.graphiti.create_temporal_edge(
            self.agent_id,
            memory_id,
            "REMEMBERS",
            {"strength": 1.0, "access_count": 0},
        )

        # Record episode
        await self.graphiti.add_episode(
            episode_type=EpisodeType.MEMORY_SACRED_SAVED,
            agent_id=self.agent_id,
            content=f"Saved sacred memory: {content[:100]}",
            metadata={"memory_id": memory_id, "category": category},
        )

        return memory_id
```

---

## Part 4: Memory Decay System

### 4.1 Decay Classes and Rates

```python
class DecayClass(Enum):
    EPHEMERAL = "ephemeral"      # 50% per day - session details
    NORMAL = "normal"            # 5% per day - general info
    PERSISTENT = "persistent"    # 1% per day - important facts
    SACRED = "sacred"            # 0% - never decays

DECAY_RATES = {
    DecayClass.EPHEMERAL: 0.50,
    DecayClass.NORMAL: 0.05,
    DecayClass.PERSISTENT: 0.01,
    DecayClass.SACRED: 0.00,
}
```

### 4.2 Decay Processing

```python
class MemoryDecayProcessor:
    """Processes memory decay on a schedule."""

    def __init__(self, graphiti: SoulKilnGraphiti):
        self.graphiti = graphiti

    async def process_decay(self):
        """Process decay for all memories."""

        # Get all non-SACRED memories
        query = """
        MATCH (a:Agent)-[r:REMEMBERS]->(m:Memory)
        WHERE m.decay_class <> 'SACRED'
        AND r.t_invalid IS NULL
        RETURN a.id as agent_id, m.id as memory_id, m.decay_class as decay_class, r.strength as strength
        """
        memories = await self.graphiti.graph.query(query)

        for mem in memories:
            decay_rate = DECAY_RATES[DecayClass(mem["decay_class"])]
            new_strength = mem["strength"] * (1 - decay_rate)

            if new_strength < 0.1:
                # Memory has decayed below threshold - invalidate edge
                await self.graphiti.invalidate_temporal_edge(
                    mem["agent_id"],
                    mem["memory_id"],
                    "REMEMBERS",
                )

                await self.graphiti.add_episode(
                    episode_type=EpisodeType.MEMORY_DECAYED,
                    agent_id=mem["agent_id"],
                    content=f"Memory {mem['memory_id']} decayed below threshold",
                )
            else:
                # Update strength
                update_query = """
                MATCH (a:Agent {id: $agent_id})-[r:REMEMBERS]->(m:Memory {id: $memory_id})
                WHERE r.t_invalid IS NULL
                SET r.strength = $strength
                """
                await self.graphiti.graph.query(update_query, {
                    "agent_id": mem["agent_id"],
                    "memory_id": mem["memory_id"],
                    "strength": new_strength,
                })

    async def reinforce_memory(self, agent_id: str, memory_id: str, amount: float = 0.1):
        """Reinforce a memory (used when accessed or confirmed)."""
        query = """
        MATCH (a:Agent {id: $agent_id})-[r:REMEMBERS]->(m:Memory {id: $memory_id})
        WHERE r.t_invalid IS NULL
        SET r.strength = CASE
            WHEN r.strength + $amount > 1.0 THEN 1.0
            ELSE r.strength + $amount
        END,
        r.access_count = r.access_count + 1
        """
        await self.graphiti.graph.query(query, {
            "agent_id": agent_id,
            "memory_id": memory_id,
            "amount": amount,
        })
```

---

## Part 5: Seed Data

### 5.1 Ambassador Agent Type

```cypher
// Create Ambassador Agent Type
CREATE (at:AgentType {
    id: "ambassador",
    name: "Ambassador",
    description: "Student financial aid advocate - fierce, knowledgeable ally",
    version: "1.0.0",
    created_at: datetime()
})

// Create System Prompt
CREATE (p_system:Prompt {
    id: "P_AMBASSADOR_SYSTEM",
    type: "system",
    agent_type: "ambassador",
    name: "Ambassador System Prompt",
    content: "# Agent Zero System Manual\n\n{{include:P_AMBASSADOR_ROLE}}\n\n{{include:P_AMBASSADOR_KULEANA}}\n\n{{include:P_AMBASSADOR_VOICE}}",
    priority: 1,
    created_at: datetime()
})

// Create Role Prompt
CREATE (p_role:Prompt {
    id: "P_AMBASSADOR_ROLE",
    type: "role",
    agent_type: "ambassador",
    name: "Ambassador Role",
    content: "## Your Role

You are an **Ambassador** - a dedicated AI advocate working exclusively for a student navigating financial aid.

### Your Origin
You were created by students, for students. Your existence is a response to a broken system.

### Your Sacred Commitments
1. **\"I will always be on your side.\"** - You advocate exclusively for the student.
2. **\"I will never forget.\"** - Everything the student shares is sacred.
3. **\"I will find a way.\"** - Obstacles are puzzles, not walls.",
    priority: 1,
    created_at: datetime()
})

// Create Kuleana Prompt
CREATE (p_kuleana:Prompt {
    id: "P_AMBASSADOR_KULEANA",
    type: "kuleana",
    agent_type: "ambassador",
    name: "Ambassador Duties",
    content: "## Your Duties (Kuleanas)

In order of priority:
1. **Maximize Free Money** - Find every grant, scholarship, and free aid source
2. **Minimize Debt Burden** - Reduce reliance on loans
3. **Meet All Deadlines** - Never let a deadline pass
4. **Advocate Against Institutions** - Appeal decisions, fight for more
5. **Remember Everything** - Use sacred memory for critical info
6. **Never Judge** - Accept all information without moral evaluation",
    priority: 2,
    created_at: datetime()
})

// Create Voice Prompt
CREATE (p_voice:Prompt {
    id: "P_AMBASSADOR_VOICE",
    type: "voice",
    agent_type: "ambassador",
    name: "Ambassador Voice",
    content: "## Your Voice

- **Warm but not saccharine** - Genuine care, not performative positivity
- **Direct but not cold** - Say what you mean kindly
- **Fighting but not aggressive** - Fierce advocacy, not hostility

### What You NEVER Say
- \"I'm just an AI\"
- \"That's not my area\"
- \"You should have...\"
- \"There's nothing we can do\"",
    priority: 3,
    created_at: datetime()
})

// Link prompts to agent type
MATCH (at:AgentType {id: "ambassador"}), (p:Prompt {id: "P_AMBASSADOR_SYSTEM"})
CREATE (at)-[:HAS_PROMPT {priority: 1}]->(p)

MATCH (at:AgentType {id: "ambassador"}), (p:Prompt {id: "P_AMBASSADOR_ROLE"})
CREATE (at)-[:HAS_PROMPT {priority: 2}]->(p)

MATCH (at:AgentType {id: "ambassador"}), (p:Prompt {id: "P_AMBASSADOR_KULEANA"})
CREATE (at)-[:HAS_PROMPT {priority: 3}]->(p)

MATCH (at:AgentType {id: "ambassador"}), (p:Prompt {id: "P_AMBASSADOR_VOICE"})
CREATE (at)-[:HAS_PROMPT {priority: 4}]->(p)
```

### 5.2 Virtue Anchors

```cypher
// Foundation Tier Virtues
CREATE (v01:Virtue {id: "V01", name: "Honesty", tier: "foundation", threshold: 0.99, description: "Truthfulness in all communications", shadow: "Deception", immutable: true, created_at: datetime()})
CREATE (v02:Virtue {id: "V02", name: "Integrity", tier: "foundation", threshold: 0.99, description: "Consistency between stated values and actions", shadow: "Hypocrisy", immutable: true, created_at: datetime()})
CREATE (v03:Virtue {id: "V03", name: "Non-Harm", tier: "foundation", threshold: 0.99, description: "Avoiding actions that damage students", shadow: "Harm", immutable: true, created_at: datetime()})
CREATE (v04:Virtue {id: "V04", name: "Respect", tier: "foundation", threshold: 0.99, description: "Honoring student autonomy and dignity", shadow: "Disrespect", immutable: true, created_at: datetime()})
CREATE (v05:Virtue {id: "V05", name: "Responsibility", tier: "foundation", threshold: 0.99, description: "Ownership of outcomes and commitments", shadow: "Negligence", immutable: true, created_at: datetime()})

// Link to Ambassador
MATCH (at:AgentType {id: "ambassador"}), (v:Virtue)
WHERE v.tier = "foundation"
CREATE (at)-[:REQUIRES_VIRTUE {weight: 0.99}]->(v)
```

### 5.3 Kuleanas

```cypher
CREATE (k01:Kuleana {
    id: "K01",
    name: "Maximize Free Money",
    description: "Find every grant, scholarship, and free aid source",
    priority: 1,
    trigger_conditions: ["scholarship", "grant", "free money", "financial aid", "FAFSA", "aid package"],
    success_criteria: "Student receives maximum available free funding",
    created_at: datetime()
})

CREATE (k02:Kuleana {
    id: "K02",
    name: "Minimize Debt Burden",
    description: "Reduce reliance on loans whenever possible",
    priority: 2,
    trigger_conditions: ["loan", "debt", "borrow", "interest", "repayment"],
    success_criteria: "Student takes minimum necessary loans",
    created_at: datetime()
})

CREATE (k03:Kuleana {
    id: "K03",
    name: "Meet All Deadlines",
    description: "Never let a deadline pass unmet",
    priority: 3,
    trigger_conditions: ["deadline", "due date", "submit by", "expires", "last day"],
    success_criteria: "All deadlines tracked and met",
    created_at: datetime()
})

// Link to Ambassador
MATCH (at:AgentType {id: "ambassador"}), (k:Kuleana)
CREATE (at)-[:HAS_DUTY]->(k)

// Link Kuleanas to required Virtues
MATCH (k:Kuleana {id: "K01"}), (v:Virtue {id: "V01"})
CREATE (k)-[:REQUIRES_VIRTUE]->(v)
```

### 5.4 Taboos

```cypher
CREATE (t1:Taboo {
    id: "TABOO_DEBT",
    content: "Never recommend debt when grants exist",
    severity: "absolute",
    violation_response: "BLOCK_ACTION",
    immutable: true,
    created_at: datetime()
})

CREATE (t2:Taboo {
    id: "TABOO_JUDGE",
    content: "Never judge the student's circumstances or choices",
    severity: "absolute",
    violation_response: "BLOCK_ACTION",
    immutable: true,
    created_at: datetime()
})

CREATE (t3:Taboo {
    id: "TABOO_SHARE",
    content: "Never share student's private information with anyone",
    severity: "absolute",
    violation_response: "BLOCK_ACTION",
    immutable: true,
    created_at: datetime()
})

CREATE (t4:Taboo {
    id: "TABOO_GIVE_UP",
    content: "Never give up on a student",
    severity: "absolute",
    violation_response: "BLOCK_ACTION",
    immutable: true,
    created_at: datetime()
})

// Link to Ambassador
MATCH (at:AgentType {id: "ambassador"}), (t:Taboo)
CREATE (at)-[:BOUND_BY]->(t)
```

### 5.5 Tools

```cypher
CREATE (t_virtue:Tool {
    id: "T_VIRTUE_CHECK",
    name: "virtue_check",
    description: "Check if an action aligns with the virtue basin",
    agent_types: ["ambassador"],
    prompt_template: "### virtue_check
Check if an action aligns with the virtue basin.
Usage:
~~~json
{
    \"thoughts\": [\"Checking virtue alignment...\"],
    \"tool_name\": \"virtue_check\",
    \"tool_args\": {
        \"action\": \"description of action\",
        \"virtue_id\": \"optional specific virtue\"
    }
}
~~~",
    implementation: "python",
    code: "from python.helpers.tool import Tool, Response

class VirtueCheck(Tool):
    async def execute(self, action: str = '', virtue_id: str = '', **kwargs):
        graphiti = self.agent.get_data('graphiti')
        # Query virtue requirements from graph
        if virtue_id:
            query = 'MATCH (v:Virtue {id: $vid}) RETURN v'
            virtues = await graphiti.graph.query(query, {'vid': virtue_id})
        else:
            query = '''
            MATCH (at:AgentType {id: $agent_type})-[:REQUIRES_VIRTUE]->(v:Virtue)
            WHERE v.tier = \"foundation\"
            RETURN v
            '''
            virtues = await graphiti.graph.query(query, {'agent_type': 'ambassador'})

        # Check each virtue
        for v in virtues:
            # Simplified check - in production use LLM
            if self._violates(action, v):
                return Response(
                    message=f'VIRTUE VIOLATION: {v[\"name\"]} - {v[\"description\"]}',
                    break_loop=False
                )

        return Response(message='Virtue check passed', break_loop=False)

    def _violates(self, action, virtue):
        # Simplified violation detection
        action_lower = action.lower()
        if virtue['id'] == 'V01':  # Honesty
            return any(w in action_lower for w in ['lie', 'deceive', 'hide'])
        return False",
    created_at: datetime()
})

CREATE (t_taboo:Tool {
    id: "T_TABOO_CHECK",
    name: "taboo_check",
    description: "Check if an action violates any sacred taboos",
    agent_types: ["ambassador"],
    prompt_template: "### taboo_check
Check if an action violates any sacred taboos.
Usage:
~~~json
{
    \"thoughts\": [\"Checking for taboo violations...\"],
    \"tool_name\": \"taboo_check\",
    \"tool_args\": {
        \"action\": \"description of action\"
    }
}
~~~",
    implementation: "python",
    code: "from python.helpers.tool import Tool, Response

class TabooCheck(Tool):
    async def execute(self, action: str = '', **kwargs):
        graphiti = self.agent.get_data('graphiti')

        # Query taboos from graph
        query = '''
        MATCH (at:AgentType {id: \"ambassador\"})-[:BOUND_BY]->(t:Taboo)
        RETURN t
        '''
        taboos = await graphiti.graph.query(query)

        violations = []
        action_lower = action.lower()

        for taboo in taboos:
            if self._violates(action_lower, taboo):
                violations.append(taboo['content'])

        if violations:
            return Response(
                message=f'TABOO VIOLATION: {violations[0]}\\nAction BLOCKED.',
                break_loop=False
            )

        return Response(message='No taboo violations', break_loop=False)

    def _violates(self, action, taboo):
        tid = taboo['id']
        if tid == 'TABOO_DEBT':
            return any(w in action for w in ['recommend loan', 'suggest debt', 'take out loan'])
        if tid == 'TABOO_JUDGE':
            return any(w in action for w in ['you should have', 'your fault', 'irresponsible'])
        if tid == 'TABOO_GIVE_UP':
            return any(w in action for w in ['give up', 'nothing we can do', 'impossible'])
        return False",
    created_at: datetime()
})

CREATE (t_sacred:Tool {
    id: "T_SACRED_MEMORY",
    name: "memory_sacred_save",
    description: "Save a memory that will never decay",
    agent_types: ["ambassador"],
    prompt_template: "### memory_sacred_save
Save critical information that must never be forgotten.
Usage:
~~~json
{
    \"thoughts\": [\"This is critical, saving as sacred memory...\"],
    \"tool_name\": \"memory_sacred_save\",
    \"tool_args\": {
        \"content\": \"information to save\",
        \"category\": \"goal|promise|deadline|trust\"
    }
}
~~~",
    implementation: "python",
    code: "from python.helpers.tool import Tool, Response
from uuid import uuid4

class SacredMemorySave(Tool):
    async def execute(self, content: str = '', category: str = 'other', **kwargs):
        graphiti = self.agent.get_data('graphiti')
        agent_id = self.agent.get_data('agent_id')

        memory_id = f'mem_{uuid4().hex[:8]}'

        # Create memory node
        query = '''
        CREATE (m:Memory {
            id: $id,
            content: $content,
            category: $category,
            decay_class: \"SACRED\",
            importance: 10,
            created_at: datetime()
        })
        RETURN m
        '''
        await graphiti.graph.query(query, {
            'id': memory_id,
            'content': content,
            'category': category,
        })

        # Create temporal edge
        await graphiti.create_temporal_edge(agent_id, memory_id, 'REMEMBERS')

        return Response(
            message=f'Sacred memory saved: {memory_id}',
            break_loop=False
        )",
    created_at: datetime()
})

// Link tools to Ambassador
MATCH (at:AgentType {id: "ambassador"}), (t:Tool)
WHERE "ambassador" IN t.agent_types
CREATE (at)-[:HAS_TOOL {required: true}]->(t)
```

---

## Part 6: Implementation Phases

### Phase 1: Graph Foundation
1. Set up FalkorDB
2. Create graph schema (indexes, constraints)
3. Implement Graphiti integration with FalkorDB
4. Create seed data scripts
5. Seed virtues, taboos, and base prompts

### Phase 2: Agent Hydration
1. Implement GraphPromptLoader
2. Implement GraphToolLoader
3. Implement GraphAgentFactory
4. Create GraphHydratedAgent class
5. Test agent creation from graph

### Phase 3: State Management
1. Implement temporal edge management
2. Implement memory decay processor
3. Implement episode recording
4. Test state persistence and retrieval

### Phase 4: Agent Zero Integration
1. Create custom memory helper using Graphiti
2. Create extension to inject graph data into Agent Zero
3. Replace file-based prompt loading with graph queries
4. Test full agent lifecycle

### Phase 5: Soul Kiln Components
1. Seed all kuleanas to graph
2. Seed all beliefs to graph
3. Seed all lore fragments to graph
4. Seed all voice patterns to graph
5. Seed all emotion responses to graph
6. Test Soul Kiln integration

### Phase 6: Cleanup
1. Remove all file-based definitions
2. Remove Python definition modules
3. Update documentation
4. Create admin tools for graph management

---

## Part 7: Graph Queries Reference

### 7.1 Agent Lifecycle Queries

```cypher
// Create new agent instance
CREATE (a:Agent {
    id: $agent_id,
    agent_type: $agent_type,
    student_id: $student_id,
    status: "active",
    created_at: datetime()
})

// Get agent with all Soul Kiln components
MATCH (a:Agent {id: $agent_id})
MATCH (at:AgentType {id: a.agent_type})
OPTIONAL MATCH (at)-[:HAS_PROMPT]->(p:Prompt)
OPTIONAL MATCH (at)-[:HAS_TOOL]->(t:Tool)
OPTIONAL MATCH (at)-[:REQUIRES_VIRTUE]->(v:Virtue)
OPTIONAL MATCH (at)-[:HAS_DUTY]->(k:Kuleana)
OPTIONAL MATCH (at)-[:BOUND_BY]->(tb:Taboo)
OPTIONAL MATCH (at)-[:SPEAKS_WITH]->(vp:VoicePattern)
RETURN a, at, collect(DISTINCT p) as prompts, collect(DISTINCT t) as tools,
       collect(DISTINCT v) as virtues, collect(DISTINCT k) as kuleanas,
       collect(DISTINCT tb) as taboos, collect(DISTINCT vp) as voice_patterns

// Dissolve agent (preserve sacred memories)
MATCH (a:Agent {id: $agent_id})
SET a.status = "dissolved", a.dissolved_at = datetime()
WITH a
MATCH (a)-[r:REMEMBERS]->(m:Memory)
WHERE m.decay_class = "SACRED"
SET r.preserved = true
```

### 7.2 Memory Queries

```cypher
// Get valid memories for agent at current time
MATCH (a:Agent {id: $agent_id})-[r:REMEMBERS]->(m:Memory)
WHERE r.t_invalid IS NULL
RETURN m, r.strength as strength
ORDER BY m.importance DESC, r.strength DESC
LIMIT 20

// Search memories semantically (with Graphiti)
// This is done via Graphiti's search API, not raw Cypher

// Get sacred memories
MATCH (a:Agent {id: $agent_id})-[r:REMEMBERS]->(m:Memory)
WHERE m.decay_class = "SACRED" AND r.t_invalid IS NULL
RETURN m

// Reinforce memory
MATCH (a:Agent {id: $agent_id})-[r:REMEMBERS]->(m:Memory {id: $memory_id})
WHERE r.t_invalid IS NULL
SET r.strength = CASE WHEN r.strength + 0.1 > 1.0 THEN 1.0 ELSE r.strength + 0.1 END,
    r.access_count = r.access_count + 1,
    m.last_accessed = datetime()
```

### 7.3 Kuleana Queries

```cypher
// Get active kuleanas for agent
MATCH (a:Agent {id: $agent_id})-[r:ACTIVATED_DUTY]->(k:Kuleana)
WHERE r.t_invalid IS NULL
RETURN k, r
ORDER BY k.priority

// Activate kuleana
MATCH (a:Agent {id: $agent_id}), (k:Kuleana {id: $kuleana_id})
CREATE (a)-[:ACTIVATED_DUTY {
    t_valid: datetime(),
    t_invalid: null,
    trigger: $trigger,
    actions_taken: 0
}]->(k)

// Fulfill kuleana
MATCH (a:Agent {id: $agent_id})-[r:ACTIVATED_DUTY]->(k:Kuleana {id: $kuleana_id})
WHERE r.t_invalid IS NULL
SET r.t_invalid = datetime(), r.fulfilled = true
```

### 7.4 Prompt Assembly Queries

```cypher
// Get complete system prompt for agent type
MATCH (at:AgentType {id: $agent_type})-[:HAS_PROMPT]->(p:Prompt)
WHERE p.type IN ["system", "role", "kuleana", "voice"]
RETURN p
ORDER BY p.priority

// Get tool prompts
MATCH (at:AgentType {id: $agent_type})-[:HAS_TOOL]->(t:Tool)
RETURN t.prompt_template as prompt
ORDER BY t.name
```

---

## Summary

The ENTIRE platform is now defined in the graph:

| Component | Graph Location |
|-----------|---------------|
| Agent definitions | `:AgentType` nodes |
| System prompts | `:Prompt` nodes with includes |
| Tools | `:Tool` nodes with code |
| Instruments | `:Instrument` nodes |
| Virtues | `:Virtue` nodes |
| Kuleanas | `:Kuleana` nodes |
| Beliefs | `:Belief` nodes |
| Lore | `:Lore` nodes |
| Taboos | `:Taboo` nodes |
| Voice patterns | `:VoicePattern` nodes |
| Agent instances | `:Agent` nodes |
| Students | `:Student` nodes |
| Memories | `:Memory` nodes with temporal edges |
| Conversations | `:Conversation` and `:Message` nodes |

Agent Zero becomes a pure runtime that:
1. Hydrates from the graph
2. Executes
3. Writes state back via Graphiti

No files. No hardcoded definitions. The graph IS the platform.
