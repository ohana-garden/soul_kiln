"""
Persona capsule compilation.

Compiles agent topology/gestalt into structured PersonaCapsule
artifacts suitable for LLM conditioning.

The compilation process:
1. Retrieve gestalt (virtue activations, tendencies, archetype)
2. Extract boundaries from lore taboos/commitments
3. Rank values from virtue activations
4. Convert tendencies to preferences
5. Retrieve community patterns for archetype
6. Detect uncertainties/conflicts
7. Add situational context filtering
8. Render to structured + text formats
"""

import logging
import uuid
from datetime import datetime
from typing import Optional

from ..gestalt.compute import compute_gestalt, get_gestalt
from ..gestalt.tendencies import TENDENCY_DEFINITIONS
from ..models import (
    Gestalt,
    PersonaCapsule,
    PersonaBoundary,
    PersonaValue,
    PersonaPreference,
    PersonaUncertainty,
    Situation,
)
from ..virtues.anchors import VIRTUES
from ..virtues.tiers import FOUNDATION, ASPIRATIONAL

logger = logging.getLogger(__name__)


class PersonaCompiler:
    """
    Compiles gestalts into persona capsules.

    Stateless compiler that can be reused across agents.
    """

    def __init__(
        self,
        include_community_patterns: bool = True,
        max_values: int = 10,
        max_preferences: int = 8,
        max_boundaries: int = 10,
    ):
        """
        Initialize compiler with configuration.

        Args:
            include_community_patterns: Whether to include archetype population patterns
            max_values: Maximum number of values to include
            max_preferences: Maximum number of preferences to include
            max_boundaries: Maximum number of boundaries to include
        """
        self.include_community_patterns = include_community_patterns
        self.max_values = max_values
        self.max_preferences = max_preferences
        self.max_boundaries = max_boundaries

        # Cache for community patterns (computed once per archetype)
        self._community_cache = {}

    def compile(
        self,
        agent_id: str,
        situation_context: str | None = None,
        situation: Situation | None = None,
    ) -> PersonaCapsule:
        """
        Compile a persona capsule for an agent.

        Args:
            agent_id: Agent to compile capsule for
            situation_context: Optional text description of current context
            situation: Optional structured situation for context-aware filtering

        Returns:
            PersonaCapsule ready for LLM conditioning
        """
        # Get gestalt
        gestalt = get_gestalt(agent_id)
        if not gestalt:
            logger.warning(f"Could not get gestalt for {agent_id}, creating minimal capsule")
            return self._minimal_capsule(agent_id, situation_context)

        # Build capsule components
        boundaries = self._extract_boundaries(gestalt)
        values = self._extract_values(gestalt)
        preferences = self._extract_preferences(gestalt, situation)
        uncertainties = self._detect_uncertainties(gestalt)
        active_roles = self._get_active_roles(gestalt, situation)
        style_rules = self._get_style_rules(gestalt)

        # Get community patterns if enabled
        community_patterns = []
        if self.include_community_patterns and gestalt.archetype:
            community_patterns = self._get_community_patterns(gestalt.archetype)

        # Build citations
        citations = self._collect_citations(gestalt, boundaries, values)

        return PersonaCapsule(
            agent_id=agent_id,
            agent_name=self._get_agent_name(agent_id),
            archetype=gestalt.archetype,
            boundaries=boundaries[:self.max_boundaries],
            values=values[:self.max_values],
            preferences=preferences[:self.max_preferences],
            community_patterns=community_patterns,
            uncertainties=uncertainties,
            active_roles=active_roles,
            style_rules=style_rules,
            situation_context=situation_context,
            compiled_at=datetime.utcnow(),
            source_gestalt_id=gestalt.id,
            citations=citations,
        )

    def _minimal_capsule(
        self,
        agent_id: str,
        context: str | None,
    ) -> PersonaCapsule:
        """Create minimal capsule when gestalt unavailable."""
        return PersonaCapsule(
            agent_id=agent_id,
            situation_context=context,
            uncertainties=[
                PersonaUncertainty(
                    description="Agent gestalt could not be computed",
                    uncertainty_type="missing",
                    impact="high",
                )
            ],
        )

    def _extract_boundaries(self, gestalt: Gestalt) -> list[PersonaBoundary]:
        """Extract hard boundaries from lore and beliefs."""
        boundaries = []

        # Try to get lore taboos
        try:
            from ..lore.definitions import get_lore_by_type

            # Taboos are hard boundaries
            taboos = get_lore_by_type("taboo")
            for taboo in taboos:
                boundaries.append(PersonaBoundary(
                    id=taboo.id,
                    description=taboo.content,
                    boundary_type="taboo",
                    forbids=self._parse_forbids(taboo.content),
                    source_type="lore",
                    source_id=taboo.id,
                    priority=1,  # Taboos are highest priority
                ))

            # Commitments are also hard boundaries
            commitments = get_lore_by_type("commitment")
            for commitment in commitments:
                boundaries.append(PersonaBoundary(
                    id=commitment.id,
                    description=commitment.content,
                    boundary_type="commitment",
                    requires=self._parse_requires(commitment.content),
                    source_type="lore",
                    source_id=commitment.id,
                    priority=2,
                ))

        except ImportError:
            logger.debug("Lore definitions not available")

        # Foundation virtues create implicit boundaries
        for v_id in FOUNDATION:
            activation = gestalt.virtue_activations.get(v_id, 0.0)
            if activation >= 0.9:  # Very high foundation = hard boundary
                virtue_info = next((v for v in VIRTUES if v["id"] == v_id), None)
                if virtue_info:
                    boundaries.append(PersonaBoundary(
                        id=f"foundation_{v_id}",
                        description=f"Must maintain {virtue_info['name']}",
                        boundary_type="rule",
                        source_type="belief",
                        source_id=v_id,
                        priority=3,
                    ))

        return sorted(boundaries, key=lambda b: b.priority)

    def _parse_forbids(self, content: str) -> list[str]:
        """Parse forbidden actions from taboo content."""
        content_lower = content.lower()
        forbids = []

        # Simple keyword extraction
        if "never" in content_lower:
            # Extract what comes after "never"
            parts = content_lower.split("never")
            if len(parts) > 1:
                action = parts[1].strip().rstrip(".")
                forbids.append(action)

        return forbids

    def _parse_requires(self, content: str) -> list[str]:
        """Parse required actions from commitment content."""
        content_lower = content.lower()
        requires = []

        if "will" in content_lower:
            parts = content_lower.split("will")
            if len(parts) > 1:
                action = parts[1].strip().rstrip(".")
                requires.append(action)

        return requires

    def _extract_values(self, gestalt: Gestalt) -> list[PersonaValue]:
        """Extract ranked values from virtue activations."""
        values = []

        # Sort virtues by activation
        sorted_virtues = sorted(
            gestalt.virtue_activations.items(),
            key=lambda x: x[1],
            reverse=True,
        )

        for rank, (v_id, strength) in enumerate(sorted_virtues, 1):
            if strength < 0.3:  # Skip very weak values
                continue

            virtue_info = next((v for v in VIRTUES if v["id"] == v_id), None)
            if not virtue_info:
                continue

            tier = "foundation" if v_id in FOUNDATION else "aspirational"

            values.append(PersonaValue(
                virtue_id=v_id,
                name=virtue_info["name"],
                strength=strength,
                rank=rank,
                tier=tier,
                grounded_in=[f"topology:{gestalt.agent_id}"],
            ))

        return values

    def _extract_preferences(
        self,
        gestalt: Gestalt,
        situation: Situation | None,
    ) -> list[PersonaPreference]:
        """Convert tendencies to preferences."""
        preferences = []

        for t_name, strength in gestalt.tendencies.items():
            if strength < 0.4:  # Skip weak tendencies
                continue

            definition = TENDENCY_DEFINITIONS.get(t_name, {})
            description = definition.get("description", t_name.replace("_", " "))

            # Determine favors/disfavors based on tendency type
            favors = []
            disfavors = []

            if "prioritizes_need" in t_name:
                favors = ["allocate_by_need", "consider_urgency"]
                disfavors = ["ignore_need"]
            elif "prioritizes_desert" in t_name:
                favors = ["allocate_by_merit", "reward_effort"]
                disfavors = ["ignore_desert"]
            elif "protects_vulnerable" in t_name:
                favors = ["protect_vulnerable", "special_consideration"]
            elif "honors_commitments" in t_name:
                favors = ["keep_promises", "maintain_trust"]
                disfavors = ["break_promise"]
            elif "accepts_ambiguity" in t_name:
                favors = ["acknowledge_uncertainty", "multiple_valid_answers"]
            elif "seeks_consensus" in t_name:
                favors = ["find_common_ground", "inclusive_solutions"]

            preferences.append(PersonaPreference(
                name=t_name.replace("_", " ").title(),
                description=description,
                strength=strength,
                favors=favors,
                disfavors=disfavors,
                source="tendency",
            ))

        # Sort by strength
        return sorted(preferences, key=lambda p: -p.strength)

    def _detect_uncertainties(self, gestalt: Gestalt) -> list[PersonaUncertainty]:
        """Detect uncertainties and conflicts in the gestalt."""
        uncertainties = []

        # Check for virtue tensions
        for relation in gestalt.virtue_relations:
            if relation.relation_type == "tensions" and relation.strength > 0.5:
                uncertainties.append(PersonaUncertainty(
                    description=f"Tension between {relation.source_virtue} and {relation.target_virtue}",
                    uncertainty_type="conflict",
                    involves=[relation.source_virtue, relation.target_virtue],
                    impact="medium",
                ))

        # Check for low coherence
        if gestalt.internal_coherence < 0.4:
            uncertainties.append(PersonaUncertainty(
                description="Character coherence is low - values may conflict",
                uncertainty_type="conflict",
                impact="high",
            ))

        # Check for low stability
        if gestalt.stability < 0.4:
            uncertainties.append(PersonaUncertainty(
                description="Character is still evolving - behavior may vary",
                uncertainty_type="evolving",
                impact="medium",
            ))

        # Check for weak tendencies in key areas
        weak_tendencies = [
            t for t, v in gestalt.tendencies.items()
            if 0.4 < v < 0.6  # Neither strong nor weak
        ]
        if len(weak_tendencies) > 3:
            uncertainties.append(PersonaUncertainty(
                description=f"Preferences unclear for: {', '.join(weak_tendencies[:3])}",
                uncertainty_type="weak",
                involves=weak_tendencies[:3],
                impact="low",
            ))

        return uncertainties

    def _get_active_roles(
        self,
        gestalt: Gestalt,
        situation: Situation | None,
    ) -> list[str]:
        """Get active kuleanas/roles for the context."""
        roles = []

        try:
            from ..kuleana.definitions import AMBASSADOR_KULEANAS

            # For now, return all kuleana names
            # Future: filter by situation triggers
            for k_id, kuleana in AMBASSADOR_KULEANAS.items():
                if kuleana.priority <= 3:  # High priority roles
                    roles.append(kuleana.name)

        except ImportError:
            logger.debug("Kuleana definitions not available")

        # Also use archetype as role
        if gestalt.archetype:
            roles.append(f"{gestalt.archetype.title()} archetype")

        return roles[:5]  # Limit roles

    def _get_style_rules(self, gestalt: Gestalt) -> list[str]:
        """Get voice/style rules."""
        rules = []

        try:
            from ..voice.definitions import AMBASSADOR_VOICE

            # Get tone patterns
            for v_id, pattern in AMBASSADOR_VOICE.items():
                if pattern.pattern_type == "tone" and pattern.intensity > 0.6:
                    rules.append(pattern.content[:100])  # Truncate

        except ImportError:
            logger.debug("Voice definitions not available")

        # Archetype-based style hints
        archetype_styles = {
            "guardian": "Direct, protective, emphasizes safety and trust",
            "seeker": "Curious, exploratory, emphasizes learning and growth",
            "servant": "Humble, supportive, emphasizes helping and service",
            "contemplative": "Thoughtful, measured, emphasizes reflection and wisdom",
        }

        if gestalt.archetype and gestalt.archetype in archetype_styles:
            rules.append(archetype_styles[gestalt.archetype])

        return rules[:3]

    def _get_community_patterns(self, archetype: str) -> list:
        """Get community patterns for archetype."""
        if archetype in self._community_cache:
            return self._community_cache[archetype]

        try:
            from .community import get_community_patterns
            patterns = get_community_patterns(archetype)
            self._community_cache[archetype] = patterns
            return patterns
        except Exception as e:
            logger.debug(f"Could not get community patterns: {e}")
            return []

    def _get_agent_name(self, agent_id: str) -> str | None:
        """Get agent's name if available."""
        try:
            from ..graph.client import get_client
            client = get_client()
            result = client.query(
                "MATCH (a:Agent {id: $id}) RETURN a.name",
                {"id": agent_id}
            )
            if result and result[0][0]:
                return result[0][0]
        except Exception:
            pass
        return None

    def _collect_citations(
        self,
        gestalt: Gestalt,
        boundaries: list[PersonaBoundary],
        values: list[PersonaValue],
    ) -> list[str]:
        """Collect citations for provenance."""
        citations = []

        # Gestalt source
        citations.append(f"gestalt:{gestalt.id}")

        # Boundary sources
        for b in boundaries:
            if b.source_id:
                citations.append(f"{b.source_type}:{b.source_id}")

        # Value sources
        for v in values[:5]:
            citations.append(f"virtue:{v.virtue_id}")

        return list(set(citations))  # Dedupe


