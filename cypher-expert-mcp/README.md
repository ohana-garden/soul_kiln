# Cypher Expert MCP Server

An MCP (Model Context Protocol) server that exposes a world-class Cypher query expert agent. The agent receives natural language requests and returns optimized, correct Cypher queries with explanations. It can also execute queries against connected FalkorDB or Neo4j-compatible graph databases.

## Features

- **Natural Language to Cypher**: Generate optimized Cypher queries from plain English descriptions
- **Query Execution**: Execute queries with safety rails (limits, injection prevention, plan inspection)
- **Query Analysis**: EXPLAIN/PROFILE queries to identify bottlenecks and suggest optimizations
- **Schema Introspection**: Automatically discover graph schema (labels, relationships, indexes)
- **Multi-turn Chat**: Iterative query building through conversation
- **Self-Correction**: Agent validates and improves queries through lint and analysis feedback
- **Learning Memory**: Stores query history for improving future suggestions

## Installation

```bash
# From the cypher-expert-mcp directory
pip install -e .

# Or with development dependencies
pip install -e ".[dev]"
```

## Quick Start

### Running the MCP Server

```bash
# Start the server (connects to localhost:6379 by default)
cypher-expert

# Or run directly with Python
python -m cypher_expert_mcp.server
```

### Configuring for Claude Desktop

Add to your Claude Desktop configuration (`claude_desktop_config.json`):

```json
{
  "mcpServers": {
    "cypher-expert": {
      "command": "cypher-expert",
      "env": {
        "FALKORDB_HOST": "localhost",
        "FALKORDB_PORT": "6379",
        "GRAPH_NAME": "virtue_basin"
      }
    }
  }
}
```

## MCP Tools

### generate_cypher

Generate Cypher queries from natural language descriptions.

**Parameters:**
- `request` (string, required): Natural language description of the query
- `schema_context` (boolean, default: true): Auto-fetch current schema for context
- `optimize` (boolean, default: true): Run through optimization pass

**Example:**
```
Generate a query to find all users who purchased products in the Electronics category in the last 30 days
```

### execute_cypher

Execute a Cypher query with safety rails.

**Parameters:**
- `query` (string, required): The Cypher query to execute
- `params` (object, default: {}): Query parameters for $placeholders
- `explain_first` (boolean, default: true): Show query plan before running
- `limit` (integer, default: 100): Maximum rows to return

**Example:**
```cypher
MATCH (p:Person)-[:PURCHASED]->(prod:Product)
WHERE p.id = $userId
RETURN p.name, collect(prod.name) AS products
```

### analyze_query

Analyze a query using PROFILE/EXPLAIN to identify performance issues.

**Parameters:**
- `query` (string, required): The Cypher query to analyze
- `params` (object, default: {}): Query parameters for accurate profiling

**Returns:** Query plan, bottlenecks, and optimization suggestions.

### introspect_schema

Retrieve the complete schema of the connected graph database.

**Returns:** Labels, relationship types, property keys, indexes, constraints, and counts.

### suggest_indexes

Analyze query patterns and suggest indexes for performance.

**Parameters:**
- `queries` (array of strings, required): Sample queries to analyze

### cypher_chat

Multi-turn conversation for iterative query building.

**Parameters:**
- `message` (string, required): Your message or question
- `conversation_id` (string, optional): ID to continue a previous conversation

### lint_cypher

Validate Cypher syntax and check for anti-patterns.

**Parameters:**
- `query` (string, required): The Cypher query to lint

**Returns:** Syntax errors, warnings, style issues, and a quality score.

### dry_run

Validate a query without executing it (EXPLAIN mode).

**Parameters:**
- `query` (string, required): The Cypher query to validate
- `params` (object, default: {}): Query parameters

## Resources

The server exposes knowledge resources for context:

- `cypher://reference` - Complete Cypher syntax reference
- `cypher://schema` - Live schema from connected database
- `cypher://optimization` - Query optimization patterns
- `cypher://examples` - 50+ annotated query examples

## Architecture

```
cypher-expert-mcp/
├── src/
│   ├── server.py          # MCP server entry point
│   ├── tools/
│   │   ├── query.py       # generate_cypher, execute_cypher, cypher_chat
│   │   ├── schema.py      # introspect_schema, suggest_indexes
│   │   └── validate.py    # analyze_query, lint_cypher, dry_run
│   ├── agent/
│   │   ├── core.py        # CypherAgent with ReAct loop
│   │   ├── prompts.py     # System prompts and few-shot examples
│   │   └── memory.py      # Query history and learned patterns
│   └── knowledge/
│       ├── cypher_reference.md
│       ├── optimization_patterns.md
│       ├── falkordb_specifics.md
│       └── common_queries.md
├── pyproject.toml
└── README.md
```

## Agent Capabilities

The Cypher agent uses a ReAct-style loop for query generation:

1. **Generate**: Create initial query from natural language + schema context
2. **Lint**: Check syntax and anti-patterns
3. **Analyze**: Run EXPLAIN to inspect query plan
4. **Optimize**: If issues found, regenerate with corrections
5. **Return**: Final query with confidence score and explanation

### Key Optimizations

- **Index usage**: Ensures queries use available indexes
- **Bounded paths**: Converts unbounded `[*]` to bounded `[*1..10]`
- **Parameter injection**: Always uses `$param` instead of string interpolation
- **Cartesian prevention**: Warns about disconnected MATCH patterns
- **Result limiting**: Auto-adds LIMIT to prevent runaway queries

## Knowledge Base

The agent has access to comprehensive Cypher knowledge:

- **cypher_reference.md**: Complete syntax reference (clauses, functions, operators)
- **optimization_patterns.md**: Query plan reading, index strategies, rewrites
- **falkordb_specifics.md**: FalkorDB differences from Neo4j
- **common_queries.md**: 50+ annotated examples for common patterns

## Safety Features

- **Parameter enforcement**: Warns about string interpolation (injection risk)
- **Unbounded path detection**: Rejects `[*]` patterns without bounds
- **Dangerous delete detection**: Requires WHERE clause for DETACH DELETE
- **Result limiting**: Auto-limits queries to prevent memory exhaustion
- **Query plan inspection**: Shows EXPLAIN output before execution

## Development

### Running Tests

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=cypher_expert_mcp --cov-report=html

# Run specific test file
pytest tests/test_query.py -v
```

### Code Quality

```bash
# Format code
black src tests

# Lint
ruff check src tests

# Type check
mypy src
```

## Integration with Agent Zero

The Cypher agent can be integrated as a sub-agent in Agent Zero:

```python
from agent_zero import Agent
from cypher_expert_mcp.agent import CypherAgent, CYPHER_EXPERT_PROMPT

cypher_agent = Agent(
    name="cypher_expert",
    system_prompt=CYPHER_EXPERT_PROMPT,
    tools=[
        FalkorDBTool(),
        CypherLinterTool(),
        QueryProfilerTool(),
    ],
    max_iterations=5,
    reflection_enabled=True
)
```

## License

MIT License - see LICENSE file for details.
