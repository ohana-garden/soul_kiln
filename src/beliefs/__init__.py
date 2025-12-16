"""
Belief Lattice — Internal Cosmology.

Beliefs form the agent's worldview—what it holds to be true
about reality and what matters.
"""

from .definitions import AMBASSADOR_BELIEFS, get_belief_definition

# Core operations require database connection - import separately when needed:
# from src.beliefs.core import (
#     create_belief,
#     get_belief,
#     challenge_belief,
#     confirm_belief,
#     revise_belief,
#     get_beliefs_by_type,
#     check_belief_coherence,
# )

__all__ = [
    "AMBASSADOR_BELIEFS",
    "get_belief_definition",
]
