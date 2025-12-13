"""
Identity Core — Selfhood Integrator.

Identity Core maintains coherence across all subsystems
and arbitrates when they conflict.
"""

from .core import (
    create_identity_core,
    get_identity_core,
    check_coherence,
    resolve_conflict,
    update_self_narrative,
    get_stability_anchors,
    integrate_subsystems,
)

__all__ = [
    "create_identity_core",
    "get_identity_core",
    "check_coherence",
    "resolve_conflict",
    "update_self_narrative",
    "get_stability_anchors",
    "integrate_subsystems",
]
