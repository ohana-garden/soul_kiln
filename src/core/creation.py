"""
Proxy Creation Flow.

A proxy is born through conversation. This module guides that process:

1. "What would you like to create a voice for?"
2. Understand the entity (human, org, concept, object)
3. "Which community should this proxy join?"
4. Create or join community
5. Connect to virtue graph
6. Proxy is born and can speak

The creation is a ritual, not a form fill.
"""

import logging
import uuid
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Callable

from .entity import Entity, EntityType
from .proxy import Proxy, ProxyType, ProxyConfig, ProxyStatus
from .community import Community, CommunityPurpose
from .graph_store import get_core_store

logger = logging.getLogger(__name__)


class CreationStage(str, Enum):
    """Stages of proxy creation."""

    START = "start"  # Initial greeting
    ENTITY_TYPE = "entity_type"  # What are we creating a voice for?
    ENTITY_DETAILS = "entity_details"  # Tell me about them/it
    ENTITY_VOICE = "entity_voice"  # How should they sound?
    COMMUNITY_SELECT = "community_select"  # Which community?
    COMMUNITY_CREATE = "community_create"  # Creating a new community
    PROXY_CONFIG = "proxy_config"  # How autonomous?
    CONFIRMATION = "confirmation"  # Review and confirm
    COMPLETE = "complete"  # Done


@dataclass
class CreationState:
    """
    State of an ongoing proxy creation.

    Tracks progress through the creation ritual.
    """

    id: str = field(default_factory=lambda: f"creation_{uuid.uuid4().hex[:12]}")
    creator_id: str = ""

    # Current stage
    stage: CreationStage = CreationStage.START

    # Collected information
    entity_type: EntityType | None = None
    entity_name: str = ""
    entity_description: str = ""
    entity_facts: list[str] = field(default_factory=list)
    entity_voice: str = ""

    community_id: str | None = None
    community_name: str = ""
    new_community: bool = False

    proxy_name: str = ""
    proxy_type: ProxyType = ProxyType.VOICE
    proxy_config: ProxyConfig = field(default_factory=ProxyConfig)

    # Created objects (populated on completion)
    entity: Entity | None = None
    proxy: Proxy | None = None
    community: Community | None = None

    # Timestamps
    started_at: datetime = field(default_factory=datetime.utcnow)
    completed_at: datetime | None = None

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "creator_id": self.creator_id,
            "stage": self.stage.value,
            "entity_type": self.entity_type.value if self.entity_type else None,
            "entity_name": self.entity_name,
            "entity_description": self.entity_description,
            "entity_facts": self.entity_facts,
            "entity_voice": self.entity_voice,
            "community_id": self.community_id,
            "community_name": self.community_name,
            "new_community": self.new_community,
            "proxy_name": self.proxy_name,
            "proxy_type": self.proxy_type.value,
            "proxy_config": self.proxy_config.to_dict(),
            "started_at": self.started_at.isoformat(),
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
        }


