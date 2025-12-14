"""Schema introspection and index suggestion tools."""

from __future__ import annotations

import json
import re
from dataclasses import dataclass, field
from typing import Any, TYPE_CHECKING

from falkordb import FalkorDB

if TYPE_CHECKING:
    from ..server import ServerConfig


@dataclass
class SchemaInfo:
    """Complete schema information from the graph database."""

    labels: list[str] = field(default_factory=list)
    relationship_types: list[str] = field(default_factory=list)
    property_keys: list[str] = field(default_factory=list)
    indexes: list[dict[str, Any]] = field(default_factory=list)
    constraints: list[dict[str, Any]] = field(default_factory=list)
    node_count: int = 0
    edge_count: int = 0
    label_counts: dict[str, int] = field(default_factory=dict)
    relationship_type_counts: dict[str, int] = field(default_factory=dict)

    def to_json(self) -> str:
        return json.dumps(
            {
                "labels": self.labels,
                "relationship_types": self.relationship_types,
                "property_keys": self.property_keys,
                "indexes": self.indexes,
                "constraints": self.constraints,
                "node_count": self.node_count,
                "edge_count": self.edge_count,
                "label_counts": self.label_counts,
                "relationship_type_counts": self.relationship_type_counts,
            },
            indent=2,
        )


@dataclass
class IndexSuggestion:
    """A suggested index for performance improvement."""

    label: str
    property_key: str
    reason: str
    priority: str  # "high", "medium", "low"
    create_statement: str
    estimated_impact: str


@dataclass
class IndexSuggestionResult:
    """Result from suggest_indexes tool."""

    suggestions: list[IndexSuggestion] = field(default_factory=list)
    existing_indexes: list[dict[str, Any]] = field(default_factory=list)
    analysis_notes: list[str] = field(default_factory=list)

    def to_json(self) -> str:
        return json.dumps(
            {
                "suggestions": [
                    {
                        "label": s.label,
                        "property_key": s.property_key,
                        "reason": s.reason,
                        "priority": s.priority,
                        "create_statement": s.create_statement,
                        "estimated_impact": s.estimated_impact,
                    }
                    for s in self.suggestions
                ],
                "existing_indexes": self.existing_indexes,
                "analysis_notes": self.analysis_notes,
            },
            indent=2,
        )


def get_db_connection(config: "ServerConfig") -> tuple[FalkorDB, Any]:
    """Create a database connection."""
    db = FalkorDB(host=config.host, port=config.port)
    graph = db.select_graph(config.graph_name)
    return db, graph


async def introspect_schema_impl(config: "ServerConfig") -> SchemaInfo:
    """Retrieve complete schema from the graph database."""
    try:
        _, graph = get_db_connection(config)
    except Exception as e:
        # Return empty schema if connection fails
        return SchemaInfo()

    schema = SchemaInfo()

    # Get labels
    try:
        result = graph.query("CALL db.labels()")
        schema.labels = [row[0] for row in result.result_set if row]
    except Exception:
        # Try alternative method
        try:
            result = graph.query("MATCH (n) RETURN DISTINCT labels(n) AS labels")
            label_set = set()
            for row in result.result_set:
                if row and row[0]:
                    for label in row[0]:
                        label_set.add(label)
            schema.labels = sorted(label_set)
        except Exception:
            pass

    # Get relationship types
    try:
        result = graph.query("CALL db.relationshipTypes()")
        schema.relationship_types = [row[0] for row in result.result_set if row]
    except Exception:
        # Try alternative method
        try:
            result = graph.query("MATCH ()-[r]->() RETURN DISTINCT type(r) AS type")
            schema.relationship_types = [row[0] for row in result.result_set if row]
        except Exception:
            pass

    # Get property keys
    try:
        result = graph.query("CALL db.propertyKeys()")
        schema.property_keys = [row[0] for row in result.result_set if row]
    except Exception:
        # Try to infer from nodes
        try:
            result = graph.query("MATCH (n) RETURN DISTINCT keys(n) AS keys LIMIT 100")
            key_set = set()
            for row in result.result_set:
                if row and row[0]:
                    for key in row[0]:
                        key_set.add(key)
            schema.property_keys = sorted(key_set)
        except Exception:
            pass

    # Get indexes
    try:
        result = graph.query("CALL db.indexes()")
        for row in result.result_set:
            if row:
                schema.indexes.append(
                    {
                        "label": row[0] if len(row) > 0 else None,
                        "property": row[1] if len(row) > 1 else None,
                        "type": row[2] if len(row) > 2 else "BTREE",
                    }
                )
    except Exception:
        pass

    # Get constraints
    try:
        result = graph.query("CALL db.constraints()")
        for row in result.result_set:
            if row:
                schema.constraints.append(
                    {
                        "name": row[0] if len(row) > 0 else None,
                        "type": row[1] if len(row) > 1 else None,
                    }
                )
    except Exception:
        pass

    # Get counts
    try:
        result = graph.query("MATCH (n) RETURN count(n) AS count")
        if result.result_set:
            schema.node_count = result.result_set[0][0]
    except Exception:
        pass

    try:
        result = graph.query("MATCH ()-[r]->() RETURN count(r) AS count")
        if result.result_set:
            schema.edge_count = result.result_set[0][0]
    except Exception:
        pass

    # Get label counts
    for label in schema.labels:
        try:
            result = graph.query(f"MATCH (n:{label}) RETURN count(n) AS count")
            if result.result_set:
                schema.label_counts[label] = result.result_set[0][0]
        except Exception:
            pass

    # Get relationship type counts
    for rel_type in schema.relationship_types:
        try:
            result = graph.query(
                f"MATCH ()-[r:{rel_type}]->() RETURN count(r) AS count"
            )
            if result.result_set:
                schema.relationship_type_counts[rel_type] = result.result_set[0][0]
        except Exception:
            pass

    return schema


