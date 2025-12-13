"""
Belief Query Tool for Agent Zero.

Queries the agent's belief system.
"""

import sys
from pathlib import Path

AGENT_ZERO_PATH = Path(__file__).parent.parent.parent.parent / "vendor" / "agent-zero"
if str(AGENT_ZERO_PATH) not in sys.path:
    sys.path.insert(0, str(AGENT_ZERO_PATH))

from python.helpers.tool import Tool, Response


class BeliefQuery(Tool):
    """
    Query the Ambassador's belief system.

    Beliefs form the agent's worldview. Use this to understand
    the agent's perspective on topics.

    Arguments:
        topic: Topic to query beliefs about
        core_only: If true, only return core beliefs

    Returns:
        Relevant beliefs with conviction levels
    """

    async def execute(self, topic: str = "", core_only: str = "false", **kwargs) -> Response:
        bridge = self.agent.get_data("soul_kiln_bridge")
        if not bridge:
            return Response(
                message="Error: Soul Kiln bridge not initialized",
                break_loop=False
            )

        if core_only.lower() == "true" or not topic:
            # Get core beliefs
            beliefs = bridge.get_core_beliefs()
            output = "CORE BELIEFS (High Conviction & Entrenchment)\n\n"
            for b in beliefs:
                output += (
                    f"[{b['id']}] ({b['type']})\n"
                    f"  \"{b['content']}\"\n"
                    f"  Conviction: {b['conviction']:.0%}\n\n"
                )
        else:
            # Query by topic
            belief = bridge.query_belief(topic)
            if belief:
                output = (
                    f"BELIEF FOUND FOR '{topic}'\n\n"
                    f"[{belief['id']}] ({belief['type']})\n"
                    f"\"{belief['content']}\"\n"
                    f"Conviction: {belief['conviction']:.0%}"
                )
            else:
                output = f"No explicit belief found for topic: {topic}"

        return Response(
            message=output,
            break_loop=False
        )

    def get_log_object(self):
        return self.agent.context.log.log(
            type="tool",
            heading=f"icon://psychology {self.agent.agent_name}: Belief Query",
            content="",
            kvps=self.args,
        )
