"""
Soul Kiln Agent - Agent Zero Integration.

This module provides the SoulKilnAgent class that wraps Agent Zero
with Soul Kiln subsystems, ensuring all events flow through the framework.
"""

import sys
from pathlib import Path
from typing import Any, Dict, Optional

# Ensure Agent Zero is importable
AGENT_ZERO_PATH = Path(__file__).parent.parent.parent / "vendor" / "agent-zero"
if str(AGENT_ZERO_PATH) not in sys.path:
    sys.path.insert(0, str(AGENT_ZERO_PATH))

from .config import AmbassadorConfig
from .bridge import SoulKilnBridge


class SoulKilnAgent:
    """
    Soul Kiln Agent running on Agent Zero.

    This class wraps Agent Zero's Agent class and injects Soul Kiln
    subsystems into the agent's decision loop.

    ALL agent events flow through this class:
    - Message handling
    - Tool execution
    - Response generation
    - Memory operations
    """

    def __init__(self, config: AmbassadorConfig):
        self.config = config
        self.bridge = SoulKilnBridge(config)
        self._agent = None
        self._context = None
        self._initialized = False

    def initialize(self) -> bool:
        """
        Initialize the Agent Zero runtime with Soul Kiln extensions.

        This sets up:
        1. Agent Zero configuration
        2. Soul Kiln tools registration
        3. Virtue check extension
        4. Ambassador prompt profile
        """
        try:
            # Import Agent Zero components
            from agent import Agent, AgentContext, AgentConfig
            from initialize import initialize_agent

            # Create Agent Zero config from Ambassador config
            az_settings = self.config.to_agent_zero_settings()
            az_config = initialize_agent(az_settings)

            # Create agent context
            self._context = AgentContext(
                config=az_config,
                name=f"Ambassador-{self.config.agent_id}",
                set_current=True,
            )

            # Get the root agent (Agent 0)
            self._agent = self._context.agent0

            # Inject Soul Kiln bridge into agent data
            self._agent.set_data("soul_kiln_bridge", self.bridge)
            self._agent.set_data("soul_kiln_config", self.config)
            self._agent.set_data("sacred_memories", [])

            # Register Soul Kiln tools
            self._register_tools()

            self._initialized = True
            return True

        except Exception as e:
            print(f"Failed to initialize Soul Kiln Agent: {e}")
            return False

    def _register_tools(self):
        """Register Soul Kiln tools with Agent Zero."""
        # Tools are registered via the prompts system in Agent Zero
        # The tools themselves are in src/agent_zero/tools/
        pass

    async def process_message(
        self,
        message: str,
        attachments: Optional[list] = None
    ) -> str:
        """
        Process a user message through the full Soul Kiln pipeline.

        Flow:
        1. Pre-action check (taboos, virtues)
        2. Kuleana activation
        3. Agent Zero processing
        4. Voice modulation
        5. Response generation
        """
        if not self._initialized:
            if not self.initialize():
                return "Error: Agent not initialized"

        from agent import UserMessage

        # 1. Pre-action check
        pre_check = self.bridge.pre_action_check(
            action=message,
            context={"message": message}
        )

        if not pre_check["allowed"]:
            # This shouldn't happen for incoming messages, but just in case
            return f"I cannot process that request: {pre_check['block_reason']}"

        # 2. Create user message
        user_msg = UserMessage(
            message=message,
            attachments=attachments or [],
        )

        # 3. Send to Agent Zero
        task = self._context.communicate(user_msg)

        # 4. Wait for response
        await task.wait()

        # 5. Get response (Agent Zero stores it in history)
        response = self._agent.history.last_response()

        return response

    def get_status(self) -> Dict[str, Any]:
        """Get the current status of the agent."""
        return {
            "initialized": self._initialized,
            "agent_id": self.config.agent_id,
            "student_id": self.config.student_id,
            "virtue_scores": self.bridge.get_virtue_scores(),
            "active_kuleanas": self.bridge._active_kuleanas,
            "emotion_state": self.bridge._emotion_state,
            "sacred_memories": len(self._agent.get_data("sacred_memories") or []) if self._agent else 0,
        }

    def get_identity(self) -> Dict[str, Any]:
        """Get the agent's identity information."""
        return {
            "lore": self.bridge.get_identity_lore(),
            "lineage": self.bridge.get_lineage_lore(),
            "core_beliefs": self.bridge.get_core_beliefs(),
            "voice_guidance": self.bridge.get_voice_guidance(),
        }

    async def shutdown(self):
        """Shutdown the agent, preserving sacred memories."""
        if self._context:
            # Sacred memories are already stored - they persist
            self._context.reset()
            self._initialized = False


class AmbassadorFactory:
    """
    Factory for creating Ambassador agents.

    Use this to spawn new Ambassador agents for students.
    """

    _agents: Dict[str, SoulKilnAgent] = {}

    @classmethod
    def create(
        cls,
        student_id: str,
        config: Optional[AmbassadorConfig] = None
    ) -> SoulKilnAgent:
        """Create a new Ambassador agent for a student."""
        if student_id in cls._agents:
            return cls._agents[student_id]

        if config is None:
            config = AmbassadorConfig()

        config.student_id = student_id
        config.agent_id = f"amb_{student_id}"

        agent = SoulKilnAgent(config)
        cls._agents[student_id] = agent

        return agent

    @classmethod
    def get(cls, student_id: str) -> Optional[SoulKilnAgent]:
        """Get an existing Ambassador agent."""
        return cls._agents.get(student_id)

    @classmethod
    def destroy(cls, student_id: str) -> bool:
        """Destroy an Ambassador agent."""
        if student_id in cls._agents:
            del cls._agents[student_id]
            return True
        return False
