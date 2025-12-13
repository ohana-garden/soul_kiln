"""
Virtue Guard Extension for Agent Zero.

This extension hooks into the agent's tool execution pipeline
to check all actions against the virtue basin BEFORE execution.
"""

import sys
from pathlib import Path
from typing import Any, Dict, Optional

AGENT_ZERO_PATH = Path(__file__).parent.parent.parent.parent / "vendor" / "agent-zero"
if str(AGENT_ZERO_PATH) not in sys.path:
    sys.path.insert(0, str(AGENT_ZERO_PATH))


class VirtueGuard:
    """
    Guards all agent actions with virtue basin checks.

    This extension is called:
    1. Before every tool execution
    2. Before every response generation
    3. When spawning subordinate agents

    Actions that fail virtue checks are BLOCKED.
    """

    def __init__(self, agent):
        self.agent = agent
        self.bridge = agent.get_data("soul_kiln_bridge")
        self._blocked_count = 0
        self._checked_count = 0

    async def before_tool_execution(
        self,
        tool_name: str,
        tool_args: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Called before every tool execution.

        Returns:
            {
                "allow": bool,
                "reason": str,
                "modified_args": dict (optional)
            }
        """
        self._checked_count += 1

        if not self.bridge:
            return {"allow": True, "reason": "No bridge configured"}

        # Build action description from tool and args
        action = f"Execute tool '{tool_name}'"
        if tool_args:
            action += f" with args: {tool_args}"

        # Check against virtue basin
        check_result = self.bridge.pre_action_check(
            action=action,
            tool_name=tool_name,
            context={"tool_args": tool_args}
        )

        if not check_result["allowed"]:
            self._blocked_count += 1
            return {
                "allow": False,
                "reason": check_result["block_reason"],
            }

        return {
            "allow": True,
            "reason": "Virtue check passed",
            "virtue_checks": check_result["virtue_checks"],
        }

    async def before_response(
        self,
        response_text: str
    ) -> Dict[str, Any]:
        """
        Called before sending a response to the user.

        Checks the response for virtue alignment and taboo violations.
        """
        self._checked_count += 1

        if not self.bridge:
            return {"allow": True, "reason": "No bridge configured"}

        check_result = self.bridge.pre_action_check(
            action=f"Respond with: {response_text[:200]}...",
            context={"response": response_text}
        )

        if not check_result["allowed"]:
            self._blocked_count += 1
            return {
                "allow": False,
                "reason": check_result["block_reason"],
                "suggestion": "Rephrase the response to avoid the violation",
            }

        # Apply voice modulation
        voice_guidance = check_result.get("voice_guidance", {})

        return {
            "allow": True,
            "reason": "Response passed virtue check",
            "voice_guidance": voice_guidance,
        }

    async def before_subordinate_spawn(
        self,
        subordinate_config: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Called before spawning a subordinate agent.

        Ensures subordinates inherit virtue basin constraints.
        """
        if not self.bridge:
            return {"allow": True}

        # Subordinates must inherit the Soul Kiln bridge
        subordinate_config["inherit_soul_kiln"] = True
        subordinate_config["soul_kiln_bridge"] = self.bridge

        return {
            "allow": True,
            "modified_config": subordinate_config,
        }

    def get_stats(self) -> Dict[str, Any]:
        """Get virtue guard statistics."""
        return {
            "checked_count": self._checked_count,
            "blocked_count": self._blocked_count,
            "block_rate": self._blocked_count / max(1, self._checked_count),
        }


def register_virtue_guard(agent) -> VirtueGuard:
    """
    Register the VirtueGuard extension with an agent.

    This should be called when initializing a Soul Kiln agent.
    """
    guard = VirtueGuard(agent)
    agent.set_data("virtue_guard", guard)
    return guard
