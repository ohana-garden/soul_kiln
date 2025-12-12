"""Mercy system - empathy, warnings, and teaching over punishment."""

from .judgment import evaluate_failure
from .chances import issue_warning, get_active_warnings, expire_old_warnings, clear_warnings_on_growth
from .lessons import create_failure_lesson, apply_lessons_to_trajectory
from .harm import detect_deliberate_harm, check_trust_violation

__all__ = [
    "evaluate_failure",
    "issue_warning",
    "get_active_warnings",
    "expire_old_warnings",
    "clear_warnings_on_growth",
    "create_failure_lesson",
    "apply_lessons_to_trajectory",
    "detect_deliberate_harm",
    "check_trust_violation",
]
