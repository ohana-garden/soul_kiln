"""
Ambassador Agent.

Onboards new users and helps create their first proxy.
"""

import logging
from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from typing import Callable

from .entity import Proxy, ProxyConfig
from .manager import ProxyManager, get_proxy_manager

logger = logging.getLogger(__name__)


class OnboardingState(str, Enum):
    """States of the onboarding conversation."""

    GREETING = "greeting"
    EXPLORING_ROLE = "exploring_role"
    EXPLORING_COMMUNITY = "exploring_community"
    CONFIRMING = "confirming"
    CREATING = "creating"
    COMPLETE = "complete"


@dataclass
class OnboardingContext:
    """Context gathered during onboarding."""

    user_id: str
    state: OnboardingState = OnboardingState.GREETING
    name: str | None = None
    role: str | None = None
    community: str | None = None
    goals: list[str] | None = None
    started_at: datetime | None = None
    messages: list[dict] | None = None

    def to_dict(self) -> dict:
        return {
            "user_id": self.user_id,
            "state": self.state.value,
            "name": self.name,
            "role": self.role,
            "community": self.community,
            "goals": self.goals,
            "started_at": self.started_at.isoformat() if self.started_at else None,
        }


class Ambassador:
    """
    Onboarding agent for new users.

    Guides users through:
    1. Understanding what they're here for
    2. Identifying their role
    3. Connecting to a community
    4. Creating their first proxy
    """

    GREETING = """Welcome. I'm the Ambassador - I help new arrivals find their footing here.

What brings you to us today? Are you here for a specific purpose, or exploring?"""

    ROLE_PROMPT = """I'd like to understand your role better.

When you're working on {context}, what's your position? Are you the decision maker, a specialist, someone coordinating others?"""

    COMMUNITY_PROMPT = """Got it. You're a {role}.

Which community would you like your proxy to represent you in? We have several, including grant-getting for nonprofits, and others forming."""

    CONFIRM_PROMPT = """Let me make sure I have this right:

You'd like a proxy named "{name}" as a {role} in the {community} community.

Does that sound right?"""

    COMPLETE_PROMPT = """Your proxy is ready. {name} will represent you in conversations here.

When you speak, {name} speaks with your voice. When you're quiet, {name} will continue advocating for you.

The conversation you were headed to is just ahead. Ready?"""

    def __init__(
        self,
        proxy_manager: ProxyManager | None = None,
        llm_fn: Callable[[str, str], str] | None = None,
    ):
        """
        Initialize the Ambassador.

        Args:
            proxy_manager: Proxy manager for creating proxies
            llm_fn: LLM function for dynamic responses
        """
        self._proxy_manager = proxy_manager or get_proxy_manager()
        self._llm_fn = llm_fn
        self._contexts: dict[str, OnboardingContext] = {}

    def start_onboarding(self, user_id: str) -> tuple[str, OnboardingContext]:
        """
        Start onboarding for a new user.

        Returns:
            (greeting message, context)
        """
        context = OnboardingContext(
            user_id=user_id,
            state=OnboardingState.GREETING,
            started_at=datetime.utcnow(),
            messages=[],
        )
        self._contexts[user_id] = context

        logger.info(f"Started onboarding for user {user_id}")
        return self.GREETING, context

    def process_message(
        self,
        user_id: str,
        message: str,
    ) -> tuple[str, OnboardingContext]:
        """
        Process a message during onboarding.

        Returns:
            (response, updated context)
        """
        context = self._contexts.get(user_id)
        if not context:
            return self.start_onboarding(user_id)

        # Record message
        if context.messages is None:
            context.messages = []
        context.messages.append({
            "role": "user",
            "content": message,
            "timestamp": datetime.utcnow().isoformat(),
        })

        # Process based on state
        if context.state == OnboardingState.GREETING:
            return self._process_greeting(context, message)

        elif context.state == OnboardingState.EXPLORING_ROLE:
            return self._process_role(context, message)

        elif context.state == OnboardingState.EXPLORING_COMMUNITY:
            return self._process_community(context, message)

        elif context.state == OnboardingState.CONFIRMING:
            return self._process_confirmation(context, message)

        return "I'm not sure where we are. Let's start over.", context

    def _process_greeting(
        self,
        context: OnboardingContext,
        message: str,
    ) -> tuple[str, OnboardingContext]:
        """Process greeting response."""
        # Extract any hints about purpose
        message_lower = message.lower()

        # Look for role hints
        role_hints = {
            "grant": "grant writing",
            "nonprofit": "nonprofit work",
            "fundrais": "fundraising",
            "director": "organizational leadership",
            "coordin": "coordination",
            "manag": "management",
        }

        detected_context = None
        for hint, context_type in role_hints.items():
            if hint in message_lower:
                detected_context = context_type
                break

        context.state = OnboardingState.EXPLORING_ROLE

        if detected_context:
            response = self.ROLE_PROMPT.format(context=detected_context)
        else:
            response = """Tell me more about what you do. What's your role when you're working on the things that bring you here?"""

        return response, context

    def _process_role(
        self,
        context: OnboardingContext,
        message: str,
    ) -> tuple[str, OnboardingContext]:
        """Process role response."""
        # Extract role
        role = self._extract_role(message)
        context.role = role

        # Suggest a name based on role
        context.name = self._suggest_proxy_name(role)

        context.state = OnboardingState.EXPLORING_COMMUNITY

        response = self.COMMUNITY_PROMPT.format(role=role)
        return response, context

    def _process_community(
        self,
        context: OnboardingContext,
        message: str,
    ) -> tuple[str, OnboardingContext]:
        """Process community response."""
        # Extract community
        community = self._extract_community(message)
        context.community = community

        context.state = OnboardingState.CONFIRMING

        response = self.CONFIRM_PROMPT.format(
            name=context.name,
            role=context.role,
            community=context.community,
        )
        return response, context

    def _process_confirmation(
        self,
        context: OnboardingContext,
        message: str,
    ) -> tuple[str, OnboardingContext]:
        """Process confirmation response."""
        message_lower = message.lower()

        # Check for confirmation
        if any(word in message_lower for word in ["yes", "right", "correct", "good", "perfect"]):
            # Create the proxy
            context.state = OnboardingState.CREATING
            proxy = self._create_proxy(context)

            context.state = OnboardingState.COMPLETE

            response = self.COMPLETE_PROMPT.format(name=context.name)

            # Clean up context
            del self._contexts[context.user_id]

            return response, context

        elif any(word in message_lower for word in ["no", "not", "change", "actually"]):
            # Go back to role exploration
            context.state = OnboardingState.EXPLORING_ROLE
            return "No problem. Tell me more about your role - what should I call your proxy?", context

        else:
            # Unclear, ask again
            return "I want to make sure I get this right. Is the description accurate, or should we adjust something?", context

    def _extract_role(self, message: str) -> str:
        """Extract role from message."""
        message_lower = message.lower()

        # Common role patterns
        role_patterns = [
            ("director", "Director"),
            ("executive", "Executive Director"),
            ("manager", "Manager"),
            ("coordinator", "Coordinator"),
            ("writer", "Grant Writer"),
            ("specialist", "Specialist"),
            ("officer", "Officer"),
            ("lead", "Lead"),
            ("founder", "Founder"),
        ]

        for pattern, role in role_patterns:
            if pattern in message_lower:
                return role

        # Use LLM if available
        if self._llm_fn:
            prompt = f"Extract a job title/role from this message. Return only the role, 2-3 words max: '{message}'"
            return self._llm_fn(prompt, "")[:50]

        return "Representative"

    def _extract_community(self, message: str) -> str:
        """Extract community from message."""
        message_lower = message.lower()

        # Known communities
        community_patterns = [
            ("grant", "grant-getter"),
            ("nonprofit", "grant-getter"),
            ("funding", "grant-getter"),
        ]

        for pattern, community in community_patterns:
            if pattern in message_lower:
                return community

        # Default to grant-getter for now
        return "grant-getter"

    def _suggest_proxy_name(self, role: str) -> str:
        """Suggest a proxy name based on role."""
        # Just use a simple format for now
        return f"My {role}"

    def _create_proxy(self, context: OnboardingContext) -> Proxy:
        """Create the proxy from onboarding context."""
        proxy = self._proxy_manager.create_proxy(
            owner_id=context.user_id,
            name=context.name or "My Proxy",
            role=context.role or "Representative",
            communities=[context.community] if context.community else [],
        )

        logger.info(
            f"Created proxy {proxy.id} for user {context.user_id} "
            f"as {context.role} in {context.community}"
        )

        return proxy

    def get_context(self, user_id: str) -> OnboardingContext | None:
        """Get onboarding context for a user."""
        return self._contexts.get(user_id)

    def is_onboarding(self, user_id: str) -> bool:
        """Check if user is currently onboarding."""
        return user_id in self._contexts


# Singleton
_ambassador: Ambassador | None = None


def get_ambassador() -> Ambassador:
    """Get the singleton ambassador."""
    global _ambassador
    if _ambassador is None:
        _ambassador = Ambassador()
    return _ambassador
