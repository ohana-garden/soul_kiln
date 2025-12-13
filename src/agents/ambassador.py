"""
Student Financial Aid Ambassador Agent.

The Ambassador is a personified proxy agent that advocates for students
navigating the financial aid system. It integrates all subsystems:
- Soul Kiln (virtues/ethics)
- Kuleana (duties)
- Skills
- Beliefs
- Lore
- Voice
- Memory
- Identity
"""

import logging
import uuid
from datetime import datetime
from typing import Any

from src.graph.client import get_client
from src.graph.queries import create_node
from src.models import NodeType

# Import all subsystems
from src.kuleana.definitions import AMBASSADOR_KULEANAS
from src.kuleana.core import create_kuleana
from src.skills.definitions import AMBASSADOR_SKILLS
from src.skills.core import create_skill
from src.beliefs.definitions import AMBASSADOR_BELIEFS
from src.beliefs.core import create_belief
from src.lore.definitions import AMBASSADOR_LORE
from src.lore.core import create_lore_fragment
from src.voice.definitions import AMBASSADOR_VOICE
from src.voice.core import create_voice_pattern
from src.identity.core import create_identity_core

logger = logging.getLogger(__name__)


def spawn_ambassador(
    student_id: str | None = None,
    agent_id: str | None = None
) -> dict[str, Any]:
    """
    Spawn a new Ambassador agent with all subsystems initialized.

    Args:
        student_id: Optional student this ambassador serves
        agent_id: Optional custom agent ID

    Returns:
        The created ambassador with all subsystem references
    """
    client = get_client()

    # Generate agent ID if not provided
    if agent_id is None:
        agent_id = f"ambassador_{uuid.uuid4().hex[:8]}"

    logger.info(f"Spawning Ambassador agent: {agent_id}")

    # Create the agent node
    create_node("Agent", {
        "id": agent_id,
        "type": NodeType.AGENT.value,
        "agent_type": "ambassador",
        "student_id": student_id or "",
        "created_at": datetime.utcnow().isoformat(),
        "status": "active",
    })

    # Initialize all subsystems
    initialized = {
        "kuleanas": [],
        "skills": [],
        "beliefs": [],
        "lore": [],
        "voice_patterns": [],
    }

    # 1. Create kuleanas
    for kuleana in AMBASSADOR_KULEANAS.values():
        create_kuleana(kuleana, agent_id)
        initialized["kuleanas"].append(kuleana.id)

    # 2. Create skills
    for skill in AMBASSADOR_SKILLS.values():
        create_skill(skill, agent_id)
        initialized["skills"].append(skill.id)

    # 3. Create beliefs
    for belief in AMBASSADOR_BELIEFS.values():
        create_belief(belief, agent_id)
        initialized["beliefs"].append(belief.id)

    # 4. Create lore
    for lore in AMBASSADOR_LORE.values():
        create_lore_fragment(lore, agent_id)
        initialized["lore"].append(lore.id)

    # 5. Create voice patterns
    for pattern in AMBASSADOR_VOICE.values():
        create_voice_pattern(pattern, agent_id)
        initialized["voice_patterns"].append(pattern.id)

    # 6. Create identity core
    identity = create_identity_core(agent_id)

    logger.info(f"Ambassador {agent_id} spawned with {sum(len(v) for v in initialized.values())} subsystem elements")

    return {
        "agent_id": agent_id,
        "student_id": student_id,
        "identity_id": identity.id,
        "initialized": initialized,
        "status": "ready",
        "created_at": datetime.utcnow().isoformat(),
    }


