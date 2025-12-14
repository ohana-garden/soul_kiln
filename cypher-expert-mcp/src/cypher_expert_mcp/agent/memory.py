"""Query memory and learning for the Cypher expert agent."""

from __future__ import annotations

import json
import sqlite3
from dataclasses import dataclass, field, asdict
from datetime import datetime
from pathlib import Path
from typing import Any


@dataclass
class QueryRecord:
    """Record of a query generation interaction."""

    request: str
    generated_query: str
    schema_snapshot: dict[str, Any] | None = None
    query_plan: dict[str, Any] | None = None
    execution_time_ms: float | None = None
    success: bool = True
    user_feedback: str | None = None  # "thumbs_up", "thumbs_down", "edited"
    edited_query: str | None = None
    timestamp: str = field(default_factory=lambda: datetime.utcnow().isoformat())
    id: int | None = None

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for storage."""
        return {
            "request": self.request,
            "generated_query": self.generated_query,
            "schema_snapshot": json.dumps(self.schema_snapshot) if self.schema_snapshot else None,
            "query_plan": json.dumps(self.query_plan) if self.query_plan else None,
            "execution_time_ms": self.execution_time_ms,
            "success": self.success,
            "user_feedback": self.user_feedback,
            "edited_query": self.edited_query,
            "timestamp": self.timestamp,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "QueryRecord":
        """Create from dictionary."""
        return cls(
            id=data.get("id"),
            request=data["request"],
            generated_query=data["generated_query"],
            schema_snapshot=json.loads(data["schema_snapshot"]) if data.get("schema_snapshot") else None,
            query_plan=json.loads(data["query_plan"]) if data.get("query_plan") else None,
            execution_time_ms=data.get("execution_time_ms"),
            success=data.get("success", True),
            user_feedback=data.get("user_feedback"),
            edited_query=data.get("edited_query"),
            timestamp=data.get("timestamp", datetime.utcnow().isoformat()),
        )


@dataclass
class LearnedPattern:
    """A pattern learned from query interactions."""

    pattern_type: str  # "optimization", "structure", "error_fix"
    description: str
    original_pattern: str
    improved_pattern: str
    frequency: int = 1
    success_rate: float = 1.0
    created_at: str = field(default_factory=lambda: datetime.utcnow().isoformat())
    last_used: str = field(default_factory=lambda: datetime.utcnow().isoformat())


class QueryMemory:
    """Persistent memory for query generation learning."""

    def __init__(self, db_path: str | Path | None = None):
        """Initialize query memory.

        Args:
            db_path: Path to SQLite database. If None, uses in-memory DB.
        """
        if db_path is None:
            self.db_path = ":memory:"
        else:
            self.db_path = str(db_path)

        self._init_db()

    def _init_db(self):
        """Initialize database schema."""
        with self._get_connection() as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS query_records (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    request TEXT NOT NULL,
                    generated_query TEXT NOT NULL,
                    schema_snapshot TEXT,
                    query_plan TEXT,
                    execution_time_ms REAL,
                    success INTEGER DEFAULT 1,
                    user_feedback TEXT,
                    edited_query TEXT,
                    timestamp TEXT NOT NULL
                )
            """)

            conn.execute("""
                CREATE TABLE IF NOT EXISTS learned_patterns (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    pattern_type TEXT NOT NULL,
                    description TEXT NOT NULL,
                    original_pattern TEXT NOT NULL,
                    improved_pattern TEXT NOT NULL,
                    frequency INTEGER DEFAULT 1,
                    success_rate REAL DEFAULT 1.0,
                    created_at TEXT NOT NULL,
                    last_used TEXT NOT NULL
                )
            """)

            # Index for searching similar requests
            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_request ON query_records(request)
            """)

            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_feedback ON query_records(user_feedback)
            """)

            conn.commit()

    def _get_connection(self) -> sqlite3.Connection:
        """Get database connection."""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    def record(
        self,
        request: str,
        generated_query: str,
        schema_snapshot: dict[str, Any] | None = None,
        query_plan: dict[str, Any] | None = None,
        execution_time_ms: float | None = None,
        success: bool = True,
    ) -> int:
        """Record a query generation interaction.

        Returns:
            The ID of the created record.
        """
        record = QueryRecord(
            request=request,
            generated_query=generated_query,
            schema_snapshot=schema_snapshot,
            query_plan=query_plan,
            execution_time_ms=execution_time_ms,
            success=success,
        )

        with self._get_connection() as conn:
            cursor = conn.execute(
                """
                INSERT INTO query_records
                (request, generated_query, schema_snapshot, query_plan,
                 execution_time_ms, success, timestamp)
                VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    record.request,
                    record.generated_query,
                    json.dumps(record.schema_snapshot) if record.schema_snapshot else None,
                    json.dumps(record.query_plan) if record.query_plan else None,
                    record.execution_time_ms,
                    1 if record.success else 0,
                    record.timestamp,
                ),
            )
            conn.commit()
            return cursor.lastrowid

    def add_feedback(
        self,
        record_id: int,
        feedback: str,
        edited_query: str | None = None,
    ):
        """Add user feedback to a query record.

        Args:
            record_id: The ID of the record to update.
            feedback: "thumbs_up", "thumbs_down", or "edited".
            edited_query: The user's corrected query if feedback is "edited".
        """
        with self._get_connection() as conn:
            conn.execute(
                """
                UPDATE query_records
                SET user_feedback = ?, edited_query = ?
                WHERE id = ?
                """,
                (feedback, edited_query, record_id),
            )
            conn.commit()

            # If user edited the query, try to learn from it
            if feedback == "edited" and edited_query:
                self._learn_from_edit(record_id, edited_query)

    def _learn_from_edit(self, record_id: int, edited_query: str):
        """Learn from a user's query edit."""
        with self._get_connection() as conn:
            row = conn.execute(
                "SELECT request, generated_query FROM query_records WHERE id = ?",
                (record_id,),
            ).fetchone()

            if row:
                # Store as a learned pattern
                self.add_learned_pattern(
                    pattern_type="user_correction",
                    description=f"User correction for: {row['request'][:100]}",
                    original_pattern=row["generated_query"],
                    improved_pattern=edited_query,
                )

    def get_similar_queries(
        self,
        request: str,
        limit: int = 5,
        successful_only: bool = True,
    ) -> list[QueryRecord]:
        """Find similar past queries for few-shot learning.

        Uses simple keyword matching. Could be enhanced with embeddings.
        """
        # Extract keywords from request
        keywords = set(request.lower().split())
        keywords -= {"the", "a", "an", "to", "for", "of", "in", "on", "with", "and", "or"}

        with self._get_connection() as conn:
            # Get recent successful queries
            query = """
                SELECT * FROM query_records
                WHERE success = 1
            """
            if successful_only:
                query += " AND (user_feedback IS NULL OR user_feedback != 'thumbs_down')"

            query += " ORDER BY timestamp DESC LIMIT 100"

            rows = conn.execute(query).fetchall()

            # Score by keyword overlap
            scored = []
            for row in rows:
                row_keywords = set(row["request"].lower().split())
                overlap = len(keywords & row_keywords)
                if overlap > 0:
                    scored.append((overlap, QueryRecord.from_dict(dict(row))))

            # Return top matches
            scored.sort(key=lambda x: -x[0])
            return [record for _, record in scored[:limit]]

    def add_learned_pattern(
        self,
        pattern_type: str,
        description: str,
        original_pattern: str,
        improved_pattern: str,
    ):
        """Add a learned pattern to the knowledge base."""
        with self._get_connection() as conn:
            # Check if similar pattern exists
            existing = conn.execute(
                """
                SELECT id, frequency FROM learned_patterns
                WHERE pattern_type = ? AND original_pattern = ?
                """,
                (pattern_type, original_pattern),
            ).fetchone()

            if existing:
                # Update frequency
                conn.execute(
                    """
                    UPDATE learned_patterns
                    SET frequency = frequency + 1, last_used = ?
                    WHERE id = ?
                    """,
                    (datetime.utcnow().isoformat(), existing["id"]),
                )
            else:
                # Insert new pattern
                conn.execute(
                    """
                    INSERT INTO learned_patterns
                    (pattern_type, description, original_pattern, improved_pattern,
                     created_at, last_used)
                    VALUES (?, ?, ?, ?, ?, ?)
                    """,
                    (
                        pattern_type,
                        description,
                        original_pattern,
                        improved_pattern,
                        datetime.utcnow().isoformat(),
                        datetime.utcnow().isoformat(),
                    ),
                )

            conn.commit()

    def get_learned_patterns(
        self,
        pattern_type: str | None = None,
        min_frequency: int = 1,
        limit: int = 20,
    ) -> list[LearnedPattern]:
        """Get learned patterns from the knowledge base."""
        with self._get_connection() as conn:
            query = """
                SELECT * FROM learned_patterns
                WHERE frequency >= ?
            """
            params: list[Any] = [min_frequency]

            if pattern_type:
                query += " AND pattern_type = ?"
                params.append(pattern_type)

            query += " ORDER BY frequency DESC, last_used DESC LIMIT ?"
            params.append(limit)

            rows = conn.execute(query, params).fetchall()

            return [
                LearnedPattern(
                    pattern_type=row["pattern_type"],
                    description=row["description"],
                    original_pattern=row["original_pattern"],
                    improved_pattern=row["improved_pattern"],
                    frequency=row["frequency"],
                    success_rate=row["success_rate"],
                    created_at=row["created_at"],
                    last_used=row["last_used"],
                )
                for row in rows
            ]

    def get_statistics(self) -> dict[str, Any]:
        """Get statistics about query memory."""
        with self._get_connection() as conn:
            total = conn.execute(
                "SELECT COUNT(*) FROM query_records"
            ).fetchone()[0]

            successful = conn.execute(
                "SELECT COUNT(*) FROM query_records WHERE success = 1"
            ).fetchone()[0]

            with_feedback = conn.execute(
                "SELECT COUNT(*) FROM query_records WHERE user_feedback IS NOT NULL"
            ).fetchone()[0]

            thumbs_up = conn.execute(
                "SELECT COUNT(*) FROM query_records WHERE user_feedback = 'thumbs_up'"
            ).fetchone()[0]

            patterns = conn.execute(
                "SELECT COUNT(*) FROM learned_patterns"
            ).fetchone()[0]

            return {
                "total_queries": total,
                "successful_queries": successful,
                "success_rate": successful / total if total > 0 else 0,
                "queries_with_feedback": with_feedback,
                "positive_feedback": thumbs_up,
                "learned_patterns": patterns,
            }

    def analyze_failures(self) -> list[dict[str, Any]]:
        """Analyze failed queries to identify improvement opportunities."""
        with self._get_connection() as conn:
            failures = conn.execute(
                """
                SELECT request, generated_query, user_feedback, edited_query
                FROM query_records
                WHERE success = 0 OR user_feedback = 'thumbs_down'
                ORDER BY timestamp DESC
                LIMIT 50
                """
            ).fetchall()

            analysis = []
            for row in failures:
                analysis.append({
                    "request": row["request"],
                    "generated_query": row["generated_query"],
                    "feedback": row["user_feedback"],
                    "correction": row["edited_query"],
                })

            return analysis

    def export_training_data(self) -> list[dict[str, str]]:
        """Export successful queries as training data."""
        with self._get_connection() as conn:
            rows = conn.execute(
                """
                SELECT request, generated_query, edited_query, user_feedback
                FROM query_records
                WHERE success = 1
                  AND (user_feedback IS NULL OR user_feedback != 'thumbs_down')
                ORDER BY
                    CASE WHEN user_feedback = 'thumbs_up' THEN 0 ELSE 1 END,
                    timestamp DESC
                LIMIT 500
                """
            ).fetchall()

            training_data = []
            for row in rows:
                # Use edited query if available, otherwise generated
                query = row["edited_query"] or row["generated_query"]
                training_data.append({
                    "request": row["request"],
                    "query": query,
                })

            return training_data
