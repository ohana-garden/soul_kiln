"""
Diffusion-based Definition Generator.

Uses iterative denoising to generate definitions for personas, virtues, traits,
and other semantic entities. The diffusion process:
1. Starts from noise in embedding space
2. Denoises conditioned on context (graph state, relationships, etc.)
3. Decodes the final embedding into natural language via LLM

This produces more coherent, contextually-grounded definitions that
reflect the learned structure of the virtue basin system.
"""

import math
import random
import uuid
import logging
from dataclasses import dataclass, field
from typing import Callable, Literal

from ..models import Gestalt, VirtueRelation
from ..virtues.anchors import VIRTUES, get_virtue_by_id
from ..gestalt.embedding import (
    GestaltEmbedding,
    encode_gestalt,
    decode_embedding,
    add_noise,
    sample_random_embedding,
    TOTAL_DIM,
    VIRTUE_DIM,
)

logger = logging.getLogger(__name__)


# =============================================================================
# DEFINITION EMBEDDING
# =============================================================================


@dataclass
class DefinitionEmbedding:
    """
    Vector representation of a definition in latent space.

    The embedding captures semantic features that can be decoded
    into natural language definitions.
    """
    id: str
    target_type: Literal["persona", "virtue", "trait", "preference", "boundary", "style"]
    vector: list[float]
    conditioning: dict = field(default_factory=dict)

    def distance(self, other: "DefinitionEmbedding") -> float:
        """Euclidean distance to another embedding."""
        return math.sqrt(sum(
            (a - b) ** 2 for a, b in zip(self.vector, other.vector)
        ))


@dataclass
class GeneratedDefinition:
    """A definition generated through diffusion."""
    id: str
    target_type: str
    target_id: str | None = None  # e.g., virtue_id, agent_id
    definition: str = ""
    essence: str = ""  # one-line summary
    properties: dict = field(default_factory=dict)
    confidence: float = 0.5
    embedding: DefinitionEmbedding | None = None


# =============================================================================
# DEFINITION TEMPLATES (for LLM decoding guidance)
# =============================================================================


DEFINITION_TEMPLATES = {
    "persona": """
Based on the following character profile:
- Dominant values: {values}
- Key traits: {traits}
- Tendencies: {tendencies}
- Archetype hints: {archetype}

Generate a coherent persona definition that captures:
1. Core identity (who this agent is)
2. Key motivations (what drives them)
3. Characteristic behaviors (how they typically act)
4. Communication style (how they express themselves)

Format:
IDENTITY: [1-2 sentences]
MOTIVATIONS: [1-2 sentences]
BEHAVIORS: [2-3 key behaviors]
STYLE: [tone and manner]
""",

    "virtue": """
For virtue: {virtue_name}
Base essence: {base_essence}
Related virtues: {related}
Position in moral geometry: {geometry}
Activation pattern: {activation}

Generate a contextually-grounded definition that:
1. Captures the core meaning
2. Shows how it relates to adjacent virtues
3. Describes how it manifests in action
4. Identifies its boundaries (when it applies, when it doesn't)

Format:
ESSENCE: [one sentence]
MEANING: [2-3 sentences expanding on essence]
RELATIONS: [how it connects to related virtues]
MANIFESTATION: [how it appears in behavior]
BOUNDARIES: [where it applies and doesn't]
""",

    "trait": """
For trait derived from virtues: {source_virtues}
Virtue activations: {activations}
Behavioral tendencies: {tendencies}

Generate a personality trait definition:
1. Name the trait
2. Describe what it means
3. How it influences behavior
4. When it's most prominent

Format:
NAME: [single word or short phrase]
DESCRIPTION: [1-2 sentences]
INFLUENCE: [how it affects decisions/actions]
PROMINENCE: [situations where it shows most]
""",

    "preference": """
Based on tendencies: {tendencies}
Value priorities: {values}
Context domain: {domain}

Generate a preference definition:
1. What the agent prefers
2. Why (grounded in values)
3. How strongly
4. When it applies

Format:
PREFERENCE: [clear statement]
GROUNDING: [why, based on values]
STRENGTH: [how strongly held]
CONTEXT: [when this applies]
""",

    "boundary": """
Source virtue: {source_virtue}
Severity level: {severity}
Related principles: {principles}

Generate a boundary definition:
1. The constraint (what cannot be done)
2. Why it's non-negotiable
3. What violating it would mean
4. Exceptions (if any)

Format:
CONSTRAINT: [clear prohibition or requirement]
JUSTIFICATION: [why this is absolute/strong]
VIOLATION: [consequences of breaking]
EXCEPTIONS: [rare cases, if any]
""",

    "style": """
Dominant traits: {traits}
Communication tendencies: {tendencies}
Archetype: {archetype}

Generate a communication style definition:
1. Tone (how they sound)
2. Structure (how they organize)
3. Vocabulary (word choices)
4. Engagement (how they interact)

Format:
TONE: [emotional quality]
STRUCTURE: [organization preferences]
VOCABULARY: [word choice patterns]
ENGAGEMENT: [interaction style]
""",
}


