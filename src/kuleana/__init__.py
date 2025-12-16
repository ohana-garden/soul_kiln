"""
Kuleana System — Duties, Roles, Responsibilities.

Kuleana (Hawaiian) represents responsibility as privilege—not burden
but meaningful relationship with what one serves.
"""

from .definitions import AMBASSADOR_KULEANAS, get_kuleana_definition

# Core operations require database connection - import separately when needed:
# from src.kuleana.core import (
#     create_kuleana,
#     get_kuleana,
#     activate_kuleana,
#     fulfill_kuleana,
#     check_kuleana_requirements,
#     get_active_kuleanas,
#     get_kuleanas_for_agent,
# )

__all__ = [
    "AMBASSADOR_KULEANAS",
    "get_kuleana_definition",
]
