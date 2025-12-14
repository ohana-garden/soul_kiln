"""Query validation, analysis, and linting tools."""

from __future__ import annotations

import json
import re
from dataclasses import dataclass, field
from typing import Any, TYPE_CHECKING

from falkordb import FalkorDB

if TYPE_CHECKING:
    from ..server import ServerConfig


@dataclass
class QueryPlanOperation:
    """A single operation in a query plan."""

    operation: str
    label: str | None = None
    property_key: str | None = None
    estimated_rows: int | None = None
    actual_rows: int | None = None
    db_hits: int | None = None
    children: list["QueryPlanOperation"] = field(default_factory=list)


@dataclass
class Bottleneck:
    """An identified performance bottleneck."""

    operation: str
    severity: str  # "critical", "warning", "info"
    description: str
    suggestion: str
    estimated_impact: str


@dataclass
class AnalysisResult:
    """Result from analyze_query tool."""

    valid: bool
    query_plan: dict[str, Any] = field(default_factory=dict)
    bottlenecks: list[dict[str, Any]] = field(default_factory=list)
    statistics: dict[str, Any] = field(default_factory=dict)
    optimization_suggestions: list[str] = field(default_factory=list)
    error: str | None = None

    def to_json(self) -> str:
        return json.dumps(
            {
                "valid": self.valid,
                "query_plan": self.query_plan,
                "bottlenecks": self.bottlenecks,
                "statistics": self.statistics,
                "optimization_suggestions": self.optimization_suggestions,
                "error": self.error,
            },
            indent=2,
        )


@dataclass
class LintIssue:
    """A single lint issue."""

    severity: str  # "error", "warning", "info"
    message: str
    line: int | None = None
    column: int | None = None
    rule: str | None = None
    suggestion: str | None = None


@dataclass
class LintResult:
    """Result from lint_cypher tool."""

    valid: bool
    issues: list[LintIssue] = field(default_factory=list)
    score: int = 100  # 0-100, deducted for issues

    def to_json(self) -> str:
        return json.dumps(
            {
                "valid": self.valid,
                "issues": [
                    {
                        "severity": i.severity,
                        "message": i.message,
                        "line": i.line,
                        "column": i.column,
                        "rule": i.rule,
                        "suggestion": i.suggestion,
                    }
                    for i in self.issues
                ],
                "score": self.score,
            },
            indent=2,
        )


@dataclass
class DryRunResult:
    """Result from dry_run tool."""

    valid: bool
    query_plan: dict[str, Any] = field(default_factory=dict)
    estimated_rows: int | None = None
    warnings: list[str] = field(default_factory=list)
    error: str | None = None

    def to_json(self) -> str:
        return json.dumps(
            {
                "valid": self.valid,
                "query_plan": self.query_plan,
                "estimated_rows": self.estimated_rows,
                "warnings": self.warnings,
                "error": self.error,
            },
            indent=2,
        )


def get_db_connection(config: "ServerConfig") -> tuple[FalkorDB, Any]:
    """Create a database connection."""
    db = FalkorDB(host=config.host, port=config.port)
    graph = db.select_graph(config.graph_name)
    return db, graph


async def analyze_query_impl(
    query: str,
    params: dict[str, Any],
    config: "ServerConfig",
) -> AnalysisResult:
    """Analyze query using PROFILE/EXPLAIN to identify bottlenecks."""
    result = AnalysisResult(valid=True)

    try:
        _, graph = get_db_connection(config)
    except Exception as e:
        return AnalysisResult(valid=False, error=f"Connection failed: {str(e)}")

    # Run EXPLAIN to get query plan without execution
    try:
        explain_result = graph.query(f"EXPLAIN {query}", params or {})
        result.query_plan = _parse_explain_result(explain_result)
    except Exception as e:
        return AnalysisResult(valid=False, error=f"Query analysis failed: {str(e)}")

    # Analyze the plan for bottlenecks
    result.bottlenecks = _identify_bottlenecks(result.query_plan, query)

    # Generate optimization suggestions
    result.optimization_suggestions = _generate_suggestions(
        result.bottlenecks, query
    )

    # Try PROFILE for actual statistics (if query is safe)
    if _is_safe_for_profile(query):
        try:
            profile_result = graph.query(f"PROFILE {query}", params or {})
            result.statistics = _parse_profile_statistics(profile_result)
        except Exception:
            # PROFILE may fail on some queries, that's okay
            pass

    return result


