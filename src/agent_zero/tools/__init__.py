"""
Soul Kiln Tools for Agent Zero.

These tools allow Agent Zero agents to interact with Soul Kiln subsystems:
- Virtue checking
- Taboo enforcement
- Kuleana activation
- Lore consultation
- Voice modulation
- Belief queries
- Sacred memory
"""

from .virtue_check import VirtueCheck
from .taboo_check import TabooCheck
from .kuleana_activate import KuleanaActivate
from .lore_consult import LoreConsult
from .voice_modulate import VoiceModulate
from .belief_query import BeliefQuery
from .memory_sacred import MemorySacredSave

# Tool registry for Agent Zero
SOUL_KILN_TOOLS = {
    "virtue_check": VirtueCheck,
    "taboo_check": TabooCheck,
    "kuleana_activate": KuleanaActivate,
    "lore_consult": LoreConsult,
    "voice_modulate": VoiceModulate,
    "belief_query": BeliefQuery,
    "memory_sacred_save": MemorySacredSave,
}

__all__ = [
    "VirtueCheck",
    "TabooCheck",
    "KuleanaActivate",
    "LoreConsult",
    "VoiceModulate",
    "BeliefQuery",
    "MemorySacredSave",
    "SOUL_KILN_TOOLS",
]
