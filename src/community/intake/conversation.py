"""
Intake Conversation Handler.

Manages the conversational flow for agent creation.
100% conversational UX - no forms, no commands.
"""

import logging
import uuid
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Callable

from .factory import AgentFactory, CreatedAgent, get_agent_factory
from .prompts import get_intake_prompt

logger = logging.getLogger(__name__)


class ConversationState(str, Enum):
    """States in the intake conversation."""

    GREETING = "greeting"           # Initial contact
    EXPLORING = "exploring"         # Understanding their needs
    MATCHING = "matching"           # Matching to community
    GATHERING = "gathering"         # Collecting context
    CONFIRMING = "confirming"       # Confirming before creation
    CREATING = "creating"           # Creating the agent
    HANDOFF = "handoff"             # Transitioning to new agent
    COMPLETE = "complete"           # Done


@dataclass
class GatheredContext:
    """Context gathered during intake conversation."""

    # Core identification
    organization_name: str = ""
    organization_type: str = ""
    mission: str = ""

    # Who they serve
    target_population: str = ""
    geographic_area: str = ""

    # Their situation
    experience_level: str = ""  # new, some, experienced
    immediate_goal: str = ""
    timeline: str = ""

    # Grant-specific (if Grant-Getter)
    past_grants: list[str] = field(default_factory=list)
    funding_needs: str = ""
    focus_areas: list[str] = field(default_factory=list)

    # Preferences
    guidance_level: str = "medium"
    communication_style: str = "conversational"

    # Raw notes from conversation
    notes: list[str] = field(default_factory=list)

    def to_dict(self) -> dict:
        """Convert to dictionary for agent creation."""
        return {
            "organization_name": self.organization_name,
            "organization_type": self.organization_type,
            "mission": self.mission,
            "target_population": self.target_population,
            "geographic_area": self.geographic_area,
            "experience_level": self.experience_level,
            "immediate_goal": self.immediate_goal,
            "timeline": self.timeline,
            "past_grants": self.past_grants,
            "funding_needs": self.funding_needs,
            "focus_areas": self.focus_areas,
        }

    def is_sufficient_for_grant_getter(self) -> bool:
        """Check if we have enough context for Grant-Getter."""
        return bool(
            self.organization_name and
            self.organization_type and
            (self.mission or self.immediate_goal)
        )

    def get_missing_fields(self) -> list[str]:
        """Get list of important missing fields."""
        missing = []
        if not self.organization_name:
            missing.append("organization name")
        if not self.organization_type:
            missing.append("organization type")
        if not self.mission and not self.immediate_goal:
            missing.append("mission or immediate goal")
        return missing


@dataclass
class Message:
    """A message in the conversation."""

    role: str  # "user" or "assistant"
    content: str
    timestamp: datetime = field(default_factory=datetime.utcnow)
    metadata: dict = field(default_factory=dict)