async def suggest_indexes_impl(
    queries: list[str],
    config: "ServerConfig",
) -> IndexSuggestionResult:
    """Analyze queries and suggest indexes."""
    result = IndexSuggestionResult()

    # Get current schema
    schema = await introspect_schema_impl(config)
    result.existing_indexes = schema.indexes

    # Analyze each query for index opportunities
    property_access_patterns: dict[tuple[str, str], int] = {}  # (label, prop) -> count

    for query in queries:
        patterns = _extract_index_patterns(query)
        for label, prop in patterns:
            key = (label, prop)
            property_access_patterns[key] = property_access_patterns.get(key, 0) + 1

    # Filter out patterns that already have indexes
    existing_index_keys = set()
    for idx in schema.indexes:
        if idx.get("label") and idx.get("property"):
            existing_index_keys.add((idx["label"], idx["property"]))

    # Generate suggestions
    for (label, prop), count in sorted(
        property_access_patterns.items(), key=lambda x: -x[1]
    ):
        if (label, prop) in existing_index_keys:
            result.analysis_notes.append(
                f"Index already exists for {label}.{prop}"
            )
            continue

        # Determine priority based on frequency and query patterns
        if count >= 5:
            priority = "high"
            estimated_impact = "Significant - frequently accessed property"
        elif count >= 2:
            priority = "medium"
            estimated_impact = "Moderate - occasionally accessed property"
        else:
            priority = "low"
            estimated_impact = "Minor - rarely accessed property"

        result.suggestions.append(
            IndexSuggestion(
                label=label,
                property_key=prop,
                reason=f"Property accessed in {count} queries with label filter",
                priority=priority,
                create_statement=f"CREATE INDEX ON :{label}({prop})",
                estimated_impact=estimated_impact,
            )
        )

    # Check for common missing indexes
    common_id_props = ["id", "uuid", "name", "email"]
    for label in schema.labels:
        for prop in common_id_props:
            if prop in schema.property_keys:
                if (label, prop) not in existing_index_keys:
                    if (label, prop) not in property_access_patterns:
                        result.analysis_notes.append(
                            f"Consider index on {label}.{prop} if used for lookups"
                        )

    return result


def _extract_index_patterns(query: str) -> list[tuple[str, str]]:
    """Extract label/property patterns that would benefit from indexes."""
    patterns = []

    # Pattern 1: WHERE n.prop = value with labeled node
    # Example: MATCH (n:Person) WHERE n.email = $email
    match_pattern = re.compile(
        r"MATCH\s+\((\w+):(\w+)\).*?WHERE\s+\1\.(\w+)\s*=",
        re.IGNORECASE | re.DOTALL,
    )
    for match in match_pattern.finditer(query):
        label = match.group(2)
        prop = match.group(3)
        patterns.append((label, prop))

    # Pattern 2: WHERE n.prop IN [...] with labeled node
    in_pattern = re.compile(
        r"MATCH\s+\((\w+):(\w+)\).*?WHERE\s+\1\.(\w+)\s+IN\s+",
        re.IGNORECASE | re.DOTALL,
    )
    for match in in_pattern.finditer(query):
        label = match.group(2)
        prop = match.group(3)
        patterns.append((label, prop))

    # Pattern 3: Property access in MERGE
    merge_pattern = re.compile(
        r"MERGE\s+\((\w+):(\w+)\s*\{(\w+):",
        re.IGNORECASE,
    )
    for match in merge_pattern.finditer(query):
        label = match.group(2)
        prop = match.group(3)
        patterns.append((label, prop))

    # Pattern 4: ORDER BY with label context
    # This is trickier - we'd need to track variable bindings
    order_pattern = re.compile(
        r"MATCH\s+\((\w+):(\w+)\).*?ORDER\s+BY\s+\1\.(\w+)",
        re.IGNORECASE | re.DOTALL,
    )
    for match in order_pattern.finditer(query):
        label = match.group(2)
        prop = match.group(3)
        patterns.append((label, prop))

    return patterns


# Public function wrappers
async def introspect_schema() -> SchemaInfo:
    """Return labels, relationship types, property keys, indexes, constraints."""
    from ..server import config

    return await introspect_schema_impl(config)


async def suggest_indexes(queries: list[str]) -> IndexSuggestionResult:
    """Analyze queries and suggest indexes for performance."""
    from ..server import config

    return await suggest_indexes_impl(queries, config)