async def lint_cypher_impl(query: str) -> LintResult:
    """Validate Cypher syntax and check for anti-patterns."""
    from .ethics import review_query_ethics

    result = LintResult(valid=True)
    issues = []

    # Basic syntax checks
    syntax_issues = _check_syntax(query)
    issues.extend(syntax_issues)

    # Anti-pattern checks
    antipattern_issues = _check_antipatterns(query)
    issues.extend(antipattern_issues)

    # Style checks
    style_issues = _check_style(query)
    issues.extend(style_issues)

    # Security checks
    security_issues = _check_security(query)
    issues.extend(security_issues)

    # Ethical checks
    ethical_review = review_query_ethics(query)
    for concern in ethical_review.concerns:
        severity_map = {"block": "error", "warning": "warning", "info": "info"}
        issues.append(LintIssue(
            severity=severity_map.get(concern.severity, "warning"),
            message=f"[ETHICS/{concern.category.upper()}] {concern.description}",
            rule=f"ethics/{concern.category}",
            suggestion=concern.suggestion,
        ))

    result.issues = issues

    # Calculate score
    error_count = sum(1 for i in issues if i.severity == "error")
    warning_count = sum(1 for i in issues if i.severity == "warning")
    info_count = sum(1 for i in issues if i.severity == "info")

    result.score = max(0, 100 - (error_count * 30) - (warning_count * 10) - (info_count * 2))
    result.valid = error_count == 0

    return result


async def dry_run_impl(
    query: str,
    params: dict[str, Any],
    config: "ServerConfig",
) -> DryRunResult:
    """Execute query in dry-run mode (EXPLAIN without execution)."""
    result = DryRunResult(valid=True)

    # First lint the query
    lint_result = await lint_cypher_impl(query)
    if not lint_result.valid:
        result.valid = False
        result.error = "Query has syntax errors"
        result.warnings = [i.message for i in lint_result.issues if i.severity == "error"]
        return result

    result.warnings = [i.message for i in lint_result.issues if i.severity == "warning"]

    try:
        _, graph = get_db_connection(config)
    except Exception as e:
        return DryRunResult(valid=False, error=f"Connection failed: {str(e)}")

    # Run EXPLAIN
    try:
        explain_result = graph.query(f"EXPLAIN {query}", params or {})
        result.query_plan = _parse_explain_result(explain_result)

        # Extract estimated rows if available
        if "estimated_rows" in result.query_plan:
            result.estimated_rows = result.query_plan["estimated_rows"]

    except Exception as e:
        return DryRunResult(valid=False, error=f"EXPLAIN failed: {str(e)}")

    return result


def _parse_explain_result(explain_result: Any) -> dict[str, Any]:
    """Parse EXPLAIN result into structured format."""
    plan = {
        "raw": [],
        "operations": [],
    }

    try:
        if explain_result.result_set:
            for row in explain_result.result_set:
                if row:
                    line = str(row[0]) if row[0] else str(row)
                    plan["raw"].append(line)

                    # Try to parse operation
                    op = _parse_operation_line(line)
                    if op:
                        plan["operations"].append(op)
    except Exception:
        plan["raw"] = [str(explain_result)]

    return plan


