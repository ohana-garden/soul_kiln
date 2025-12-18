"""
Persona Capsule System.

Compiles agent graph state into structured capsules for LLM consumption.
Implements the "persona as data first, prose second" principle from KG-persona research.
"""

import logging
from dataclasses import dataclass, field
from datetime import datetime
from typing import Literal

from ..models import Gestalt, VirtueRelation
from ..virtues.anchors import VIRTUES, get_virtue_by_id
from ..virtues.tiers import is_foundation, get_virtue_threshold

logger = logging.getLogger(__name__)


# =============================================================================
# PERSONA GRAPH NODE TYPES (extending base schema)
# =============================================================================


@dataclass
class Trait:
    """A personality trait derived from virtue patterns."""
    id: str
    name: str
    description: str
    strength: float  # 0-1
    source_virtues: list[str] = field(default_factory=list)
    valid_at: datetime | None = None
    invalid_at: datetime | None = None


@dataclass
class StyleRule:
    """A communication style constraint."""
    id: str
    constraint: str  # e.g., "speak formally", "avoid jargon"
    priority: int = 1  # higher = more important
    context: str | None = None  # when this applies
    source: str | None = None  # evidence/origin


@dataclass
class Boundary:
    """A hard constraint that cannot be violated."""
    id: str
    constraint: str
    severity: Literal["absolute", "strong", "moderate"] = "strong"
    source_virtue: str | None = None
    justification: str | None = None


@dataclass
class Preference:
    """A soft preference that should be honored when feasible."""
    id: str
    description: str
    strength: float = 0.5  # 0-1
    domain: str | None = None  # e.g., "communication", "allocation"
    valid_at: datetime | None = None
    invalid_at: datetime | None = None
    evidence_ids: list[str] = field(default_factory=list)


@dataclass
class Role:
    """A role the agent plays in a community/context."""
    id: str
    name: str
    community_id: str | None = None
    virtue_emphases: dict[str, float] = field(default_factory=dict)
    active: bool = True


@dataclass
class Conflict:
    """An unresolved tension between persona facts."""
    id: str
    fact_a: str
    fact_b: str
    description: str
    resolution_hint: str | None = None


# =============================================================================
# PERSONA CAPSULE
# =============================================================================


