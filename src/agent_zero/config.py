"""
Ambassador Agent Configuration for Agent Zero.

Configures the Agent Zero runtime with Soul Kiln subsystems.
"""

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional


@dataclass
class AmbassadorConfig:
    """Configuration for an Ambassador agent running on Agent Zero."""

    # Identity
    agent_id: str = ""
    student_id: str = ""

    # Model configuration (uses Agent Zero's model system)
    chat_model_provider: str = "anthropic"
    chat_model_name: str = "claude-3-5-sonnet-20241022"

    # Soul Kiln subsystem weights for coherence
    subsystem_weights: Dict[str, float] = field(default_factory=lambda: {
        "soul_kiln": 0.95,      # Virtue basin - highest weight
        "lore": 0.90,           # Identity lore
        "kuleana": 0.85,        # Duties/responsibilities
        "beliefs": 0.80,        # Worldview
        "memory": 0.75,         # Episodic memory
        "voice": 0.70,          # Communication patterns
        "skills": 0.65,         # Competencies
    })

    # Virtue basin configuration
    virtue_check_on_every_action: bool = True
    virtue_basin_sync_interval: int = 10  # Steps between full syncs

    # Memory configuration
    memory_decay_enabled: bool = True
    sacred_memory_ids: List[str] = field(default_factory=list)

    # Tool access
    enabled_tools: List[str] = field(default_factory=lambda: [
        # Soul Kiln tools
        "virtue_check",
        "kuleana_activate",
        "taboo_check",
        "lore_consult",
        "voice_modulate",
        "belief_query",
        "memory_sacred_save",

        # Standard Agent Zero tools
        "search_engine",
        "code_execution_tool",
        "memory_save",
        "memory_load",
        "call_subordinate",
        "response",
    ])

    # Kuleana (duty) priorities - overrides for specific sessions
    kuleana_overrides: Dict[str, int] = field(default_factory=dict)

    # Voice modulation settings
    default_voice_intensity: float = 0.7
    emotion_response_enabled: bool = True

    # Additional settings
    additional: Dict[str, Any] = field(default_factory=dict)

    def to_agent_zero_settings(self) -> Dict[str, Any]:
        """Convert to Agent Zero settings format."""
        return {
            "chat_model_provider": self.chat_model_provider,
            "chat_model_name": self.chat_model_name,
            "chat_model_api_base": "",
            "chat_model_ctx_length": 200000,
            "chat_model_vision": True,
            "chat_model_rl_requests": 0,
            "chat_model_rl_input": 0,
            "chat_model_rl_output": 0,
            "chat_model_kwargs": {},

            "util_model_provider": self.chat_model_provider,
            "util_model_name": self.chat_model_name,
            "util_model_api_base": "",
            "util_model_ctx_length": 200000,
            "util_model_rl_requests": 0,
            "util_model_rl_input": 0,
            "util_model_rl_output": 0,
            "util_model_kwargs": {},

            "embed_model_provider": "openai",
            "embed_model_name": "text-embedding-3-small",
            "embed_model_api_base": "",
            "embed_model_rl_requests": 0,
            "embed_model_kwargs": {},

            "browser_model_provider": self.chat_model_provider,
            "browser_model_name": self.chat_model_name,
            "browser_model_api_base": "",
            "browser_model_vision": True,
            "browser_model_kwargs": {},

            "agent_profile": "ambassador",
            "agent_memory_subdir": f"ambassador_{self.agent_id}",
            "agent_knowledge_subdir": "financial_aid",
            "mcp_servers": "",
            "browser_http_headers": {},
        }


# Default Ambassador configuration
DEFAULT_AMBASSADOR_CONFIG = AmbassadorConfig()
