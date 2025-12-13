"""
Context-Aware Retrieval.

Retrieves relevant context from the graph for agent operations.
Combines episodic memory, semantic knowledge, and behavioral constraints.
"""
from datetime import datetime
from typing import Optional, Dict, Any, List

from src.graph import get_client


class ContextRetriever:
    """Retrieves contextual information for agents."""

    def __init__(self):
        self.client = get_client()

    def get_agent_context(
        self,
        agent_id: str,
        include_virtues: bool = True,
        include_kuleanas: bool = True,
        include_beliefs: bool = True,
        include_taboos: bool = True,
        include_voice: bool = True,
        include_memories: bool = True,
        memory_limit: int = 5,
    ) -> Dict[str, Any]:
        """
        Get comprehensive context for an agent.

        Args:
            agent_id: Agent instance ID
            include_*: Flags to include various context types
            memory_limit: Max recent memories to include

        Returns:
            Dictionary with all requested context
        """
        context = {"agent_id": agent_id}

        # Get agent basic info
        agent_info = self._get_agent_info(agent_id)
        if agent_info:
            context["agent"] = agent_info

        if include_virtues:
            context["virtues"] = self._get_agent_virtues(agent_id)

        if include_kuleanas:
            context["kuleanas"] = self._get_agent_kuleanas(agent_id)

        if include_beliefs:
            context["beliefs"] = self._get_agent_beliefs(agent_id)

        if include_taboos:
            context["taboos"] = self._get_agent_taboos(agent_id)

        if include_voice:
            context["voice"] = self._get_agent_voice(agent_id)

        if include_memories:
            context["recent_memories"] = self._get_recent_memories(
                agent_id, memory_limit
            )

        return context

    def _get_agent_info(self, agent_id: str) -> Optional[Dict[str, Any]]:
        """Get basic agent information."""
        query = """
        MATCH (a:AgentInstance {id: $agent_id})
        OPTIONAL MATCH (a)-[:IS_TYPE]->(t:AgentType)
        RETURN a, t
        """
        result = self.client.query(query, {"agent_id": agent_id})

        if result and result[0]:
            agent = dict(result[0][0].properties) if result[0][0] else {}
            agent_type = dict(result[0][1].properties) if result[0][1] else {}
            return {
                "instance": agent,
                "type": agent_type,
            }
        return None

    def _get_agent_virtues(self, agent_id: str) -> List[Dict[str, Any]]:
        """Get virtues associated with the agent's type."""
        query = """
        MATCH (a:AgentInstance {id: $agent_id})-[:IS_TYPE]->(t:AgentType)
        MATCH (t)-[r:HAS_VIRTUE]->(v:Virtue)
        WHERE r.t_invalid IS NULL
        RETURN v, r.priority as priority
        ORDER BY r.priority DESC
        """
        result = self.client.query(query, {"agent_id": agent_id})

        virtues = []
        for row in result:
            if row[0]:
                virtue = dict(row[0].properties)
                virtue["priority"] = row[1] if len(row) > 1 else 0
                virtues.append(virtue)
        return virtues

    def _get_agent_kuleanas(self, agent_id: str) -> List[Dict[str, Any]]:
        """Get responsibilities (kuleanas) for the agent's type."""
        query = """
        MATCH (a:AgentInstance {id: $agent_id})-[:IS_TYPE]->(t:AgentType)
        MATCH (t)-[r:HAS_KULEANA]->(k:Kuleana)
        WHERE r.t_invalid IS NULL
        RETURN k, r.priority as priority
        ORDER BY r.priority DESC
        """
        result = self.client.query(query, {"agent_id": agent_id})

        kuleanas = []
        for row in result:
            if row[0]:
                kuleana = dict(row[0].properties)
                kuleana["priority"] = row[1] if len(row) > 1 else 0
                kuleanas.append(kuleana)
        return kuleanas

    def _get_agent_beliefs(self, agent_id: str) -> List[Dict[str, Any]]:
        """Get beliefs for the agent's type."""
        query = """
        MATCH (a:AgentInstance {id: $agent_id})-[:IS_TYPE]->(t:AgentType)
        MATCH (t)-[r:HOLDS_BELIEF]->(b:Belief)
        WHERE r.t_invalid IS NULL
        RETURN b, r.strength as strength
        ORDER BY r.strength DESC
        """
        result = self.client.query(query, {"agent_id": agent_id})

        beliefs = []
        for row in result:
            if row[0]:
                belief = dict(row[0].properties)
                belief["strength"] = row[1] if len(row) > 1 else 1.0
                beliefs.append(belief)
        return beliefs

    def _get_agent_taboos(self, agent_id: str) -> List[Dict[str, Any]]:
        """Get taboos (forbidden actions) for the agent's type."""
        query = """
        MATCH (a:AgentInstance {id: $agent_id})-[:IS_TYPE]->(t:AgentType)
        MATCH (t)-[r:OBSERVES_TABOO]->(tb:Taboo)
        WHERE r.t_invalid IS NULL
        RETURN tb, r.severity as severity
        ORDER BY r.severity DESC
        """
        result = self.client.query(query, {"agent_id": agent_id})

        taboos = []
        for row in result:
            if row[0]:
                taboo = dict(row[0].properties)
                taboo["severity"] = row[1] if len(row) > 1 else "high"
                taboos.append(taboo)
        return taboos

    def _get_agent_voice(self, agent_id: str) -> Dict[str, Any]:
        """Get voice patterns for the agent's type."""
        query = """
        MATCH (a:AgentInstance {id: $agent_id})-[:IS_TYPE]->(t:AgentType)
        MATCH (t)-[r:USES_VOICE]->(v:VoicePattern)
        WHERE r.t_invalid IS NULL
        RETURN v
        """
        result = self.client.query(query, {"agent_id": agent_id})

        voice = {}
        for row in result:
            if row[0]:
                pattern = dict(row[0].properties)
                voice[pattern.get("context", "default")] = pattern

        # Also get emotion responses
        emotion_query = """
        MATCH (a:AgentInstance {id: $agent_id})-[:IS_TYPE]->(t:AgentType)
        MATCH (t)-[:USES_VOICE]->(:VoicePattern)-[:EMOTION_RESPONSE]->(e:EmotionResponse)
        RETURN e
        """
        emotion_result = self.client.query(emotion_query, {"agent_id": agent_id})

        voice["emotions"] = {}
        for row in emotion_result:
            if row[0]:
                emotion = dict(row[0].properties)
                voice["emotions"][emotion.get("emotion", "neutral")] = emotion

        return voice

    def _get_recent_memories(
        self,
        agent_id: str,
        limit: int,
    ) -> List[Dict[str, Any]]:
        """Get recent memories for the agent."""
        query = """
        MATCH (a:AgentInstance {id: $agent_id})-[r:HAS_MEMORY]->(m:Memory)
        WHERE r.t_invalid IS NULL
        RETURN m
        ORDER BY m.last_accessed DESC, m.importance DESC
        LIMIT $limit
        """
        result = self.client.query(query, {"agent_id": agent_id, "limit": limit})

        return [dict(row[0].properties) for row in result if row[0]]

    def get_conversation_context(
        self,
        conversation_id: str,
        message_limit: int = 20,
    ) -> Dict[str, Any]:
        """
        Get context for a conversation.

        Args:
            conversation_id: Conversation ID
            message_limit: Max messages to include

        Returns:
            Conversation context dictionary
        """
        # Get conversation info
        query = """
        MATCH (c:Conversation {id: $conv_id})
        RETURN c
        """
        result = self.client.query(query, {"conv_id": conversation_id})

        context = {}
        if result and result[0] and result[0][0]:
            context["conversation"] = dict(result[0][0].properties)

        # Get recent messages
        msg_query = """
        MATCH (c:Conversation {id: $conv_id})-[:HAS_MESSAGE]->(m:Message)
        RETURN m
        ORDER BY m.timestamp DESC
        LIMIT $limit
        """
        msg_result = self.client.query(msg_query, {
            "conv_id": conversation_id,
            "limit": message_limit,
        })

        context["messages"] = [
            dict(row[0].properties) for row in msg_result if row[0]
        ]

        # Get related episodes
        episode_query = """
        MATCH (c:Conversation {id: $conv_id})-[:CONTAINS_EPISODE]->(e:Episode)
        RETURN e
        ORDER BY e.created_at DESC
        LIMIT 5
        """
        episode_result = self.client.query(episode_query, {"conv_id": conversation_id})

        context["episodes"] = [
            dict(row[0].properties) for row in episode_result if row[0]
        ]

        return context

    def get_relevant_lore(
        self,
        agent_id: str,
        topic: str = None,
        limit: int = 5,
    ) -> List[Dict[str, Any]]:
        """
        Get relevant lore/backstory for the agent.

        Args:
            agent_id: Agent instance ID
            topic: Optional topic filter
            limit: Max lore items to return

        Returns:
            List of lore dictionaries
        """
        topic_filter = "AND l.content CONTAINS $topic" if topic else ""

        query = f"""
        MATCH (a:AgentInstance {{id: $agent_id}})-[:IS_TYPE]->(t:AgentType)
        MATCH (t)-[r:HAS_LORE]->(l:Lore)
        WHERE r.t_invalid IS NULL {topic_filter}
        RETURN l
        ORDER BY l.importance DESC
        LIMIT $limit
        """

        params = {"agent_id": agent_id, "limit": limit}
        if topic:
            params["topic"] = topic

        result = self.client.query(query, params)

        return [dict(row[0].properties) for row in result if row[0]]
