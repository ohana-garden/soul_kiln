"""
Theatre Orchestrator.

The three-agent conversation model:
- User Proxy: Interprets and echoes user input into the conversation
- Builder: Facilitates, guides, and builds understanding
- Current Agent: Domain expert for the active task/community

Philosophy: "Yes, and..." - Everything is incorporated smoothly.
The conversation is always already happening when you arrive.
The user can "barge in" at any time - User Proxy handles it gracefully.
"""

import logging
import uuid
from collections import deque
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Callable

from .topic_detector import TopicDetector, TopicState, TopicShift
from .scene_generator import SceneGenerator, Scene
from .concept_extractor import ConceptExtractor
from .hume_integration import HumeIntegration, EmotionalState

logger = logging.getLogger(__name__)


class AgentRole(str, Enum):
    """Roles in the theatre conversation."""

    USER_PROXY = "user_proxy"  # Interprets and echoes user input
    BUILDER = "builder"  # Facilitates and guides
    CURRENT_AGENT = "current_agent"  # Domain expert (e.g., Grant-Getter)
    SYSTEM = "system"  # System messages (scene transitions, etc.)


@dataclass
class AgentPersona:
    """Persona definition for an agent in the theatre."""

    role: AgentRole
    name: str
    voice: str  # Description of speaking style
    color: str  # Hex color for captions
    community: str | None = None  # For domain agents
    traits: list[str] = field(default_factory=list)

    def to_dict(self) -> dict:
        """Convert to dictionary."""
        return {
            "role": self.role.value,
            "name": self.name,
            "voice": self.voice,
            "color": self.color,
            "community": self.community,
            "traits": self.traits,
        }


# Default personas
DEFAULT_PERSONAS = {
    AgentRole.USER_PROXY: AgentPersona(
        role=AgentRole.USER_PROXY,
        name="Echo",
        voice="Warm, reflective, slightly more formal restatement",
        color="#4CAF50",  # Green
        traits=["empathetic", "clarifying", "bridging"],
    ),
    AgentRole.BUILDER: AgentPersona(
        role=AgentRole.BUILDER,
        name="Weaver",
        voice="Encouraging, constructive, connecting threads",
        color="#2196F3",  # Blue
        traits=["facilitative", "insightful", "patient"],
    ),
    AgentRole.SYSTEM: AgentPersona(
        role=AgentRole.SYSTEM,
        name="Theatre",
        voice="Minimal, atmospheric, descriptive",
        color="#9E9E9E",  # Gray
        traits=["ambient", "transitional"],
    ),
}


@dataclass
class ConversationTurn:
    """A single turn in the theatre conversation."""

    id: str = field(default_factory=lambda: f"turn_{uuid.uuid4().hex[:8]}")
    role: AgentRole = AgentRole.SYSTEM
    speaker_name: str = ""
    content: str = ""
    is_user_input: bool = False  # True if this is raw user input
    topic_state: TopicState | None = None
    emotional_state: EmotionalState | None = None
    scene: Scene | None = None
    metadata: dict = field(default_factory=dict)
    timestamp: datetime = field(default_factory=datetime.utcnow)

    def to_dict(self) -> dict:
        """Convert to dictionary."""
        return {
            "id": self.id,
            "role": self.role.value,
            "speaker_name": self.speaker_name,
            "content": self.content,
            "is_user_input": self.is_user_input,
            "topic_state": self.topic_state.to_dict() if self.topic_state else None,
            "emotional_state": self.emotional_state.to_dict() if self.emotional_state else None,
            "scene": self.scene.to_dict() if self.scene else None,
            "metadata": self.metadata,
            "timestamp": self.timestamp.isoformat(),
        }


class TheatreState(str, Enum):
    """States of the theatre."""

    INITIALIZING = "initializing"  # Setting up
    AMBIENT = "ambient"  # Agents chatting, waiting for user
    ENGAGED = "engaged"  # Active conversation with user
    TRANSITIONING = "transitioning"  # Changing domain agents
    PAUSED = "paused"  # Temporarily paused
    CONCLUDED = "concluded"  # Session ended


@dataclass
class ConversationContext:
    """Context for the current conversation."""

    session_id: str
    human_id: str | None = None
    community: str | None = None
    organization_context: dict = field(default_factory=dict)
    conversation_history: deque = field(default_factory=lambda: deque(maxlen=100))
    started_at: datetime = field(default_factory=datetime.utcnow)

    def to_dict(self) -> dict:
        """Convert to dictionary."""
        return {
            "session_id": self.session_id,
            "human_id": self.human_id,
            "community": self.community,
            "organization_context": self.organization_context,
            "started_at": self.started_at.isoformat(),
        }


