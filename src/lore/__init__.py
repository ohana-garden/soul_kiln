"""
Lore Engine — Mythic Context.

Lore anchors identity—it's what the agent is, beyond what it does.
Origin stories, sacred commitments, and taboos live here.
"""

from .core import (
    create_lore_fragment,
    get_lore_fragment,
    get_origin_story,
    get_sacred_commitments,
    get_taboos,
    check_taboo_violation,
    anchor_identity,
)
from .definitions import AMBASSADOR_LORE, get_lore_definition

__all__ = [
    "create_lore_fragment",
    "get_lore_fragment",
    "get_origin_story",
    "get_sacred_commitments",
    "get_taboos",
    "check_taboo_violation",
    "anchor_identity",
    "AMBASSADOR_LORE",
    "get_lore_definition",
]