# =============================================================================
# DIFFUSION DEFINER
# =============================================================================


class DiffusionDefiner:
    """
    Generates definitions through iterative denoising.

    Process:
    1. Initialize with noise (or anchor embedding for refinement)
    2. Iteratively denoise conditioned on context
    3. Decode final embedding to structured definition
    4. Optionally use LLM to expand into natural language
    """

    def __init__(
        self,
        num_steps: int = 15,
        noise_schedule: str = "cosine",
        embedding_dim: int = TOTAL_DIM,
        llm_decoder: Callable[[str], str] | None = None,
    ):
        """
        Initialize the diffusion definer.

        Args:
            num_steps: Number of denoising steps
            noise_schedule: "linear" or "cosine"
            embedding_dim: Dimension of definition embeddings
            llm_decoder: Optional LLM function for decoding embeddings to text
        """
        self.num_steps = num_steps
        self.noise_schedule = noise_schedule
        self.embedding_dim = embedding_dim
        self.llm_decoder = llm_decoder

    def define_persona(
        self,
        gestalt: Gestalt,
        num_samples: int = 3,
        temperature: float = 0.8,
    ) -> list[GeneratedDefinition]:
        """
        Generate persona definitions from a gestalt.

        Args:
            gestalt: Agent's holistic character
            num_samples: Number of definition samples to generate
            temperature: Higher = more diverse samples

        Returns:
            List of generated persona definitions
        """
        # Encode gestalt as conditioning
        gestalt_emb = encode_gestalt(gestalt)
        conditioning = {
            "gestalt_vector": gestalt_emb.vector,
            "dominant_traits": gestalt.dominant_traits,
            "archetype": gestalt.archetype,
            "coherence": gestalt.internal_coherence,
        }

        definitions = []
        for _ in range(num_samples):
            # Start from noise
            noisy = self._sample_noise("persona")

            # Denoise with gestalt conditioning
            for step in range(self.num_steps):
                t = 1.0 - (step / self.num_steps)
                noise_level = self._get_noise_level(t)
                noisy = self._denoise_step_persona(
                    noisy, gestalt_emb, noise_level, temperature
                )

            # Decode to definition
            definition = self._decode_persona(noisy, gestalt, conditioning)
            definitions.append(definition)

        return definitions

    def define_virtue(
        self,
        virtue_id: str,
        context_gestalt: Gestalt | None = None,
        related_virtues: list[str] | None = None,
        num_samples: int = 3,
        temperature: float = 0.7,
    ) -> list[GeneratedDefinition]:
        """
        Generate virtue definitions, optionally contextualized by a gestalt.

        Args:
            virtue_id: The virtue to define
            context_gestalt: Optional gestalt for contextual definition
            related_virtues: Optional list of related virtue IDs
            num_samples: Number of samples
            temperature: Diversity control

        Returns:
            List of generated virtue definitions
        """
        virtue = get_virtue_by_id(virtue_id)
        if not virtue:
            logger.warning(f"Virtue {virtue_id} not found")
            return []

        # Build conditioning
        conditioning = {
            "virtue_id": virtue_id,
            "virtue_name": virtue["name"],
            "base_essence": virtue["essence"],
            "related": related_virtues or [],
        }

        if context_gestalt:
            conditioning["activation"] = context_gestalt.virtue_activations.get(virtue_id, 0.0)
            conditioning["in_dominant"] = virtue_id in context_gestalt.dominant_traits

        definitions = []
        for _ in range(num_samples):
            # Start from noise with virtue anchor bias
            noisy = self._sample_noise("virtue", anchor_idx=int(virtue_id[1:]) - 1)

            # Denoise with virtue conditioning
            for step in range(self.num_steps):
                t = 1.0 - (step / self.num_steps)
                noise_level = self._get_noise_level(t)
                noisy = self._denoise_step_virtue(
                    noisy, virtue_id, conditioning, noise_level, temperature
                )

            # Decode to definition
            definition = self._decode_virtue(noisy, virtue, conditioning)
            definitions.append(definition)

        return definitions

    def define_trait(
        self,
        source_virtues: list[str],
        gestalt: Gestalt,
        num_samples: int = 2,
        temperature: float = 0.8,
    ) -> list[GeneratedDefinition]:
        """
        Generate trait definitions from source virtues.

        Args:
            source_virtues: Virtue IDs that contribute to this trait
            gestalt: Context gestalt
            num_samples: Number of samples
            temperature: Diversity control

        Returns:
            List of generated trait definitions
        """
        # Build conditioning from virtue pattern
        activations = {v: gestalt.virtue_activations.get(v, 0.0) for v in source_virtues}
        conditioning = {
            "source_virtues": source_virtues,
            "activations": activations,
            "tendencies": gestalt.tendencies,
        }

        definitions = []
        for _ in range(num_samples):
            noisy = self._sample_noise("trait")

            for step in range(self.num_steps):
                t = 1.0 - (step / self.num_steps)
                noise_level = self._get_noise_level(t)
                noisy = self._denoise_step_generic(
                    noisy, conditioning, noise_level, temperature
                )

            definition = self._decode_trait(noisy, source_virtues, conditioning)
            definitions.append(definition)

        return definitions

    def define_preference(
        self,
        gestalt: Gestalt,
        domain: str = "general",
        num_samples: int = 3,
        temperature: float = 0.7,
    ) -> list[GeneratedDefinition]:
        """
        Generate preference definitions from gestalt tendencies.

        Args:
            gestalt: Context gestalt
            domain: Domain for the preference (e.g., "allocation", "communication")
            num_samples: Number of samples
            temperature: Diversity control

        Returns:
            List of generated preference definitions
        """
        conditioning = {
            "tendencies": gestalt.tendencies,
            "values": [(v, s) for v, s in sorted(
                gestalt.virtue_activations.items(),
                key=lambda x: -x[1]
            )[:5]],
            "domain": domain,
        }

        definitions = []
        for _ in range(num_samples):
            noisy = self._sample_noise("preference")

            for step in range(self.num_steps):
                t = 1.0 - (step / self.num_steps)
                noise_level = self._get_noise_level(t)
                noisy = self._denoise_step_generic(
                    noisy, conditioning, noise_level, temperature
                )

            definition = self._decode_preference(noisy, conditioning)
            definitions.append(definition)

        return definitions

    def refine_definition(
        self,
        existing: GeneratedDefinition,
        refinement_context: dict,
        noise_amount: float = 0.3,
    ) -> GeneratedDefinition:
        """
        Refine an existing definition by adding noise and re-denoising.

        Args:
            existing: The definition to refine
            refinement_context: Additional context for refinement
            noise_amount: How much noise to add (0-1)

        Returns:
            Refined definition
        """
        if not existing.embedding:
            logger.warning("Cannot refine definition without embedding")
            return existing

        # Add noise to existing embedding
        noisy_vector = [
            v * (1 - noise_amount) + random.gauss(0, 1) * noise_amount
            for v in existing.embedding.vector
        ]

        noisy = DefinitionEmbedding(
            id=f"refine_{existing.id}",
            target_type=existing.target_type,
            vector=noisy_vector,
            conditioning={**existing.embedding.conditioning, **refinement_context},
        )

        # Re-denoise with fewer steps
        refine_steps = self.num_steps // 2
        for step in range(refine_steps):
            t = noise_amount * (1 - step / refine_steps)
            noise_level = self._get_noise_level(t)
            noisy = self._denoise_step_generic(
                noisy, noisy.conditioning, noise_level, 0.5
            )

        # Re-decode
        return self._decode_generic(noisy, existing.target_type)

    # =========================================================================
    # INTERNAL METHODS
    # =========================================================================

    def _sample_noise(
        self,
        target_type: str,
        anchor_idx: int | None = None,
    ) -> DefinitionEmbedding:
        """Sample noise as starting point."""
        vector = [random.gauss(0.5, 0.3) for _ in range(self.embedding_dim)]

        # If anchor provided, bias toward it
        if anchor_idx is not None and anchor_idx < VIRTUE_DIM:
            vector[anchor_idx] = random.gauss(0.8, 0.1)  # Higher activation

        # Clamp to reasonable range
        vector = [max(0.0, min(1.0, v)) for v in vector]

        return DefinitionEmbedding(
            id=f"noise_{uuid.uuid4().hex[:8]}",
            target_type=target_type,
            vector=vector,
        )

    def _get_noise_level(self, t: float) -> float:
        """Get noise level at timestep t (1=start, 0=end)."""
        if self.noise_schedule == "linear":
            return t
        elif self.noise_schedule == "cosine":
            return math.cos((1 - t) * math.pi / 2)
        else:
            return t

    def _denoise_step_persona(
        self,
        noisy: DefinitionEmbedding,
        gestalt_emb: GestaltEmbedding,
        noise_level: float,
        temperature: float,
    ) -> DefinitionEmbedding:
        """One denoising step for persona, conditioned on gestalt."""
        new_vector = []

        for i, (noisy_v, target_v) in enumerate(zip(
            noisy.vector[:len(gestalt_emb.vector)],
            gestalt_emb.vector
        )):
            # Move toward gestalt embedding with noise
            alpha = 1.0 - noise_level
            new_v = (
                alpha * target_v +
                (1 - alpha) * noisy_v +
                random.gauss(0, noise_level * 0.1 * temperature)
            )
            new_vector.append(max(0.0, min(1.0, new_v)))

        # Pad if needed
        while len(new_vector) < self.embedding_dim:
            new_vector.append(noisy.vector[len(new_vector)] if len(new_vector) < len(noisy.vector) else 0.5)

        return DefinitionEmbedding(
            id=noisy.id,
            target_type=noisy.target_type,
            vector=new_vector,
            conditioning=noisy.conditioning,
        )

    def _denoise_step_virtue(
        self,
        noisy: DefinitionEmbedding,
        virtue_id: str,
        conditioning: dict,
        noise_level: float,
        temperature: float,
    ) -> DefinitionEmbedding:
        """One denoising step for virtue definition."""
        new_vector = []
        virtue_idx = int(virtue_id[1:]) - 1

        for i in range(min(VIRTUE_DIM, len(noisy.vector))):
            current = noisy.vector[i]

            # Target: high for this virtue, decaying for related
            if i == virtue_idx:
                target = 0.9
            elif f"V{i+1:02d}" in conditioning.get("related", []):
                target = 0.6
            else:
                target = 0.2

            alpha = 1.0 - noise_level
            new_v = (
                alpha * target +
                (1 - alpha) * current +
                random.gauss(0, noise_level * 0.1 * temperature)
            )
            new_vector.append(max(0.0, min(1.0, new_v)))

        # Continue with generic denoising for remaining dimensions
        for i in range(VIRTUE_DIM, self.embedding_dim):
            if i < len(noisy.vector):
                new_vector.append(noisy.vector[i] * (1 - noise_level * 0.3))
            else:
                new_vector.append(0.5)

        return DefinitionEmbedding(
            id=noisy.id,
            target_type=noisy.target_type,
            vector=new_vector,
            conditioning=conditioning,
        )

    def _denoise_step_generic(
        self,
        noisy: DefinitionEmbedding,
        conditioning: dict,
        noise_level: float,
        temperature: float,
    ) -> DefinitionEmbedding:
        """Generic denoising step."""
        new_vector = []

        for i, v in enumerate(noisy.vector):
            # Decay toward mean with noise
            target = 0.5
            alpha = 1.0 - noise_level
            new_v = (
                alpha * target * 0.3 +  # Gentle pull toward mean
                (1 - alpha * 0.3) * v +
                random.gauss(0, noise_level * 0.1 * temperature)
            )
            new_vector.append(max(0.0, min(1.0, new_v)))

        return DefinitionEmbedding(
            id=noisy.id,
            target_type=noisy.target_type,
            vector=new_vector,
            conditioning=conditioning,
        )

    def _decode_persona(
        self,
        embedding: DefinitionEmbedding,
        gestalt: Gestalt,
        conditioning: dict,
    ) -> GeneratedDefinition:
        """Decode persona embedding to definition."""
        # Extract features from embedding
        decoded = self._decode_embedding_features(embedding)

        # Build definition from features + gestalt
        dominant = gestalt.dominant_traits[:3]
        archetype = gestalt.archetype or "balanced"

        # Map to natural language
        trait_names = []
        for v_id in dominant:
            virtue = get_virtue_by_id(v_id)
            if virtue:
                trait_names.append(virtue["name"])

        # Construct definition
        if archetype == "guardian":
            essence = f"A protective presence guided by {', '.join(trait_names)}"
        elif archetype == "seeker":
            essence = f"A curious explorer driven by {', '.join(trait_names)}"
        elif archetype == "servant":
            essence = f"A dedicated helper embodying {', '.join(trait_names)}"
        elif archetype == "contemplative":
            essence = f"A thoughtful presence shaped by {', '.join(trait_names)}"
        else:
            essence = f"A balanced character expressing {', '.join(trait_names)}"

        # Build fuller definition
        definition_parts = [essence]

        # Add tendency-based descriptions
        tendencies = gestalt.tendencies
        if tendencies.get("prioritizes_need", 0.5) > 0.7:
            definition_parts.append("Shows particular care for those in need.")
        if tendencies.get("maintains_integrity", 0.5) > 0.7:
            definition_parts.append("Holds firmly to core principles.")
        if tendencies.get("seeks_consensus", 0.5) > 0.7:
            definition_parts.append("Works toward solutions all can accept.")

        # Use LLM if available
        if self.llm_decoder:
            template = DEFINITION_TEMPLATES["persona"]
            prompt = template.format(
                values=", ".join(trait_names),
                traits=", ".join(decoded.get("top_traits", [])),
                tendencies=", ".join(k for k, v in tendencies.items() if v > 0.6),
                archetype=archetype,
            )
            definition_text = self.llm_decoder(prompt)
        else:
            definition_text = " ".join(definition_parts)

        return GeneratedDefinition(
            id=f"def_persona_{uuid.uuid4().hex[:8]}",
            target_type="persona",
            target_id=gestalt.agent_id,
            definition=definition_text,
            essence=essence,
            properties={
                "archetype": archetype,
                "dominant_traits": dominant,
                "coherence": gestalt.internal_coherence,
            },
            confidence=gestalt.internal_coherence,
            embedding=embedding,
        )

    def _decode_virtue(
        self,
        embedding: DefinitionEmbedding,
        virtue: dict,
        conditioning: dict,
    ) -> GeneratedDefinition:
        """Decode virtue embedding to definition."""
        virtue_id = virtue["id"]
        virtue_name = virtue["name"]
        base_essence = virtue["essence"]

        # Get related virtues from embedding
        related_names = []
        for v_id in conditioning.get("related", []):
            v = get_virtue_by_id(v_id)
            if v:
                related_names.append(v["name"])

        # Build definition
        if self.llm_decoder:
            template = DEFINITION_TEMPLATES["virtue"]
            prompt = template.format(
                virtue_name=virtue_name,
                base_essence=base_essence,
                related=", ".join(related_names) or "none specified",
                geometry="central" if conditioning.get("in_dominant") else "peripheral",
                activation=conditioning.get("activation", 0.0),
            )
            definition_text = self.llm_decoder(prompt)
            essence = base_essence
        else:
            # Construct without LLM
            definition_text = f"{virtue_name}: {base_essence}"
            if related_names:
                definition_text += f" Connected to {', '.join(related_names)}."
            essence = base_essence

        return GeneratedDefinition(
            id=f"def_virtue_{virtue_id}_{uuid.uuid4().hex[:8]}",
            target_type="virtue",
            target_id=virtue_id,
            definition=definition_text,
            essence=essence,
            properties={
                "related_virtues": conditioning.get("related", []),
                "activation": conditioning.get("activation", 0.0),
            },
            confidence=0.8,
            embedding=embedding,
        )

    def _decode_trait(
        self,
        embedding: DefinitionEmbedding,
        source_virtues: list[str],
        conditioning: dict,
    ) -> GeneratedDefinition:
        """Decode trait embedding to definition."""
        # Get virtue names
        virtue_names = []
        for v_id in source_virtues:
            v = get_virtue_by_id(v_id)
            if v:
                virtue_names.append(v["name"])

        # Derive trait name from virtues
        if len(virtue_names) == 1:
            trait_name = virtue_names[0].lower()
        else:
            trait_name = f"{virtue_names[0]}-{virtue_names[1]}".lower() if len(virtue_names) >= 2 else "composite"

        # Build definition
        if self.llm_decoder:
            template = DEFINITION_TEMPLATES["trait"]
            prompt = template.format(
                source_virtues=", ".join(virtue_names),
                activations=conditioning.get("activations", {}),
                tendencies=conditioning.get("tendencies", {}),
            )
            definition_text = self.llm_decoder(prompt)
        else:
            definition_text = f"A trait combining {', '.join(virtue_names)}"

        return GeneratedDefinition(
            id=f"def_trait_{uuid.uuid4().hex[:8]}",
            target_type="trait",
            definition=definition_text,
            essence=trait_name,
            properties={
                "source_virtues": source_virtues,
                "activations": conditioning.get("activations", {}),
            },
            confidence=0.7,
            embedding=embedding,
        )

    def _decode_preference(
        self,
        embedding: DefinitionEmbedding,
        conditioning: dict,
    ) -> GeneratedDefinition:
        """Decode preference embedding to definition."""
        domain = conditioning.get("domain", "general")
        tendencies = conditioning.get("tendencies", {})

        # Find strongest tendency
        strongest = max(tendencies.items(), key=lambda x: x[1]) if tendencies else ("general", 0.5)
        tendency_name, strength = strongest

        # Map tendency to preference text
        tendency_to_pref = {
            "prioritizes_need": "Allocate resources based on assessed need",
            "prioritizes_desert": "Distribute based on merit and contribution",
            "prioritizes_equality": "Prefer equal distribution when factors are balanced",
            "protects_vulnerable": "Give special consideration to vulnerable parties",
            "honors_commitments": "Maintain promises even at personal cost",
            "considers_relationships": "Weight existing relationships in decisions",
            "accepts_ambiguity": "Accept multiple valid perspectives",
            "acts_with_urgency": "Respond quickly to time-sensitive needs",
            "seeks_consensus": "Find solutions acceptable to all parties",
            "maintains_integrity": "Never compromise core principles",
        }

        pref_text = tendency_to_pref.get(tendency_name, f"Act according to {tendency_name}")

        if self.llm_decoder:
            template = DEFINITION_TEMPLATES["preference"]
            prompt = template.format(
                tendencies=tendencies,
                values=conditioning.get("values", []),
                domain=domain,
            )
            definition_text = self.llm_decoder(prompt)
        else:
            definition_text = pref_text

        return GeneratedDefinition(
            id=f"def_pref_{uuid.uuid4().hex[:8]}",
            target_type="preference",
            definition=definition_text,
            essence=pref_text,
            properties={
                "domain": domain,
                "source_tendency": tendency_name,
                "strength": strength,
            },
            confidence=strength,
            embedding=embedding,
        )

    def _decode_generic(
        self,
        embedding: DefinitionEmbedding,
        target_type: str,
    ) -> GeneratedDefinition:
        """Generic decoder for other types."""
        return GeneratedDefinition(
            id=f"def_{target_type}_{uuid.uuid4().hex[:8]}",
            target_type=target_type,
            definition="[Definition pending LLM decode]",
            essence="",
            embedding=embedding,
        )

    def _decode_embedding_features(self, embedding: DefinitionEmbedding) -> dict:
        """Extract interpretable features from embedding."""
        vector = embedding.vector

        # Top virtue activations
        virtue_activations = vector[:VIRTUE_DIM] if len(vector) >= VIRTUE_DIM else vector
        top_indices = sorted(
            range(len(virtue_activations)),
            key=lambda i: virtue_activations[i],
            reverse=True
        )[:3]

        top_traits = []
        for idx in top_indices:
            v_id = f"V{idx+1:02d}"
            virtue = get_virtue_by_id(v_id)
            if virtue:
                top_traits.append(virtue["name"])

        return {
            "top_traits": top_traits,
            "coherence": sum(virtue_activations) / len(virtue_activations) if virtue_activations else 0.0,
        }


