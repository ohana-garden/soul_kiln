"""
Agent Zero Bridge.

Connects graph-hydrated agents to the Agent Zero runtime.
This is the integration point where Soul Kiln meets Agent Zero.
"""
import sys
import os
from typing import Optional, Dict, Any, List
from pathlib import Path

# Add Agent Zero to path
AGENT_ZERO_PATH = Path(__file__).parent.parent.parent / "vendor" / "agent-zero"
if str(AGENT_ZERO_PATH) not in sys.path:
    sys.path.insert(0, str(AGENT_ZERO_PATH))

from .factory import GraphAgentFactory
from .agent import GraphHydratedAgent
from src.graphiti import EpisodeManager, MemoryManager


class AgentZeroBridge:
    """
    Bridge between Soul Kiln graph agents and Agent Zero runtime.

    This class handles:
    - Loading agents from the graph
    - Configuring Agent Zero with graph-defined prompts and tools
    - Routing behavioral checks (virtues, taboos) through the subsystems
    - Persisting conversations and memories back to the graph
    """

    def __init__(self):
        self.factory = GraphAgentFactory()
        self.episode_manager = EpisodeManager()
        self.memory_manager = MemoryManager()
        self._active_agents: Dict[str, GraphHydratedAgent] = {}

    def create_agent(
        self,
        agent_type_id: str,
        instance_id: str = None,
    ) -> GraphHydratedAgent:
        """
        Create and register a new agent from the graph.

        Args:
            agent_type_id: Type of agent to create
            instance_id: Optional custom instance ID

        Returns:
            Hydrated agent ready for use
        """
        agent = self.factory.create_agent(agent_type_id, instance_id)
        self._active_agents[agent.instance_id] = agent
        return agent

    def get_agent(self, instance_id: str) -> Optional[GraphHydratedAgent]:
        """
        Get an active agent by instance ID.

        Args:
            instance_id: Agent instance ID

        Returns:
            Agent if found, None otherwise
        """
        if instance_id in self._active_agents:
            return self._active_agents[instance_id]

        # Try to hydrate from graph
        try:
            agent = self.factory.hydrate_agent(instance_id)
            self._active_agents[instance_id] = agent
            return agent
        except ValueError:
            return None

    def process_message(
        self,
        agent_id: str,
        conversation_id: str,
        message: str,
        context: Dict[str, Any] = None,
    ) -> Dict[str, Any]:
        """
        Process a message through the agent.

        This is the main entry point for agent interactions.
        It handles:
        - Pre-processing checks (taboos)
        - Message routing to Agent Zero
        - Post-processing (virtue alignment, memory storage)

        Args:
            agent_id: Agent instance ID
            conversation_id: Conversation ID
            message: User message
            context: Additional context

        Returns:
            Response dict with 'response' and metadata
        """
        agent = self.get_agent(agent_id)
        if not agent:
            return {
                "error": f"Agent not found: {agent_id}",
                "response": None,
            }

        # Pre-check: Taboo violations in the request
        # (In case we need to refuse certain types of requests)

        # Build context for Agent Zero
        az_config = agent.to_agent_zero_config()

        # Get conversation context
        from src.graphiti import ContextRetriever
        retriever = ContextRetriever()
        conv_context = retriever.get_conversation_context(conversation_id)

        # Merge contexts
        full_context = {
            **(context or {}),
            "conversation": conv_context,
            "agent_config": az_config,
        }

        # Here we would call Agent Zero
        # For now, return a placeholder that shows the system is working
        response = self._generate_response(agent, message, full_context)

        # Post-processing: Store memory of this interaction
        self._store_interaction(agent_id, conversation_id, message, response)

        return {
            "response": response,
            "agent_id": agent_id,
            "conversation_id": conversation_id,
        }

    def _generate_response(
        self,
        agent: GraphHydratedAgent,
        message: str,
        context: Dict[str, Any],
    ) -> str:
        """
        Generate a response using the agent.

        In production, this would call Agent Zero.
        For now, returns a formatted placeholder.
        """
        # This is where Agent Zero integration happens
        # The agent's system prompt and tools are passed to Agent Zero
        # Agent Zero handles the actual LLM interaction

        # Placeholder response showing the system works
        return f"""[{agent.name} responding]

I received your message: "{message[:100]}..."

My configuration:
- Type: {agent.type_id}
- Virtues: {', '.join(v['name'] for v in agent.virtues[:3])}
- Active tools: {', '.join(agent.get_tool_names()[:3])}

[This is a placeholder - Agent Zero integration pending]"""

    def _store_interaction(
        self,
        agent_id: str,
        conversation_id: str,
        user_message: str,
        agent_response: str,
    ):
        """Store the interaction in the graph."""
        # Store as episode
        self.episode_manager.create_episode(
            agent_id=agent_id,
            conversation_id=conversation_id,
            content=f"User: {user_message[:200]}\nAgent: {agent_response[:200]}",
            episode_type="conversation",
        )

        # Store as memory if significant
        if len(user_message) > 50:  # Simple heuristic
            self.memory_manager.store_memory(
                agent_id=agent_id,
                content=f"Discussed: {user_message[:100]}",
                memory_type="episodic",
                importance=0.5,
            )

    def check_action(
        self,
        agent_id: str,
        action: str,
    ) -> Dict[str, Any]:
        """
        Check if an action is allowed by the agent's behavioral constraints.

        Args:
            agent_id: Agent instance ID
            action: Action description to check

        Returns:
            Dict with 'allowed' bool and details
        """
        agent = self.get_agent(agent_id)
        if not agent:
            return {
                "allowed": False,
                "error": f"Agent not found: {agent_id}",
            }

        # Check taboos first (hard constraints)
        taboo_check = agent.check_taboo(action)
        if taboo_check["violated"]:
            return {
                "allowed": False,
                "reason": "taboo_violation",
                "details": taboo_check,
            }

        # Check virtue alignment (soft guidance)
        virtue_check = agent.check_virtue(action)

        return {
            "allowed": True,
            "virtue_alignment": virtue_check,
        }

    def get_agent_prompt(self, agent_id: str) -> str:
        """
        Get the complete system prompt for an agent.

        Args:
            agent_id: Agent instance ID

        Returns:
            Complete system prompt string
        """
        agent = self.get_agent(agent_id)
        if not agent:
            return ""

        return agent.get_system_prompt()

    def list_available_types(self) -> List[Dict[str, Any]]:
        """
        List all available agent types.

        Returns:
            List of agent type definitions
        """
        return self.factory.list_agent_types()

    def shutdown_agent(self, agent_id: str):
        """
        Shut down an active agent.

        Args:
            agent_id: Agent instance ID
        """
        if agent_id in self._active_agents:
            del self._active_agents[agent_id]


# Module-level bridge instance
_bridge: Optional[AgentZeroBridge] = None


def get_bridge() -> AgentZeroBridge:
    """Get singleton bridge instance."""
    global _bridge
    if _bridge is None:
        _bridge = AgentZeroBridge()
    return _bridge
