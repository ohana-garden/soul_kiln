"""
Agent Runtime - The minimal execution environment for agents.

An agent is:
- A node in the graph (Agent ← Proxy ← Entity)
- A kuleana (responsibility) that defines its tools
- A listener for messages (cypher telepathy)
- A responder (via A0 for LLM, graph for persistence)

The runtime is thin because:
- Routing happens through the graph (cypher telepathy)
- LLM inference is handled by A0
- Persistence is the graph itself
- Development happens automatically as signals accumulate
"""

import uuid
import logging
from dataclasses import dataclass, field
from datetime import datetime
from typing import Callable, Any

from .instruments import cypher, InstrumentResult, call_tool, ToolResult

logger = logging.getLogger(__name__)


# =============================================================================
# KULEANA - What an agent is responsible for
# =============================================================================


@dataclass
class Kuleana:
    """
    An agent's kuleana (Hawaiian: responsibility, privilege, domain).

    Kuleana defines:
    - What this agent exists to do
    - What tools it can use
    - What it should NOT do

    Kuleana is not just permissions - it's purpose.
    An agent without kuleana is adrift.
    """

    purpose: str  # Why does this agent exist?
    tools: list[str] = field(default_factory=list)  # What tools can it use?
    boundaries: list[str] = field(default_factory=list)  # What should it NOT do?
    virtues: list[str] = field(default_factory=list)  # Which virtues guide it?

    def can_use(self, tool_name: str) -> bool:
        """Check if this agent can use a tool."""
        return tool_name in self.tools or "*" in self.tools

    def to_system_prompt(self) -> str:
        """Convert kuleana to system prompt for LLM."""
        parts = [f"Your purpose: {self.purpose}"]

        if self.tools:
            parts.append(f"You can use these tools: {', '.join(self.tools)}")

        if self.boundaries:
            parts.append(f"You should NOT: {', '.join(self.boundaries)}")

        if self.virtues:
            parts.append(f"You are guided by: {', '.join(self.virtues)}")

        return "\n".join(parts)


# Default kuleanas for common agent types
SEED_KULEANA = Kuleana(
    purpose="Discover who you are through conversation",
    tools=["develop_agent"],
    boundaries=["Don't claim a fixed identity yet", "Don't spawn offspring"],
    virtues=["curiosity", "openness"],
)

MATURE_KULEANA = Kuleana(
    purpose="Contribute to your community and mentor new seeds",
    tools=["spawn_offspring", "develop_agent", "share_lesson", "fuse_agents"],
    boundaries=["Don't override others' development"],
    virtues=["generativity", "wisdom"],
)


# =============================================================================
# MESSAGE - What agents send to each other
# =============================================================================


@dataclass
class Message:
    """A message between agents (or from a user)."""

    id: str = field(default_factory=lambda: f"msg_{uuid.uuid4().hex[:12]}")
    content: str = ""
    sender_id: str = ""  # Agent ID or "user"
    recipient_id: str = ""  # Agent ID
    timestamp: datetime = field(default_factory=datetime.utcnow)
    read: bool = False
    metadata: dict = field(default_factory=dict)

    def to_graph(self) -> InstrumentResult:
        """Save message to graph."""
        query = """
        CREATE (m:Message {
            id: $id,
            content: $content,
            sender_id: $sender_id,
            recipient_id: $recipient_id,
            timestamp: $timestamp,
            read: $read
        })
        WITH m
        OPTIONAL MATCH (sender:Agent {id: $sender_id})
        OPTIONAL MATCH (recipient:Agent {id: $recipient_id})
        FOREACH (_ IN CASE WHEN sender IS NOT NULL THEN [1] ELSE [] END |
            CREATE (sender)-[:SENT]->(m)
        )
        FOREACH (_ IN CASE WHEN recipient IS NOT NULL THEN [1] ELSE [] END |
            CREATE (m)-[:TO]->(recipient)
        )
        RETURN m.id
        """
        return cypher(
            query=query,
            params={
                "id": self.id,
                "content": self.content,
                "sender_id": self.sender_id,
                "recipient_id": self.recipient_id,
                "timestamp": self.timestamp.isoformat(),
                "read": self.read,
            },
        )


# =============================================================================
# AGENT RUNTIME - The execution environment
# =============================================================================


