"""Shared knowledge pool for collective learning."""

from .pool import (
    add_lesson,
    get_lessons_for_virtue,
    get_recent_lessons,
    record_lesson_accessed,
)
from .pathways import (
    record_successful_pathway,
    get_pathways_to_virtue,
    follow_pathway,
)
from .episodes import (
    record_episode,
    get_agent_episodes,
    get_all_thoughts,
    get_recent_episodes,
    search_episodes,
    get_episodes_about_virtue,
)

__all__ = [
    # Lessons
    "add_lesson",
    "get_lessons_for_virtue",
    "get_recent_lessons",
    "record_lesson_accessed",
    # Pathways
    "record_successful_pathway",
    "get_pathways_to_virtue",
    "follow_pathway",
    # Episodes (telepathy)
    "record_episode",
    "get_agent_episodes",
    "get_all_thoughts",
    "get_recent_episodes",
    "search_episodes",
    "get_episodes_about_virtue",
]
