"""Core agent implementation for Cypher query generation."""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Any

from .prompts import (
    CYPHER_EXPERT_PROMPT,
    CHAT_SYSTEM_PROMPT,
    OPTIMIZATION_PROMPT,
    get_few_shot_examples,
    get_schema_context_prompt,
    format_generation_prompt,
)
from .memory import QueryMemory


@dataclass
class GenerationResult:
    """Result from query generation."""

    query: str
    explanation: str
    confidence: float
    parameters: dict[str, Any] = field(default_factory=dict)
    warnings: list[str] = field(default_factory=list)
    alternatives: list[str] = field(default_factory=list)
    ethical_review: dict[str, Any] | None = None


@dataclass
class ChatResult:
    """Result from chat interaction."""

    message: str
    suggested_query: str | None = None
    clarifying_questions: list[str] = field(default_factory=list)


class CypherAgent:
    """Agent for generating and optimizing Cypher queries.

    This is a lightweight ReAct-style agent that:
    1. Generates initial query from natural language
    2. Self-validates using lint and analysis
    3. Iterates to fix issues
    4. Returns with confidence score

    For deployment with Agent Zero, this can be wrapped as a sub-agent
    with additional tools for database access and profiling.
    """

    def __init__(
        self,
        max_iterations: int = 5,
        memory: QueryMemory | None = None,
    ):
        """Initialize the agent.

        Args:
            max_iterations: Maximum self-correction iterations.
            memory: Query memory for learning. Creates in-memory if None.
        """
        self.max_iterations = max_iterations
        self.memory = memory or QueryMemory()
        self._few_shot_examples = get_few_shot_examples()

    async def generate_query(
        self,
        request: str,
        schema: dict[str, Any] | None = None,
    ) -> GenerationResult:
        """Generate a Cypher query from natural language.

        This implements a ReAct-style loop:
        1. Generate initial query
        2. Validate/analyze
        3. If issues, regenerate with fixes
        4. Return with confidence

        Args:
            request: Natural language description of desired query.
            schema: Optional schema context (labels, relationships, etc.)

        Returns:
            GenerationResult with query, explanation, and confidence.
        """
        # Get similar past queries for context
        similar = self.memory.get_similar_queries(request, limit=3)

        # Build generation context
        examples = self._few_shot_examples[:3]
        if similar:
            # Add relevant past queries as examples
            for record in similar[:2]:
                examples.append({
                    "request": record.request,
                    "query": record.generated_query,
                    "schema": "From history",
                    "explanation": "Previously generated query",
                })

        # Generate initial query
        query, explanation = self._generate_initial(request, schema, examples)

        if not query:
            return GenerationResult(
                query="",
                explanation="Failed to generate query",
                confidence=0.0,
                warnings=["Could not parse natural language request"],
            )

        # Self-validation loop
        warnings = []
        confidence = 0.8  # Start with decent confidence

        for iteration in range(self.max_iterations):
            # Lint check
            lint_issues = self._lint_query(query)

            if lint_issues["errors"]:
                # Critical issues - try to fix
                confidence -= 0.2
                fixed = self._fix_syntax_issues(query, lint_issues["errors"])
                if fixed and fixed != query:
                    query = fixed
                    continue
                else:
                    warnings.extend([f"Syntax issue: {e}" for e in lint_issues["errors"]])
                    break

            warnings.extend(lint_issues.get("warnings", []))

            # Pattern analysis
            pattern_issues = self._analyze_patterns(query)
            if pattern_issues:
                confidence -= 0.1 * len(pattern_issues)
                warnings.extend(pattern_issues)

            # If no critical issues, we're done
            break

        # Clamp confidence
        confidence = max(0.1, min(1.0, confidence))

        # Extract parameters from query
        parameters = self._extract_parameters(query)

        return GenerationResult(
            query=query,
            explanation=explanation,
            confidence=confidence,
            parameters=parameters,
            warnings=warnings,
        )

    async def optimize_query(
        self,
        query: str,
        optimization_hints: list[str],
        schema: dict[str, Any] | None = None,
    ) -> GenerationResult | None:
        """Optimize a query based on analysis feedback.

        Args:
            query: The query to optimize.
            optimization_hints: Suggestions from query analysis.
            schema: Optional schema context.

        Returns:
            Optimized query result or None if optimization not possible.
        """
        if not optimization_hints:
            return None

        # Apply known optimization patterns
        optimized = query

        for hint in optimization_hints:
            hint_lower = hint.lower()

            # Handle unbounded paths
            if "unbounded" in hint_lower and "path" in hint_lower:
                optimized = self._bound_paths(optimized)

            # Handle full scans
            if "full" in hint_lower and "scan" in hint_lower:
                # Can't fix without knowing which property to use
                # Just note the warning
                pass

            # Handle Cartesian products
            if "cartesian" in hint_lower:
                # Hard to fix automatically - would need semantic understanding
                pass

        if optimized != query:
            return GenerationResult(
                query=optimized,
                explanation=f"Optimized based on: {', '.join(optimization_hints)}",
                confidence=0.7,
                warnings=["Query was automatically optimized"],
            )

        return None

    async def chat(
        self,
        history: list[dict[str, str]],
        schema: dict[str, Any] | None = None,
    ) -> ChatResult:
        """Handle a chat message in multi-turn conversation.

        Args:
            history: Conversation history with role/content dicts.
            schema: Current schema context.

        Returns:
            ChatResult with response and optional query suggestion.
        """
        if not history:
            return ChatResult(
                message="Hello! I'm a Cypher query expert. How can I help you today?",
                clarifying_questions=["What kind of data are you working with?"],
            )

        last_message = history[-1]["content"] if history else ""

        # Check if this looks like a query request
        query_keywords = ["find", "get", "show", "list", "count", "match", "return",
                         "create", "update", "delete", "merge", "how many", "which"]

        is_query_request = any(kw in last_message.lower() for kw in query_keywords)

        if is_query_request:
            # Try to generate a query
            result = await self.generate_query(last_message, schema)

            if result.query and result.confidence > 0.5:
                return ChatResult(
                    message=self._format_query_response(result),
                    suggested_query=result.query,
                )
            else:
                # Need clarification
                return ChatResult(
                    message="I'd like to help you with that query. Could you provide more details?",
                    clarifying_questions=self._generate_clarifying_questions(last_message, schema),
                )

        # General conversation
        return ChatResult(
            message=self._generate_conversational_response(last_message, schema),
            clarifying_questions=[],
        )

    def _generate_initial(
        self,
        request: str,
        schema: dict[str, Any] | None,
        examples: list[dict],
    ) -> tuple[str, str]:
        """Generate initial query from request.

        In a full implementation, this would call an LLM.
        Here we use pattern matching for common cases.
        """
        request_lower = request.lower()

        # Pattern: Find/Get nodes by property
        if match := re.search(r"find (?:all )?(\w+)s? (?:where|with|that have) (\w+)\s*=\s*['\"]?(\w+)", request_lower):
            label = match.group(1).capitalize()
            prop = match.group(2)
            value = match.group(3)
            query = f"MATCH (n:{label}) WHERE n.{prop} = ${prop} RETURN n"
            explanation = f"Simple lookup of {label} nodes by {prop} property"
            return query, explanation

        # Pattern: Count nodes
        if "count" in request_lower and "how many" not in request_lower:
            if match := re.search(r"count (?:all )?(\w+)s?", request_lower):
                label = match.group(1).capitalize()
                query = f"MATCH (n:{label}) RETURN count(n) AS count"
                explanation = f"Count all {label} nodes"
                return query, explanation

        # Pattern: How many
        if "how many" in request_lower:
            if match := re.search(r"how many (\w+)s?", request_lower):
                label = match.group(1).capitalize()
                query = f"MATCH (n:{label}) RETURN count(n) AS count"
                explanation = f"Count all {label} nodes"
                return query, explanation

        # Pattern: Path between
        if "path" in request_lower and "between" in request_lower:
            query = """MATCH path = shortestPath((a)-[*1..10]-(b))
WHERE a.id = $startId AND b.id = $endId
RETURN path"""
            explanation = "Find shortest path between two nodes"
            return query, explanation

        # Pattern: Related to / connected to
        if "related to" in request_lower or "connected to" in request_lower:
            query = """MATCH (a)-[r]-(b)
WHERE a.id = $nodeId
RETURN type(r) AS relationship, b"""
            explanation = "Find all nodes related to a given node"
            return query, explanation

        # Pattern: Delete
        if "delete" in request_lower:
            if match := re.search(r"delete (?:all )?(\w+)s? (?:where|with) (\w+)\s*=", request_lower):
                label = match.group(1).capitalize()
                prop = match.group(2)
                query = f"""MATCH (n:{label})
WHERE n.{prop} = ${prop}
DETACH DELETE n
RETURN count(*) AS deleted"""
                explanation = f"Delete {label} nodes matching condition"
                return query, explanation

        # Default: provide template
        query = """MATCH (n)
WHERE n.id = $id
RETURN n"""
        explanation = "Basic node lookup template - customize based on your needs"
        return query, explanation

    def _lint_query(self, query: str) -> dict[str, list[str]]:
        """Basic lint check on query."""
        errors = []
        warnings = []

        # Check balanced delimiters
        if query.count("(") != query.count(")"):
            errors.append("Unbalanced parentheses")
        if query.count("[") != query.count("]"):
            errors.append("Unbalanced brackets")
        if query.count("{") != query.count("}"):
            errors.append("Unbalanced braces")

        # Check for common typos
        query_upper = query.upper()
        typos = [("MACTCH", "MATCH"), ("WEHRE", "WHERE"), ("RETRUN", "RETURN")]
        for typo, correct in typos:
            if typo in query_upper:
                errors.append(f"Typo: '{typo}' should be '{correct}'")

        # Check for required clauses
        if "MATCH" in query_upper and "RETURN" not in query_upper:
            if not any(kw in query_upper for kw in ["CREATE", "MERGE", "SET", "DELETE"]):
                errors.append("Query has MATCH but no RETURN clause")

        # Warnings
        if re.search(r"\[\*\]", query):
            warnings.append("Unbounded variable-length path [*]")

        if re.search(r"WHERE\s+\w+\.\w+\s*=\s*['\"][^$]", query):
            warnings.append("String literal instead of parameter")

        return {"errors": errors, "warnings": warnings}

    def _fix_syntax_issues(self, query: str, errors: list[str]) -> str | None:
        """Attempt to fix common syntax issues."""
        fixed = query

        for error in errors:
            if "MACTCH" in error:
                fixed = re.sub(r"\bMACTCH\b", "MATCH", fixed, flags=re.I)
            elif "WEHRE" in error:
                fixed = re.sub(r"\bWEHRE\b", "WHERE", fixed, flags=re.I)
            elif "RETRUN" in error:
                fixed = re.sub(r"\bRETRUN\b", "RETURN", fixed, flags=re.I)

        return fixed if fixed != query else None

    def _analyze_patterns(self, query: str) -> list[str]:
        """Analyze query for anti-patterns."""
        issues = []

        # Unbounded paths
        if re.search(r"\[\*\]", query) or re.search(r"\[\*\d+\.\.\]", query):
            issues.append("Contains unbounded variable-length path")

        # Potential Cartesian product
        matches = re.findall(r"\bMATCH\b", query, re.I)
        if len(matches) > 1 and "WHERE" not in query.upper():
            issues.append("Multiple MATCH clauses without WHERE - possible Cartesian product")

        # COLLECT + UNWIND anti-pattern
        if "COLLECT" in query.upper() and "UNWIND" in query.upper():
            issues.append("COLLECT followed by UNWIND may be unnecessary")

        return issues

    def _bound_paths(self, query: str) -> str:
        """Add bounds to unbounded variable-length paths."""
        # Replace [*] with [*1..10]
        query = re.sub(r"\[\*\]", "[*1..10]", query)
        # Replace [*n..] with [*n..10]
        query = re.sub(r"\[\*(\d+)\.\.\]", r"[*\1..10]", query)
        return query

    def _extract_parameters(self, query: str) -> dict[str, Any]:
        """Extract parameter placeholders from query."""
        params = {}
        for match in re.finditer(r"\$(\w+)", query):
            param_name = match.group(1)
            params[param_name] = f"<{param_name}>"  # Placeholder
        return params

    def _format_query_response(self, result: GenerationResult) -> str:
        """Format a query generation result as chat response."""
        parts = [
            "Here's a Cypher query for your request:",
            "",
            "```cypher",
            result.query,
            "```",
            "",
            f"**Explanation:** {result.explanation}",
        ]

        if result.parameters:
            parts.append("")
            parts.append("**Parameters needed:**")
            for name in result.parameters:
                parts.append(f"- `${name}`")

        if result.warnings:
            parts.append("")
            parts.append("**Notes:**")
            for warning in result.warnings:
                parts.append(f"- {warning}")

        parts.append("")
        parts.append(f"Confidence: {result.confidence:.0%}")

        return "\n".join(parts)

    def _generate_clarifying_questions(
        self,
        request: str,
        schema: dict[str, Any] | None,
    ) -> list[str]:
        """Generate clarifying questions for ambiguous request."""
        questions = []

        if not schema:
            questions.append("What node labels exist in your graph?")
            questions.append("What relationships connect them?")
        else:
            if len(schema.get("labels", [])) > 5:
                questions.append(f"Which of these labels are you interested in: {', '.join(schema['labels'][:5])}...?")

        if "find" in request.lower() or "get" in request.lower():
            questions.append("Should the results include related nodes, or just the matching ones?")
            questions.append("Do you need all results, or just the top N?")

        if not questions:
            questions.append("Could you provide more details about what you're looking for?")

        return questions

    def _generate_conversational_response(
        self,
        message: str,
        schema: dict[str, Any] | None,
    ) -> str:
        """Generate a conversational response."""
        message_lower = message.lower()

        if any(w in message_lower for w in ["hello", "hi", "hey"]):
            return "Hello! I'm ready to help you write Cypher queries. What would you like to do with your graph data?"

        if "thank" in message_lower:
            return "You're welcome! Let me know if you need help with any other queries."

        if "help" in message_lower:
            return """I can help you with:
- Generating Cypher queries from natural language descriptions
- Explaining how queries work
- Optimizing slow queries
- Exploring your graph schema

Just describe what you want to find or do, and I'll suggest a query!"""

        if schema:
            schema_str = get_schema_context_prompt(schema)
            return f"I see your graph has this schema:\n{schema_str}\n\nWhat would you like to query?"

        return "I'm here to help with Cypher queries. What are you trying to accomplish?"


async def reason_and_act(
    request: str,
    schema: dict[str, Any] | None = None,
    max_iterations: int = 5,
) -> GenerationResult:
    """Lightweight ReAct loop for query generation.

    This is the standalone function version for use without Agent Zero.

    Args:
        request: Natural language query request.
        schema: Optional schema context.
        max_iterations: Maximum self-correction iterations.

    Returns:
        GenerationResult with query, explanation, and confidence.
    """
    agent = CypherAgent(max_iterations=max_iterations)
    return await agent.generate_query(request, schema)