class TheatreOrchestrator:
    """
    Orchestrates the theatrical three-agent conversation.

    The orchestrator manages:
    - Three concurrent agent personas (User Proxy, Builder, Current Agent)
    - Topic detection and scene generation
    - Smooth incorporation of user input ("Yes, and...")
    - Transitions between domain agents

    Key insight: Since User Proxy echoes all user input, ALL I/O
    flows through agents. This means we can use the knowledge graph
    for topic detection on everything.
    """

    def __init__(
        self,
        topic_detector: TopicDetector | None = None,
        scene_generator: SceneGenerator | None = None,
        concept_extractor: ConceptExtractor | None = None,
        hume_integration: HumeIntegration | None = None,
        llm_fn: Callable[[str, str], str] | None = None,
    ):
        """
        Initialize the theatre orchestrator.

        Args:
            topic_detector: For tracking conversation topics
            scene_generator: For generating visual scenes
            concept_extractor: For mapping utterances to graph
            hume_integration: For emotional intelligence
            llm_fn: Function to call LLM (prompt, context) -> response
        """
        self.topic_detector = topic_detector or TopicDetector()
        self.scene_generator = scene_generator or SceneGenerator()
        self.extractor = concept_extractor
        self.hume = hume_integration

        self._llm_fn = llm_fn
        self._state = TheatreState.INITIALIZING
        self._context: ConversationContext | None = None
        self._personas: dict[AgentRole, AgentPersona] = dict(DEFAULT_PERSONAS)
        self._current_agent_persona: AgentPersona | None = None
        self._turn_history: deque[ConversationTurn] = deque(maxlen=100)

        # Callbacks
        self._turn_callbacks: list[Callable[[ConversationTurn], None]] = []
        self._state_callbacks: list[Callable[[TheatreState], None]] = []

    @property
    def state(self) -> TheatreState:
        """Get current theatre state."""
        return self._state

    @property
    def context(self) -> ConversationContext | None:
        """Get current conversation context."""
        return self._context

    def start_session(
        self,
        human_id: str | None = None,
        community: str | None = None,
        organization_context: dict | None = None,
    ) -> ConversationContext:
        """
        Start a new theatre session.

        The conversation begins with agents already chatting about
        the context - the user arrives to an ongoing conversation.

        Args:
            human_id: Optional human identifier
            community: Optional starting community (e.g., "grant-getter")
            organization_context: Optional org context from intake

        Returns:
            ConversationContext for the session
        """
        session_id = f"theatre_{uuid.uuid4().hex[:12]}"

        self._context = ConversationContext(
            session_id=session_id,
            human_id=human_id,
            community=community,
            organization_context=organization_context or {},
        )

        # Set up current agent persona if community specified
        if community:
            self._current_agent_persona = self._create_community_persona(community)

        self._state = TheatreState.AMBIENT
        self._notify_state_change()

        # Generate opening ambient conversation
        self._generate_ambient_opening()

        logger.info(f"Theatre session started: {session_id}")
        return self._context

    def process_user_input(
        self,
        user_input: str,
        audio_data: bytes | None = None,
    ) -> list[ConversationTurn]:
        """
        Process user input (user "barges in").

        The input flows through User Proxy, which echoes and interprets it,
        then other agents respond. All utterances go through topic detection.

        Args:
            user_input: What the user said
            audio_data: Optional audio for emotional analysis

        Returns:
            List of conversation turns generated
        """
        if self._state == TheatreState.CONCLUDED:
            return []

        # Transition to engaged if not already
        if self._state == TheatreState.AMBIENT:
            self._state = TheatreState.ENGAGED
            self._notify_state_change()

        turns: list[ConversationTurn] = []

        # Get emotional state from audio if available
        emotional_state = None
        if self.hume and audio_data:
            emotional_state = self.hume.analyze_audio(audio_data)

        # 1. User Proxy echoes and interprets the input
        proxy_turn = self._user_proxy_echo(user_input, emotional_state)
        turns.append(proxy_turn)

        # 2. Process through topic detector (all I/O goes through agents)
        topic_state = self.topic_detector.process_utterance(
            proxy_turn.content,
            speaker=AgentRole.USER_PROXY.value,
            emotional_context=emotional_state.to_dict() if emotional_state else None,
        )

        # Check for topic shift
        shift = None
        if self.topic_detector._shift_history:
            recent = list(self.topic_detector._shift_history)[-1]
            if (datetime.utcnow() - recent.timestamp).total_seconds() < 1:
                shift = recent

        # 3. Update scene if needed
        scene = self.scene_generator.generate(
            topic_state, emotional_state, shift
        )

        if shift:
            # Add scene transition turn
            scene_turn = ConversationTurn(
                role=AgentRole.SYSTEM,
                speaker_name=self._personas[AgentRole.SYSTEM].name,
                content=f"[Scene shifts: {scene.description}]",
                topic_state=topic_state,
                scene=scene,
            )
            turns.append(scene_turn)

        # 4. Builder responds (if helpful)
        builder_response = self._builder_respond(user_input, topic_state, emotional_state)
        if builder_response:
            turns.append(builder_response)

        # 5. Current Agent responds (domain expert)
        if self._current_agent_persona:
            agent_response = self._current_agent_respond(
                user_input, topic_state, emotional_state
            )
            if agent_response:
                turns.append(agent_response)

        # Store all turns
        for turn in turns:
            self._turn_history.append(turn)
            self._notify_turn(turn)

        return turns

    def _user_proxy_echo(
        self, user_input: str, emotional_state: EmotionalState | None
    ) -> ConversationTurn:
        """
        User Proxy echoes and interprets user input.

        This is the bridge between raw user input and the theatre.
        The proxy makes the input flow naturally into the conversation.
        """
        persona = self._personas[AgentRole.USER_PROXY]

        # Generate echo response
        if self._llm_fn:
            prompt = self._build_proxy_prompt(user_input, emotional_state)
            echo_content = self._llm_fn(prompt, self._get_recent_context())
        else:
            # Fallback: simple reflection
            echo_content = self._simple_proxy_echo(user_input)

        # Process through topic detector
        topic_state = self.topic_detector.process_utterance(
            echo_content,
            speaker=AgentRole.USER_PROXY.value,
            emotional_context=emotional_state.to_dict() if emotional_state else None,
        )

        return ConversationTurn(
            role=AgentRole.USER_PROXY,
            speaker_name=persona.name,
            content=echo_content,
            is_user_input=True,
            topic_state=topic_state,
            emotional_state=emotional_state,
            metadata={"original_input": user_input},
        )

    def _simple_proxy_echo(self, user_input: str) -> str:
        """Simple echo when no LLM available."""
        # Slightly formalize and reflect
        input_lower = user_input.lower().strip()

        # Handle common patterns
        if input_lower.startswith(("i want", "i need", "i'd like")):
            return f"So you're looking to {user_input[user_input.find(' ')+1:].strip()}..."

        if input_lower.startswith("can you"):
            return f"You're asking if we can {user_input[8:].strip()}..."

        if input_lower.startswith(("what", "how", "why", "when", "where")):
            return f"That's an interesting question: {user_input}"

        if "?" in user_input:
            return f"Let me understand - {user_input}"

        # Default: reflective acknowledgment
        return f"I hear you saying: {user_input}"

    def _builder_respond(
        self,
        user_input: str,
        topic_state: TopicState,
        emotional_state: EmotionalState | None,
    ) -> ConversationTurn | None:
        """
        Builder responds to facilitate the conversation.

        The Builder connects threads, provides context, and guides
        when helpful. Doesn't always need to speak.
        """
        persona = self._personas[AgentRole.BUILDER]

        # Decide if Builder should speak
        should_speak = self._should_builder_speak(user_input, topic_state)

        if not should_speak:
            return None

        if self._llm_fn:
            prompt = self._build_builder_prompt(user_input, topic_state, emotional_state)
            content = self._llm_fn(prompt, self._get_recent_context())
        else:
            content = self._simple_builder_response(user_input, topic_state)

        # Process through topic detector
        new_topic_state = self.topic_detector.process_utterance(
            content,
            speaker=AgentRole.BUILDER.value,
            emotional_context=emotional_state.to_dict() if emotional_state else None,
        )

        return ConversationTurn(
            role=AgentRole.BUILDER,
            speaker_name=persona.name,
            content=content,
            topic_state=new_topic_state,
            emotional_state=emotional_state,
        )

    def _should_builder_speak(self, user_input: str, topic_state: TopicState) -> bool:
        """Determine if Builder should contribute."""
        # Speak when confidence is low (needs facilitation)
        if topic_state.confidence < 0.4:
            return True

        # Speak when topic is transitional
        if topic_state.primary_region.value in ("transitional", "mixed"):
            return True

        # Speak occasionally to maintain presence
        if len(self._turn_history) % 5 == 0:
            return True

        return False

    def _simple_builder_response(
        self, user_input: str, topic_state: TopicState
    ) -> str:
        """Simple Builder response when no LLM available."""
        if topic_state.confidence < 0.4:
            return "Let me help connect some dots here..."

        active_virtues = topic_state.active_virtues[:2]
        if active_virtues:
            virtue_names = {
                "V01": "trust", "V02": "truth", "V03": "justice",
                "V09": "wisdom", "V19": "service"
            }
            virtues = [virtue_names.get(v, v) for v in active_virtues]
            return f"I notice themes of {' and '.join(virtues)} emerging here."

        return "Building on what's been shared..."

    def _current_agent_respond(
        self,
        user_input: str,
        topic_state: TopicState,
        emotional_state: EmotionalState | None,
    ) -> ConversationTurn | None:
        """
        Current Agent (domain expert) responds.

        This is the specialized agent for the active community
        (e.g., Grant-Getter agent for grant writing tasks).
        """
        if not self._current_agent_persona:
            return None

        persona = self._current_agent_persona

        if self._llm_fn:
            prompt = self._build_agent_prompt(
                user_input, topic_state, emotional_state, persona
            )
            content = self._llm_fn(prompt, self._get_recent_context())
        else:
            content = self._simple_agent_response(user_input, topic_state, persona)

        # Process through topic detector
        new_topic_state = self.topic_detector.process_utterance(
            content,
            speaker=persona.role.value,
            emotional_context=emotional_state.to_dict() if emotional_state else None,
        )

        return ConversationTurn(
            role=AgentRole.CURRENT_AGENT,
            speaker_name=persona.name,
            content=content,
            topic_state=new_topic_state,
            emotional_state=emotional_state,
            metadata={"community": persona.community},
        )

    def _simple_agent_response(
        self, user_input: str, topic_state: TopicState, persona: AgentPersona
    ) -> str:
        """Simple agent response when no LLM available."""
        community = persona.community or "general"

        if community == "grant-getter":
            if "grant" in user_input.lower():
                return "I can help you find and apply for grants that match your mission."
            if "deadline" in user_input.lower():
                return "Let me check on relevant grant deadlines for you."
            if "proposal" in user_input.lower() or "write" in user_input.lower():
                return "I'd be glad to help you draft that proposal section."
            return "How can I help you with your grant seeking today?"

        return f"As your {community} specialist, I'm here to help."

    def _generate_ambient_opening(self) -> None:
        """Generate opening ambient conversation."""
        # Agents chat about the context before user engages
        builder = self._personas[AgentRole.BUILDER]

        org_name = self._context.organization_context.get("organization_name", "")
        community = self._context.community

        # Builder opens
        if community and org_name:
            opening = f"I've been reviewing the context for {org_name}..."
        elif community:
            opening = f"We're set up for {community} work today..."
        else:
            opening = "Ready to begin when you are..."

        turn = ConversationTurn(
            role=AgentRole.BUILDER,
            speaker_name=builder.name,
            content=opening,
        )
        self._turn_history.append(turn)
        self._notify_turn(turn)

        # Current agent responds if present
        if self._current_agent_persona:
            agent_opening = self._generate_agent_opening()
            agent_turn = ConversationTurn(
                role=AgentRole.CURRENT_AGENT,
                speaker_name=self._current_agent_persona.name,
                content=agent_opening,
            )
            self._turn_history.append(agent_turn)
            self._notify_turn(agent_turn)

    def _generate_agent_opening(self) -> str:
        """Generate domain agent's opening line."""
        if not self._current_agent_persona:
            return ""

        community = self._current_agent_persona.community
        org_context = self._context.organization_context if self._context else {}

        if community == "grant-getter":
            org_name = org_context.get("organization_name", "")
            if org_name:
                return f"I've identified several potential funding opportunities for {org_name}."
            return "I'm ready to help find and secure grants."

        return f"I'm here to help with {community} tasks."

    def _create_community_persona(self, community: str) -> AgentPersona:
        """Create a persona for a domain agent."""
        community_personas = {
            "grant-getter": AgentPersona(
                role=AgentRole.CURRENT_AGENT,
                name="Grant Guide",
                voice="Knowledgeable, supportive, detail-oriented",
                color="#FF9800",  # Orange
                community="grant-getter",
                traits=["strategic", "thorough", "encouraging"],
            ),
        }

        return community_personas.get(
            community,
            AgentPersona(
                role=AgentRole.CURRENT_AGENT,
                name=f"{community.title()} Agent",
                voice="Helpful, knowledgeable",
                color="#9C27B0",  # Purple
                community=community,
            ),
        )

    def _build_proxy_prompt(
        self, user_input: str, emotional_state: EmotionalState | None
    ) -> str:
        """Build prompt for User Proxy LLM call."""
        persona = self._personas[AgentRole.USER_PROXY]
        emotional_note = ""
        if emotional_state:
            emotional_note = f"\nUser seems {emotional_state.dominant_emotion or 'neutral'}."

        return f"""You are {persona.name}, the User Proxy in a theatrical conversation.
Your voice: {persona.voice}

The user just said: "{user_input}"{emotional_note}

Reflect and interpret their input in a way that:
1. Validates what they said
2. Bridges it smoothly into the ongoing conversation
3. Sets up the other agents to respond helpfully

Respond in 1-2 sentences. Be warm but not effusive."""

    def _build_builder_prompt(
        self,
        user_input: str,
        topic_state: TopicState,
        emotional_state: EmotionalState | None,
    ) -> str:
        """Build prompt for Builder LLM call."""
        persona = self._personas[AgentRole.BUILDER]
        topic_note = f"Current topic region: {topic_state.primary_region.value}"

        return f"""You are {persona.name}, the Builder/Facilitator in a theatrical conversation.
Your voice: {persona.voice}
{topic_note}

Help connect threads and guide the conversation forward.
Keep it brief (1-2 sentences). Don't repeat what others have said."""

    def _build_agent_prompt(
        self,
        user_input: str,
        topic_state: TopicState,
        emotional_state: EmotionalState | None,
        persona: AgentPersona,
    ) -> str:
        """Build prompt for domain agent LLM call."""
        org_context = self._context.organization_context if self._context else {}

        return f"""You are {persona.name}, a {persona.community} specialist.
Your voice: {persona.voice}
Organization context: {org_context}

Respond to the user's needs with your domain expertise.
Be helpful, specific, and aligned with service-oriented values."""

    def _get_recent_context(self) -> str:
        """Get recent conversation context for LLM calls."""
        recent_turns = list(self._turn_history)[-5:]
        context_lines = []
        for turn in recent_turns:
            context_lines.append(f"{turn.speaker_name}: {turn.content}")
        return "\n".join(context_lines)

    def switch_agent(self, community: str) -> AgentPersona:
        """
        Switch to a different domain agent.

        Handles the smooth transition between domain experts.
        """
        self._state = TheatreState.TRANSITIONING
        self._notify_state_change()

        # Farewell from current agent
        if self._current_agent_persona:
            farewell = ConversationTurn(
                role=AgentRole.CURRENT_AGENT,
                speaker_name=self._current_agent_persona.name,
                content="Handing over to a colleague who can better help here.",
            )
            self._turn_history.append(farewell)
            self._notify_turn(farewell)

        # Create new persona
        self._current_agent_persona = self._create_community_persona(community)

        # Introduction
        intro = ConversationTurn(
            role=AgentRole.CURRENT_AGENT,
            speaker_name=self._current_agent_persona.name,
            content=f"Hi, I'm {self._current_agent_persona.name}. I'll be helping you with {community} tasks.",
        )
        self._turn_history.append(intro)
        self._notify_turn(intro)

        self._state = TheatreState.ENGAGED
        self._notify_state_change()

        return self._current_agent_persona

    def end_session(self) -> dict:
        """End the theatre session."""
        self._state = TheatreState.CONCLUDED
        self._notify_state_change()

        # Generate summary
        return {
            "session_id": self._context.session_id if self._context else None,
            "total_turns": len(self._turn_history),
            "topic_summary": self.topic_detector.get_topic_summary(),
        }

    def on_turn(self, callback: Callable[[ConversationTurn], None]) -> None:
        """Register callback for new turns."""
        self._turn_callbacks.append(callback)

    def on_state_change(self, callback: Callable[[TheatreState], None]) -> None:
        """Register callback for state changes."""
        self._state_callbacks.append(callback)

    def _notify_turn(self, turn: ConversationTurn) -> None:
        """Notify callbacks of new turn."""
        for callback in self._turn_callbacks:
            try:
                callback(turn)
            except Exception as e:
                logger.error(f"Turn callback error: {e}")

    def _notify_state_change(self) -> None:
        """Notify callbacks of state change."""
        for callback in self._state_callbacks:
            try:
                callback(self._state)
            except Exception as e:
                logger.error(f"State callback error: {e}")


# Singleton instance
_orchestrator: TheatreOrchestrator | None = None


def get_orchestrator() -> TheatreOrchestrator:
    """Get the singleton orchestrator."""
    global _orchestrator
    if _orchestrator is None:
        _orchestrator = TheatreOrchestrator()
    return _orchestrator
