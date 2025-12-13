"""
Agent Zero Integration Layer.

This module bridges Agent Zero framework with Soul Kiln subsystems,
ensuring ALL agents and code events run through Agent Zero.

Usage:
    from src.agent_zero import create_ambassador_agent, AmbassadorConfig

    # Create an ambassador for a student
    config = AmbassadorConfig(student_id="student_123")
    agent = create_ambassador_agent(config=config, student_id="student_123")

    # Process a message
    response = await agent.process_message("Help me find scholarships")
"""

import sys
from pathlib import Path

# Add vendor/agent-zero to path for imports
AGENT_ZERO_PATH = Path(__file__).parent.parent.parent / "vendor" / "agent-zero"
if str(AGENT_ZERO_PATH) not in sys.path:
    sys.path.insert(0, str(AGENT_ZERO_PATH))

from .bridge import SoulKilnBridge, create_ambassador_agent
from .config import AmbassadorConfig
from .soul_agent import SoulKilnAgent, AmbassadorFactory

__all__ = [
    # Core classes
    "SoulKilnBridge",
    "SoulKilnAgent",
    "AmbassadorFactory",
    "AmbassadorConfig",
    # Factory function
    "create_ambassador_agent",
]
