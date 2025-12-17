"""
Proxy Autonomy.

Handles when and how proxies speak for users during silence.
"""

import logging
from dataclasses import dataclass
from datetime import datetime, timedelta
from enum import Enum
from typing import Callable, Any

from .entity import Proxy

logger = logging.getLogger(__name__)


class AutonomyMode(str, Enum):
    """Modes of proxy autonomy."""

    PASSTHROUGH = "passthrough"  # Only pass user voice
    ASSIST = "assist"  # Fill gaps, ask clarifications
    ADVOCATE = "advocate"  # Actively represent position
    SILENT = "silent"  # Don't speak


@dataclass
class AutonomyContext:
    """Context for autonomy decisions."""

    proxy: Proxy
    session_id: str
    current_topic: str | None = None
    last_user_speech: datetime | None = None
    last_proxy_speech: datetime | None = None
    conversation_state: str = "active"  # active, winding_down, stalled
    pending_question: bool = False
    question_for_user: str | None = None


class ProxyAutonomy:
    """
    Manages when and how proxies act autonomously.

    Decides:
    - When to speak for the user
    - What to say
    - When to ask for clarification
    - When to defer to the user
    """

    # Timing thresholds (seconds)
    SILENCE_THRESHOLD = 3.0  # Silence before proxy considers speaking
    EXTENDED_SILENCE = 10.0  # When to step back to observe
    QUESTION_TIMEOUT = 15.0  # How long to wait for user answer

    def __init__(self, llm_fn: Callable[[str, str], str] | None = None):
        """
        Initialize autonomy system.

        Args:
            llm_fn: Function to generate responses (prompt, context) -> response
        """
        self._llm_fn = llm_fn
        self._contexts: dict[str, AutonomyContext] = {}

    def create_context(
        self,
        proxy: Proxy,
        session_id: str,
    ) -> AutonomyContext:
        """Create autonomy context for a proxy in a session."""
        context = AutonomyContext(
            proxy=proxy,
            session_id=session_id,
        )
        self._contexts[f"{proxy.id}:{session_id}"] = context
        return context

    def get_context(
        self,
        proxy_id: str,
        session_id: str,
    ) -> AutonomyContext | None:
        """Get autonomy context."""
        return self._contexts.get(f"{proxy_id}:{session_id}")

    def record_user_speech(
        self,
        proxy_id: str,
        session_id: str,
        text: str,
    ) -> None:
        """Record that user spoke."""
        context = self.get_context(proxy_id, session_id)
        if context:
            context.last_user_speech = datetime.utcnow()
            context.pending_question = False
            context.question_for_user = None

            # Update position if stance detected
            self._extract_position(context, text)

    def record_proxy_speech(
        self,
        proxy_id: str,
        session_id: str,
    ) -> None:
        """Record that proxy spoke."""
        context = self.get_context(proxy_id, session_id)
        if context:
            context.last_proxy_speech = datetime.utcnow()

    def should_speak(
        self,
        proxy_id: str,
        session_id: str,
    ) -> tuple[bool, str | None]:
        """
        Determine if proxy should speak.

        Returns:
            (should_speak, reason)
        """
        context = self.get_context(proxy_id, session_id)
        if not context:
            return False, None

        proxy = context.proxy

        # Check autonomy level
        if proxy.config.autonomy_level < 0.1:
            return False, None

        now = datetime.utcnow()
        silence_duration = self._get_silence_duration(context)

        # Not enough silence yet
        if silence_duration < self.SILENCE_THRESHOLD:
            return False, None

        # Extended silence - suggest stepping back
        if silence_duration > self.EXTENDED_SILENCE:
            return False, "extended_silence"

        # Pending question from proxy
        if context.pending_question:
            if silence_duration > self.QUESTION_TIMEOUT:
                # User didn't answer, proxy should handle it
                return True, "question_timeout"
            return False, "waiting_for_answer"

        # Check if there's something to say
        autonomy = proxy.config.autonomy_level
        if autonomy > 0.7:
            return True, "high_autonomy"
        elif autonomy > 0.3 and context.conversation_state == "stalled":
            return True, "conversation_stalled"

        return False, None

    def generate_response(
        self,
        proxy_id: str,
        session_id: str,
        conversation_history: list[dict],
        reason: str,
    ) -> str | None:
        """
        Generate a proxy response.

        Args:
            proxy_id: Proxy ID
            session_id: Session ID
            conversation_history: Recent conversation
            reason: Why proxy is speaking

        Returns:
            Generated response or None
        """
        context = self.get_context(proxy_id, session_id)
        if not context:
            return None

        proxy = context.proxy

        # Build prompt based on reason
        if reason == "question_timeout":
            return self._handle_question_timeout(context, conversation_history)

        elif reason == "conversation_stalled":
            return self._handle_stalled(context, conversation_history)

        elif reason == "high_autonomy":
            return self._handle_autonomous(context, conversation_history)

        return None

    def should_defer(
        self,
        proxy_id: str,
        session_id: str,
        decision_type: str,
    ) -> bool:
        """
        Check if proxy should defer to user on a decision.

        Args:
            proxy_id: Proxy ID
            session_id: Session ID
            decision_type: Type of decision (commit, agree, disagree, etc.)

        Returns:
            True if should defer
        """
        context = self.get_context(proxy_id, session_id)
        if not context:
            return True  # Default to defer

        proxy = context.proxy

        # Always defer on major decisions if configured
        major_decisions = {"commit", "agree_major", "disagree_major", "change_direction"}
        if proxy.config.defer_on_major and decision_type in major_decisions:
            return True

        # Low autonomy = always defer
        if proxy.config.autonomy_level < 0.3:
            return True

        # Check position confidence
        if context.current_topic:
            position = proxy.get_position(context.current_topic)
            if position and position.confidence < proxy.config.clarify_threshold:
                return True

        return False

    def set_pending_question(
        self,
        proxy_id: str,
        session_id: str,
        question: str,
    ) -> None:
        """Record that proxy asked user a question."""
        context = self.get_context(proxy_id, session_id)
        if context:
            context.pending_question = True
            context.question_for_user = question

    def _get_silence_duration(self, context: AutonomyContext) -> float:
        """Get duration of silence since last speech."""
        now = datetime.utcnow()

        # Use whichever is more recent
        last_speech = context.last_user_speech
        if context.last_proxy_speech:
            if not last_speech or context.last_proxy_speech > last_speech:
                last_speech = context.last_proxy_speech

        if not last_speech:
            return 0.0

        return (now - last_speech).total_seconds()

    def _extract_position(self, context: AutonomyContext, text: str) -> None:
        """Extract and record position from user speech."""
        # Simple heuristics - would use NLP in production
        stance_indicators = {
            "agree": ["I agree", "yes", "exactly", "right", "correct"],
            "disagree": ["I disagree", "no", "actually", "but", "however"],
            "support": ["I support", "in favor", "should do"],
            "oppose": ["I oppose", "against", "shouldn't"],
        }

        text_lower = text.lower()
        for stance, indicators in stance_indicators.items():
            for indicator in indicators:
                if indicator.lower() in text_lower:
                    if context.current_topic:
                        context.proxy.record_position(
                            topic=context.current_topic,
                            stance=stance,
                            confidence=0.6,
                            source="user_stated",
                        )
                    break

    def _handle_question_timeout(
        self,
        context: AutonomyContext,
        history: list[dict],
    ) -> str | None:
        """Handle when user didn't answer proxy's question."""
        if not self._llm_fn:
            return "I'll proceed with my best judgment."

        prompt = f"""The user's proxy asked: "{context.question_for_user}"
The user has been silent. Generate a brief response that:
1. Acknowledges the silence
2. Offers to proceed with a reasonable default
3. Stays in character as {context.proxy.name}, a {context.proxy.role}

Keep it under 20 words."""

        return self._llm_fn(prompt, str(history[-5:]))

    def _handle_stalled(
        self,
        context: AutonomyContext,
        history: list[dict],
    ) -> str | None:
        """Handle stalled conversation."""
        if not self._llm_fn:
            return "Should we continue with this, or move to something else?"

        prompt = f"""The conversation has stalled. Generate a brief prompt that:
1. Acknowledges the pause naturally
2. Offers a path forward
3. Stays in character as {context.proxy.name}, a {context.proxy.role}

Keep it under 15 words."""

        return self._llm_fn(prompt, str(history[-5:]))

    def _handle_autonomous(
        self,
        context: AutonomyContext,
        history: list[dict],
    ) -> str | None:
        """Generate autonomous contribution."""
        if not self._llm_fn:
            return None

        # Build context from proxy's positions
        positions_context = ""
        if context.proxy.positions:
            positions_context = "Known positions:\n"
            for topic, pos in list(context.proxy.positions.items())[:5]:
                positions_context += f"- {topic}: {pos.stance}\n"

        prompt = f"""Generate a brief contribution to the conversation as {context.proxy.name}, a {context.proxy.role}.

{positions_context}

The contribution should:
1. Be relevant to the current discussion
2. Represent the user's interests
3. Be concise (under 25 words)
4. Not commit to major decisions without the user"""

        return self._llm_fn(prompt, str(history[-5:]))