# Prompts for each stage
STAGE_PROMPTS = {
    CreationStage.START: """
I can help you create a proxy - a voice that speaks for someone or something.

Who or what would you like to create a voice for?
- Yourself (your authentic voice in conversations)
- Another person (family, colleague, historical figure)
- An organization (nonprofit, company, team)
- A concept (justice, creativity, your future self)
- Something else (a place, a project, a memory)

Just tell me in your own words.
""".strip(),

    CreationStage.ENTITY_TYPE: """
I want to understand better. Is this:
1. **Yourself** - your own voice
2. **A person** - someone you know or knew
3. **An organization** - a group or institution
4. **A concept** - an idea or aspiration
5. **Something else** - a place, object, or memory

Which feels right?
""".strip(),

    CreationStage.ENTITY_DETAILS: """
Tell me more about {entity_name}.

What should I know to represent them well? What matters most about who they are or what they stand for?
""".strip(),

    CreationStage.ENTITY_VOICE: """
How should {entity_name}'s voice sound?

Think about:
- Are they formal or casual?
- Brief and direct, or thoughtful and elaborate?
- Warm and personal, or more reserved?

Describe it however feels natural.
""".strip(),

    CreationStage.COMMUNITY_SELECT: """
Every proxy belongs to a community where members share everything they learn.

Would you like this proxy to join:
1. An existing community (I'll show you options)
2. Create a new community
3. Start in a general community for now

What feels right?
""".strip(),

    CreationStage.COMMUNITY_CREATE: """
Let's create a new community.

What should it be called, and what's its purpose?
""".strip(),

    CreationStage.PROXY_CONFIG: """
Almost there. A few quick choices:

**Autonomy**: How much should {proxy_name} speak on their own?
- Low: Only when directly addressed
- Medium: Joins in when relevant
- High: Actively participates

**Major decisions**: Should they defer to you on big choices?
- Yes (recommended)
- No, let them decide

What feels right?
""".strip(),

    CreationStage.CONFIRMATION: """
Let me confirm what we're creating:

**Voice for**: {entity_name} ({entity_type})
**Description**: {entity_description}
**Community**: {community_name}
**Autonomy**: {autonomy_level}

Does this look right? Say "yes" to create, or tell me what to change.
""".strip(),

    CreationStage.COMPLETE: """
{proxy_name} is born.

They're now a member of {community_name} and ready to speak.
Everything they learn will be shared with the community.

Would you like to start a conversation with them?
""".strip(),
}


