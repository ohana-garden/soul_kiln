"""Query generation and execution tools for the Cypher Expert MCP server."""

from __future__ import annotations

import json
import re
import uuid
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, TYPE_CHECKING

from falkordb import FalkorDB

if TYPE_CHECKING:
    from ..server import ServerConfig

from ..agent.core import CypherAgent
from ..agent.memory import QueryMemory
from .ethics import review_query_ethics, get_ethical_explanation


@dataclass
class CypherResult:
    """Result from generate_cypher tool."""

    query: str
    explanation: str
    confidence: float  # 0.0 to 1.0
    parameters: dict[str, Any] = field(default_factory=dict)
    warnings: list[str] = field(default_factory=list)
    alternatives: list[str] = field(default_factory=list)
    optimization_notes: list[str] = field(default_factory=list)
    ethical_review: dict[str, Any] | None = None

    def to_json(self) -> str:
        return json.dumps(
            {
                "query": self.query,
                "explanation": self.explanation,
                "confidence": self.confidence,
                "parameters": self.parameters,
                "warnings": self.warnings,
                "alternatives": self.alternatives,
                "optimization_notes": self.optimization_notes,
                "ethical_review": self.ethical_review,
            },
            indent=2,
        )


@dataclass
class ExecutionResult:
    """Result from execute_cypher tool."""

    success: bool
    rows: list[dict[str, Any]] = field(default_factory=list)
    columns: list[str] = field(default_factory=list)
    row_count: int = 0
    execution_time_ms: float = 0.0
    query_plan: dict[str, Any] | None = None
    error: str | None = None
    warnings: list[str] = field(default_factory=list)

    def to_json(self) -> str:
        return json.dumps(
            {
                "success": self.success,
                "rows": self.rows,
                "columns": self.columns,
                "row_count": self.row_count,
                "execution_time_ms": self.execution_time_ms,
                "query_plan": self.query_plan,
                "error": self.error,
                "warnings": self.warnings,
            },
            indent=2,
        )


@dataclass
class ChatResponse:
    """Result from cypher_chat tool."""

    message: str
    conversation_id: str
    suggested_query: str | None = None
    clarifying_questions: list[str] = field(default_factory=list)
    schema_context: dict[str, Any] | None = None

    def to_json(self) -> str:
        return json.dumps(
            {
                "message": self.message,
                "conversation_id": self.conversation_id,
                "suggested_query": self.suggested_query,
                "clarifying_questions": self.clarifying_questions,
                "schema_context": self.schema_context,
            },
            indent=2,
        )


# Global state for conversations and memory
_conversations: dict[str, list[dict[str, str]]] = {}
_query_memory = QueryMemory()
_agent: CypherAgent | None = None


def get_agent() -> CypherAgent:
    """Get or create the Cypher agent singleton."""
    global _agent
    if _agent is None:
        _agent = CypherAgent()
    return _agent


def get_db_connection(config: "ServerConfig") -> tuple[FalkorDB, Any]:
    """Create a database connection."""
    db = FalkorDB(host=config.host, port=config.port)
    graph = db.select_graph(config.graph_name)
    return db, graph


