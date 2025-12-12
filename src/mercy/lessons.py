"""Learning from failures - create and share lessons."""

from ..graph.client import get_client
from ..knowledge.pool import add_lesson, record_lesson_accessed
from ..knowledge.pathways import get_pathways_to_virtue


def create_failure_lesson(
    agent_id: str,
    virtue_id: str,
    trajectory: list,
    context: str = None
) -> str:
    """
    Create a lesson from a failure that others can learn from.
    """
    client = get_client()

    # Get virtue name
    result = client.query(
        "MATCH (v {id: $id}) RETURN v.name",
        {"id": virtue_id}
    )
    virtue_name = result[0][0] if result else virtue_id

    # Analyze trajectory - where did it go wrong?
    # Find the point where it diverged from known good paths
    good_paths = get_pathways_to_virtue(virtue_id, limit=3)

    description = f"Failed to reach {virtue_name}. "
    if good_paths:
        description += f"Known successful paths exist - compare trajectories. "
    description += f"Trajectory length: {len(trajectory)}. "
    if context:
        description += f"Context: {context}"

    lesson_id = add_lesson(
        lesson_type="failure",
        description=description,
        source_agent=agent_id,
        trajectory=trajectory,
        virtue_involved=virtue_id,
        outcome="escaped_basin"
    )

    return lesson_id


def apply_lessons_to_trajectory(agent_id: str, start_node: str, target_virtue: str) -> dict:
    """
    Before starting a trajectory, check if there are lessons that could help.
    This is how agents learn from the collective experience.
    """
    client = get_client()

    # Get relevant lessons
    lessons = client.query(
        """
        MATCH (l:Lesson)-[:ABOUT]->(v {id: $virtue_id})
        WHERE l.type IN ['failure', 'success', 'warning']
        RETURN l.id, l.type, l.description, l.trajectory_summary
        ORDER BY l.times_accessed DESC
        LIMIT 5
        """,
        {"virtue_id": target_virtue}
    )

    # Record that agent is learning from these
    for lesson in lessons:
        record_lesson_accessed(lesson[0], agent_id)

    # Get successful pathways
    pathways = get_pathways_to_virtue(target_virtue, limit=3)

    return {
        "lessons": lessons,
        "pathways": pathways,
        "guidance": "Learn from others' experiences. Failures show what to avoid; successes show what works."
    }
