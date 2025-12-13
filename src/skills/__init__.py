"""
Skill Forge — Competency Engine.

Skills are how agents do things. They connect to tools
and require specific virtues to be active.
"""

from .core import (
    create_skill,
    get_skill,
    use_skill,
    update_mastery,
    check_skill_prerequisites,
    get_skills_for_agent,
    decay_unused_skills,
)
from .definitions import AMBASSADOR_SKILLS, get_skill_definition

__all__ = [
    "create_skill",
    "get_skill",
    "use_skill",
    "update_mastery",
    "check_skill_prerequisites",
    "get_skills_for_agent",
    "decay_unused_skills",
    "AMBASSADOR_SKILLS",
    "get_skill_definition",
]
