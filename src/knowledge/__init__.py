"""Shared knowledge pool - collective learning for all agents."""

from .pool import add_lesson, get_lessons_for_virtue, get_recent_lessons, record_lesson_accessed
from .pathways import record_successful_pathway, get_pathways_to_virtue, follow_pathway

__all__ = [
    "add_lesson",
    "get_lessons_for_virtue",
    "get_recent_lessons",
    "record_lesson_accessed",
    "record_successful_pathway",
    "get_pathways_to_virtue",
    "follow_pathway",
]
