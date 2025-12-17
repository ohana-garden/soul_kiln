"""
Conversational Intake System for Agent Creation.

Provides a 100% conversational UX for creating agents:
1. Intake conversation understands user needs
2. Matches to appropriate community
3. Creates agent with proper context
4. Hands off to the new agent
"""

from .conversation import IntakeConversation, ConversationState
from .factory import AgentFactory, AgentConfig
from .prompts import load_prompt, load_community_prompts

__all__ = [
    "IntakeConversation",
    "ConversationState",
    "AgentFactory",
    "AgentConfig",
    "load_prompt",
    "load_community_prompts",
]
