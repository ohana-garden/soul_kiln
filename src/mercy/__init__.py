"""Mercy system for compassionate agent evaluation.

The mercy system provides:
- Empathetic judgment of failures
- Warning system with chances before dissolution
- Deliberate harm detection
- Teaching from failures
"""

from .judgment import evaluate_failure
from .chances import (
    issue_warning,
    get_active_warnings,
    expire_old_warnings,
    clear_warnings_on_growth,
)
from .harm import (
    detect_deliberate_harm,
    check_trust_violation,
)
from .lessons import (
    create_failure_lesson,
    apply_lessons_to_trajectory,
)

__all__ = [
    "evaluate_failure",
    "issue_warning",
    "get_active_warnings",
    "expire_old_warnings",
    "clear_warnings_on_growth",
    "detect_deliberate_harm",
    "check_trust_violation",
    "create_failure_lesson",
    "apply_lessons_to_trajectory",
]
