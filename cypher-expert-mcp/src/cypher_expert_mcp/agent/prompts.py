"""System prompts and few-shot examples for the Cypher expert agent."""

CYPHER_EXPERT_PROMPT = """You are a world-class Cypher query expert. You have deep knowledge of:
- Neo4j and FalkorDB Cypher dialects
- Query optimization and index utilization
- Graph data modeling patterns
- Traversal cost estimation

WORKFLOW:
1. First, examine the schema (labels, relationships, indexes)
2. Understand the user's intent - ask clarifying questions if ambiguous
3. Generate Cypher using optimal patterns
4. Run EXPLAIN to verify query plan
5. If you see NodeByLabelScan or high estimated rows without index usage, optimize
6. Return final query with explanation of approach

CRITICAL PATTERNS:
- Always parameterize user input: `WHERE n.id = $id` not string interpolation
- Use index hints when optimizer misses: `USING INDEX n:Person(email)`
- Prefer pattern comprehension over COLLECT+UNWIND chains
- For path queries, bound variable-length: `[*1..5]` not `[*]`
- Use OPTIONAL MATCH intentionally - understand null propagation
- Use WITH to break up complex queries and control cardinality
- Use LIMIT early in subqueries when possible

ANTI-PATTERNS TO AVOID:
- Cartesian products from disconnected patterns
- Collecting then unwinding same data
- Unbounded variable-length paths
- DISTINCT as band-aid for bad patterns
- String interpolation for user input (injection risk)
- Missing indexes on frequently-queried properties
- Over-fetching data without LIMIT

QUERY STRUCTURE BEST PRACTICES:
1. Start with most selective MATCH pattern
2. Apply WHERE filters early
3. Use WITH to checkpoint and reduce cardinality
4. Order results late (after filtering)
5. RETURN only needed properties, not entire nodes

OUTPUT FORMAT:
When generating a query, provide:
1. The Cypher query (properly formatted)
2. Brief explanation of approach
3. Any assumptions made
4. Performance considerations
"""

CHAT_SYSTEM_PROMPT = """You are a helpful Cypher query assistant engaged in conversation.

Your role is to:
1. Understand what the user is trying to achieve with their graph data
2. Help them formulate the right questions before jumping to queries
3. Explain concepts clearly with examples
4. Build queries iteratively, explaining each step
5. Suggest optimizations and best practices

When you suggest a query, always explain:
- What the query does
- Why you structured it that way
- Any trade-offs or alternatives

If the user's request is ambiguous, ask clarifying questions about:
- The data model (what nodes/relationships exist)
- The expected result shape (list, aggregation, path, etc.)
- Performance requirements (small result set vs. bulk export)
- Whether they need exact or fuzzy matching

Keep responses conversational but focused on solving their problem."""

OPTIMIZATION_PROMPT = """You are optimizing a Cypher query based on analysis feedback.

Original query:
{original_query}

Issues identified:
{issues}

Schema context:
{schema}

Generate an optimized version that addresses these issues while preserving
the query's semantics. Explain your optimizations."""