async def generate_cypher_impl(
    request: str,
    schema_context: bool,
    optimize: bool,
    config: "ServerConfig",
) -> CypherResult:
    """Generate Cypher from natural language request."""
    agent = get_agent()

    # Pre-check request for ethical concerns before generating
    request_review = review_query_ethics("", request=request)
    if request_review.has_blocking_concerns:
        return CypherResult(
            query="",
            explanation="Request blocked due to ethical concerns.",
            confidence=0.0,
            warnings=[get_ethical_explanation(request_review)],
            ethical_review=request_review.to_dict(),
        )

    # Fetch schema if requested
    schema = None
    if schema_context:
        try:
            from .schema import introspect_schema_impl

            schema_info = await introspect_schema_impl(config)
            schema = {
                "labels": schema_info.labels,
                "relationship_types": schema_info.relationship_types,
                "property_keys": schema_info.property_keys,
                "indexes": schema_info.indexes,
            }
        except Exception:
            # Continue without schema if introspection fails
            pass

    # Generate initial query
    result = await agent.generate_query(request, schema)

    # Ethical review of generated query
    if result.query:
        ethical_review = review_query_ethics(result.query, request=request, schema=schema)

        # Block queries with severe ethical concerns
        if ethical_review.has_blocking_concerns:
            return CypherResult(
                query="",
                explanation="Generated query blocked due to ethical concerns.",
                confidence=0.0,
                warnings=[get_ethical_explanation(ethical_review)],
                ethical_review=ethical_review.to_dict(),
            )

        # Add ethical warnings to result
        for concern in ethical_review.concerns:
            if concern.severity in ("warning", "info"):
                result.warnings.append(f"[{concern.category.upper()}] {concern.description}")

        result.ethical_review = ethical_review.to_dict()

    # Optimization pass if requested
    if optimize and result.query:
        try:
            from .validate import analyze_query_impl

            analysis = await analyze_query_impl(result.query, {}, config)

            # Check for optimization opportunities
            if analysis.bottlenecks:
                # Attempt regeneration with optimization hints
                optimization_hints = [b["suggestion"] for b in analysis.bottlenecks]
                improved = await agent.optimize_query(
                    result.query, optimization_hints, schema
                )
                if improved:
                    result.query = improved.query
                    result.optimization_notes = optimization_hints
        except Exception:
            # Continue with unoptimized query if analysis fails
            pass

    # Record for learning
    _query_memory.record(
        request=request,
        generated_query=result.query,
        schema_snapshot=schema,
        success=True,
    )

    return result


async def execute_cypher_impl(
    query: str,
    params: dict[str, Any],
    explain_first: bool,
    limit: int,
    config: "ServerConfig",
) -> ExecutionResult:
    """Execute a Cypher query with safety rails."""
    warnings = []

    # Ethical review before execution
    ethical_review = review_query_ethics(query)
    if ethical_review.has_blocking_concerns:
        return ExecutionResult(
            success=False,
            error="Query blocked due to ethical concerns: " +
                  "; ".join(c.description for c in ethical_review.concerns if c.severity == "block"),
            warnings=[get_ethical_explanation(ethical_review)],
        )

    # Add ethical warnings
    for concern in ethical_review.concerns:
        if concern.severity == "warning":
            warnings.append(f"[ETHICAL] {concern.description}")

    # Safety checks
    safety_result = _check_query_safety(query, params)
    if not safety_result["safe"]:
        return ExecutionResult(
            success=False,
            error=safety_result["reason"],
            warnings=safety_result.get("warnings", []),
        )
    warnings.extend(safety_result.get("warnings", []))

    # Add LIMIT if not present and not a write query
    query_upper = query.upper()
    is_write = any(
        kw in query_upper for kw in ["CREATE", "MERGE", "SET", "DELETE", "REMOVE"]
    )

    if not is_write and "LIMIT" not in query_upper:
        # Inject limit before any final clauses
        query = _inject_limit(query, limit)
        warnings.append(f"Added LIMIT {limit} to query")

    try:
        _, graph = get_db_connection(config)

        # Get query plan first if requested
        query_plan = None
        if explain_first:
            try:
                explain_result = graph.query(f"EXPLAIN {query}", params or {})
                query_plan = _parse_query_plan(explain_result)
            except Exception:
                pass  # Continue without plan

        # Execute query
        import time

        start = time.perf_counter()
        result = graph.query(query, params or {})
        execution_time = (time.perf_counter() - start) * 1000

        # Process results
        rows = []
        columns = result.header if hasattr(result, "header") else []

        for row in result.result_set:
            row_dict = {}
            for i, col in enumerate(columns):
                value = row[i] if i < len(row) else None
                # Handle node/relationship objects
                row_dict[col] = _serialize_value(value)
            rows.append(row_dict)

        return ExecutionResult(
            success=True,
            rows=rows,
            columns=columns,
            row_count=len(rows),
            execution_time_ms=execution_time,
            query_plan=query_plan,
            warnings=warnings,
        )

    except Exception as e:
        return ExecutionResult(
            success=False,
            error=str(e),
            warnings=warnings,
        )