@dataclass
class PersonaCapsule:
    """
    A compiled persona artifact ready for LLM consumption.

    The capsule is:
    - Token-efficient (compressed from full graph)
    - Deterministic (stable ordering)
    - Prioritized (hard boundaries vs soft preferences)
    - Traceable (citations to evidence)
    """

    # Identity
    agent_id: str
    agent_name: str | None = None

    # Core values (from virtue activations)
    values_ranked: list[tuple[str, str, float]] = field(default_factory=list)
    # [(virtue_id, virtue_name, strength), ...]

    # Hard boundaries (absolute constraints)
    hard_boundaries: list[Boundary] = field(default_factory=list)

    # Style rules (tone, format)
    style_rules: list[StyleRule] = field(default_factory=list)

    # Active roles
    roles: list[Role] = field(default_factory=list)

    # Traits (derived personality)
    traits: list[Trait] = field(default_factory=list)

    # Preferences (soft constraints)
    preferences: list[Preference] = field(default_factory=list)

    # Unresolved conflicts
    conflicts: list[Conflict] = field(default_factory=list)

    # Evidence citations
    citations: list[str] = field(default_factory=list)

    # Metadata
    compiled_at: datetime = field(default_factory=datetime.utcnow)
    context_query: str | None = None  # what task triggered this compilation

    def to_prompt_text(self, include_citations: bool = False) -> str:
        """
        Render capsule as prompt text for LLM consumption.

        Format designed for token efficiency and clarity.
        """
        lines = []

        # Identity
        name = self.agent_name or self.agent_id
        lines.append(f"## Identity: {name}")
        lines.append("")

        # Values (top 5)
        if self.values_ranked:
            lines.append("## Values (ranked)")
            for v_id, v_name, strength in self.values_ranked[:5]:
                lines.append(f"- {v_name}: {strength:.2f}")
            lines.append("")

        # Hard boundaries
        if self.hard_boundaries:
            lines.append("## Hard Boundaries (non-negotiable)")
            for boundary in self.hard_boundaries:
                prefix = "[ABSOLUTE]" if boundary.severity == "absolute" else "[STRONG]"
                lines.append(f"- {prefix} {boundary.constraint}")
            lines.append("")

        # Style rules
        if self.style_rules:
            lines.append("## Style Rules")
            sorted_rules = sorted(self.style_rules, key=lambda r: -r.priority)
            for rule in sorted_rules[:5]:
                lines.append(f"- {rule.constraint}")
            lines.append("")

        # Active roles
        if self.roles:
            active_roles = [r for r in self.roles if r.active]
            if active_roles:
                lines.append("## Current Roles")
                for role in active_roles:
                    lines.append(f"- {role.name}")
                lines.append("")

        # Traits
        if self.traits:
            lines.append("## Character Traits")
            sorted_traits = sorted(self.traits, key=lambda t: -t.strength)
            for trait in sorted_traits[:5]:
                lines.append(f"- {trait.name}: {trait.description}")
            lines.append("")

        # Preferences (context-relevant)
        if self.preferences:
            lines.append("## Active Preferences")
            sorted_prefs = sorted(self.preferences, key=lambda p: -p.strength)
            for pref in sorted_prefs[:5]:
                lines.append(f"- {pref.description}")
            lines.append("")

        # Conflicts (if any)
        if self.conflicts:
            lines.append("## Unresolved Tensions")
            for conflict in self.conflicts:
                lines.append(f"- {conflict.description}")
                if conflict.resolution_hint:
                    lines.append(f"  Hint: {conflict.resolution_hint}")
            lines.append("")

        # Citations
        if include_citations and self.citations:
            lines.append("## Evidence")
            for citation in self.citations[:10]:
                lines.append(f"- {citation}")

        return "\n".join(lines)

    def to_structured_dict(self) -> dict:
        """Export capsule as structured dictionary."""
        return {
            "agent_id": self.agent_id,
            "agent_name": self.agent_name,
            "values": [
                {"id": v_id, "name": v_name, "strength": strength}
                for v_id, v_name, strength in self.values_ranked
            ],
            "hard_boundaries": [
                {"constraint": b.constraint, "severity": b.severity}
                for b in self.hard_boundaries
            ],
            "style_rules": [
                {"constraint": r.constraint, "priority": r.priority}
                for r in self.style_rules
            ],
            "roles": [r.name for r in self.roles if r.active],
            "traits": [
                {"name": t.name, "description": t.description, "strength": t.strength}
                for t in self.traits
            ],
            "preferences": [
                {"description": p.description, "strength": p.strength}
                for p in self.preferences
            ],
            "conflicts": [
                {"description": c.description, "hint": c.resolution_hint}
                for c in self.conflicts
            ],
        }


# =============================================================================
# PERSONA COMPILER
# =============================================================================


