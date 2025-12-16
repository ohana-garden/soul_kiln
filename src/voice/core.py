"""
Core voice operations.

Functions for creating, querying, and applying voice patterns.
"""

import logging
from datetime import datetime
from typing import Any

from ..graph.client import get_client
from ..graph.queries import create_node, create_edge
from ..models import VoicePattern, NodeType, EdgeType

logger = logging.getLogger(__name__)


def create_voice_pattern(pattern: VoicePattern, agent_id: str | None = None) -> VoicePattern:
    """
    Create a voice pattern in the graph.

    Args:
        pattern: The voice pattern
        agent_id: Optional agent to bind this pattern to

    Returns:
        The created voice pattern
    """
    client = get_client()

    # Create the voice pattern node
    create_node("VoicePattern", {
        "id": pattern.id,
        "name": pattern.name,
        "pattern_type": pattern.pattern_type,
        "content": pattern.content,
        "intensity": pattern.intensity,
        "type": NodeType.VOICE_PATTERN.value,
        "applies_when": str(pattern.applies_when),
    })

    # If agent specified, bind pattern to agent
    if agent_id:
        create_edge(agent_id, pattern.id, EdgeType.VOICE_MODULATES.value, {
            "weight": pattern.intensity,
            "reason": f"Agent {agent_id} uses voice pattern {pattern.id}",
        })

    logger.info(f"Created voice pattern: {pattern.id} ({pattern.pattern_type})")
    return pattern


def get_voice_pattern(pattern_id: str) -> VoicePattern | None:
    """
    Get a voice pattern by ID.

    Args:
        pattern_id: The pattern ID

    Returns:
        The voice pattern if found, None otherwise
    """
    client = get_client()
    result = client.query(
        """
        MATCH (v:VoicePattern {id: $id})
        RETURN v
        """,
        {"id": pattern_id}
    )

    if not result:
        return None

    props = result[0][0].properties
    return _props_to_pattern(props)


def modulate_response(
    agent_id: str,
    base_response: str,
    context: str,
    detected_emotion: str | None = None
) -> dict[str, Any]:
    """
    Modulate a response based on context and detected emotion.

    Args:
        agent_id: The agent ID
        base_response: The base response to modulate
        context: The current context
        detected_emotion: Optional detected emotion from Hume.ai

    Returns:
        Modulated response with applied patterns
    """
    client = get_client()

    # Get applicable patterns
    patterns_result = client.query(
        """
        MATCH (a:Agent {id: $agent_id})-[:VOICE_MODULATES]->(v:VoicePattern)
        RETURN v
        """,
        {"agent_id": agent_id}
    )

    applied_patterns = []
    modulation_notes = []

    for row in patterns_result or []:
        pattern = _props_to_pattern(row[0].properties)
        applies_when = eval(pattern.applies_when) if isinstance(pattern.applies_when, str) else pattern.applies_when

        # Check if pattern applies
        should_apply = False
        if "always" in applies_when or "default" in applies_when:
            should_apply = True
        elif context in applies_when:
            should_apply = True
        elif detected_emotion and f"emotion:{detected_emotion}" in applies_when:
            should_apply = True

        if should_apply:
            applied_patterns.append(pattern)
            modulation_notes.append(f"{pattern.pattern_type}: {pattern.name}")

    return {
        "original": base_response,
        "context": context,
        "emotion": detected_emotion,
        "applied_patterns": [p.id for p in applied_patterns],
        "modulation_notes": modulation_notes,
        # In production, this would actually transform the response
        "modulated_response": base_response,
    }


