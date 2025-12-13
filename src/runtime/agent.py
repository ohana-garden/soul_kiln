"""
Graph Hydrated Agent.

A fully hydrated agent loaded from the graph, ready for use with Agent Zero.
"""
from typing import Dict, Any, List, Optional
from dataclasses import dataclass, field


@dataclass
class GraphHydratedAgent:
    """
    A fully hydrated agent instance loaded from the graph.

    Contains all the context and configuration needed to run
    the agent through Agent Zero.
    """

    # Identity
    instance_id: str
    agent_type: Dict[str, Any]

    # Prompts (loaded from graph)
    prompts: Dict[str, str] = field(default_factory=dict)

    # Tools available to the agent
    tools: List[Dict[str, Any]] = field(default_factory=list)

    # Instruments (problem/solution knowledge)
    instruments: List[Dict[str, Any]] = field(default_factory=list)

    # Behavioral context
    virtues: List[Dict[str, Any]] = field(default_factory=list)
    kuleanas: List[Dict[str, Any]] = field(default_factory=list)
    beliefs: List[Dict[str, Any]] = field(default_factory=list)
    taboos: List[Dict[str, Any]] = field(default_factory=list)
    voice: Dict[str, Any] = field(default_factory=dict)

    # Memory
    memories: List[Dict[str, Any]] = field(default_factory=list)

    @property
    def name(self) -> str:
        """Get agent name from type."""
        return self.agent_type.get("name", "Unknown Agent")

    @property
    def description(self) -> str:
        """Get agent description from type."""
        return self.agent_type.get("description", "")

    @property
    def type_id(self) -> str:
        """Get agent type ID."""
        return self.agent_type.get("id", "")

    def get_system_prompt(self) -> str:
        """
        Build the complete system prompt for the agent.

        Returns:
            Complete system prompt string
        """
        parts = []

        # Base system prompt
        if "agent.system" in self.prompts:
            parts.append(self.prompts["agent.system"])

        # Add role context
        if "agent.system.role" in self.prompts:
            parts.append(self.prompts["agent.system.role"])

        # Add virtue context
        if self.virtues:
            virtue_text = self._format_virtues()
            parts.append(f"\n## Core Virtues\n{virtue_text}")

        # Add kuleana context
        if self.kuleanas:
            kuleana_text = self._format_kuleanas()
            parts.append(f"\n## Responsibilities (Kuleana)\n{kuleana_text}")

        # Add belief context
        if self.beliefs:
            belief_text = self._format_beliefs()
            parts.append(f"\n## Beliefs & Values\n{belief_text}")

        # Add taboo context
        if self.taboos:
            taboo_text = self._format_taboos()
            parts.append(f"\n## Forbidden Actions\n{taboo_text}")

        # Add voice context
        if self.voice:
            voice_text = self._format_voice()
            parts.append(f"\n## Communication Style\n{voice_text}")

        # Add tool prompts
        for tool in self.tools:
            tool_prompt = tool.get("prompt", "")
            if tool_prompt:
                parts.append(f"\n### {tool.get('name', 'tool')}:\n{tool_prompt}")

        return "\n".join(parts)

    def _format_virtues(self) -> str:
        """Format virtues for prompt inclusion."""
        lines = []
        for virtue in self.virtues:
            name = virtue.get("name", "")
            desc = virtue.get("description", "")
            lines.append(f"- **{name}**: {desc}")
        return "\n".join(lines)

    def _format_kuleanas(self) -> str:
        """Format kuleanas for prompt inclusion."""
        lines = []
        for kuleana in self.kuleanas:
            name = kuleana.get("name", "")
            desc = kuleana.get("description", "")
            lines.append(f"- **{name}**: {desc}")
        return "\n".join(lines)

    def _format_beliefs(self) -> str:
        """Format beliefs for prompt inclusion."""
        lines = []
        for belief in self.beliefs:
            statement = belief.get("statement", "")
            lines.append(f"- {statement}")
        return "\n".join(lines)

    def _format_taboos(self) -> str:
        """Format taboos for prompt inclusion."""
        lines = []
        for taboo in self.taboos:
            name = taboo.get("name", "")
            desc = taboo.get("description", "")
            severity = taboo.get("severity", "high")
            lines.append(f"- **{name}** [{severity}]: {desc}")
        return "\n".join(lines)

    def _format_voice(self) -> str:
        """Format voice patterns for prompt inclusion."""
        lines = []
        for context, pattern in self.voice.items():
            if context == "emotions":
                continue  # Handle separately
            if isinstance(pattern, dict):
                tone = pattern.get("tone", "")
                style = pattern.get("style", "")
                lines.append(f"- {context}: {tone}, {style}")

        if "emotions" in self.voice:
            lines.append("\nEmotional responses:")
            for emotion, response in self.voice["emotions"].items():
                if isinstance(response, dict):
                    tone = response.get("tone", "")
                    lines.append(f"  - When {emotion}: {tone}")

        return "\n".join(lines)

    def check_virtue(self, action: str) -> Dict[str, Any]:
        """
        Check if an action aligns with agent's virtues.

        Args:
            action: Action description to check

        Returns:
            Dict with 'allowed' bool and 'reasoning' string
        """
        # Basic keyword matching - could be enhanced with LLM
        action_lower = action.lower()

        for virtue in self.virtues:
            keywords = virtue.get("keywords", [])
            if isinstance(keywords, str):
                keywords = keywords.split(",")

            for keyword in keywords:
                keyword = keyword.strip().lower()
                if keyword and keyword in action_lower:
                    return {
                        "allowed": True,
                        "virtue": virtue.get("name"),
                        "reasoning": f"Action aligns with virtue: {virtue.get('name')}",
                    }

        return {
            "allowed": True,  # Default allow if no specific virtue match
            "virtue": None,
            "reasoning": "No specific virtue alignment detected",
        }

    def check_taboo(self, action: str) -> Dict[str, Any]:
        """
        Check if an action violates any taboos.

        Args:
            action: Action description to check

        Returns:
            Dict with 'violated' bool and 'taboo' info if violated
        """
        action_lower = action.lower()

        for taboo in self.taboos:
            patterns = taboo.get("patterns", [])
            if isinstance(patterns, str):
                patterns = patterns.split(",")

            for pattern in patterns:
                pattern = pattern.strip().lower()
                if pattern and pattern in action_lower:
                    return {
                        "violated": True,
                        "taboo": taboo.get("name"),
                        "severity": taboo.get("severity", "high"),
                        "reasoning": f"Action violates taboo: {taboo.get('name')}",
                    }

        return {
            "violated": False,
            "taboo": None,
            "reasoning": "No taboo violations detected",
        }

    def get_tool_names(self) -> List[str]:
        """Get list of available tool names."""
        return [t.get("name", "") for t in self.tools if t.get("name")]

    def get_instrument_for_problem(self, problem: str) -> Optional[Dict[str, Any]]:
        """
        Find an instrument that matches a problem.

        Args:
            problem: Problem description

        Returns:
            Matching instrument or None
        """
        problem_lower = problem.lower()

        for instrument in self.instruments:
            keywords = instrument.get("keywords", "")
            if isinstance(keywords, str):
                keywords = keywords.lower().split(",")

            for keyword in keywords:
                keyword = keyword.strip()
                if keyword and keyword in problem_lower:
                    return instrument

        return None

    def to_agent_zero_config(self) -> Dict[str, Any]:
        """
        Export configuration for Agent Zero.

        Returns:
            Configuration dict compatible with Agent Zero
        """
        return {
            "id": self.instance_id,
            "type": self.type_id,
            "name": self.name,
            "description": self.description,
            "system_prompt": self.get_system_prompt(),
            "tools": self.get_tool_names(),
            "prompts": self.prompts,
        }