@dataclass
class IntakeConversation:
    """
    Manages a single intake conversation.

    Tracks state, gathers context, and handles the flow
    from initial contact through agent creation.
    """

    conversation_id: str = field(default_factory=lambda: f"intake_{uuid.uuid4().hex[:12]}")
    state: ConversationState = ConversationState.GREETING
    matched_community: str | None = None
    context: GatheredContext = field(default_factory=GatheredContext)
    messages: list[Message] = field(default_factory=list)
    created_agent: CreatedAgent | None = None
    created_at: datetime = field(default_factory=datetime.utcnow)
    human_id: str = ""  # The human we're talking to

    def __post_init__(self):
        """Initialize the factory."""
        self._factory = get_agent_factory()
        self._state_handlers: dict[ConversationState, Callable] = {
            ConversationState.GREETING: self._handle_greeting,
            ConversationState.EXPLORING: self._handle_exploring,
            ConversationState.MATCHING: self._handle_matching,
            ConversationState.GATHERING: self._handle_gathering,
            ConversationState.CONFIRMING: self._handle_confirming,
            ConversationState.CREATING: self._handle_creating,
            ConversationState.HANDOFF: self._handle_handoff,
        }

    def get_system_prompt(self) -> str:
        """Get the system prompt for the current state."""
        base_prompt = get_intake_prompt()

        # Add state-specific context
        state_context = f"\n\n## Current State: {self.state.value}\n"

        if self.matched_community:
            state_context += f"Matched community: {self.matched_community}\n"

        if self.context.organization_name:
            state_context += f"Organization: {self.context.organization_name}\n"

        missing = self.context.get_missing_fields()
        if missing and self.state == ConversationState.GATHERING:
            state_context += f"Still need to learn: {', '.join(missing)}\n"

        return base_prompt + state_context

    def process_message(self, user_message: str) -> str:
        """
        Process a user message and generate response.

        This is the main entry point for the conversation.
        In a full implementation, this would call an LLM.
        Here we provide the framework for state management.

        Args:
            user_message: What the user said

        Returns:
            Framework response (in production, LLM generates this)
        """
        # Record the message
        self.messages.append(Message(role="user", content=user_message))

        # Extract information from the message
        self._extract_context(user_message)

        # Get the handler for current state
        handler = self._state_handlers.get(self.state)
        if handler:
            response = handler(user_message)
        else:
            response = "I'm not sure how to proceed. Let's start over - what can I help you with?"

        # Record our response
        self.messages.append(Message(role="assistant", content=response))

        return response

    def _extract_context(self, message: str) -> None:
        """Extract context from user message."""
        msg_lower = message.lower()

        # Try to extract organization name (simple heuristic)
        if not self.context.organization_name:
            # Look for patterns like "I'm from X" or "We're X" or "X nonprofit"
            name_indicators = ["i'm from ", "we're ", "i work at ", "i work for ", "our organization "]
            for indicator in name_indicators:
                if indicator in msg_lower:
                    idx = msg_lower.index(indicator) + len(indicator)
                    # Take next few words as potential name
                    words = message[idx:].split()[:5]
                    potential_name = " ".join(words).strip(".,!?")
                    if len(potential_name) > 2:
                        self.context.organization_name = potential_name
                        break

        # Try to identify organization type
        if not self.context.organization_type:
            type_keywords = {
                "nonprofit": ["nonprofit", "non-profit", "501c3", "501(c)(3)", "charity"],
                "school": ["school", "university", "college", "academy", "educational institution"],
                "community_group": ["community group", "community organization", "grassroots"],
                "research": ["research", "lab", "institute", "laboratory"],
            }
            for org_type, keywords in type_keywords.items():
                if any(kw in msg_lower for kw in keywords):
                    self.context.organization_type = org_type
                    break

        # Try to identify experience level
        if not self.context.experience_level:
            if any(x in msg_lower for x in ["first time", "never applied", "new to", "don't have experience"]):
                self.context.experience_level = "new"
            elif any(x in msg_lower for x in ["some experience", "applied before", "a few grants"]):
                self.context.experience_level = "some"
            elif any(x in msg_lower for x in ["many grants", "experienced", "years of", "regularly apply"]):
                self.context.experience_level = "experienced"

        # Add to notes
        self.context.notes.append(message)

    def _handle_greeting(self, message: str) -> str:
        """Handle greeting state."""
        # Check if they've already expressed a need
        community = self._factory.match_community(message)

        if community:
            self.matched_community = community
            self.state = ConversationState.GATHERING
            return self._get_gathering_response()

        # Move to exploring
        self.state = ConversationState.EXPLORING
        return (
            "Thanks for reaching out! I'd love to understand what kind of support "
            "you're looking for. What brings you here today?"
        )

    def _handle_exploring(self, message: str) -> str:
        """Handle exploring state."""
        community = self._factory.match_community(message)

        if community:
            self.matched_community = community
            self.state = ConversationState.GATHERING
            return self._get_gathering_response()

        # Still exploring
        return (
            "Tell me more about what you're hoping to accomplish. "
            "What's the main challenge you're facing?"
        )

    def _handle_matching(self, message: str) -> str:
        """Handle matching state."""
        # Confirm the match
        self.state = ConversationState.GATHERING
        return self._get_gathering_response()

    def _handle_gathering(self, message: str) -> str:
        """Handle gathering state."""
        # Check if we have enough context
        if self.context.is_sufficient_for_grant_getter():
            self.state = ConversationState.CONFIRMING
            return self._get_confirmation_response()

        # Ask for missing info
        missing = self.context.get_missing_fields()
        if missing:
            return self._ask_for_missing(missing)

        # Generic follow-up
        return "That's helpful! Tell me more about your organization and what you're trying to achieve."

    def _handle_confirming(self, message: str) -> str:
        """Handle confirming state."""
        msg_lower = message.lower()

        # Check for confirmation
        if any(x in msg_lower for x in ["yes", "correct", "right", "sounds good", "let's do it", "create"]):
            self.state = ConversationState.CREATING
            return self._create_agent()

        # Check for corrections
        if any(x in msg_lower for x in ["no", "not quite", "actually", "wait", "change"]):
            self.state = ConversationState.GATHERING
            return "No problem! What would you like to correct or add?"

        # Unclear response
        return "Just to confirm - should I create your Grant-Getter agent with the details we discussed? (yes/no)"

    def _handle_creating(self, message: str) -> str:
        """Handle creating state - agent is being created."""
        if self.created_agent:
            self.state = ConversationState.HANDOFF
            return self.created_agent.introduction

        return "Creating your agent now..."

    def _handle_handoff(self, message: str) -> str:
        """Handle handoff state - conversation transfers to new agent."""
        self.state = ConversationState.COMPLETE
        if self.created_agent:
            return f"[{self.created_agent.name} is now your agent. Continue the conversation with them!]"
        return "[Handoff complete]"

    def _get_gathering_response(self) -> str:
        """Get initial gathering response based on matched community."""
        if self.matched_community == "grant-getter":
            return (
                "Great! I can connect you with a Grant-Getter agent who specializes in "
                "helping organizations secure funding. Before I set that up, I'd like to "
                "understand your situation better.\n\n"
                "Tell me about your organization - what's your name and what kind of work do you do?"
            )
        return "Tell me more about your organization and what you're hoping to accomplish."

    def _get_confirmation_response(self) -> str:
        """Get confirmation response with gathered details."""
        ctx = self.context
        response = "Here's what I understand:\n\n"

        if ctx.organization_name:
            response += f"**Organization**: {ctx.organization_name}\n"
        if ctx.organization_type:
            response += f"**Type**: {ctx.organization_type}\n"
        if ctx.mission:
            response += f"**Mission**: {ctx.mission}\n"
        if ctx.target_population:
            response += f"**Serves**: {ctx.target_population}\n"
        if ctx.immediate_goal:
            response += f"**Current Goal**: {ctx.immediate_goal}\n"
        if ctx.experience_level:
            response += f"**Grant Experience**: {ctx.experience_level}\n"

        response += "\nShould I create your Grant-Getter agent with this context?"

        return response

    def _ask_for_missing(self, missing: list[str]) -> str:
        """Ask for specific missing information."""
        if "organization name" in missing:
            return "What's the name of your organization?"
        if "organization type" in missing:
            return "What type of organization are you? (nonprofit, school, community group, etc.)"
        if "mission or immediate goal" in missing:
            return "What's your organization's mission, or what are you hoping to accomplish right now?"
        return "Tell me more about your organization."

    def _create_agent(self) -> str:
        """Create the agent and return introduction."""
        try:
            self.created_agent = self._factory.create_agent(
                community_name=self.matched_community or "grant-getter",
                context=self.context.to_dict(),
                preferences={
                    "guidance_level": self.context.guidance_level,
                    "communication_style": self.context.communication_style,
                },
                created_by=self.human_id,
            )

            self.state = ConversationState.HANDOFF
            return (
                f"I've created your agent! Let me introduce you:\n\n"
                f"---\n\n"
                f"{self.created_agent.introduction}"
            )

        except Exception as e:
            logger.error(f"Agent creation failed: {e}")
            self.state = ConversationState.GATHERING
            return f"I encountered an issue creating your agent. Let's try again - what's your organization's name?"

    def to_dict(self) -> dict:
        """Convert to dictionary."""
        return {
            "conversation_id": self.conversation_id,
            "state": self.state.value,
            "matched_community": self.matched_community,
            "context": self.context.to_dict(),
            "messages": [
                {"role": m.role, "content": m.content, "timestamp": m.timestamp.isoformat()}
                for m in self.messages
            ],
            "created_agent": self.created_agent.to_dict() if self.created_agent else None,
            "created_at": self.created_at.isoformat(),
            "human_id": self.human_id,
        }


def start_intake(human_id: str = "") -> IntakeConversation:
    """
    Start a new intake conversation.

    Args:
        human_id: ID of the human starting the conversation

    Returns:
        New IntakeConversation ready for messages
    """
    conversation = IntakeConversation(human_id=human_id)

    # Generate opening message
    opening = (
        "Hi! I'm here to help you find the right support. "
        "What brings you here today?"
    )
    conversation.messages.append(Message(role="assistant", content=opening))

    return conversation