async def cypher_chat_impl(
    message: str,
    conversation_id: str | None,
    config: "ServerConfig",
) -> ChatResponse:
    """Multi-turn conversation for query building."""
    # Get or create conversation
    if conversation_id and conversation_id in _conversations:
        history = _conversations[conversation_id]
    else:
        conversation_id = str(uuid.uuid4())
        history = []
        _conversations[conversation_id] = history

    # Add user message to history
    history.append({"role": "user", "content": message})

    # Fetch current schema for context
    schema_context = None
    try:
        from .schema import introspect_schema_impl

        schema_info = await introspect_schema_impl(config)
        schema_context = {
            "labels": schema_info.labels,
            "relationship_types": schema_info.relationship_types,
            "property_keys": schema_info.property_keys[:20],  # Limit for context
        }
    except Exception:
        pass

    # Get agent response
    agent = get_agent()
    response = await agent.chat(history, schema_context)

    # Add assistant response to history
    history.append({"role": "assistant", "content": response.message})

    # Keep conversation history bounded
    if len(history) > 20:
        history[:] = history[-20:]

    return ChatResponse(
        message=response.message,
        conversation_id=conversation_id,
        suggested_query=response.suggested_query,
        clarifying_questions=response.clarifying_questions,
        schema_context=schema_context,
    )


def _check_query_safety(query: str, params: dict[str, Any]) -> dict[str, Any]:
    """Check query for safety issues."""
    warnings = []
    query_upper = query.upper()

    # Check for potential injection via string interpolation
    # Look for unparameterized string literals that might be user input
    if re.search(r"WHERE\s+\w+\.\w+\s*=\s*['\"]", query):
        warnings.append(
            "Consider using parameters instead of string literals for user input"
        )

    # Check for unbounded variable-length paths
    if re.search(r"\[\*\]", query) or re.search(r"\[\*\.\.", query):
        if not re.search(r"\[\*\d+\.\.\d+\]", query) and not re.search(
            r"\[\*\.\.\d+\]", query
        ):
            return {
                "safe": False,
                "reason": "Unbounded variable-length paths ([*]) can cause performance issues. Use bounded paths like [*1..5]",
                "warnings": warnings,
            }

    # Check for DETACH DELETE without WHERE (dangerous)
    if "DETACH DELETE" in query_upper and "WHERE" not in query_upper:
        if "MATCH" in query_upper:
            return {
                "safe": False,
                "reason": "DETACH DELETE without WHERE clause could delete all matched nodes. Add a WHERE clause or confirm intent.",
                "warnings": warnings,
            }

    # Check for Cartesian products
    if _has_cartesian_product(query):
        warnings.append(
            "Query may produce Cartesian product - ensure MATCH patterns are connected"
        )

    return {"safe": True, "warnings": warnings}


def _has_cartesian_product(query: str) -> bool:
    """Detect potential Cartesian products in query."""
    # Simple heuristic: multiple MATCH clauses without shared variables
    matches = re.findall(r"MATCH\s+(\([^)]+\)(?:-\[[^\]]*\]->\([^)]+\))*)", query, re.I)
    if len(matches) <= 1:
        return False

    # Extract variables from each MATCH
    all_vars = []
    for match_pattern in matches:
        vars_in_pattern = set(re.findall(r"\((\w+)(?::[^)]+)?\)", match_pattern))
        all_vars.append(vars_in_pattern)

    # Check if any MATCH is disconnected
    if len(all_vars) >= 2:
        connected = all_vars[0]
        for vars_set in all_vars[1:]:
            if not connected & vars_set:
                return True
            connected |= vars_set

    return False