def _parse_operation_line(line: str) -> dict[str, Any] | None:
    """Parse a single operation line from query plan."""
    if not line.strip():
        return None

    op = {"raw": line}

    # Common operation patterns
    operations = [
        ("NodeByLabelScan", "full_scan"),
        ("AllNodesScan", "full_scan"),
        ("NodeByIdSeek", "seek"),
        ("NodeIndexSeek", "index_seek"),
        ("NodeIndexScan", "index_scan"),
        ("NodeUniqueIndexSeek", "index_seek"),
        ("Expand", "expand"),
        ("Filter", "filter"),
        ("ProduceResults", "results"),
        ("Projection", "project"),
        ("Aggregation", "aggregate"),
        ("Sort", "sort"),
        ("Limit", "limit"),
        ("Skip", "skip"),
        ("Distinct", "distinct"),
        ("Create", "create"),
        ("Merge", "merge"),
        ("Delete", "delete"),
        ("SetProperty", "set"),
    ]

    for op_name, op_type in operations:
        if op_name.lower() in line.lower():
            op["operation"] = op_name
            op["type"] = op_type
            break

    # Try to extract estimated rows
    rows_match = re.search(r"(\d+)\s*rows?", line, re.IGNORECASE)
    if rows_match:
        op["estimated_rows"] = int(rows_match.group(1))

    return op


def _parse_profile_statistics(profile_result: Any) -> dict[str, Any]:
    """Parse PROFILE result for execution statistics."""
    stats = {
        "total_db_hits": 0,
        "total_rows": 0,
        "execution_time_ms": 0,
    }

    try:
        # FalkorDB includes statistics in result
        if hasattr(profile_result, "statistics"):
            stats_dict = profile_result.statistics
            if "Query internal execution time" in stats_dict:
                time_str = stats_dict["Query internal execution time"]
                # Parse time like "0.5 milliseconds"
                time_match = re.search(r"([\d.]+)", time_str)
                if time_match:
                    stats["execution_time_ms"] = float(time_match.group(1))
    except Exception:
        pass

    return stats


def _identify_bottlenecks(
    query_plan: dict[str, Any],
    query: str,
) -> list[dict[str, Any]]:
    """Identify performance bottlenecks from query plan."""
    bottlenecks = []

    operations = query_plan.get("operations", [])

    for op in operations:
        op_name = op.get("operation", "")
        op_type = op.get("type", "")

        # Full scan bottleneck
        if op_type == "full_scan":
            bottlenecks.append({
                "operation": op_name,
                "severity": "critical",
                "description": f"{op_name} performs full label/node scan",
                "suggestion": "Add an index or use WHERE clause with indexed property",
                "estimated_impact": "High - O(n) where n is label cardinality",
            })

        # Large row estimates
        estimated_rows = op.get("estimated_rows", 0)
        if estimated_rows and estimated_rows > 10000:
            bottlenecks.append({
                "operation": op_name,
                "severity": "warning",
                "description": f"Operation estimates {estimated_rows} rows",
                "suggestion": "Consider adding LIMIT or more selective WHERE clause",
                "estimated_impact": "Medium - may cause memory pressure",
            })

    # Check query text for patterns
    query_upper = query.upper()

    # Unbounded variable-length path
    if re.search(r"\[\*\]", query) or re.search(r"\[\*\d+\.\.\]", query):
        bottlenecks.append({
            "operation": "VariableLengthPath",
            "severity": "critical",
            "description": "Unbounded variable-length path pattern",
            "suggestion": "Use bounded pattern like [*1..5] instead of [*]",
            "estimated_impact": "Critical - can cause exponential blowup",
        })

    # Multiple disconnected MATCH patterns
    if query_upper.count("MATCH") > 1:
        # Simple heuristic - could be Cartesian product
        bottlenecks.append({
            "operation": "MultipleMatch",
            "severity": "info",
            "description": "Multiple MATCH clauses detected",
            "suggestion": "Ensure patterns are connected to avoid Cartesian products",
            "estimated_impact": "Varies - could be O(n*m) if disconnected",
        })

    # COLLECT followed by UNWIND
    if "COLLECT" in query_upper and "UNWIND" in query_upper:
        bottlenecks.append({
            "operation": "CollectUnwind",
            "severity": "warning",
            "description": "COLLECT followed by UNWIND pattern",
            "suggestion": "Consider if pattern comprehension or direct approach would work",
            "estimated_impact": "Medium - unnecessary aggregation/expansion cycle",
        })

    # DISTINCT as potential band-aid
    if "DISTINCT" in query_upper:
        bottlenecks.append({
            "operation": "Distinct",
            "severity": "info",
            "description": "DISTINCT used - may indicate underlying pattern issue",
            "suggestion": "Verify DISTINCT is needed or if query pattern can be fixed",
            "estimated_impact": "Low-Medium - adds sorting/deduplication overhead",
        })

    return bottlenecks


