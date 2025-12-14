"""Episode recording and retrieval for telepathy.

Episodes are the atomic units of shared cognition. When an agent thinks,
reflects, or acts, the episode is recorded in the graph. Any agent can
query any other agent's episodes - this is telepathy.
"""

from datetime import datetime, timedelta
import uuid
from ..graph.client import get_client
from ..graph.queries import create_node, create_edge


def record_episode(
    agent_id: str,
    episode_type: str,
    content: str,
    stimulus: str = None,
    tokens_used: int = 0,
    metadata: dict = None
) -> str:
    """
    Record an episode to the shared knowledge graph.

    This is the core telepathy write operation. Once recorded,
    any agent can query this episode.

    Args:
        agent_id: ID of the agent generating the episode
        episode_type: "thought", "reflection", "action", or "observation"
        content: The content of the episode (thought text, action result, etc.)
        stimulus: Optional stimulus that triggered this episode
        tokens_used: Optional token count for LLM calls
        metadata: Optional additional metadata

    Returns:
        ID of the created episode node
    """
    episode_id = f"ep_{uuid.uuid4().hex[:12]}"

    create_node("Episode", {
        "id": episode_id,
        "agent_id": agent_id,
        "episode_type": episode_type,
        "content": content,
        "stimulus": stimulus,
        "tokens_used": tokens_used,
        "metadata": str(metadata or {}),
    })

    # Link episode to agent
    create_edge(agent_id, episode_id, "EXPERIENCED")

    return episode_id


def get_agent_episodes(
    agent_id: str,
    episode_type: str = None,
    limit: int = 50
) -> list:
    """
    Get episodes for a specific agent.

    Args:
        agent_id: ID of the agent
        episode_type: Optional filter by episode type
        limit: Maximum episodes to return

    Returns:
        List of episode tuples (id, type, content, stimulus, created_at)
    """
    client = get_client()

    if episode_type:
        return client.query(
            """
            MATCH (e:Episode {agent_id: $agent_id, episode_type: $type})
            RETURN e.id, e.episode_type, e.content, e.stimulus, e.created_at
            ORDER BY e.created_at DESC
            LIMIT $limit
            """,
            {"agent_id": agent_id, "type": episode_type, "limit": limit}
        )
    else:
        return client.query(
            """
            MATCH (e:Episode {agent_id: $agent_id})
            RETURN e.id, e.episode_type, e.content, e.stimulus, e.created_at
            ORDER BY e.created_at DESC
            LIMIT $limit
            """,
            {"agent_id": agent_id, "limit": limit}
        )


def get_all_thoughts(limit: int = 100) -> list:
    """
    Get all thoughts from all agents - full telepathy.

    This is the core telepathy read operation. Any agent can
    see what any other agent has thought.

    Args:
        limit: Maximum thoughts to return

    Returns:
        List of thought tuples (id, agent_id, content, stimulus, created_at)
    """
    client = get_client()
    return client.query(
        """
        MATCH (e:Episode {episode_type: 'thought'})
        RETURN e.id, e.agent_id, e.content, e.stimulus, e.created_at
        ORDER BY e.created_at DESC
        LIMIT $limit
        """,
        {"limit": limit}
    )


def get_recent_episodes(hours: int = 24, limit: int = 100) -> list:
    """
    Get episodes from the last N hours across all agents.

    Args:
        hours: How far back to look
        limit: Maximum episodes to return

    Returns:
        List of episode tuples
    """
    client = get_client()
    cutoff = (datetime.utcnow() - timedelta(hours=hours)).isoformat()

    return client.query(
        """
        MATCH (e:Episode)
        WHERE e.created_at > $cutoff
        RETURN e.id, e.agent_id, e.episode_type, e.content, e.created_at
        ORDER BY e.created_at DESC
        LIMIT $limit
        """,
        {"cutoff": cutoff, "limit": limit}
    )


def search_episodes(keyword: str, limit: int = 50) -> list:
    """
    Search episodes by keyword in content.

    Args:
        keyword: Keyword to search for (case-insensitive)
        limit: Maximum results to return

    Returns:
        List of matching episode tuples
    """
    client = get_client()
    return client.query(
        """
        MATCH (e:Episode)
        WHERE toLower(e.content) CONTAINS toLower($keyword)
        RETURN e.id, e.agent_id, e.episode_type, e.content, e.created_at
        ORDER BY e.created_at DESC
        LIMIT $limit
        """,
        {"keyword": keyword, "limit": limit}
    )


def get_episodes_about_virtue(virtue_id: str, limit: int = 50) -> list:
    """
    Get episodes that mention a specific virtue.

    Args:
        virtue_id: Virtue ID to search for (e.g., "V01", "V16")
        limit: Maximum results to return

    Returns:
        List of episode tuples mentioning the virtue
    """
    client = get_client()
    return client.query(
        """
        MATCH (e:Episode)
        WHERE e.content CONTAINS $virtue_id
        RETURN e.id, e.agent_id, e.episode_type, e.content, e.created_at
        ORDER BY e.created_at DESC
        LIMIT $limit
        """,
        {"virtue_id": virtue_id, "limit": limit}
    )


def get_episode_count_by_agent() -> list:
    """
    Get episode counts per agent - see who's thinking most.

    Returns:
        List of (agent_id, count) tuples sorted by count descending
    """
    client = get_client()
    return client.query(
        """
        MATCH (e:Episode)
        RETURN e.agent_id, count(e) as count
        ORDER BY count DESC
        """
    )


def get_episode_count_by_type() -> list:
    """
    Get episode counts by type.

    Returns:
        List of (episode_type, count) tuples
    """
    client = get_client()
    return client.query(
        """
        MATCH (e:Episode)
        RETURN e.episode_type, count(e) as count
        ORDER BY count DESC
        """
    )
