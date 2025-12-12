"""Shared knowledge pool operations - lessons from failures and successes."""

from datetime import datetime
import uuid

from ..graph.client import get_client
from ..graph.queries import create_node, create_edge


def add_lesson(
    lesson_type: str,
    description: str,
    source_agent: str,
    trajectory: list = None,
    virtue_involved: str = None,
    outcome: str = None
) -> str:
    """
    Add a lesson to the shared knowledge pool.
    Lessons are learnings from failures or successes.
    """
    client = get_client()
    lesson_id = f"lesson_{uuid.uuid4().hex[:8]}"

    create_node("Lesson", {
        "id": lesson_id,
        "type": lesson_type,  # "failure", "success", "warning", "trust_warning"
        "description": description,
        "source_agent": source_agent,
        "virtue_involved": virtue_involved,
        "outcome": outcome,
        "trajectory_summary": ",".join(trajectory[:10]) if trajectory else None,
        "times_accessed": 0
    })

    # Connect to source agent
    create_edge(source_agent, lesson_id, "TAUGHT")

    # Connect to virtue if relevant
    if virtue_involved:
        create_edge(lesson_id, virtue_involved, "ABOUT")

    return lesson_id


def get_lessons_for_virtue(virtue_id: str, limit: int = 10) -> list:
    """Get lessons related to a specific virtue."""
    client = get_client()
    return client.query(
        """
        MATCH (l:Lesson)-[:ABOUT]->(v {id: $virtue_id})
        RETURN l.id, l.type, l.description, l.outcome, l.times_accessed
        ORDER BY l.created_at DESC
        LIMIT $limit
        """,
        {"virtue_id": virtue_id, "limit": limit}
    )


def get_recent_lessons(limit: int = 20) -> list:
    """Get most recent lessons from the pool."""
    client = get_client()
    return client.query(
        """
        MATCH (l:Lesson)
        RETURN l.id, l.type, l.description, l.virtue_involved, l.source_agent
        ORDER BY l.created_at DESC
        LIMIT $limit
        """,
        {"limit": limit}
    )


def record_lesson_accessed(lesson_id: str, by_agent: str):
    """Record that an agent accessed/learned from a lesson."""
    client = get_client()
    client.execute(
        """
        MATCH (l:Lesson {id: $lesson_id})
        SET l.times_accessed = l.times_accessed + 1,
            l.last_accessed = $now
        """,
        {"lesson_id": lesson_id, "now": datetime.utcnow().isoformat()}
    )

    # Create edge showing agent learned from this
    create_edge(by_agent, lesson_id, "LEARNED_FROM")