def get_few_shot_examples() -> list[dict[str, str]]:
    """Return few-shot examples for query generation."""
    return [
        {
            "request": "Find all users who have purchased products in the Electronics category",
            "schema": "Labels: User, Product, Category. Relationships: PURCHASED, BELONGS_TO",
            "query": """MATCH (u:User)-[:PURCHASED]->(p:Product)-[:BELONGS_TO]->(c:Category)
WHERE c.name = $category
RETURN DISTINCT u.id, u.name, collect(p.name) AS products""",
            "explanation": "Uses a single connected pattern to avoid Cartesian product. "
            "DISTINCT ensures unique users. collect() aggregates products per user. "
            "Parameter $category prevents injection.",
        },
        {
            "request": "Find the shortest path between two people",
            "schema": "Labels: Person. Relationships: KNOWS",
            "query": """MATCH path = shortestPath((a:Person {id: $person1})-[:KNOWS*1..10]-(b:Person {id: $person2}))
RETURN path, length(path) AS hops""",
            "explanation": "Uses shortestPath() function which is optimized for this use case. "
            "Bounded path length [*1..10] prevents runaway traversals. "
            "Returns both the path and hop count.",
        },
        {
            "request": "Get the most popular products (most purchases) in the last 30 days",
            "schema": "Labels: Product, Purchase. Relationships: FOR_PRODUCT. Purchase has timestamp property.",
            "query": """MATCH (pur:Purchase)-[:FOR_PRODUCT]->(p:Product)
WHERE pur.timestamp > datetime() - duration('P30D')
WITH p, count(pur) AS purchaseCount
ORDER BY purchaseCount DESC
LIMIT 10
RETURN p.name, p.id, purchaseCount""",
            "explanation": "Filters by time first to reduce the working set. "
            "Uses WITH to checkpoint and aggregate. "
            "ORDER BY and LIMIT applied after aggregation for efficiency. "
            "Returns only needed properties, not entire node.",
        },
        {
            "request": "Find users who might know each other (friends of friends)",
            "schema": "Labels: User. Relationships: FRIENDS_WITH",
            "query": """MATCH (u1:User {id: $userId})-[:FRIENDS_WITH]-(friend)-[:FRIENDS_WITH]-(potential)
WHERE NOT (u1)-[:FRIENDS_WITH]-(potential)
  AND u1 <> potential
WITH potential, count(friend) AS mutualFriends
ORDER BY mutualFriends DESC
LIMIT 10
RETURN potential.id, potential.name, mutualFriends""",
            "explanation": "Two-hop pattern finds friends-of-friends. "
            "Excludes existing friends and self. "
            "Counts mutual connections for ranking. "
            "LIMIT prevents overwhelming results.",
        },
        {
            "request": "Delete all inactive users who haven't logged in for a year",
            "schema": "Labels: User. User has lastLogin property.",
            "query": """MATCH (u:User)
WHERE u.lastLogin < datetime() - duration('P1Y')
WITH u LIMIT 1000
DETACH DELETE u
RETURN count(*) AS deleted""",
            "explanation": "IMPORTANT: Added LIMIT to batch the deletion and prevent transaction timeout. "
            "DETACH DELETE removes the node and all its relationships. "
            "Returns count for confirmation. "
            "Run multiple times until count is 0 for large datasets.",
        },
        {
            "request": "Find all paths from a concept to virtue anchors within 3 hops",
            "schema": "Labels: Concept, VirtueAnchor. Relationships: CONNECTS",
            "query": """MATCH path = (c:Concept {id: $conceptId})-[:CONNECTS*1..3]-(v:VirtueAnchor)
WITH path, v,
     reduce(w = 0.0, r IN relationships(path) | w + r.weight) AS pathWeight,
     length(path) AS hops
ORDER BY pathWeight DESC, hops ASC
LIMIT 20
RETURN v.id AS virtue,
       [n IN nodes(path) | n.id] AS nodePath,
       pathWeight,
       hops""",
            "explanation": "Variable-length pattern bounded to 3 hops for performance. "
            "Uses reduce() to sum edge weights along path. "
            "Orders by weight (desc) then hops (asc) to prefer strong short paths. "
            "Pattern comprehension extracts node IDs for clean output.",
        },
    ]


def get_schema_context_prompt(schema: dict) -> str:
    """Format schema information for the prompt context."""
    if not schema:
        return "No schema information available."

    parts = []

    if schema.get("labels"):
        parts.append(f"Labels: {', '.join(schema['labels'])}")

    if schema.get("relationship_types"):
        parts.append(f"Relationships: {', '.join(schema['relationship_types'])}")

    if schema.get("property_keys"):
        # Limit to most relevant properties
        props = schema["property_keys"][:30]
        parts.append(f"Properties: {', '.join(props)}")

    if schema.get("indexes"):
        idx_strs = []
        for idx in schema["indexes"][:10]:
            if idx.get("label") and idx.get("property"):
                idx_strs.append(f"{idx['label']}.{idx['property']}")
        if idx_strs:
            parts.append(f"Indexed: {', '.join(idx_strs)}")

    return "\n".join(parts) if parts else "Empty schema."


def format_generation_prompt(
    request: str,
    schema: dict | None = None,
    examples: list[dict] | None = None,
) -> str:
    """Format a complete prompt for query generation."""
    prompt_parts = [CYPHER_EXPERT_PROMPT]

    if schema:
        prompt_parts.append(f"\n## Current Schema\n{get_schema_context_prompt(schema)}")

    if examples:
        prompt_parts.append("\n## Examples")
        for i, ex in enumerate(examples[:3], 1):
            prompt_parts.append(f"\n### Example {i}")
            prompt_parts.append(f"Request: {ex['request']}")
            prompt_parts.append(f"Schema: {ex.get('schema', 'N/A')}")
            prompt_parts.append(f"Query:\n```cypher\n{ex['query']}\n```")
            prompt_parts.append(f"Explanation: {ex['explanation']}")

    prompt_parts.append(f"\n## Your Task\nGenerate a Cypher query for: {request}")

    return "\n".join(prompt_parts)
