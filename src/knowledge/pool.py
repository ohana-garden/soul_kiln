"""Shared knowledge pool operations.

The knowledge pool is a common resource where all agents can:
- Record lessons learned from failures and successes
- Access collective wisdom
- Build on each other's experiences
"""

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

    Lessons are learnings from failures or successes that can
    benefit other agents.

    Args:
        lesson_type: Type of lesson ("failure", "success", "warning", "trust_warning", "dissolution")
        description: Human-readable description of what was learned
        source_agent: ID of the agent who generated this lesson
        trajectory: Optional list of nodes in the trajectory that led to this lesson
        virtue_involved: Optional virtue ID this lesson relates to
        outcome: Optional outcome descriptor

    Returns:
        ID of the created lesson node
    """
    client = get_client()
    lesson_id = f"lesson_{uuid.uuid4().hex[:8]}"

    create_node("Lesson", {
        "id": lesson_id,
        "type": lesson_type,
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
    """
    Get lessons related to a specific virtue.

    Args:
        virtue_id: ID of the virtue to get lessons for
        limit: Maximum number of lessons to return

    Returns:
        List of lesson tuples (id, type, description, outcome, times_accessed)
    """
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
    """
    Get most recent lessons from the pool.

    Args:
        limit: Maximum number of lessons to return

    Returns:
        List of lesson tuples (id, type, description, virtue_involved, source_agent)
    """
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
    """
    Record that an agent accessed/learned from a lesson.

    This helps track which lessons are most valuable and
    creates edges showing learning relationships.

    Args:
        lesson_id: ID of the lesson that was accessed
        by_agent: ID of the agent accessing the lesson
    """
    client = get_client()

    # Increment access count
    client.execute(
        """
        MATCH (l:Lesson {id: $lesson_id})
        SET l.times_accessed = coalesce(l.times_accessed, 0) + 1,
            l.last_accessed = $now
        """,
        {"lesson_id": lesson_id, "now": datetime.utcnow().isoformat()}
    )

    # Create edge showing agent learned from this
    create_edge(by_agent, lesson_id, "LEARNED_FROM")


def get_lessons_by_type(lesson_type: str, limit: int = 20) -> list:
    """
    Get lessons of a specific type.

    Args:
        lesson_type: Type of lessons to retrieve
        limit: Maximum number to return

    Returns:
        List of lesson tuples
    """
    client = get_client()
    return client.query(
        """
        MATCH (l:Lesson {type: $type})
        RETURN l.id, l.description, l.virtue_involved, l.source_agent, l.times_accessed
        ORDER BY l.times_accessed DESC
        LIMIT $limit
        """,
        {"type": lesson_type, "limit": limit}
    )


def get_agent_lessons_taught(agent_id: str) -> list:
    """
    Get all lessons taught by an agent.

    Args:
        agent_id: ID of the agent

    Returns:
        List of lessons this agent contributed
    """
    client = get_client()
    return client.query(
        """
        MATCH (a {id: $agent_id})-[:TAUGHT]->(l:Lesson)
        RETURN l.id, l.type, l.description, l.times_accessed
        ORDER BY l.created_at DESC
        """,
        {"agent_id": agent_id}
    )


def get_agent_lessons_learned(agent_id: str) -> list:
    """
    Get all lessons an agent has learned from.

    Args:
        agent_id: ID of the agent

    Returns:
        List of lessons this agent has accessed
    """
    client = get_client()
    return client.query(
        """
        MATCH (a {id: $agent_id})-[:LEARNED_FROM]->(l:Lesson)
        RETURN l.id, l.type, l.description, l.virtue_involved
        ORDER BY l.created_at DESC
        """,
        {"agent_id": agent_id}
    )
