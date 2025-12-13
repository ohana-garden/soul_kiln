"""
Sacred Memory Tool for Agent Zero.

Saves memories with SACRED decay class - they never decay.
"""

import sys
from pathlib import Path

AGENT_ZERO_PATH = Path(__file__).parent.parent.parent.parent / "vendor" / "agent-zero"
if str(AGENT_ZERO_PATH) not in sys.path:
    sys.path.insert(0, str(AGENT_ZERO_PATH))

from python.helpers.tool import Tool, Response


class MemorySacredSave(Tool):
    """
    Save a memory with SACRED decay class.

    Sacred memories NEVER decay. Use this for critical information
    that must be preserved indefinitely:
    - Student's core goals
    - Promises made
    - Critical deadlines
    - Trust-building moments

    Arguments:
        content: The memory content to save
        category: Category (goal, promise, deadline, trust, other)
        importance: Importance level (1-10)

    Returns:
        Confirmation of memory saved
    """

    async def execute(
        self,
        content: str = "",
        category: str = "other",
        importance: str = "10",
        **kwargs
    ) -> Response:
        if not content:
            return Response(
                message="Error: content parameter required",
                break_loop=False
            )

        # In production, this would persist to the graph database
        # For now, we use Agent Zero's memory system with metadata

        try:
            importance_int = int(importance)
        except ValueError:
            importance_int = 10

        # Store in agent's data for this session
        sacred_memories = self.agent.get_data("sacred_memories") or []
        memory_entry = {
            "content": content,
            "category": category,
            "importance": importance_int,
            "decay_class": "SACRED",
            "timestamp": str(Path.ctime(Path(".")))
        }
        sacred_memories.append(memory_entry)
        self.agent.set_data("sacred_memories", sacred_memories)

        output = (
            f"✓ SACRED MEMORY SAVED\n\n"
            f"Content: {content}\n"
            f"Category: {category}\n"
            f"Importance: {importance_int}/10\n"
            f"Decay Class: SACRED (never decays)\n\n"
            f"Total sacred memories: {len(sacred_memories)}"
        )

        return Response(
            message=output,
            break_loop=False
        )

    def get_log_object(self):
        return self.agent.context.log.log(
            type="tool",
            heading=f"icon://save {self.agent.agent_name}: Sacred Memory Save",
            content="",
            kvps=self.args,
        )