def _generate_suggestions(
    bottlenecks: list[dict[str, Any]],
    query: str,
) -> list[str]:
    """Generate optimization suggestions based on bottlenecks."""
    suggestions = []

    for bottleneck in bottlenecks:
        if bottleneck["severity"] in ("critical", "warning"):
            suggestions.append(bottleneck["suggestion"])

    # Add general suggestions based on query patterns
    query_upper = query.upper()

    if "ORDER BY" in query_upper and "LIMIT" not in query_upper:
        suggestions.append(
            "Consider adding LIMIT when using ORDER BY to avoid sorting all results"
        )

    if "OPTIONAL MATCH" in query_upper:
        suggestions.append(
            "OPTIONAL MATCH can be slow - ensure it's necessary and understand NULL propagation"
        )

    if re.search(r"WHERE\s+NOT\s+", query_upper):
        suggestions.append(
            "Negative patterns (WHERE NOT) may prevent index usage"
        )

    return list(set(suggestions))  # Dedupe


def _is_safe_for_profile(query: str) -> bool:
    """Check if query is safe to run with PROFILE (no side effects)."""
    query_upper = query.upper()
    write_keywords = ["CREATE", "MERGE", "SET", "DELETE", "REMOVE", "DROP"]
    return not any(kw in query_upper for kw in write_keywords)


def _check_syntax(query: str) -> list[LintIssue]:
    """Check for basic syntax issues."""
    issues = []

    # Check balanced parentheses
    if query.count("(") != query.count(")"):
        issues.append(LintIssue(
            severity="error",
            message="Unbalanced parentheses",
            rule="syntax/balanced-parens",
        ))

    # Check balanced brackets
    if query.count("[") != query.count("]"):
        issues.append(LintIssue(
            severity="error",
            message="Unbalanced brackets",
            rule="syntax/balanced-brackets",
        ))

    # Check balanced braces
    if query.count("{") != query.count("}"):
        issues.append(LintIssue(
            severity="error",
            message="Unbalanced braces",
            rule="syntax/balanced-braces",
        ))

    # Check for common typos
    query_upper = query.upper()
    typos = [
        ("MACTCH", "MATCH"),
        ("WEHRE", "WHERE"),
        ("RETRUN", "RETURN"),
        ("CERATE", "CREATE"),
        ("DELTE", "DELETE"),
    ]
    for typo, correct in typos:
        if typo in query_upper:
            issues.append(LintIssue(
                severity="error",
                message=f"Possible typo: '{typo}' should be '{correct}'",
                rule="syntax/typo",
                suggestion=f"Replace with {correct}",
            ))

    # Check for missing RETURN in read query
    if "MATCH" in query_upper and "RETURN" not in query_upper:
        if not any(kw in query_upper for kw in ["CREATE", "MERGE", "SET", "DELETE"]):
            issues.append(LintIssue(
                severity="error",
                message="Query has MATCH but no RETURN clause",
                rule="syntax/missing-return",
                suggestion="Add RETURN clause to specify what to return",
            ))

    return issues


