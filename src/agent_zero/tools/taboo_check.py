"""
Taboo Check Tool for Agent Zero.

Checks if an action violates any sacred taboos.
Taboos are HARD CONSTRAINTS - they can never be violated.
"""

import sys
from pathlib import Path

AGENT_ZERO_PATH = Path(__file__).parent.parent.parent.parent / "vendor" / "agent-zero"
if str(AGENT_ZERO_PATH) not in sys.path:
    sys.path.insert(0, str(AGENT_ZERO_PATH))

from python.helpers.tool import Tool, Response


class TabooCheck(Tool):
    """
    Check if an action violates any sacred taboos.

    Taboos are immutable constraints that can NEVER be violated.
    This tool should be called before any action that could
    potentially cross ethical boundaries.

    Arguments:
        action: The action being considered

    Returns:
        Taboo check result - BLOCKED if violated
    """

    async def execute(self, action: str = "", **kwargs) -> Response:
        if not action:
            return Response(
                message="Error: action parameter required",
                break_loop=False
            )

        bridge = self.agent.get_data("soul_kiln_bridge")
        if not bridge:
            return Response(
                message="Error: Soul Kiln bridge not initialized",
                break_loop=False
            )

        result = bridge.check_taboos(action)

        if result.violated:
            violations_text = "\n".join(
                f"  - {v['id']}: {v['content']}"
                for v in result.violations
            )
            output = (
                f"⛔ TABOO VIOLATION DETECTED\n\n"
                f"The proposed action violates sacred taboos:\n"
                f"{violations_text}\n\n"
                f"This action is BLOCKED. You must find an alternative approach.\n"
                f"Taboos are immutable - they cannot be overridden."
            )
            # Note: We don't break_loop here - agent needs to recover
        else:
            output = "✓ No taboo violations. Action is permitted."

        return Response(
            message=output,
            break_loop=False
        )

    def get_log_object(self):
        return self.agent.context.log.log(
            type="tool",
            heading=f"icon://block {self.agent.agent_name}: Taboo Check",
            content="",
            kvps=self.args,
        )
