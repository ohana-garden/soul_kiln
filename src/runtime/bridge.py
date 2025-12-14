"""
Agent Zero Bridge.

Connects graph-hydrated agents to the Agent Zero runtime.
ALL EXECUTION HAPPENS THROUGH GRAPH-LOADED SSFs - no hardcoded behavior.
"""
import sys
import os
import logging
from typing import Optional, Dict, Any, List
from pathlib import Path

# Add Agent Zero to path
AGENT_ZERO_PATH = Path(__file__).parent.parent.parent / "vendor" / "agent-zero"
if str(AGENT_ZERO_PATH) not in sys.path:
    sys.path.insert(0, str(AGENT_ZERO_PATH))

from .factory import GraphAgentFactory
from .agent import GraphHydratedAgent
from .ssf import get_ssf_registry, SSFRegistry
from src.graphiti import EpisodeManager, MemoryManager
from src.graph import get_client
from src.llm import get_llm_client

logger = logging.getLogger(__name__)


class AgentZeroBridge:
    """
    Bridge between Soul Kiln graph agents and Agent Zero runtime.

    ALL behavior is loaded from the graph:
    - Prompts come from graph
    - Tools are SSFs in the graph
    - Hooks are SSFs in the graph
    - Validation rules are SSFs in the graph
    """

    def __init__(self):
        self.factory = GraphAgentFactory()
        self.episode_manager = EpisodeManager()
        self.memory_manager = MemoryManager()
        self.ssf_registry = get_ssf_registry()
        self.llm_client = get_llm_client()
        self._active_agents: Dict[str, GraphHydratedAgent] = {}
        self._client = get_client()

    def create_agent(
        self,
        agent_type_id: str,
        instance_id: str = None,
    ) -> GraphHydratedAgent:
        """Create and register a new agent from the graph."""
        agent = self.factory.create_agent(agent_type_id, instance_id)
        self._active_agents[agent.instance_id] = agent
        return agent

    def get_agent(self, instance_id: str) -> Optional[GraphHydratedAgent]:
        """Get an active agent by instance ID."""
        if instance_id in self._active_agents:
            return self._active_agents[instance_id]

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

        All processing uses SSFs from the graph:
        1. Run pre-response hooks (validation, taboo checks)
        2. Generate response using graph-defined prompts
        3. Run post-response hooks (logging, memory)
        """
        agent = self.get_agent(agent_id)
        if not agent:
            return {
                "error": f"Agent not found: {agent_id}",
                "response": None,
            }

        # Build execution context
        exec_context = {
            "agent_id": agent_id,
            "agent": {"name": agent.name, "type_id": agent.type_id},
            "conversation_id": conversation_id,
            "message": message,
            **(context or {}),
        }

        # Step 1: Run pre-response hooks from graph
        hook_results = self._run_hooks(agent.type_id, "pre_response", exec_context)

        # Check if any hook blocked the request
        for result in hook_results:
            if result.get("taboo_check", {}).get("violated"):
                return {
                    "error": "Request blocked by taboo check",
                    "response": None,
                    "taboo_violations": result["taboo_check"]["violations"],
                }

        # Step 2: Generate response using graph-loaded SSFs
        response = self._generate_response(agent, message, exec_context)

        # Step 3: Run post-response hooks
        exec_context["response"] = response
        self._run_hooks(agent.type_id, "post_response", exec_context)

        # Step 4: Store interaction in graph
        self._store_interaction(agent_id, conversation_id, message, response)

        return {
            "response": response,
            "agent_id": agent_id,
            "conversation_id": conversation_id,
            "hooks_executed": len(hook_results),
        }

    def _run_hooks(
        self,
        agent_type_id: str,
        hook_type: str,
        context: Dict[str, Any],
    ) -> List[Dict[str, Any]]:
        """Run all hooks of a given type for an agent."""
        # Get hook SSFs from graph
        query = """
        MATCH (t:AgentType {id: $type_id})-[:HAS_SSF]->(s:SSF)
        WHERE s.ssf_type = 'hook' AND s.hook_type = $hook_type
        RETURN s.id as ssf_id
        """
        result = self._client.query(query, {
            "type_id": agent_type_id,
            "hook_type": hook_type,
        })

        results = []
        for row in result:
            if row[0]:
                ssf_id = row[0]
                try:
                    hook_result = self.ssf_registry.execute(ssf_id, context)
                    results.append(hook_result)
                except Exception as e:
                    results.append({"error": str(e), "ssf_id": ssf_id})

        return results

    def _generate_response(
        self,
        agent: GraphHydratedAgent,
        message: str,
        context: Dict[str, Any],
    ) -> str:
        """
        Generate a response using graph-loaded prompts and LLM.

        This builds the full prompt from graph data and calls Claude.
        """
        # Step 1: Build system prompt from graph using prompt generator SSF
        system_prompt = self._build_system_prompt(agent)

        # Step 2: Check if any tools should be activated
        tool_results = self._check_tool_activation(agent.type_id, message, context)

        # Step 3: Build enhanced user message with tool context
        user_message = message
        if tool_results:
            tool_context = "\n\n[Tool Results from Graph SSFs]\n"
            for tool_name, result in tool_results.items():
                if isinstance(result, dict) and "prompt" in result:
                    tool_context += f"\n{tool_name}:\n{result['prompt']}\n"
                elif isinstance(result, dict) and "error" not in result:
                    tool_context += f"\n{tool_name}: {result}\n"
            user_message = f"{message}\n{tool_context}"

        # Step 4: Call LLM if configured
        if self.llm_client.is_configured:
            try:
                logger.info(f"Generating LLM response for agent {agent.name}")
                llm_response = self.llm_client.generate(
                    system_prompt=system_prompt,
                    user_message=user_message,
                    temperature=0.7,
                )
                logger.info(
                    f"LLM response generated: {llm_response.input_tokens} in, "
                    f"{llm_response.output_tokens} out"
                )
                return llm_response.content
            except Exception as e:
                logger.error(f"LLM generation failed: {e}")
                return self._fallback_response(agent, message, tool_results, str(e))
        else:
            # LLM not configured - return informative fallback
            logger.warning("LLM not configured, using fallback response")
            return self._fallback_response(agent, message, tool_results)

    def _fallback_response(
        self,
        agent: GraphHydratedAgent,
        message: str,
        tool_results: Dict[str, Any],
        error: str = None,
    ) -> str:
        """Generate a fallback response when LLM is unavailable."""
        parts = [f"[{agent.name} - LLM Not Configured]"]

        if error:
            parts.append(f"\n⚠️ Error: {error}")

        parts.append(f"\n\n💬 Your message: \"{message[:200]}\"")

        if tool_results:
            parts.append("\n\n📊 Tool Results (from Graph SSFs):")
            for tool_name, result in tool_results.items():
                if isinstance(result, dict) and "prompt" in result:
                    parts.append(f"\n  {tool_name}:\n    {result['prompt'][:300]}")
                elif isinstance(result, dict) and "error" not in result:
                    parts.append(f"\n  {tool_name}: {result}")

        parts.append(f"\n\n🎭 Agent loaded from graph:")
        parts.append(f"  - Type: {agent.type_id}")
        parts.append(f"  - Virtues: {len(agent.virtues)}")
        parts.append(f"  - Kuleanas: {len(agent.kuleanas)}")
        parts.append(f"  - SSFs: {len(self._get_agent_ssfs(agent.type_id))}")

        parts.append("\n\n💡 To enable LLM responses, set ANTHROPIC_API_KEY in your .env file")

        return "\n".join(parts)

    def _build_system_prompt(self, agent: GraphHydratedAgent) -> str:
        """Build system prompt using graph-loaded prompt generator SSF."""
        # Try to find a prompt generator SSF
        query = """
        MATCH (t:AgentType {id: $type_id})-[:HAS_SSF]->(s:SSF)
        WHERE s.ssf_type = 'prompt_generator'
        RETURN s.id as ssf_id, s.prompt_template as template
        LIMIT 1
        """
        result = self._client.query(query, {"type_id": agent.type_id})

        if result and result[0]:
            template = result[0][1] if len(result[0]) > 1 else ""
            if template:
                # Build context for template
                context = {
                    "base_prompt": agent.prompts.get("agent.system", ""),
                    "virtues_section": self._format_section(agent.virtues, "name", "description"),
                    "kuleanas_section": self._format_section(agent.kuleanas, "name", "description"),
                    "beliefs_section": self._format_section(agent.beliefs, "statement"),
                    "taboos_section": self._format_section(agent.taboos, "name", "description"),
                    "voice_section": self._format_voice(agent.voice),
                }
                return self.ssf_registry._render_template(template, context)

        # Fallback to agent's built-in prompt builder
        return agent.get_system_prompt()

    def _format_section(self, items: List[Dict], *keys) -> str:
        """Format a list of items for prompt inclusion."""
        lines = []
        for item in items:
            parts = [str(item.get(k, "")) for k in keys if item.get(k)]
            if parts:
                lines.append(f"- {': '.join(parts)}")
        return "\n".join(lines) if lines else "None defined"

    def _format_voice(self, voice: Dict) -> str:
        """Format voice patterns for prompt."""
        lines = []
        for key, value in voice.items():
            if key != "emotions" and isinstance(value, dict):
                tone = value.get("tone", "")
                if tone:
                    lines.append(f"- {key}: {tone}")
        return "\n".join(lines) if lines else "Default professional tone"

    def _check_tool_activation(
        self,
        agent_type_id: str,
        message: str,
        context: Dict[str, Any],
    ) -> Dict[str, Any]:
        """Check if any tool SSFs should be activated based on message."""
        results = {}

        # Get tool SSFs
        query = """
        MATCH (t:AgentType {id: $type_id})-[:HAS_SSF]->(s:SSF)
        WHERE s.ssf_type = 'tool'
        RETURN s.id as ssf_id, s.name as name, s.description as desc
        """
        tools = self._client.query(query, {"type_id": agent_type_id})

        message_lower = message.lower()

        for row in tools:
            if row[0]:
                ssf_id = row[0]
                name = row[1] if len(row) > 1 else ssf_id
                desc = row[2] if len(row) > 2 else ""

                # Simple activation check - in production this would be smarter
                keywords = desc.lower().split() if desc else []
                should_activate = any(kw in message_lower for kw in keywords if len(kw) > 3)

                if should_activate:
                    try:
                        result = self.ssf_registry.execute(ssf_id, context)
                        results[name] = result
                    except Exception as e:
                        results[name] = {"error": str(e)}

        return results

    def _get_agent_ssfs(self, agent_type_id: str) -> List[str]:
        """Get all SSF IDs for an agent type."""
        query = """
        MATCH (t:AgentType {id: $type_id})-[:HAS_SSF]->(s:SSF)
        RETURN s.id
        """
        result = self._client.query(query, {"type_id": agent_type_id})
        return [row[0] for row in result if row[0]]

    def _store_interaction(
        self,
        agent_id: str,
        conversation_id: str,
        user_message: str,
        agent_response: str,
    ):
        """Store the interaction in the graph."""
        self.episode_manager.create_episode(
            agent_id=agent_id,
            conversation_id=conversation_id,
            content=f"User: {user_message[:200]}\nAgent: {agent_response[:200]}",
            episode_type="conversation",
        )

        if len(user_message) > 50:
            self.memory_manager.store_memory(
                agent_id=agent_id,
                content=f"Discussed: {user_message[:100]}",
                memory_type="episodic",
                importance=0.5,
            )

    def execute_tool(
        self,
        agent_id: str,
        tool_ssf_id: str,
        tool_args: Dict[str, Any],
    ) -> Dict[str, Any]:
        """
        Execute a specific tool SSF.

        Args:
            agent_id: Agent instance ID
            tool_ssf_id: SSF ID of the tool to execute
            tool_args: Arguments for the tool

        Returns:
            Tool execution result
        """
        agent = self.get_agent(agent_id)
        if not agent:
            return {"error": f"Agent not found: {agent_id}"}

        context = {
            "agent_id": agent_id,
            "agent": {"name": agent.name, "type_id": agent.type_id},
            **tool_args,
        }

        try:
            return self.ssf_registry.execute(tool_ssf_id, context)
        except Exception as e:
            return {"error": str(e)}

    def check_action(
        self,
        agent_id: str,
        action: str,
    ) -> Dict[str, Any]:
        """Check if an action is allowed by behavioral constraints."""
        agent = self.get_agent(agent_id)
        if not agent:
            return {"allowed": False, "error": f"Agent not found: {agent_id}"}

        taboo_check = agent.check_taboo(action)
        if taboo_check["violated"]:
            return {
                "allowed": False,
                "reason": "taboo_violation",
                "details": taboo_check,
            }

        virtue_check = agent.check_virtue(action)
        return {
            "allowed": True,
            "virtue_alignment": virtue_check,
        }

    def get_agent_prompt(self, agent_id: str) -> str:
        """Get the complete system prompt (built from graph)."""
        agent = self.get_agent(agent_id)
        if not agent:
            return ""
        return self._build_system_prompt(agent)

    def list_available_types(self) -> List[Dict[str, Any]]:
        """List all available agent types."""
        return self.factory.list_agent_types()

    def list_agent_ssfs(self, agent_type_id: str) -> List[Dict[str, Any]]:
        """List all SSFs for an agent type."""
        query = """
        MATCH (t:AgentType {id: $type_id})-[:HAS_SSF]->(s:SSF)
        RETURN s
        """
        result = self._client.query(query, {"type_id": agent_type_id})
        return [dict(row[0].properties) for row in result if row[0]]

    def shutdown_agent(self, agent_id: str):
        """Shut down an active agent."""
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