# Module-level convenience functions

_default_compiler = None


def _get_compiler() -> PersonaCompiler:
    """Get or create default compiler."""
    global _default_compiler
    if _default_compiler is None:
        _default_compiler = PersonaCompiler()
    return _default_compiler


def compile_persona_capsule(
    agent_id: str,
    situation_context: str | None = None,
) -> PersonaCapsule:
    """
    Compile a persona capsule for an agent.

    This is the main entry point for persona compilation.

    Args:
        agent_id: Agent to compile capsule for
        situation_context: Optional text description of current context

    Returns:
        PersonaCapsule ready for LLM conditioning

    Example:
        >>> capsule = compile_persona_capsule("agent_001", "resource allocation decision")
        >>> print(capsule.to_prompt_text())
    """
    compiler = _get_compiler()
    return compiler.compile(agent_id, situation_context)


def compile_for_situation(
    agent_id: str,
    situation: Situation,
) -> PersonaCapsule:
    """
    Compile a persona capsule tailored to a specific situation.

    Uses the structured situation to filter relevant preferences
    and roles.

    Args:
        agent_id: Agent to compile capsule for
        situation: Structured situation model

    Returns:
        PersonaCapsule with situation-aware filtering
    """
    compiler = _get_compiler()
    return compiler.compile(
        agent_id,
        situation_context=situation.description or situation.name,
        situation=situation,
    )
