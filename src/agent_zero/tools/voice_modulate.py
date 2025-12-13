"""
Voice Modulation Tool for Agent Zero.

Provides voice guidance for how the agent should communicate.
"""

import sys
from pathlib import Path

AGENT_ZERO_PATH = Path(__file__).parent.parent.parent.parent / "vendor" / "agent-zero"
if str(AGENT_ZERO_PATH) not in sys.path:
    sys.path.insert(0, str(AGENT_ZERO_PATH))

from python.helpers.tool import Tool, Response


class VoiceModulate(Tool):
    """
    Get voice modulation guidance.

    Provides guidance on how to communicate based on the current
    emotional context and Ambassador voice patterns.

    Arguments:
        emotion: Detected emotion to respond to (confusion, frustration, anxiety, excitement, sadness)
        pattern_type: Type of pattern to get (tone, lexicon, metaphor, boundary)

    Returns:
        Voice guidance for the response
    """

    async def execute(self, emotion: str = "", pattern_type: str = "", **kwargs) -> Response:
        bridge = self.agent.get_data("soul_kiln_bridge")
        if not bridge:
            return Response(
                message="Error: Soul Kiln bridge not initialized",
                break_loop=False
            )

        if emotion:
            bridge.set_emotion_state(emotion)

        guidance = bridge.get_voice_guidance(emotion if emotion else None)

        output = "VOICE MODULATION GUIDANCE\n\n"

        if emotion and guidance.get("emotion_response"):
            er = guidance["emotion_response"]
            output += (
                f"EMOTION DETECTED: {er['emotion'].upper()}\n"
                f"Intensity: {er['intensity']:.0%}\n\n"
                f"Response Guidance:\n{er['guidance']}\n\n"
            )

        if pattern_type:
            from src.voice.definitions import get_patterns_by_type
            patterns = get_patterns_by_type(pattern_type)
            output += f"{pattern_type.upper()} PATTERNS:\n"
            for p in patterns:
                output += f"  • {p.name}: {p.content[:100]}...\n"
        else:
            # General guidance
            output += "COMMUNICATION BOUNDARIES:\n"
            for n in guidance["boundaries"]["never"]:
                output += f"  ⛔ NEVER: {n[:80]}...\n"
            for a in guidance["boundaries"]["always"]:
                output += f"  ✓ ALWAYS: {a[:80]}...\n"

        return Response(
            message=output,
            break_loop=False
        )

    def get_log_object(self):
        return self.agent.context.log.log(
            type="tool",
            heading=f"icon://record_voice_over {self.agent.agent_name}: Voice Modulation",
            content="",
            kvps=self.args,
        )