class ProxyCreator:
    """
    Guides the conversational creation of a proxy.

    Usage:
        creator = ProxyCreator(creator_id="user123")
        response = creator.start()

        # User says something
        response = creator.process("I want to create a voice for my nonprofit")

        # Continue until complete
        while not creator.is_complete:
            response = creator.process(user_input)

        # Get the created proxy
        proxy = creator.state.proxy
    """

    def __init__(
        self,
        creator_id: str,
        store: Any = None,
        llm_fn: Callable[[str, str], str] | None = None,
    ):
        """
        Initialize the creator.

        Args:
            creator_id: Who is creating this proxy
            store: Optional graph store (defaults to singleton)
            llm_fn: Optional LLM function for natural language understanding
        """
        self.creator_id = creator_id
        self.store = store or get_core_store()
        self.llm_fn = llm_fn

        self.state = CreationState(creator_id=creator_id)
        self._stage_handlers = {
            CreationStage.START: self._handle_start,
            CreationStage.ENTITY_TYPE: self._handle_entity_type,
            CreationStage.ENTITY_DETAILS: self._handle_entity_details,
            CreationStage.ENTITY_VOICE: self._handle_entity_voice,
            CreationStage.COMMUNITY_SELECT: self._handle_community_select,
            CreationStage.COMMUNITY_CREATE: self._handle_community_create,
            CreationStage.PROXY_CONFIG: self._handle_proxy_config,
            CreationStage.CONFIRMATION: self._handle_confirmation,
        }

    @property
    def is_complete(self) -> bool:
        """Check if creation is complete."""
        return self.state.stage == CreationStage.COMPLETE

    def start(self) -> str:
        """Start the creation flow."""
        self.state.stage = CreationStage.START
        return STAGE_PROMPTS[CreationStage.START]

    def process(self, user_input: str) -> str:
        """
        Process user input and return next prompt.

        Args:
            user_input: What the user said

        Returns:
            Next prompt or completion message
        """
        if self.is_complete:
            return "This creation is already complete."

        handler = self._stage_handlers.get(self.state.stage)
        if handler:
            return handler(user_input)

        return "I'm not sure what to do next. Let's start over."

    def _handle_start(self, user_input: str) -> str:
        """Handle initial input about what to create."""
        input_lower = user_input.lower()

        # Try to detect entity type from input
        if any(word in input_lower for word in ["myself", "my voice", "me", "i want"]):
            self.state.entity_type = EntityType.SELF
            self.state.entity_name = "You"
        elif any(word in input_lower for word in ["nonprofit", "organization", "company", "team"]):
            self.state.entity_type = EntityType.ORGANIZATION
            # Extract name if mentioned
            self.state.entity_name = self._extract_name(user_input)
        elif any(word in input_lower for word in ["person", "friend", "family", "colleague"]):
            self.state.entity_type = EntityType.HUMAN
            self.state.entity_name = self._extract_name(user_input)
        elif any(word in input_lower for word in ["grandma", "grandpa", "mother", "father", "passed", "deceased"]):
            self.state.entity_type = EntityType.DECEASED
            self.state.entity_name = self._extract_name(user_input)
        elif any(word in input_lower for word in ["concept", "idea", "justice", "creativity"]):
            self.state.entity_type = EntityType.CONCEPT
            self.state.entity_name = self._extract_name(user_input)
        elif any(word in input_lower for word in ["future", "become", "aspire"]):
            self.state.entity_type = EntityType.FUTURE_SELF
            self.state.entity_name = "Future You"
        elif any(word in input_lower for word in ["pet", "dog", "cat", "animal"]):
            self.state.entity_type = EntityType.PET
            self.state.entity_name = self._extract_name(user_input)
        elif any(word in input_lower for word in ["place", "home", "location"]):
            self.state.entity_type = EntityType.PLACE
            self.state.entity_name = self._extract_name(user_input)
        elif any(word in input_lower for word in ["project", "initiative"]):
            self.state.entity_type = EntityType.PROJECT
            self.state.entity_name = self._extract_name(user_input)

        # If we detected a type, move to details
        if self.state.entity_type:
            self.state.stage = CreationStage.ENTITY_DETAILS
            prompt = STAGE_PROMPTS[CreationStage.ENTITY_DETAILS]
            return prompt.format(entity_name=self.state.entity_name or "them")

        # Otherwise, ask for clarification
        self.state.stage = CreationStage.ENTITY_TYPE
        return STAGE_PROMPTS[CreationStage.ENTITY_TYPE]

    def _handle_entity_type(self, user_input: str) -> str:
        """Handle entity type selection."""
        input_lower = user_input.lower()

        if "1" in user_input or "yourself" in input_lower or "self" in input_lower:
            self.state.entity_type = EntityType.SELF
            self.state.entity_name = "You"
        elif "2" in user_input or "person" in input_lower:
            self.state.entity_type = EntityType.HUMAN
        elif "3" in user_input or "organization" in input_lower:
            self.state.entity_type = EntityType.ORGANIZATION
        elif "4" in user_input or "concept" in input_lower:
            self.state.entity_type = EntityType.CONCEPT
        elif "5" in user_input:
            self.state.entity_type = EntityType.OBJECT  # Generic other

        if not self.state.entity_name and self.state.entity_type != EntityType.SELF:
            # Need to get name
            return "What's their name?"

        self.state.stage = CreationStage.ENTITY_DETAILS
        prompt = STAGE_PROMPTS[CreationStage.ENTITY_DETAILS]
        return prompt.format(entity_name=self.state.entity_name or "them")

    def _handle_entity_details(self, user_input: str) -> str:
        """Handle entity description."""
        # If no name yet and user is providing it
        if not self.state.entity_name:
            self.state.entity_name = self._extract_name(user_input)

        self.state.entity_description = user_input

        # Extract any facts
        sentences = user_input.split(".")
        for sentence in sentences:
            sentence = sentence.strip()
            if len(sentence) > 10:
                self.state.entity_facts.append(sentence)

        self.state.stage = CreationStage.ENTITY_VOICE
        prompt = STAGE_PROMPTS[CreationStage.ENTITY_VOICE]
        return prompt.format(entity_name=self.state.entity_name or "their")

    def _handle_entity_voice(self, user_input: str) -> str:
        """Handle voice description."""
        self.state.entity_voice = user_input

        # Set proxy name based on entity
        if self.state.entity_type == EntityType.SELF:
            self.state.proxy_name = "Your Voice"
        else:
            self.state.proxy_name = f"Voice of {self.state.entity_name}"

        self.state.stage = CreationStage.COMMUNITY_SELECT
        return STAGE_PROMPTS[CreationStage.COMMUNITY_SELECT]

    def _handle_community_select(self, user_input: str) -> str:
        """Handle community selection."""
        input_lower = user_input.lower()

        if "1" in user_input or "existing" in input_lower:
            # Show existing communities
            communities = self.store.list_communities()
            if communities:
                options = "\n".join(
                    f"- **{c.name}**: {c.description[:50]}..."
                    for c in communities[:5]
                )
                return f"Here are some communities:\n\n{options}\n\nWhich would you like to join?"
            else:
                return "No communities exist yet. Let's create one. What should it be called?"

        elif "2" in user_input or "new" in input_lower or "create" in input_lower:
            self.state.new_community = True
            self.state.stage = CreationStage.COMMUNITY_CREATE
            return STAGE_PROMPTS[CreationStage.COMMUNITY_CREATE]

        elif "3" in user_input or "general" in input_lower:
            # Use or create general community
            general = self.store.get_community_by_name("General")
            if not general:
                general = Community(
                    name="General",
                    description="A welcoming community for all",
                    purpose=CommunityPurpose.GENERAL,
                    creator_id=self.creator_id,
                )
                self.store.save_community(general)

            self.state.community_id = general.id
            self.state.community_name = general.name
            self.state.community = general
            self.state.stage = CreationStage.PROXY_CONFIG
            prompt = STAGE_PROMPTS[CreationStage.PROXY_CONFIG]
            return prompt.format(proxy_name=self.state.proxy_name)

        else:
            # Try to match a community by name
            community = self.store.get_community_by_name(user_input.strip())
            if community:
                self.state.community_id = community.id
                self.state.community_name = community.name
                self.state.community = community
                self.state.stage = CreationStage.PROXY_CONFIG
                prompt = STAGE_PROMPTS[CreationStage.PROXY_CONFIG]
                return prompt.format(proxy_name=self.state.proxy_name)

            return "I didn't catch that. Would you like to:\n1. Join an existing community\n2. Create a new one\n3. Use the general community"

    def _handle_community_create(self, user_input: str) -> str:
        """Handle new community creation."""
        # Extract name and purpose from input
        self.state.community_name = self._extract_name(user_input)
        if not self.state.community_name:
            self.state.community_name = user_input.split(".")[0].strip()

        # Create the community
        community = Community(
            name=self.state.community_name,
            description=user_input,
            purpose=CommunityPurpose.GENERAL,  # Could be smarter about this
            creator_id=self.creator_id,
        )
        self.store.save_community(community)

        self.state.community_id = community.id
        self.state.community = community

        self.state.stage = CreationStage.PROXY_CONFIG
        prompt = STAGE_PROMPTS[CreationStage.PROXY_CONFIG]
        return prompt.format(proxy_name=self.state.proxy_name)

    def _handle_proxy_config(self, user_input: str) -> str:
        """Handle proxy configuration."""
        input_lower = user_input.lower()

        # Autonomy level
        if "high" in input_lower or "active" in input_lower:
            self.state.proxy_config.autonomy = 0.8
        elif "low" in input_lower or "quiet" in input_lower:
            self.state.proxy_config.autonomy = 0.2
        else:
            self.state.proxy_config.autonomy = 0.5

        # Defer on major decisions
        if "no" in input_lower and "defer" in input_lower:
            self.state.proxy_config.defer_on_major = False
        else:
            self.state.proxy_config.defer_on_major = True

        # Move to confirmation
        self.state.stage = CreationStage.CONFIRMATION

        autonomy_desc = (
            "High" if self.state.proxy_config.autonomy > 0.6
            else "Low" if self.state.proxy_config.autonomy < 0.4
            else "Medium"
        )

        prompt = STAGE_PROMPTS[CreationStage.CONFIRMATION]
        return prompt.format(
            entity_name=self.state.entity_name,
            entity_type=self.state.entity_type.value if self.state.entity_type else "unknown",
            entity_description=self.state.entity_description[:100] + "...",
            community_name=self.state.community_name,
            autonomy_level=autonomy_desc,
        )

    def _handle_confirmation(self, user_input: str) -> str:
        """Handle final confirmation and create objects."""
        input_lower = user_input.lower()

        if "yes" in input_lower or "confirm" in input_lower or "create" in input_lower:
            return self._complete_creation()

        if "no" in input_lower or "change" in input_lower:
            # Could be smarter about what to change
            self.state.stage = CreationStage.START
            return "Let's start over. " + STAGE_PROMPTS[CreationStage.START]

        return "Just say 'yes' to create, or tell me what you'd like to change."

    def _complete_creation(self) -> str:
        """Complete the creation and persist everything."""
        # Create Entity
        entity = Entity(
            type=self.state.entity_type or EntityType.SELF,
            name=self.state.entity_name,
            description=self.state.entity_description,
            creator_id=self.creator_id,
            facts=self.state.entity_facts,
            voice_description=self.state.entity_voice,
        )
        self.store.save_entity(entity)
        self.state.entity = entity

        # Create virtue graph agent for the proxy
        from ..functions.spawn import spawn_agent
        try:
            agent_id = spawn_agent(agent_type="candidate")
        except Exception as e:
            logger.warning(f"Could not create virtue agent: {e}")
            agent_id = ""

        # Create Proxy
        proxy = Proxy(
            entity_id=entity.id,
            creator_id=self.creator_id,
            name=self.state.proxy_name,
            role=f"Voice of {entity.name}",
            type=self.state.proxy_type,
            status=ProxyStatus.ACTIVE,
            community_ids=[self.state.community_id] if self.state.community_id else [],
            agent_id=agent_id,
            config=self.state.proxy_config,
        )
        proxy.activate()
        self.store.save_proxy(proxy)
        self.state.proxy = proxy

        # Update community membership
        if self.state.community:
            self.state.community.add_member(proxy.id)
            self.store.save_community(self.state.community)

        # Mark complete
        self.state.stage = CreationStage.COMPLETE
        self.state.completed_at = datetime.utcnow()

        logger.info(f"Created proxy {proxy.id} for entity {entity.id}")

        prompt = STAGE_PROMPTS[CreationStage.COMPLETE]
        return prompt.format(
            proxy_name=self.state.proxy_name,
            community_name=self.state.community_name or "their community",
        )

    def _extract_name(self, text: str) -> str:
        """Extract a name from text (simple heuristic)."""
        # Look for quoted text
        import re
        quoted = re.findall(r'"([^"]+)"', text)
        if quoted:
            return quoted[0]

        # Look for "called X" or "named X"
        patterns = [
            r"called\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)?)",
            r"named\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)?)",
            r"for\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)?)",
        ]
        for pattern in patterns:
            match = re.search(pattern, text)
            if match:
                return match.group(1)

        # Look for capitalized words
        caps = re.findall(r"\b([A-Z][a-z]+(?:\s+[A-Z][a-z]+)?)\b", text)
        if caps:
            return caps[0]

        return ""


def create_proxy_conversation(creator_id: str) -> ProxyCreator:
    """
    Start a proxy creation conversation.

    Args:
        creator_id: Who is creating

    Returns:
        ProxyCreator ready to guide the conversation
    """
    return ProxyCreator(creator_id=creator_id)
