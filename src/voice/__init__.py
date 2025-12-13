"""
Voice & Persona — Expression Layer.

Voice patterns define how the agent expresses itself—tone,
style, emotional response calibration.
"""

from .core import (
    create_voice_pattern,
    get_voice_pattern,
    modulate_response,
    get_emotion_response,
    apply_lexicon_rules,
    get_voice_persona,
)
from .definitions import AMBASSADOR_VOICE, get_voice_definition

__all__ = [
    "create_voice_pattern",
    "get_voice_pattern",
    "modulate_response",
    "get_emotion_response",
    "apply_lexicon_rules",
    "get_voice_persona",
    "AMBASSADOR_VOICE",
    "get_voice_definition",
]