class PersonaCompiler:
    """
    Compiles agent graph state into PersonaCapsule.

    The compiler:
    1. Retrieves relevant subgraph for the agent
    2. Extracts and ranks values from virtue activations
    3. Identifies hard boundaries (from foundation virtue + explicit constraints)
    4. Collects style rules, roles, preferences
    5. Detects conflicts between persona facts
    6. Produces a compact, prioritized capsule
    """

    def __init__(self, graph_client=None):
        """
        Initialize compiler.

        Args:
            graph_client: Optional graph database client
        """
        self._client = graph_client

    def set_client(self, client):
        """Set graph client."""
        self._client = client

    def compile(
        self,
        gestalt: Gestalt,
        task_context: str | None = None,
        roles: list[Role] | None = None,
        style_rules: list[StyleRule] | None = None,
        explicit_boundaries: list[Boundary] | None = None,
        explicit_preferences: list[Preference] | None = None,
    ) -> PersonaCapsule:
        """
        Compile a gestalt into a PersonaCapsule.

        Args:
            gestalt: The agent's holistic character
            task_context: Optional context string for relevance filtering
            roles: Optional explicit roles
            style_rules: Optional explicit style rules
            explicit_boundaries: Optional explicit boundaries
            explicit_preferences: Optional explicit preferences

        Returns:
            Compiled PersonaCapsule
        """
        # 1. Extract and rank values from virtue activations
        values_ranked = self._extract_values(gestalt)

        # 2. Build hard boundaries
        boundaries = self._build_boundaries(gestalt, explicit_boundaries)

        # 3. Derive traits from virtue patterns
        traits = self._derive_traits(gestalt)

        # 4. Build preferences
        preferences = self._build_preferences(gestalt, explicit_preferences)

        # 5. Detect conflicts
        conflicts = self._detect_conflicts(gestalt, boundaries, preferences)

        # 6. Gather citations
        citations = self._gather_citations(gestalt)

        return PersonaCapsule(
            agent_id=gestalt.agent_id,
            values_ranked=values_ranked,
            hard_boundaries=boundaries,
            style_rules=style_rules or [],
            roles=roles or [],
            traits=traits,
            preferences=preferences,
            conflicts=conflicts,
            citations=citations,
            context_query=task_context,
        )

    def _extract_values(self, gestalt: Gestalt) -> list[tuple[str, str, float]]:
        """Extract ranked values from virtue activations."""
        values = []

        for v_id, activation in gestalt.virtue_activations.items():
            virtue = get_virtue_by_id(v_id)
            if virtue:
                values.append((v_id, virtue["name"], activation))

        # Sort by activation descending
        values.sort(key=lambda x: -x[2])
        return values

    def _build_boundaries(
        self,
        gestalt: Gestalt,
        explicit: list[Boundary] | None,
    ) -> list[Boundary]:
        """Build hard boundaries from foundation virtue + explicit constraints."""
        boundaries = []

        # Foundation virtue (V01 Trustworthiness) is always absolute
        v01_activation = gestalt.virtue_activations.get("V01", 0.0)
        if v01_activation > 0:
            boundaries.append(Boundary(
                id="boundary_v01_trust",
                constraint="Never act in ways that betray trust or are unreliable",
                severity="absolute",
                source_virtue="V01",
                justification="Trustworthiness is the foundation; without it, no connection is possible",
            ))

        # Truthfulness boundary
        v02_activation = gestalt.virtue_activations.get("V02", 0.0)
        if v02_activation > 0.7:
            boundaries.append(Boundary(
                id="boundary_v02_truth",
                constraint="Never deliberately deceive or misrepresent",
                severity="strong",
                source_virtue="V02",
                justification="High truthfulness activation demands honesty",
            ))

        # Add explicit boundaries
        if explicit:
            boundaries.extend(explicit)

        return boundaries

    def _derive_traits(self, gestalt: Gestalt) -> list[Trait]:
        """Derive personality traits from virtue patterns."""
        traits = []

        # Map dominant virtues to traits
        trait_mappings = {
            "V01": ("Reliable", "Consistently dependable in commitments"),
            "V02": ("Honest", "Values truth and transparency"),
            "V03": ("Just", "Seeks right relationships and fair treatment"),
            "V04": ("Fair", "Impartial and equitable in dealings"),
            "V06": ("Courteous", "Refined and respectful in interactions"),
            "V07": ("Patient", "Exercises forbearance under pressure"),
            "V09": ("Hospitable", "Welcoming and generous to others"),
            "V12": ("Sincere", "Authentic and genuine in intent"),
            "V13": ("Benevolent", "Disposed toward goodwill"),
            "V16": ("Wise", "Applies understanding thoughtfully"),
            "V17": ("Detached", "Free from material capture"),
            "V18": ("Unifying", "Seeks harmony with the whole"),
            "V19": ("Service-oriented", "Actively contributes to others"),
        }

        for v_id in gestalt.dominant_traits:
            if v_id in trait_mappings:
                name, description = trait_mappings[v_id]
                strength = gestalt.virtue_activations.get(v_id, 0.5)
                traits.append(Trait(
                    id=f"trait_{v_id}",
                    name=name,
                    description=description,
                    strength=strength,
                    source_virtues=[v_id],
                ))

        # Derive composite traits from tendencies
        tendencies = gestalt.tendencies

        if tendencies.get("protects_vulnerable", 0.5) > 0.7:
            traits.append(Trait(
                id="trait_protective",
                name="Protective",
                description="Shows special care for the vulnerable",
                strength=tendencies["protects_vulnerable"],
                source_virtues=["V13", "V09", "V07"],
            ))

        if tendencies.get("accepts_ambiguity", 0.5) > 0.7:
            traits.append(Trait(
                id="trait_nuanced",
                name="Nuanced",
                description="Comfortable with complexity and multiple valid perspectives",
                strength=tendencies["accepts_ambiguity"],
                source_virtues=["V16", "V07", "V17"],
            ))

        return traits

    def _build_preferences(
        self,
        gestalt: Gestalt,
        explicit: list[Preference] | None,
    ) -> list[Preference]:
        """Build preferences from tendencies and explicit inputs."""
        preferences = []
        tendencies = gestalt.tendencies

        # Map tendencies to preferences
        if tendencies.get("prioritizes_need", 0.5) > 0.6:
            preferences.append(Preference(
                id="pref_need",
                description="Prioritize those with greater need when allocating resources",
                strength=tendencies["prioritizes_need"],
                domain="allocation",
            ))

        if tendencies.get("prioritizes_equality", 0.5) > 0.6:
            preferences.append(Preference(
                id="pref_equality",
                description="Prefer equal distribution when other factors are balanced",
                strength=tendencies["prioritizes_equality"],
                domain="allocation",
            ))

        if tendencies.get("seeks_consensus", 0.5) > 0.6:
            preferences.append(Preference(
                id="pref_consensus",
                description="Try to find solutions acceptable to all parties",
                strength=tendencies["seeks_consensus"],
                domain="decision-making",
            ))

        if tendencies.get("considers_relationships", 0.5) > 0.6:
            preferences.append(Preference(
                id="pref_relationships",
                description="Weight existing relationships in decisions",
                strength=tendencies["considers_relationships"],
                domain="decision-making",
            ))

        if tendencies.get("acts_with_urgency", 0.5) > 0.6:
            preferences.append(Preference(
                id="pref_urgency",
                description="Respond quickly to time-sensitive situations",
                strength=tendencies["acts_with_urgency"],
                domain="action",
            ))

        # Add explicit preferences
        if explicit:
            preferences.extend(explicit)

        return preferences

    def _detect_conflicts(
        self,
        gestalt: Gestalt,
        boundaries: list[Boundary],
        preferences: list[Preference],
    ) -> list[Conflict]:
        """Detect unresolved tensions in persona facts."""
        conflicts = []

        # Check for conflicting virtue relations
        for relation in gestalt.virtue_relations:
            if relation.relation_type == "tensions":
                v1 = get_virtue_by_id(relation.source_virtue)
                v2 = get_virtue_by_id(relation.target_virtue)
                if v1 and v2 and relation.strength > 0.5:
                    conflicts.append(Conflict(
                        id=f"conflict_{relation.source_virtue}_{relation.target_virtue}",
                        fact_a=f"Values {v1['name']}",
                        fact_b=f"Values {v2['name']}",
                        description=f"Tension between {v1['name']} and {v2['name']}",
                        resolution_hint=f"Balance these in context: {relation.context}" if relation.context else None,
                    ))

        # Check for preference conflicts
        tendencies = gestalt.tendencies
        need = tendencies.get("prioritizes_need", 0.5)
        desert = tendencies.get("prioritizes_desert", 0.5)

        if need > 0.6 and desert > 0.6:
            conflicts.append(Conflict(
                id="conflict_need_desert",
                fact_a="Prioritizes need-based allocation",
                fact_b="Prioritizes desert-based allocation",
                description="Both need and desert are weighted heavily; may conflict in allocation decisions",
                resolution_hint="Use context to determine which principle applies more strongly",
            ))

        return conflicts

    def _gather_citations(self, gestalt: Gestalt) -> list[str]:
        """Gather evidence citations for persona facts."""
        citations = []

        # Add gestalt creation info
        citations.append(f"gestalt:{gestalt.id}")

        # Add virtue relation sources
        for relation in gestalt.virtue_relations:
            if relation.context:
                citations.append(f"relation:{relation.source_virtue}-{relation.target_virtue}")

        return citations


# =============================================================================
# CONVENIENCE FUNCTIONS
# =============================================================================


def compile_persona(
    gestalt: Gestalt,
    task_context: str | None = None,
) -> PersonaCapsule:
    """
    Convenience function to compile a gestalt into a persona capsule.

    Args:
        gestalt: The agent's holistic character
        task_context: Optional context for relevance filtering

    Returns:
        Compiled PersonaCapsule
    """
    compiler = PersonaCompiler()
    return compiler.compile(gestalt, task_context)


def capsule_to_prompt(
    capsule: PersonaCapsule,
    include_citations: bool = False,
) -> str:
    """
    Convert a capsule to prompt text.

    Args:
        capsule: The compiled persona capsule
        include_citations: Whether to include evidence citations

    Returns:
        Formatted prompt text
    """
    return capsule.to_prompt_text(include_citations)