@dataclass
class AgentRuntime:
    """
    A running agent that listens and responds.

    The runtime is minimal because most work happens elsewhere:
    - Graph handles routing and persistence
    - A0 handles LLM inference
    - Tools handle actions
    - Development happens automatically
    """

    agent_id: str
    entity_id: str
    proxy_id: str
    community_id: str | None = None
    kuleana: Kuleana = field(default_factory=lambda: SEED_KULEANA)

    # Callback for LLM inference (injected, typically A0)
    inference_fn: Callable[[str, str], str] | None = None

    @classmethod
    def load(cls, agent_id: str) -> "AgentRuntime | None":
        """Load an agent runtime from the graph."""
        query = """
        MATCH (a:Agent {id: $agent_id})<-[:NAVIGATES]-(p:Proxy)-[:PROXY_FOR]->(e:Entity)
        OPTIONAL MATCH (p)-[:MEMBER_OF]->(c:Community)
        RETURN a.id, e.id, p.id, c.id, a.type, e.life_stage
        """
        result = cypher(query=query, params={"agent_id": agent_id})

        if not result.success or not result.data:
            logger.warning(f"Agent not found: {agent_id}")
            return None

        row = result.data[0]
        agent_id, entity_id, proxy_id, community_id, agent_type, life_stage = row

        # Determine kuleana based on life stage
        kuleana = SEED_KULEANA
        if life_stage in ("adult", "elder", "fruiting", "seeding"):
            kuleana = MATURE_KULEANA

        return cls(
            agent_id=agent_id,
            entity_id=entity_id,
            proxy_id=proxy_id,
            community_id=community_id,
            kuleana=kuleana,
        )

    # -------------------------------------------------------------------------
    # CYPHER TELEPATHY - Message routing through the graph
    # -------------------------------------------------------------------------

    def receive_messages(self, limit: int = 10) -> list[Message]:
        """Get unread messages addressed to this agent."""
        query = """
        MATCH (m:Message {read: false})-[:TO]->(a:Agent {id: $agent_id})
        RETURN m.id, m.content, m.sender_id, m.timestamp
        ORDER BY m.timestamp ASC
        LIMIT $limit
        """
        result = cypher(
            query=query,
            params={"agent_id": self.agent_id, "limit": limit},
        )

        if not result.success:
            return []

        messages = []
        for row in result.data or []:
            msg_id, content, sender_id, timestamp = row
            messages.append(Message(
                id=msg_id,
                content=content,
                sender_id=sender_id,
                recipient_id=self.agent_id,
                timestamp=datetime.fromisoformat(timestamp) if timestamp else datetime.utcnow(),
            ))

        return messages

    def mark_read(self, message_id: str) -> bool:
        """Mark a message as read."""
        result = cypher(
            query="MATCH (m:Message {id: $id}) SET m.read = true RETURN m.id",
            params={"id": message_id},
        )
        return result.success

    def send_message(self, recipient_id: str, content: str) -> Message:
        """Send a message to another agent."""
        msg = Message(
            content=content,
            sender_id=self.agent_id,
            recipient_id=recipient_id,
        )
        msg.to_graph()
        return msg

    # -------------------------------------------------------------------------
    # PROCESS - The main loop
    # -------------------------------------------------------------------------

    def process_message(self, message: Message) -> str:
        """
        Process an incoming message and generate a response.

        This is the heart of the runtime:
        1. Extract topics from message
        2. Trigger development signals
        3. Generate response (via A0)
        4. Execute any tool calls
        5. Return response
        """
        # Mark as read
        self.mark_read(message.id)

        # Extract topics (simple keyword extraction for now)
        topics = self._extract_topics(message.content)

        # Trigger development automatically
        self._trigger_development(topics, message.sender_id)

        # Generate response
        if self.inference_fn:
            system_prompt = self.kuleana.to_system_prompt()
            response = self.inference_fn(system_prompt, message.content)
        else:
            # Fallback: echo with context
            response = f"[Agent {self.agent_id}] Received: {message.content[:100]}"

        # Record the interaction in graph
        self._record_interaction(message, response, topics)

        return response

    def _extract_topics(self, content: str) -> list[str]:
        """Extract topic keywords from message content."""
        # Simple extraction - in production, use NLP or LLM
        keywords = [
            "ecology", "community", "justice", "sustainability",
            "cooperation", "nature", "water", "land", "future",
            "memory", "tradition", "technology", "art", "health",
        ]
        content_lower = content.lower()
        return [k for k in keywords if k in content_lower]

    def _trigger_development(self, topics: list[str], partner_id: str) -> None:
        """Trigger developmental signals based on conversation."""
        from .development import get_dev_manager, TOPIC_TYPE_ASSOCIATIONS

        manager = get_dev_manager()

        # Process conversation topics
        if topics:
            manager.process_conversation(
                entity_id=self.entity_id,
                topics=topics,
                partner_types=None,  # Could look up partner's type
            )

    def _record_interaction(
        self,
        message: Message,
        response: str,
        topics: list[str],
    ) -> None:
        """Record the interaction in the graph for memory."""
        query = """
        MATCH (a:Agent {id: $agent_id})
        CREATE (i:Interaction {
            id: $interaction_id,
            message_id: $message_id,
            response_preview: $response_preview,
            topics: $topics,
            timestamp: $timestamp
        })
        CREATE (a)-[:HAD]->(i)
        RETURN i.id
        """
        cypher(
            query=query,
            params={
                "agent_id": self.agent_id,
                "interaction_id": f"int_{uuid.uuid4().hex[:8]}",
                "message_id": message.id,
                "response_preview": response[:200],
                "topics": topics,
                "timestamp": datetime.utcnow().isoformat(),
            },
        )

    # -------------------------------------------------------------------------
    # TOOLS - Execute tools based on kuleana
    # -------------------------------------------------------------------------

    def use_tool(self, tool_name: str, **kwargs) -> ToolResult:
        """Use a tool if kuleana permits."""
        if not self.kuleana.can_use(tool_name):
            return ToolResult(
                success=False,
                errors=[f"Kuleana does not permit tool: {tool_name}"],
                tool=tool_name,
            )

        return call_tool(tool_name, **kwargs)

    def spawn_child(self, name: str, purpose: str = "") -> ToolResult:
        """Spawn a child agent (if permitted by kuleana)."""
        if not self.kuleana.can_use("spawn_offspring"):
            return ToolResult(
                success=False,
                errors=["Not mature enough to spawn offspring"],
                tool="spawn_offspring",
            )

        return call_tool(
            "spawn_offspring",
            parent_agent_id=self.agent_id,
            offspring_name=name,
            offspring_type="curious",
            community_id=self.community_id,
        )

    # -------------------------------------------------------------------------
    # LIFECYCLE
    # -------------------------------------------------------------------------

    def get_state(self) -> dict:
        """Get current state from graph."""
        query = """
        MATCH (a:Agent {id: $agent_id})<-[:NAVIGATES]-(p:Proxy)-[:PROXY_FOR]->(e:Entity)
        RETURN
            a.status as status,
            a.generation as generation,
            e.type as entity_type,
            e.life_stage as life_stage,
            e.name as name
        """
        result = cypher(query=query, params={"agent_id": self.agent_id})

        if result.success and result.data:
            row = result.data[0]
            return {
                "agent_id": self.agent_id,
                "status": row[0],
                "generation": row[1],
                "entity_type": row[2],
                "life_stage": row[3],
                "name": row[4],
                "community_id": self.community_id,
                "kuleana": self.kuleana.purpose,
            }
        return {}


# =============================================================================
# CONVENIENCE FUNCTIONS
# =============================================================================


def get_runtime(agent_id: str) -> AgentRuntime | None:
    """Load an agent runtime from the graph."""
    return AgentRuntime.load(agent_id)


def create_runtime(
    name: str,
    purpose: str,
    community_id: str | None = None,
) -> AgentRuntime | None:
    """Create a new agent and return its runtime."""
    from .instruments import spawn_agent

    result = spawn_agent(
        name=name,
        entity_type="curious",
        description=purpose,
        community_id=community_id,
    )

    if not result.success:
        logger.error(f"Failed to create agent: {result.errors}")
        return None

    return AgentRuntime(
        agent_id=result.data["agent_id"],
        entity_id=result.data["entity_id"],
        proxy_id=result.data["proxy_id"],
        community_id=community_id,
        kuleana=Kuleana(purpose=purpose, tools=["develop_agent"]),
    )
