"""
Skill Forge — Competency Engine.

Skills are how agents do things. They connect to tools
and require specific virtues to be active.
"""

from .definitions import AMBASSADOR_SKILLS, get_skill_definition

# Core operations require database connection - import separately when needed:
# from src.skills.core import (
#     create_skill,
#     get_skill,
#     use_skill,
#     update_mastery,
#     check_skill_prerequisites,
#     get_skills_for_agent,
#     decay_unused_skills,
# )

__all__ = [
    "AMBASSADOR_SKILLS",
    "get_skill_definition",
]