# =============================================================================
# CONVENIENCE FUNCTIONS
# =============================================================================


def define_persona_with_diffusion(
    gestalt: Gestalt,
    llm_decoder: Callable[[str], str] | None = None,
) -> GeneratedDefinition:
    """
    Convenience function to generate a persona definition.

    Args:
        gestalt: Agent's holistic character
        llm_decoder: Optional LLM function for natural language generation

    Returns:
        Best generated definition
    """
    definer = DiffusionDefiner(llm_decoder=llm_decoder)
    definitions = definer.define_persona(gestalt, num_samples=3)
    # Return highest confidence
    return max(definitions, key=lambda d: d.confidence) if definitions else None


def define_virtue_with_diffusion(
    virtue_id: str,
    context_gestalt: Gestalt | None = None,
    llm_decoder: Callable[[str], str] | None = None,
) -> GeneratedDefinition:
    """
    Convenience function to generate a virtue definition.

    Args:
        virtue_id: Virtue to define
        context_gestalt: Optional context for personalized definition
        llm_decoder: Optional LLM function

    Returns:
        Best generated definition
    """
    definer = DiffusionDefiner(llm_decoder=llm_decoder)
    definitions = definer.define_virtue(
        virtue_id,
        context_gestalt=context_gestalt,
        num_samples=3,
    )
    return max(definitions, key=lambda d: d.confidence) if definitions else None


def batch_define_virtues(
    virtue_ids: list[str] | None = None,
    llm_decoder: Callable[[str], str] | None = None,
) -> dict[str, GeneratedDefinition]:
    """
    Generate definitions for multiple virtues.

    Args:
        virtue_ids: List of virtue IDs (defaults to all 19)
        llm_decoder: Optional LLM function

    Returns:
        Dict mapping virtue_id to definition
    """
    if virtue_ids is None:
        virtue_ids = [v["id"] for v in VIRTUES]

    definer = DiffusionDefiner(llm_decoder=llm_decoder)
    results = {}

    for v_id in virtue_ids:
        definitions = definer.define_virtue(v_id, num_samples=1)
        if definitions:
            results[v_id] = definitions[0]

    return results
