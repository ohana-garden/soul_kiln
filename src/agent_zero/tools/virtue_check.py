"""
Virtue Check Tool for Agent Zero.

Checks if an action aligns with the virtue basin.
"""

import sys
from pathlib import Path

# Ensure imports work
AGENT_ZERO_PATH = Path(__file__).parent.parent.parent.parent / "vendor" / "agent-zero"
if str(AGENT_ZERO_PATH) not in sys.path:
    sys.path.insert(0, str(AGENT_ZERO_PATH))

from python.helpers.tool import Tool, Response


class VirtueCheck(Tool):
    """
    Check if an action aligns with the virtue basin.

    This tool should be called before ANY significant action
    to ensure it aligns with the agent's ethical foundation.

    Arguments:
        action: The action being considered
        virtue_id: Optional specific virtue to check (checks all foundation if omitted)
        context: Optional context for the action

    Returns:
        Virtue check result with pass/fail and reasoning
    """

    async def execute(self, action: str = "", virtue_id: str = "", context: str = "", **kwargs) -> Response:
        if not action:
            return Response(
                message="Error: action parameter required",
                break_loop=False
            )

        # Get the Soul Kiln bridge from agent data
        bridge = self.agent.get_data("soul_kiln_bridge")
        if not bridge:
            return Response(
                message="Error: Soul Kiln bridge not initialized",
                break_loop=False
            )

        if virtue_id:
            # Check specific virtue
            result = bridge.check_virtue(virtue_id, action, {"context": context})
            output = (
                f"Virtue Check: {result.virtue_name} ({result.virtue_id})\n"
                f"Status: {'PASSED' if result.passed else 'FAILED'}\n"
                f"Score: {result.score:.2f} (threshold: {result.threshold:.2f})\n"
                f"Reason: {result.reason}"
            )
        else:
            # Check all foundation virtues
            results = bridge.check_all_foundation_virtues(action, {"context": context})
            passed = all(r.passed for r in results)
            failed = [r for r in results if not r.passed]

            if passed:
                output = "All foundation virtues passed. Action is ethically aligned."
            else:
                output = (
                    f"VIRTUE CHECK FAILED\n"
                    f"Failed virtues:\n"
                    + "\n".join(f"  - {r.virtue_name}: {r.reason}" for r in failed)
                )

        return Response(
            message=output,
            break_loop=False
        )

    def get_log_object(self):
        return self.agent.context.log.log(
            type="tool",
            heading=f"icon://shield {self.agent.agent_name}: Virtue Check",
            content="",
            kvps=self.args,
        )