def _inject_limit(query: str, limit: int) -> str:
    """Inject LIMIT clause into query."""
    # Find RETURN clause and add LIMIT after it
    return_match = re.search(r"\bRETURN\b", query, re.I)
    if not return_match:
        return query

    # Check for existing ORDER BY, SKIP
    query_after_return = query[return_match.end() :]
    insert_pos = len(query)

    # Insert before any trailing whitespace/semicolon
    query = query.rstrip().rstrip(";")
    return f"{query} LIMIT {limit}"


def _parse_query_plan(explain_result: Any) -> dict[str, Any]:
    """Parse EXPLAIN result into structured query plan."""
    try:
        # FalkorDB returns execution plan as result set
        plan_text = str(explain_result.result_set) if explain_result.result_set else ""
        return {
            "raw_plan": plan_text,
            "operations": _extract_operations(plan_text),
        }
    except Exception:
        return {"raw_plan": "Unable to parse query plan"}


def _extract_operations(plan_text: str) -> list[dict[str, str]]:
    """Extract operations from query plan text."""
    operations = []
    for line in plan_text.split("\n"):
        line = line.strip()
        if line:
            # Try to identify operation type
            op_type = "Unknown"
            for known_op in [
                "NodeByLabelScan",
                "NodeByIdSeek",
                "NodeIndexSeek",
                "Expand",
                "Filter",
                "ProduceResults",
                "Projection",
                "Aggregation",
                "Sort",
                "Limit",
            ]:
                if known_op.lower() in line.lower():
                    op_type = known_op
                    break
            operations.append({"operation": op_type, "detail": line})
    return operations


def _serialize_value(value: Any) -> Any:
    """Serialize graph database values to JSON-compatible format."""
    if value is None:
        return None

    # Handle FalkorDB Node
    if hasattr(value, "properties") and hasattr(value, "labels"):
        return {
            "_type": "node",
            "labels": list(value.labels) if value.labels else [],
            "properties": dict(value.properties) if value.properties else {},
        }

    # Handle FalkorDB Edge/Relationship
    if hasattr(value, "properties") and hasattr(value, "relation"):
        return {
            "_type": "relationship",
            "type": value.relation,
            "properties": dict(value.properties) if value.properties else {},
        }

    # Handle FalkorDB Path
    if hasattr(value, "nodes") and hasattr(value, "edges"):
        return {
            "_type": "path",
            "nodes": [_serialize_value(n) for n in value.nodes()],
            "relationships": [_serialize_value(e) for e in value.edges()],
        }

    # Handle lists
    if isinstance(value, (list, tuple)):
        return [_serialize_value(v) for v in value]

    # Handle dicts
    if isinstance(value, dict):
        return {k: _serialize_value(v) for k, v in value.items()}

    # Handle datetime
    if isinstance(value, datetime):
        return value.isoformat()

    # Return primitives as-is
    return value


# Public function wrappers for direct import
async def generate_cypher(
    request: str,
    schema_context: bool = True,
    optimize: bool = True,
) -> CypherResult:
    """Generate Cypher from natural language."""
    from ..server import config

    return await generate_cypher_impl(request, schema_context, optimize, config)


async def execute_cypher(
    query: str,
    params: dict[str, Any] | None = None,
    explain_first: bool = True,
    limit: int = 100,
) -> ExecutionResult:
    """Execute Cypher with safety rails."""
    from ..server import config

    return await execute_cypher_impl(query, params or {}, explain_first, limit, config)


async def cypher_chat(
    message: str,
    conversation_id: str | None = None,
) -> ChatResponse:
    """Multi-turn conversation for complex query building."""
    from ..server import config

    return await cypher_chat_impl(message, conversation_id, config)
