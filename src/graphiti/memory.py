"""
Episode and Memory Management.

Implements Graphiti-style episodic memory with temporal awareness.
Episodes capture conversation contexts and can be retrieved based on
relevance and recency.
"""
from datetime import datetime
from typing import Optional, Dict, Any, List
from uuid import uuid4

from src.graph import get_client


class EpisodeManager:
    """Manages conversational episodes in the graph."""

    def __init__(self):
        self.client = get_client()

    def create_episode(
        self,
        agent_id: str,
        conversation_id: str,
        content: str,
        episode_type: str = "conversation",
        metadata: Dict[str, Any] = None,
    ) -> str:
        """
        Create a new episode node.

        Args:
            agent_id: ID of the agent instance
            conversation_id: ID of the conversation
            content: Episode content/summary
            episode_type: Type of episode (conversation, action, observation)
            metadata: Additional metadata

        Returns:
            Episode ID
        """
        episode_id = str(uuid4())
        now = datetime.utcnow().isoformat()
        meta = metadata or {}

        # Create episode node
        query = """
        CREATE (e:Episode {
            id: $episode_id,
            content: $content,
            episode_type: $episode_type,
            created_at: datetime($now),
            metadata: $metadata
        })
        RETURN e.id as episode_id
        """

        self.client.execute(query, {
            "episode_id": episode_id,
            "content": content,
            "episode_type": episode_type,
            "now": now,
            "metadata": str(meta),  # FalkorDB may need string serialization
        })

        # Link to agent and conversation
        self._link_episode(episode_id, agent_id, conversation_id, now)

        return episode_id

    def _link_episode(
        self,
        episode_id: str,
        agent_id: str,
        conversation_id: str,
        timestamp: str,
    ):
        """Link episode to agent and conversation."""
        # Link to agent
        query = """
        MATCH (e:Episode {id: $episode_id})
        MATCH (a:AgentInstance {id: $agent_id})
        CREATE (a)-[:HAS_EPISODE {t_valid: datetime($ts), t_invalid: null}]->(e)
        """
        self.client.execute(query, {
            "episode_id": episode_id,
            "agent_id": agent_id,
            "ts": timestamp,
        })

        # Link to conversation
        query = """
        MATCH (e:Episode {id: $episode_id})
        MATCH (c:Conversation {id: $conv_id})
        CREATE (c)-[:CONTAINS_EPISODE {t_valid: datetime($ts), t_invalid: null}]->(e)
        """
        self.client.execute(query, {
            "episode_id": episode_id,
            "conv_id": conversation_id,
            "ts": timestamp,
        })

    def get_recent_episodes(
        self,
        agent_id: str,
        limit: int = 10,
        episode_type: str = None,
    ) -> List[Dict[str, Any]]:
        """
        Get recent episodes for an agent.

        Args:
            agent_id: Agent instance ID
            limit: Maximum episodes to return
            episode_type: Optional type filter

        Returns:
            List of episode dictionaries
        """
        type_filter = "AND e.episode_type = $episode_type" if episode_type else ""

        query = f"""
        MATCH (a:AgentInstance {{id: $agent_id}})-[:HAS_EPISODE]->(e:Episode)
        WHERE true {type_filter}
        RETURN e
        ORDER BY e.created_at DESC
        LIMIT $limit
        """

        params = {"agent_id": agent_id, "limit": limit}
        if episode_type:
            params["episode_type"] = episode_type

        result = self.client.query(query, params)

        return [dict(row[0].properties) for row in result if row[0]]


class MemoryManager:
    """Manages agent memories with semantic connections."""

    def __init__(self):
        self.client = get_client()

    def store_memory(
        self,
        agent_id: str,
        content: str,
        memory_type: str = "episodic",
        importance: float = 0.5,
        embedding: List[float] = None,
        metadata: Dict[str, Any] = None,
    ) -> str:
        """
        Store a memory for an agent.

        Args:
            agent_id: Agent instance ID
            content: Memory content
            memory_type: Type (episodic, semantic, procedural)
            importance: Importance score 0-1
            embedding: Optional vector embedding
            metadata: Additional metadata

        Returns:
            Memory ID
        """
        memory_id = str(uuid4())
        now = datetime.utcnow().isoformat()

        query = """
        CREATE (m:Memory {
            id: $memory_id,
            content: $content,
            memory_type: $memory_type,
            importance: $importance,
            created_at: datetime($now),
            last_accessed: datetime($now),
            access_count: 1
        })
        RETURN m.id as memory_id
        """

        self.client.execute(query, {
            "memory_id": memory_id,
            "content": content,
            "memory_type": memory_type,
            "importance": importance,
            "now": now,
        })

        # Link to agent
        link_query = """
        MATCH (m:Memory {id: $memory_id})
        MATCH (a:AgentInstance {id: $agent_id})
        CREATE (a)-[:HAS_MEMORY {t_valid: datetime($now), t_invalid: null}]->(m)
        """

        self.client.execute(link_query, {
            "memory_id": memory_id,
            "agent_id": agent_id,
            "now": now,
        })

        return memory_id

    def recall_memories(
        self,
        agent_id: str,
        query_text: str = None,
        memory_type: str = None,
        limit: int = 10,
        min_importance: float = 0.0,
    ) -> List[Dict[str, Any]]:
        """
        Recall memories for an agent.

        Args:
            agent_id: Agent instance ID
            query_text: Optional text to match (basic contains)
            memory_type: Optional type filter
            limit: Maximum memories to return
            min_importance: Minimum importance threshold

        Returns:
            List of memory dictionaries
        """
        filters = ["m.importance >= $min_importance"]

        if memory_type:
            filters.append("m.memory_type = $memory_type")
        if query_text:
            filters.append("m.content CONTAINS $query_text")

        filter_str = " AND ".join(filters)

        query = f"""
        MATCH (a:AgentInstance {{id: $agent_id}})-[r:HAS_MEMORY]->(m:Memory)
        WHERE r.t_invalid IS NULL AND {filter_str}
        RETURN m
        ORDER BY m.importance DESC, m.last_accessed DESC
        LIMIT $limit
        """

        params = {
            "agent_id": agent_id,
            "min_importance": min_importance,
            "limit": limit,
        }
        if memory_type:
            params["memory_type"] = memory_type
        if query_text:
            params["query_text"] = query_text

        result = self.client.query(query, params)

        memories = []
        for row in result:
            if row[0]:
                memory = dict(row[0].properties)
                # Update access count
                self._touch_memory(memory["id"])
                memories.append(memory)

        return memories

    def _touch_memory(self, memory_id: str):
        """Update memory access time and count."""
        now = datetime.utcnow().isoformat()
        query = """
        MATCH (m:Memory {id: $memory_id})
        SET m.last_accessed = datetime($now),
            m.access_count = m.access_count + 1
        """
        self.client.execute(query, {"memory_id": memory_id, "now": now})

    def forget_memory(self, memory_id: str) -> bool:
        """
        Soft-delete a memory by invalidating its edges.

        Args:
            memory_id: Memory ID to forget

        Returns:
            True if memory was found
        """
        now = datetime.utcnow().isoformat()
        query = """
        MATCH ()-[r:HAS_MEMORY]->(m:Memory {id: $memory_id})
        WHERE r.t_invalid IS NULL
        SET r.t_invalid = datetime($now)
        RETURN m.id as memory_id
        """
        result = self.client.query(query, {"memory_id": memory_id, "now": now})
        return len(result) > 0
