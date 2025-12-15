"""
Agent Factory.

Creates agents from conversational intake data.
Handles the full lifecycle from context gathering to agent instantiation.
"""

import logging
import uuid
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Callable

from ..model import Community
from ..registry import get_registry
from ..membership import MembershipManager
from ..integration import get_community_integration
from .prompts import get_agent_prompt, get_tool_prompts, render_prompt

logger = logging.getLogger(__name__)


class GuidanceLevel(str, Enum):
    """How much guidance the agent should provide."""
    HIGH = "high"      # Explain everything, step-by-step
    MEDIUM = "medium"  # Context when useful
    LOW = "low"        # Concise, trust user expertise


class CommunicationStyle(str, Enum):
    """How the agent should communicate."""
    FORMAL = "formal"
    CONVERSATIONAL = "conversational"
    BRIEF = "brief"


@dataclass
class AgentConfig:
    """Configuration for creating an agent."""

    # Identity
    agent_id: str = field(default_factory=lambda: f"agent_{uuid.uuid4().hex[:12]}")
    name: str = ""

    # Community assignment
    community_id: str = ""
    community_name: str = ""

    # User/Organization context
    context: dict[str, Any] = field(default_factory=dict)

    # Preferences
    guidance_level: GuidanceLevel = GuidanceLevel.MEDIUM
    communication_style: CommunicationStyle = CommunicationStyle.CONVERSATIONAL

    # Metadata
    created_at: datetime = field(default_factory=datetime.utcnow)
    created_by: str = ""  # Human creator
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict:
        """Convert to dictionary."""
        return {
            "agent_id": self.agent_id,
            "name": self.name,
            "community_id": self.community_id,
            "community_name": self.community_name,
            "context": self.context,
            "preferences": {
                "guidance_level": self.guidance_level.value,
                "communication_style": self.communication_style.value,
            },
            "created_at": self.created_at.isoformat(),
            "created_by": self.created_by,
            "metadata": self.metadata,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "AgentConfig":
        """Create from dictionary."""
        prefs = data.get("preferences", {})
        return cls(
            agent_id=data.get("agent_id", f"agent_{uuid.uuid4().hex[:12]}"),
            name=data.get("name", ""),
            community_id=data.get("community_id", ""),
            community_name=data.get("community_name", ""),
            context=data.get("context", {}),
            guidance_level=GuidanceLevel(prefs.get("guidance_level", "medium")),
            communication_style=CommunicationStyle(prefs.get("communication_style", "conversational")),
            created_by=data.get("created_by", ""),
            metadata=data.get("metadata", {}),
        )


@dataclass
class CreatedAgent:
    """Result of agent creation."""

    agent_id: str
    name: str
    community: Community
    system_prompt: str
    tool_prompts: dict[str, str]
    config: AgentConfig
    introduction: str  # What the agent says when it first meets the user

    def to_dict(self) -> dict:
        """Convert to dictionary."""
        return {
            "agent_id": self.agent_id,
            "name": self.name,
            "community_id": self.community.id,
            "community_name": self.community.name,
            "system_prompt": self.system_prompt,
            "tool_prompts": self.tool_prompts,
            "config": self.config.to_dict(),
            "introduction": self.introduction,
        }


class AgentFactory:
    """
    Factory for creating agents from conversational intake.

    Handles:
    - Matching user needs to communities
    - Creating agent with proper context
    - Generating personalized prompts
    - Registering agent in community
    """

    # Community matching keywords
    COMMUNITY_KEYWORDS = {
        "grant-getter": [
            "grant", "funding", "proposal", "nonprofit", "charity",
            "foundation", "funder", "application", "submission",
            "scholarship", "fellowship", "award", "donation"
        ],
    }

    def __init__(self):
        """Initialize the factory."""
        self._integration = get_community_integration()
        self._creation_callbacks: list[Callable[[CreatedAgent], None]] = []

    def match_community(self, user_input: str) -> str | None:
        """
        Match user input to the best community.

        Args:
            user_input: What the user said about their needs

        Returns:
            Community name or None if no match
        """
        input_lower = user_input.lower()

        best_match = None
        best_score = 0

        for community_name, keywords in self.COMMUNITY_KEYWORDS.items():
            score = sum(1 for kw in keywords if kw in input_lower)
            if score > best_score:
                best_score = score
                best_match = community_name

        return best_match if best_score > 0 else None

    def create_agent(
        self,
        community_name: str,
        context: dict[str, Any],
        preferences: dict[str, str] | None = None,
        created_by: str = "",
        agent_name: str | None = None,
    ) -> CreatedAgent:
        """
        Create an agent in a community.

        Args:
            community_name: Target community (e.g., "grant-getter")
            context: User/organization context gathered during intake
            preferences: User preferences (guidance_level, communication_style)
            created_by: Human creator ID
            agent_name: Optional custom name for the agent

        Returns:
            CreatedAgent with all configuration and prompts
        """
        # Normalize community name
        normalized_name = community_name.lower().replace("-", "_")

        # Get or create the community
        community = self._integration.get_community_by_name(
            self._display_name(community_name)
        )
        if not community:
            # Try to find by variations
            for c in self._integration.list_communities():
                if c.name.lower().replace("-", "_") == normalized_name:
                    community = c
                    break

        if not community:
            raise ValueError(f"Community not found: {community_name}")

        # Build agent config
        prefs = preferences or {}
        config = AgentConfig(
            name=agent_name or self._generate_name(community.name, context),
            community_id=community.id,
            community_name=community.name,
            context=context,
            guidance_level=GuidanceLevel(prefs.get("guidance_level", "medium")),
            communication_style=CommunicationStyle(prefs.get("communication_style", "conversational")),
            created_by=created_by,
        )

        # Join the community
        self._integration.join_community(config.agent_id, community.id)

        # Generate the system prompt
        prompt_context = {
            "context": context,
            "preferences": {
                "guidance_level": config.guidance_level.value,
                "communication_style": config.communication_style.value,
            },
        }
        system_prompt = get_agent_prompt(normalized_name, prompt_context)

        # Get tool prompts
        tool_prompts = get_tool_prompts(normalized_name)

        # Generate introduction
        introduction = self._generate_introduction(community, context, config)

        # Create the result
        agent = CreatedAgent(
            agent_id=config.agent_id,
            name=config.name,
            community=community,
            system_prompt=system_prompt,
            tool_prompts=tool_prompts,
            config=config,
            introduction=introduction,
        )

        # Notify callbacks
        for callback in self._creation_callbacks:
            try:
                callback(agent)
            except Exception as e:
                logger.error(f"Agent creation callback error: {e}")

        logger.info(f"Created agent {agent.agent_id} ({agent.name}) in {community.name}")
        return agent

    def on_agent_created(self, callback: Callable[[CreatedAgent], None]) -> None:
        """Register a callback for agent creation."""
        self._creation_callbacks.append(callback)

    def _display_name(self, name: str) -> str:
        """Convert internal name to display name."""
        return name.replace("_", "-").title().replace("-", "-")

    def _generate_name(self, community_name: str, context: dict) -> str:
        """Generate a friendly name for the agent."""
        org_name = context.get("organization_name", "")
        if org_name:
            # Use first word of org name
            first_word = org_name.split()[0] if org_name.split() else ""
            if community_name == "Grant-Getter":
                return f"{first_word}'s Grant Guide"
        return f"Your {community_name} Agent"

    def _generate_introduction(
        self,
        community: Community,
        context: dict,
        config: AgentConfig,
    ) -> str:
        """Generate the agent's introduction message."""
        org_name = context.get("organization_name", "your organization")
        mission = context.get("mission", "")
        goal = context.get("immediate_goal", "")

        if community.name == "Grant-Getter":
            intro = f"Hi! I'm {config.name}, and I'm here to help {org_name} secure grant funding."

            if mission:
                intro += f" I understand your mission is {mission} - that's meaningful work."

            intro += "\n\nI can help you with:"
            intro += "\n- **Finding grants** that match your programs"
            intro += "\n- **Writing proposals** section by section"
            intro += "\n- **Checking compliance** before you submit"
            intro += "\n- **Tracking deadlines** so nothing slips through"

            if goal:
                intro += f"\n\nYou mentioned wanting to {goal}. Would you like to start there, or is there something else on your mind?"
            else:
                intro += "\n\nWhat would you like to focus on first?"

            return intro

        # Generic introduction for other communities
        return f"Hi! I'm {config.name}, ready to help you with {community.name.lower()} tasks. What would you like to work on?"


# Singleton factory
_factory: AgentFactory | None = None


def get_agent_factory() -> AgentFactory:
    """Get the singleton agent factory."""
    global _factory
    if _factory is None:
        _factory = AgentFactory()
    return _factory
