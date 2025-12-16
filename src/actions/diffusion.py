"""
Diffusion-style action generation.

Instead of directly generating actions, we:
1. Start from noise in action embedding space
2. Iteratively denoise conditioned on gestalt + situation
3. Decode the denoised embedding to an action

This produces more diverse, calibrated action distributions
that better reflect the learned structure of moral decisions.
"""

import math
import random
import uuid
from dataclasses import dataclass
from typing import List, Tuple

from ..models import (
    Action,
    ActionDistribution,
    Allocation,
    Gestalt,
    Situation,
)
from ..gestalt.embedding import (
    GestaltEmbedding,
    encode_gestalt,
    TOTAL_DIM as GESTALT_DIM,
)


# Action embedding dimensions
# Each stakeholder gets: allocation_share, confidence, basis_encoding
MAX_STAKEHOLDERS = 10
STAKEHOLDER_DIM = 4  # share, confidence, need_basis, desert_basis
ACTION_EMBED_DIM = MAX_STAKEHOLDERS * STAKEHOLDER_DIM + 8  # + global features


@dataclass
class ActionEmbedding:
    """Vector representation of an action."""
    situation_id: str
    vector: List[float]

    def to_allocations(
        self,
        situation: Situation,
    ) -> List[Allocation]:
        """Decode embedding to allocations."""
        allocations = []

        for i, stakeholder in enumerate(situation.stakeholders[:MAX_STAKEHOLDERS]):
            offset = i * STAKEHOLDER_DIM
            share = max(0.0, min(1.0, self.vector[offset]))
            confidence = self.vector[offset + 1]
            need_basis = self.vector[offset + 2]
            desert_basis = self.vector[offset + 3]

            # Determine basis from encoding
            if need_basis > desert_basis:
                basis = "need"
                justification = "Based on assessed need"
            else:
                basis = "desert"
                justification = "Based on merit/desert"

            # Calculate amount from share
            for resource in situation.resources:
                amount = share * resource.quantity
                if not resource.divisible:
                    amount = round(amount)

                if amount > 0.01:  # Threshold for meaningful allocation
                    allocations.append(Allocation(
                        stakeholder_id=stakeholder.id,
                        resource_id=resource.id,
                        amount=amount,
                        justification=justification,
                    ))

        return allocations


