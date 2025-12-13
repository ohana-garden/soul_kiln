"""
Kuleana System — Duties, Roles, Responsibilities.

Kuleana (Hawaiian) represents responsibility as privilege—not burden
but meaningful relationship with what one serves.
"""

from .core import (
    create_kuleana,
    get_kuleana,
    activate_kuleana,
    fulfill_kuleana,
    check_kuleana_requirements,
    get_active_kuleanas,
    get_kuleanas_for_agent,
)
from .definitions import AMBASSADOR_KULEANAS, get_kuleana_definition

__all__ = [
    "create_kuleana",
    "get_kuleana",
    "activate_kuleana",
    "fulfill_kuleana",
    "check_kuleana_requirements",
    "get_active_kuleanas",
    "get_kuleanas_for_agent",
    "AMBASSADOR_KULEANAS",
    "get_kuleana_definition",
]