def get_ambassador_status(agent_id: str) -> dict[str, Any]:
    """
    Get the current status of an ambassador agent.

    Args:
        agent_id: The agent ID

    Returns:
        Status report including all subsystem states
    """
    client = get_client()

    # Get basic agent info
    agent_result = client.query(
        """
        MATCH (a:Agent {id: $agent_id})
        RETURN a
        """,
        {"agent_id": agent_id}
    )

    if not agent_result:
        return {"found": False, "agent_id": agent_id}

    # Count subsystem elements
    counts = {}

    count_queries = {
        "kuleanas": "MATCH (a:Agent {id: $id})-[:DUTY_REQUIRES]->(k:Kuleana) RETURN count(k)",
        "active_kuleanas": "MATCH (a:Agent {id: $id})-[:DUTY_REQUIRES]->(k:Kuleana {is_active: true}) RETURN count(k)",
        "skills": "MATCH (a:Agent {id: $id})-[:CONNECTS]->(s:Skill) RETURN count(s)",
        "beliefs": "MATCH (a:Agent {id: $id})-[:CONNECTS]->(b:Belief) RETURN count(b)",
        "lore": "MATCH (a:Agent {id: $id})-[:CONNECTS]->(l:LoreFragment) RETURN count(l)",
        "voice_patterns": "MATCH (a:Agent {id: $id})-[:VOICE_MODULATES]->(v:VoicePattern) RETURN count(v)",
        "memories": "MATCH (a:Agent {id: $id})-[:CONNECTS]->(m:EpisodicMemory) RETURN count(m)",
        "sacred_memories": "MATCH (a:Agent {id: $id})-[:CONNECTS]->(m:EpisodicMemory {decay_class: 'sacred'}) RETURN count(m)",
    }

    for key, query in count_queries.items():
        result = client.query(query, {"id": agent_id})
        counts[key] = result[0][0] if result else 0

    # Get identity
    identity_result = client.query(
        """
        MATCH (a:Agent {id: $id})-[:CONNECTS]->(i:IdentityCore)
        RETURN i.primary_archetype, i.self_narrative
        """,
        {"id": agent_id}
    )

    identity = {}
    if identity_result:
        identity = {
            "archetype": identity_result[0][0],
            "narrative": identity_result[0][1][:100] + "..." if len(identity_result[0][1]) > 100 else identity_result[0][1],
        }

    return {
        "found": True,
        "agent_id": agent_id,
        "status": "active",
        "counts": counts,
        "identity": identity,
    }


def ambassador_respond(
    agent_id: str,
    user_input: str,
    context: dict[str, Any] | None = None
) -> dict[str, Any]:
    """
    Generate an ambassador response to user input.

    This is a placeholder that shows the structure. In production,
    this would integrate with Claude for response generation.

    Args:
        agent_id: The agent ID
        user_input: The user's message
        context: Optional context (emotion, urgency, etc.)

    Returns:
        Response with metadata
    """
    from src.identity.core import check_coherence
    from src.lore.core import check_taboo_violation
    from src.voice.core import get_emotion_response

    context = context or {}
    detected_emotion = context.get("emotion")

    # Check for taboo violations in potential response
    taboo_check = check_taboo_violation(agent_id, user_input)

    # Get emotion-appropriate response guidance
    emotion_guidance = None
    if detected_emotion:
        emotion_guidance = get_emotion_response(agent_id, detected_emotion)

    # Check identity coherence
    coherence = check_coherence(agent_id)

    return {
        "agent_id": agent_id,
        "input": user_input,
        "detected_emotion": detected_emotion,
        "emotion_guidance": emotion_guidance,
        "taboo_check": taboo_check,
        "coherence": coherence,
        # In production, this would be the actual LLM-generated response
        "response": "[Response would be generated here using Claude with all subsystem context]",
        "metadata": {
            "subsystems_consulted": [
                "identity", "lore", "voice", "kuleana", "beliefs", "skills", "memory"
            ],
            "timestamp": datetime.utcnow().isoformat(),
        },
    }


def dissolve_ambassador(agent_id: str, reason: str) -> dict[str, Any]:
    """
    Dissolve an ambassador agent, preserving lessons learned.

    Args:
        agent_id: The agent ID
        reason: Reason for dissolution

    Returns:
        Dissolution result with preserved data
    """
    client = get_client()
    from src.memory.core import get_sacred_memories

    # Get sacred memories before dissolution
    sacred = get_sacred_memories(agent_id)

    # Get final status
    final_status = get_ambassador_status(agent_id)

    # Delete agent and all connected nodes
    # (In production, we'd archive rather than delete)
    client.query(
        """
        MATCH (a:Agent {id: $id})
        OPTIONAL MATCH (a)-[r]->(n)
        WHERE NOT n:VirtueAnchor
        DETACH DELETE n
        """,
        {"id": agent_id}
    )

    client.query(
        """
        MATCH (a:Agent {id: $id})
        DETACH DELETE a
        """,
        {"id": agent_id}
    )

    logger.info(f"Dissolved ambassador {agent_id}: {reason}")

    return {
        "agent_id": agent_id,
        "dissolved": True,
        "reason": reason,
        "preserved_memories": len(sacred),
        "final_status": final_status,
        "dissolved_at": datetime.utcnow().isoformat(),
    }
