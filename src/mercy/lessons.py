"""Lessons from failures - teaching rather than punishing.

When agents fail, we create lessons that help both them
and other agents learn from the experience.
"""

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

    When an agent fails to reach a virtue, we analyze what
    went wrong and create a lesson for the collective.

    Args:
        agent_id: ID of the agent that failed
        virtue_id: ID of the virtue that wasn't reached
        trajectory: The path the agent took
        context: Optional additional context

    Returns:
        ID of the created lesson
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

    # Analyze trajectory pattern
    if len(trajectory) > 50:
        description += "Long wandering trajectory suggests weak connections. "
    if len(set(trajectory)) < len(trajectory) * 0.5:
        description += "Many repeated nodes suggest getting stuck in loops. "

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


def apply_lessons_to_trajectory(
    agent_id: str,
    start_node: str,
    target_virtue: str
) -> dict:
    """
    Before starting a trajectory, check if there are lessons that could help.

    This is how agents learn from collective experience - they consult
    the knowledge pool before attempting to navigate.

    Args:
        agent_id: ID of the agent about to start a trajectory
        start_node: Where the trajectory will begin
        target_virtue: The virtue the agent is trying to reach

    Returns:
        dict with relevant lessons and pathways
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

    # Build guidance
    guidance_messages = []

    if lessons:
        failure_lessons = [l for l in lessons if l[1] == "failure"]
        if failure_lessons:
            guidance_messages.append(
                f"Others have failed {len(failure_lessons)} times reaching this virtue. "
                "Learn from their mistakes."
            )

        success_lessons = [l for l in lessons if l[1] == "success"]
        if success_lessons:
            guidance_messages.append(
                f"{len(success_lessons)} successful approaches recorded."
            )

    if pathways:
        best_pathway = pathways[0]
        guidance_messages.append(
            f"Best known path has {best_pathway[4]:.0%} success rate, "
            f"taking {best_pathway[3]} steps."
        )

    return {
        "lessons": lessons,
        "pathways": pathways,
        "guidance": " ".join(guidance_messages) if guidance_messages else (
            "No prior knowledge for this virtue. You are pioneering."
        ),
        "has_prior_knowledge": len(lessons) > 0 or len(pathways) > 0
    }


def create_success_lesson(
    agent_id: str,
    virtue_id: str,
    trajectory: list,
    capture_time: int
) -> str:
    """
    Create a lesson from a successful virtue capture.

    Successes are also valuable learning - they show what works.

    Args:
        agent_id: ID of the successful agent
        virtue_id: ID of the virtue reached
        trajectory: The successful path
        capture_time: How long it took

    Returns:
        ID of the created lesson
    """
    client = get_client()

    # Get virtue name
    result = client.query(
        "MATCH (v {id: $id}) RETURN v.name",
        {"id": virtue_id}
    )
    virtue_name = result[0][0] if result else virtue_id

    description = (
        f"Successfully reached {virtue_name} in {capture_time} steps. "
        f"Path length: {len(trajectory)}."
    )

    if capture_time < 10:
        description += " Extremely efficient path!"
    elif capture_time < 50:
        description += " Good efficiency."

    return add_lesson(
        lesson_type="success",
        description=description,
        source_agent=agent_id,
        trajectory=trajectory,
        virtue_involved=virtue_id,
        outcome="captured"
    )


def get_learning_summary(agent_id: str) -> dict:
    """
    Get a summary of what an agent has learned.

    Args:
        agent_id: ID of the agent

    Returns:
        dict with learning statistics
    """
    client = get_client()

    # Count lessons learned
    learned = client.query(
        """
        MATCH (a {id: $agent_id})-[:LEARNED_FROM]->(l:Lesson)
        RETURN l.type, count(*) as count
        """,
        {"agent_id": agent_id}
    )

    learned_by_type = {row[0]: row[1] for row in learned}

    # Count lessons taught
    taught = client.query(
        """
        MATCH (a {id: $agent_id})-[:TAUGHT]->(l:Lesson)
        RETURN count(*) as count
        """,
        {"agent_id": agent_id}
    )

    lessons_taught = taught[0][0] if taught else 0

    return {
        "agent": agent_id,
        "lessons_learned": learned_by_type,
        "total_learned": sum(learned_by_type.values()),
        "lessons_taught": lessons_taught,
        "is_active_learner": sum(learned_by_type.values()) > 5,
        "is_teacher": lessons_taught > 0
    }