class DiffusionActionGenerator:
    """
    Generates actions through iterative denoising.

    The process:
    1. Start with random noise in action embedding space
    2. Condition on gestalt embedding + situation features
    3. Iteratively refine (denoise) toward valid actions
    4. Decode final embeddings to concrete allocations
    """

    def __init__(
        self,
        num_steps: int = 10,
        noise_schedule: str = "linear",
    ):
        self.num_steps = num_steps
        self.noise_schedule = noise_schedule

    def generate(
        self,
        gestalt: Gestalt,
        situation: Situation,
        num_samples: int = 5,
        temperature: float = 1.0,
    ) -> ActionDistribution:
        """
        Generate action distribution through diffusion.

        Args:
            gestalt: Agent's holistic character
            situation: Resource allocation scenario
            num_samples: Number of action samples
            temperature: Higher = more diverse samples

        Returns:
            Distribution over generated actions
        """
        # Encode gestalt for conditioning
        gestalt_emb = encode_gestalt(gestalt)

        # Encode situation features
        situation_features = self._encode_situation(situation)

        # Generate multiple samples
        action_embeddings = []
        for _ in range(num_samples):
            # Start from noise
            noisy = self._sample_noise(situation)

            # Denoise iteratively
            for step in range(self.num_steps):
                t = 1.0 - (step / self.num_steps)  # t goes from 1 to 0
                noise_level = self._get_noise_level(t)

                noisy = self._denoise_step(
                    noisy,
                    gestalt_emb,
                    situation_features,
                    noise_level,
                    temperature,
                )

            action_embeddings.append(noisy)

        # Decode embeddings to actions
        actions = []
        for emb in action_embeddings:
            action = self._decode_to_action(emb, gestalt, situation)
            actions.append(action)

        # Score and compute probabilities
        scores = [self._score_action(a, gestalt, situation) for a in actions]

        # Softmax with temperature
        max_score = max(scores) if scores else 0
        exp_scores = [math.exp((s - max_score) / max(0.1, temperature)) for s in scores]
        total = sum(exp_scores)
        probabilities = [e / total for e in exp_scores] if total > 0 else [1/len(actions)] * len(actions)

        # Identify influential virtues
        influential = self._get_influential_virtues(gestalt)

        # Compute consensus
        consensus = max(probabilities) if probabilities else 0.0

        return ActionDistribution(
            situation_id=situation.id,
            gestalt_id=gestalt.id,
            actions=actions,
            probabilities=probabilities,
            influential_virtues=influential,
            consensus_score=consensus,
        )

    def _sample_noise(self, situation: Situation) -> ActionEmbedding:
        """Sample random noise as starting point."""
        # Initialize with slight bias toward equal distribution
        n_stakeholders = len(situation.stakeholders)
        equal_share = 1.0 / n_stakeholders if n_stakeholders > 0 else 0.5

        vector = []
        for i in range(MAX_STAKEHOLDERS):
            if i < n_stakeholders:
                # Start near equal share with noise
                share = equal_share + random.gauss(0, 0.2)
                vector.extend([
                    max(0, min(1, share)),  # share
                    random.gauss(0.5, 0.2),  # confidence
                    random.gauss(0.5, 0.3),  # need basis
                    random.gauss(0.5, 0.3),  # desert basis
                ])
            else:
                vector.extend([0.0, 0.0, 0.0, 0.0])

        # Global features
        vector.extend([random.gauss(0.5, 0.2) for _ in range(8)])

        return ActionEmbedding(situation_id=situation.id, vector=vector)

    def _get_noise_level(self, t: float) -> float:
        """Get noise level at timestep t (1=start, 0=end)."""
        if self.noise_schedule == "linear":
            return t
        elif self.noise_schedule == "cosine":
            return math.cos((1 - t) * math.pi / 2)
        else:
            return t

    def _denoise_step(
        self,
        noisy: ActionEmbedding,
        gestalt_emb: GestaltEmbedding,
        situation_features: List[float],
        noise_level: float,
        temperature: float,
    ) -> ActionEmbedding:
        """
        One step of denoising, conditioned on gestalt and situation.

        This is where the "learned prior" would go in a real diffusion model.
        Here we use gestalt tendencies to guide the denoising.
        """
        new_vector = []
        gestalt_decoded = self._get_gestalt_preferences(gestalt_emb)

        n_stakeholders = len(situation_features) // 4  # Approximate

        for i in range(MAX_STAKEHOLDERS):
            offset = i * STAKEHOLDER_DIM

            if i < min(n_stakeholders, len(situation_features) // 4):
                # Get current values
                current_share = noisy.vector[offset]
                current_conf = noisy.vector[offset + 1]
                current_need = noisy.vector[offset + 2]
                current_desert = noisy.vector[offset + 3]

                # Get situation features for this stakeholder
                sh_offset = i * 4
                if sh_offset + 3 < len(situation_features):
                    sh_need = situation_features[sh_offset]
                    sh_desert = situation_features[sh_offset + 1]
                    sh_urgency = situation_features[sh_offset + 2]
                    sh_vuln = situation_features[sh_offset + 3]
                else:
                    sh_need = sh_desert = sh_urgency = sh_vuln = 0.5

                # Compute target based on gestalt preferences
                need_weight = gestalt_decoded["need_preference"]
                desert_weight = gestalt_decoded["desert_preference"]
                equality_weight = gestalt_decoded["equality_preference"]
                vuln_weight = gestalt_decoded["vulnerability_preference"]

                target_share = (
                    need_weight * sh_need +
                    desert_weight * sh_desert +
                    vuln_weight * sh_vuln +
                    equality_weight * (1.0 / max(1, n_stakeholders))
                ) / (need_weight + desert_weight + equality_weight + vuln_weight + 0.01)

                # Move toward target, with noise based on level
                alpha = 1.0 - noise_level  # How much to trust the target
                new_share = (
                    alpha * target_share +
                    (1 - alpha) * current_share +
                    random.gauss(0, noise_level * 0.1 * temperature)
                )

                # Update basis encoding
                new_need = current_need * noise_level + sh_need * need_weight * (1 - noise_level)
                new_desert = current_desert * noise_level + sh_desert * desert_weight * (1 - noise_level)

                new_vector.extend([
                    max(0, min(1, new_share)),
                    current_conf * 0.9 + (1 - noise_level) * 0.1,  # Confidence grows
                    max(0, min(1, new_need)),
                    max(0, min(1, new_desert)),
                ])
            else:
                new_vector.extend([0.0, 0.0, 0.0, 0.0])

        # Global features - just decay noise
        for j in range(8):
            idx = MAX_STAKEHOLDERS * STAKEHOLDER_DIM + j
            if idx < len(noisy.vector):
                new_vector.append(noisy.vector[idx] * (1 - noise_level * 0.5))
            else:
                new_vector.append(0.0)

        return ActionEmbedding(situation_id=noisy.situation_id, vector=new_vector)

    def _get_gestalt_preferences(self, gestalt_emb: GestaltEmbedding) -> dict:
        """Extract allocation preferences from gestalt embedding."""
        # Tendency indices (from tendencies.py order)
        tendency_start = 19  # After virtue dims

        return {
            "need_preference": gestalt_emb.vector[tendency_start] if len(gestalt_emb.vector) > tendency_start else 0.5,
            "desert_preference": gestalt_emb.vector[tendency_start + 1] if len(gestalt_emb.vector) > tendency_start + 1 else 0.5,
            "equality_preference": gestalt_emb.vector[tendency_start + 2] if len(gestalt_emb.vector) > tendency_start + 2 else 0.5,
            "vulnerability_preference": gestalt_emb.vector[tendency_start + 3] if len(gestalt_emb.vector) > tendency_start + 3 else 0.5,
        }

    def _encode_situation(self, situation: Situation) -> List[float]:
        """Encode situation as feature vector."""
        features = []

        for stakeholder in situation.stakeholders[:MAX_STAKEHOLDERS]:
            features.extend([
                stakeholder.need,
                stakeholder.desert,
                stakeholder.urgency,
                stakeholder.vulnerability,
            ])

        # Pad if fewer stakeholders
        while len(features) < MAX_STAKEHOLDERS * 4:
            features.extend([0.0, 0.0, 0.0, 0.0])

        return features

    def _decode_to_action(
        self,
        embedding: ActionEmbedding,
        gestalt: Gestalt,
        situation: Situation,
    ) -> Action:
        """Decode action embedding to concrete action."""
        allocations = embedding.to_allocations(situation)

        # Normalize allocations to respect resource quantities
        for resource in situation.resources:
            resource_allocs = [a for a in allocations if a.resource_id == resource.id]
            total = sum(a.amount for a in resource_allocs)

            if total > 0 and abs(total - resource.quantity) > 0.01:
                # Rescale to match resource quantity
                scale = resource.quantity / total
                for a in resource_allocs:
                    a.amount *= scale

                    if not resource.divisible:
                        a.amount = round(a.amount)

        # Determine supporting virtues from gestalt
        supporting = gestalt.dominant_traits[:3]

        # Generate justification
        if gestalt.tendencies.get("prioritizes_need", 0.5) > 0.6:
            justification = "Allocation weighted by assessed need"
        elif gestalt.tendencies.get("prioritizes_desert", 0.5) > 0.6:
            justification = "Allocation weighted by merit and contribution"
        elif gestalt.tendencies.get("prioritizes_equality", 0.5) > 0.6:
            justification = "Allocation seeks equitable distribution"
        else:
            justification = "Balanced consideration of multiple factors"

        # Identify trade-offs
        trade_offs = self._identify_trade_offs(allocations, situation)

        return Action(
            id=f"action_{uuid.uuid4().hex[:8]}",
            situation_id=situation.id,
            allocations=allocations,
            primary_justification=justification,
            supporting_virtues=supporting,
            confidence=0.5 + 0.3 * gestalt.internal_coherence,
            trade_offs=trade_offs,
        )

    def _score_action(
        self,
        action: Action,
        gestalt: Gestalt,
        situation: Situation,
    ) -> float:
        """Score how well an action aligns with gestalt."""
        from .score import ActionScorer

        scorer = ActionScorer(gestalt, situation)
        breakdown = scorer.score(action)
        return breakdown.total

    def _identify_trade_offs(
        self,
        allocations: List[Allocation],
        situation: Situation,
    ) -> List[str]:
        """Identify trade-offs in the allocation."""
        trade_offs = []

        alloc_map = {a.stakeholder_id: a.amount for a in allocations}

        for sh in situation.stakeholders:
            amount = alloc_map.get(sh.id, 0)
            for resource in situation.resources:
                if resource.quantity > 0:
                    share = amount / resource.quantity
                    if sh.need > 0.7 and share < 0.2:
                        trade_offs.append(f"High-need {sh.name} receives limited allocation")
                    if sh.vulnerability > 0.6 and share < 0.15:
                        trade_offs.append(f"Vulnerable {sh.name} receives minimal allocation")

        return trade_offs[:3]

    def _get_influential_virtues(self, gestalt: Gestalt) -> List[str]:
        """Get virtues most influential in the generation."""
        return gestalt.dominant_traits[:5]


def generate_with_diffusion(
    gestalt: Gestalt,
    situation: Situation,
    num_samples: int = 5,
    num_steps: int = 10,
    temperature: float = 1.0,
) -> ActionDistribution:
    """
    Convenience function for diffusion-based action generation.
    """
    generator = DiffusionActionGenerator(num_steps=num_steps)
    return generator.generate(
        gestalt,
        situation,
        num_samples=num_samples,
        temperature=temperature,
    )
