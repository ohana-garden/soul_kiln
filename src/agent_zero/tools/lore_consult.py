"""
Lore Consultation Tool for Agent Zero.

Consults the agent's identity lore for guidance.
"""

import sys
from pathlib import Path

AGENT_ZERO_PATH = Path(__file__).parent.parent.parent.parent / "vendor" / "agent-zero"
if str(AGENT_ZERO_PATH) not in sys.path:
    sys.path.insert(0, str(AGENT_ZERO_PATH))

from python.helpers.tool import Tool, Response


class LoreConsult(Tool):
    """
    Consult the Ambassador's identity lore.

    Lore provides the mythic/narrative context for the agent's identity.
    Use this to ground responses in the agent's core identity.

    Arguments:
        lore_type: Type of lore to consult (origin, lineage, commitment, taboo, theme)
        topic: Optional topic to search for

    Returns:
        Relevant lore fragments
    """

    async def execute(self, lore_type: str = "", topic: str = "", **kwargs) -> Response:
        bridge = self.agent.get_data("soul_kiln_bridge")
        if not bridge:
            return Response(
                message="Error: Soul Kiln bridge not initialized",
                break_loop=False
            )

        if lore_type == "identity" or not lore_type:
            # Get full identity lore
            lore = bridge.get_identity_lore()
            output = (
                f"AMBASSADOR IDENTITY LORE\n\n"
                f"ORIGIN:\n{lore['origin']}\n\n"
                f"SACRED COMMITMENTS:\n"
                + "\n".join(f"  • {c}" for c in lore['sacred_commitments'])
                + f"\n\nTABOOS:\n"
                + "\n".join(f"  ⛔ {t}" for t in lore['taboos'])
            )
        elif lore_type == "lineage":
            lineage = bridge.get_lineage_lore()
            output = (
                f"AMBASSADOR LINEAGE\n\n"
                + "\n".join(f"  • {l}" for l in lineage)
            )
        else:
            # Query by type
            from src.lore.definitions import get_lore_by_type
            fragments = get_lore_by_type(lore_type)
            if fragments:
                output = f"LORE: {lore_type.upper()}\n\n"
                for f in fragments:
                    output += f"  [{f.id}] {f.content}\n"
            else:
                output = f"No lore found for type: {lore_type}"

        return Response(
            message=output,
            break_loop=False
        )

    def get_log_object(self):
        return self.agent.context.log.log(
            type="tool",
            heading=f"icon://book {self.agent.agent_name}: Lore Consultation",
            content="",
            kvps=self.args,
        )
