"""
Kuleana Activation Tool for Agent Zero.

Determines which duties (kuleanas) are activated for the current context.
"""

import sys
from pathlib import Path

AGENT_ZERO_PATH = Path(__file__).parent.parent.parent.parent / "vendor" / "agent-zero"
if str(AGENT_ZERO_PATH) not in sys.path:
    sys.path.insert(0, str(AGENT_ZERO_PATH))

from python.helpers.tool import Tool, Response


class KuleanaActivate(Tool):
    """
    Activate kuleanas (duties) based on context.

    Kuleanas define what the agent is responsible for doing.
    This tool determines which duties are relevant and their priority.

    Arguments:
        context: The current situation/context
        return_primary: If true, only return the highest priority duty

    Returns:
        List of activated kuleanas with priorities
    """

    async def execute(self, context: str = "", return_primary: str = "false", **kwargs) -> Response:
        if not context:
            return Response(
                message="Error: context parameter required",
                break_loop=False
            )

        bridge = self.agent.get_data("soul_kiln_bridge")
        if not bridge:
            return Response(
                message="Error: Soul Kiln bridge not initialized",
                break_loop=False
            )

        kuleanas = bridge.activate_kuleanas(context)

        if not kuleanas:
            return Response(
                message="No specific duties activated for this context. Use general assistance mode.",
                break_loop=False
            )

        if return_primary.lower() == "true":
            primary = kuleanas[0]
            output = (
                f"PRIMARY DUTY ACTIVATED\n\n"
                f"Kuleana: {primary.name} ({primary.id})\n"
                f"Priority: {primary.priority}\n"
                f"Triggered by: {primary.trigger}\n\n"
                f"Required virtues: {', '.join(primary.required_virtues)}\n"
                f"Required skills: {', '.join(primary.required_skills)}\n\n"
                f"Focus your actions on fulfilling this duty."
            )
        else:
            output = f"ACTIVATED DUTIES ({len(kuleanas)} total)\n\n"
            for i, k in enumerate(kuleanas, 1):
                output += (
                    f"{i}. {k.name} ({k.id})\n"
                    f"   Priority: {k.priority} | Trigger: {k.trigger}\n"
                )
            output += "\nFocus on duties in priority order."

        return Response(
            message=output,
            break_loop=False
        )

    def get_log_object(self):
        return self.agent.context.log.log(
            type="tool",
            heading=f"icon://assignment {self.agent.agent_name}: Kuleana Activation",
            content="",
            kvps=self.args,
        )