def get_emotion_response(agent_id: str, emotion: str) -> dict[str, Any]:
    """
    Get the appropriate response modulation for a detected emotion.

    Args:
        agent_id: The agent ID
        emotion: The detected emotion (confusion, frustration, anxiety, excitement, sadness)

    Returns:
        Emotion response guidance
    """
    client = get_client()

    result = client.query(
        """
        MATCH (a:Agent {id: $agent_id})-[:VOICE_MODULATES]->(v:VoicePattern {pattern_type: 'emotion_response'})
        WHERE $emotion_trigger IN v.applies_when OR v.applies_when CONTAINS $emotion_trigger
        RETURN v
        """,
        {"agent_id": agent_id, "emotion_trigger": f"emotion:{emotion}"}
    )

    if not result:
        return {
            "emotion": emotion,
            "found": False,
            "guidance": "No specific guidance found for this emotion.",
        }

    pattern = _props_to_pattern(result[0][0].properties)
    return {
        "emotion": emotion,
        "found": True,
        "pattern_id": pattern.id,
        "guidance": pattern.content,
        "intensity": pattern.intensity,
    }


def apply_lexicon_rules(agent_id: str, text: str) -> str:
    """
    Apply lexicon rules to transform text.

    Args:
        agent_id: The agent ID
        text: The text to transform

    Returns:
        Transformed text
    """
    # In production, this would apply actual transformations
    # For now, we return the text unchanged but log what would happen

    client = get_client()

    result = client.query(
        """
        MATCH (a:Agent {id: $agent_id})-[:VOICE_MODULATES]->(v:VoicePattern {pattern_type: 'lexicon'})
        RETURN v
        ORDER BY v.intensity DESC
        """,
        {"agent_id": agent_id}
    )

    transformations = []
    for row in result or []:
        pattern = _props_to_pattern(row[0].properties)
        transformations.append(pattern.content)

    logger.debug(f"Would apply lexicon rules: {transformations}")
    return text


def get_voice_persona(agent_id: str) -> dict[str, Any]:
    """
    Get the complete voice persona for an agent.

    Args:
        agent_id: The agent ID

    Returns:
        Complete voice persona configuration
    """
    client = get_client()

    result = client.query(
        """
        MATCH (a:Agent {id: $agent_id})-[:VOICE_MODULATES]->(v:VoicePattern)
        RETURN v.pattern_type as type, collect(v) as patterns
        """,
        {"agent_id": agent_id}
    )

    persona = {
        "agent_id": agent_id,
        "tone": [],
        "lexicon": [],
        "metaphor": [],
        "emotion_response": [],
        "boundary": [],
    }

    for row in result or []:
        pattern_type = row[0]
        patterns = [_props_to_pattern(p.properties) for p in row[1]]
        if pattern_type in persona:
            persona[pattern_type] = [
                {"id": p.id, "name": p.name, "content": p.content, "intensity": p.intensity}
                for p in patterns
            ]

    return persona


def get_boundaries(agent_id: str) -> dict[str, list[str]]:
    """
    Get the voice boundaries (never say / always include) for an agent.

    Args:
        agent_id: The agent ID

    Returns:
        Dict with 'never' and 'always' lists
    """
    client = get_client()

    result = client.query(
        """
        MATCH (a:Agent {id: $agent_id})-[:VOICE_MODULATES]->(v:VoicePattern {pattern_type: 'boundary'})
        RETURN v.name, v.content
        """,
        {"agent_id": agent_id}
    )

    boundaries = {"never": [], "always": []}

    for row in result or []:
        name, content = row
        if "never" in name.lower():
            # Parse the never-say list from content
            lines = content.split("\n")
            for line in lines:
                if line.strip().startswith("-"):
                    boundaries["never"].append(line.strip("- ").strip("'\""))
        elif "always" in name.lower():
            lines = content.split("\n")
            for line in lines:
                if line.strip().startswith("-"):
                    boundaries["always"].append(line.strip("- ").strip())

    return boundaries


def _props_to_pattern(props: dict) -> VoicePattern:
    """Convert graph properties to a VoicePattern object."""
    applies_when = props.get("applies_when", "[]")
    if isinstance(applies_when, str):
        try:
            applies_when = eval(applies_when)
        except:
            applies_when = []

    return VoicePattern(
        id=props["id"],
        name=props["name"],
        pattern_type=props.get("pattern_type", "tone"),
        content=props["content"],
        applies_when=applies_when,
        intensity=props.get("intensity", 0.5),
    )