def _check_antipatterns(query: str) -> list[LintIssue]:
    """Check for known anti-patterns."""
    issues = []

    # Unbounded variable-length path
    if re.search(r"\[\*\]", query):
        issues.append(LintIssue(
            severity="warning",
            message="Unbounded variable-length path [*] can cause performance issues",
            rule="performance/unbounded-path",
            suggestion="Use bounded path like [*1..5]",
        ))

    # String interpolation instead of parameters
    if re.search(r"WHERE\s+\w+\.\w+\s*=\s*['\"][^$]", query):
        issues.append(LintIssue(
            severity="warning",
            message="String literal in WHERE clause - consider using parameters",
            rule="security/use-parameters",
            suggestion="Use $param instead of 'literal' for user input",
        ))

    # Cartesian product risk
    matches = re.findall(r"\bMATCH\b", query, re.IGNORECASE)
    if len(matches) > 1 and "WHERE" not in query.upper():
        issues.append(LintIssue(
            severity="warning",
            message="Multiple MATCH without WHERE may cause Cartesian product",
            rule="performance/cartesian-product",
            suggestion="Ensure MATCH patterns share variables or add WHERE clause",
        ))

    # COLLECT then UNWIND same data
    if re.search(r"COLLECT\s*\([^)]+\)\s*\]\s*AS\s+(\w+).*UNWIND\s+\1", query, re.I):
        issues.append(LintIssue(
            severity="warning",
            message="COLLECT followed by UNWIND of same data is often unnecessary",
            rule="performance/collect-unwind",
            suggestion="Consider using pattern comprehension or restructuring query",
        ))

    return issues


def _check_style(query: str) -> list[LintIssue]:
    """Check for style issues."""
    issues = []

    # Check for uppercase keywords (conventionally uppercase)
    keywords = ["MATCH", "WHERE", "RETURN", "CREATE", "MERGE", "SET", "DELETE",
                "WITH", "ORDER", "BY", "LIMIT", "SKIP", "OPTIONAL", "UNWIND",
                "CALL", "YIELD", "UNION", "PROFILE", "EXPLAIN"]

    for keyword in keywords:
        # Find lowercase versions
        pattern = rf"\b{keyword.lower()}\b"
        if re.search(pattern, query) and not re.search(rf"\b{keyword}\b", query):
            issues.append(LintIssue(
                severity="info",
                message=f"Keyword '{keyword.lower()}' should be uppercase",
                rule="style/uppercase-keywords",
                suggestion=f"Use {keyword} instead of {keyword.lower()}",
            ))

    return issues


def _check_security(query: str) -> list[LintIssue]:
    """Check for security issues."""
    issues = []

    # Check for potential injection via concatenation
    # Look for patterns like 'value' + variable
    if re.search(r"['\"].*\+.*['\"]|['\"].*\|\|.*['\"]", query):
        issues.append(LintIssue(
            severity="warning",
            message="String concatenation detected - potential injection risk",
            rule="security/injection-risk",
            suggestion="Use parameterized queries with $param syntax",
        ))

    # DETACH DELETE without WHERE
    if re.search(r"DETACH\s+DELETE", query, re.I) and "WHERE" not in query.upper():
        issues.append(LintIssue(
            severity="warning",
            message="DETACH DELETE without WHERE clause - may delete more than intended",
            rule="security/unsafe-delete",
            suggestion="Add WHERE clause to limit deletion scope",
        ))

    return issues


# Public function wrappers
async def analyze_query(
    query: str,
    params: dict[str, Any] | None = None,
) -> AnalysisResult:
    """PROFILE query, identify bottlenecks, suggest improvements."""
    from ..server import config

    return await analyze_query_impl(query, params or {}, config)


async def lint_cypher(query: str) -> LintResult:
    """Validate Cypher syntax and check for common anti-patterns."""
    return await lint_cypher_impl(query)


async def dry_run(
    query: str,
    params: dict[str, Any] | None = None,
) -> DryRunResult:
    """Execute a Cypher query in dry-run mode."""
    from ..server import config

    return await dry_run_impl(query, params or {}, config)
