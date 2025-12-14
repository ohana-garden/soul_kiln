"""
Community Definitions.

Pre-defined communities that can be instantiated in soul_kiln.
Each community has:
- A specific purpose
- Virtue emphasis aligned with that purpose
- Associated tools
"""

from .grant_getter import create_grant_getter_community, GRANT_GETTER_TOOLS

__all__ = [
    "create_grant_getter_community",
    "GRANT_GETTER_TOOLS",
]
