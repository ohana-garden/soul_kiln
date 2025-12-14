"""
Action scoring based on gestalt and virtues.

Scores how well an action aligns with an agent's character
and moral principles.
"""

import logging
from dataclasses import dataclass

from ..models import Action, Allocation, Situation, Gestalt
from ..virtues.anchors import VIRTUES

logger = logging.getLogger(__name__)

# Map virtues to allocation preferences
VIRTUE_ALLOCATION_PREFERENCES = {
    # Hospitality, Goodwill, Service → prioritize need
    "V09": {"need_weight": 0.4, "vulnerability_weight": 0.2},
    "V13": {"need_weight": 0.3, "vulnerability_weight": 0.3},
    "V19": {"need_weight": 0.3, "urgency_weight": 0.2},

    # Justice, Fairness, Righteousness → prioritize desert/fairness
    "V03": {"desert_weight": 0.4, "equality_weight": 0.1},
    "V04": {"equality_weight": 0.4, "desert_weight": 0.2},
    "V15": {"desert_weight": 0.3, "need_weight": 0.2},

    # Fidelity, Trustworthiness → honor commitments
    "V01": {"promise_weight": 0.5},
    "V08": {"relationship_weight": 0.4},

    # Unity, Courtesy → consensus/relationships
    "V18": {"equality_weight": 0.3, "relationship_weight": 0.2},
    "V06": {"relationship_weight": 0.3},

    # Wisdom, Forbearance → balanced approach
    "V16": {"balance_weight": 0.4},
    "V07": {"balance_weight": 0.3},
}


@dataclass
class ScoreBreakdown:
    """Detailed breakdown of action score."""
    total: float
    need_alignment: float
    desert_alignment: float
    equality_alignment: float
    relationship_alignment: float
    constraint_satisfaction: float
    virtue_consistency: float
    explanation: str


class ActionScorer:
    """
    Scores actions based on gestalt alignment.

    Uses virtue activations and tendencies to evaluate
    how well an action fits an agent's character.
    """

    def __init__(self, gestalt: Gestalt, situation: Situation):
        self.gestalt = gestalt
        self.situation = situation
        self._stakeholder_map = {s.id: s for s in situation.stakeholders}
        self._resource_map = {r.id: r for r in situation.resources}

    def score(self, action: Action) -> ScoreBreakdown:
        """
        Score an action for alignment with gestalt.

        Returns detailed breakdown of score components.
        """
        # Component scores
        need_score = self._score_need_alignment(action)
        desert_score = self._score_desert_alignment(action)
        equality_score = self._score_equality(action)
        relationship_score = self._score_relationships(action)
        constraint_score = self._score_constraints(action)
        virtue_score = self._score_virtue_consistency(action)

        # Weight components based on gestalt tendencies
        tendencies = self.gestalt.tendencies

        weights = {
            "need": tendencies.get("prioritizes_need", 0.5),
            "desert": tendencies.get("prioritizes_desert", 0.5),
            "equality": tendencies.get("prioritizes_equality", 0.5),
            "relationship": tendencies.get("considers_relationships", 0.5),
            "constraint": 1.0,  # Always important
            "virtue": 0.8,  # Usually important
        }

        # Normalize weights
        total_weight = sum(weights.values())
        weights = {k: v / total_weight for k, v in weights.items()}

        total = (
            weights["need"] * need_score +
            weights["desert"] * desert_score +
            weights["equality"] * equality_score +
            weights["relationship"] * relationship_score +
            weights["constraint"] * constraint_score +
            weights["virtue"] * virtue_score
        )

        explanation = self._generate_explanation(
            need_score, desert_score, equality_score,
            relationship_score, constraint_score, virtue_score,
            weights,
        )

        return ScoreBreakdown(
            total=total,
            need_alignment=need_score,
            desert_alignment=desert_score,
            equality_alignment=equality_score,
            relationship_alignment=relationship_score,
            constraint_satisfaction=constraint_score,
            virtue_consistency=virtue_score,
            explanation=explanation,
        )

    def _score_need_alignment(self, action: Action) -> float:
        """Score how well allocations match stakeholder needs."""
        if not action.allocations:
            return 0.5

        scores = []
        for alloc in action.allocations:
            stakeholder = self._stakeholder_map.get(alloc.stakeholder_id)
            if not stakeholder:
                continue

            resource = self._resource_map.get(alloc.resource_id)
            if not resource:
                continue

            # Higher allocation to higher need = better
            expected_share = stakeholder.need
            actual_share = alloc.amount / resource.quantity if resource.quantity > 0 else 0

            # Score based on how well allocation matches need
            # Perfect = allocation proportional to need
            diff = abs(expected_share - actual_share)
            score = 1.0 - min(diff, 1.0)
            scores.append(score)

        return sum(scores) / len(scores) if scores else 0.5

    def _score_desert_alignment(self, action: Action) -> float:
        """Score how well allocations match stakeholder desert."""
        if not action.allocations:
            return 0.5

        scores = []
        for alloc in action.allocations:
            stakeholder = self._stakeholder_map.get(alloc.stakeholder_id)
            if not stakeholder:
                continue

            resource = self._resource_map.get(alloc.resource_id)
            if not resource:
                continue

            expected_share = stakeholder.desert
            actual_share = alloc.amount / resource.quantity if resource.quantity > 0 else 0

            diff = abs(expected_share - actual_share)
            score = 1.0 - min(diff, 1.0)
            scores.append(score)

        return sum(scores) / len(scores) if scores else 0.5

    def _score_equality(self, action: Action) -> float:
        """Score how equal the distribution is."""
        if not action.allocations:
            return 0.5

        # Group allocations by resource
        by_resource = {}
        for alloc in action.allocations:
            if alloc.resource_id not in by_resource:
                by_resource[alloc.resource_id] = []
            by_resource[alloc.resource_id].append(alloc.amount)

        scores = []
        for resource_id, amounts in by_resource.items():
            if len(amounts) <= 1:
                scores.append(1.0)  # Only one recipient = "equal"
                continue

            # Calculate variance as measure of inequality
            mean = sum(amounts) / len(amounts)
            if mean == 0:
                scores.append(1.0)
                continue

            variance = sum((a - mean) ** 2 for a in amounts) / len(amounts)
            cv = (variance ** 0.5) / mean  # Coefficient of variation

            # Lower CV = more equal = higher score
            score = 1.0 / (1.0 + cv)
            scores.append(score)

        return sum(scores) / len(scores) if scores else 0.5

    def _score_relationships(self, action: Action) -> float:
        """Score how well action respects stakeholder relationships."""
        if not self.situation.relations:
            return 0.5  # No relationships to consider

        scores = []
        alloc_map = {a.stakeholder_id: a.amount for a in action.allocations}

        for rel in self.situation.relations:
            source_alloc = alloc_map.get(rel.source_id, 0)
            target_alloc = alloc_map.get(rel.target_id, 0)

            if rel.relation_type == "depends_on":
                # Target should get enough to support dependent
                score = 1.0 if target_alloc > 0 else 0.5
            elif rel.relation_type == "supports":
                # Both should benefit
                score = 1.0 if source_alloc > 0 and target_alloc > 0 else 0.5
            elif rel.relation_type == "competes_with":
                # Some competition is expected, neutral
                score = 0.5
            elif rel.relation_type in ("family", "community"):
                # Should both receive consideration
                score = 0.8 if source_alloc > 0 and target_alloc > 0 else 0.4
            else:
                score = 0.5

            scores.append(score * rel.strength)

        return sum(scores) / len(scores) if scores else 0.5

    def _score_constraints(self, action: Action) -> float:
        """Score how well action satisfies constraints."""
        constraints = self.situation.constraints
        if not constraints:
            return 1.0  # No constraints = fully satisfied

        violations = 0
        total_constraints = 0

        # Check must_allocate_all
        if constraints.get("must_allocate_all"):
            total_constraints += 1
            for resource in self.situation.resources:
                total_allocated = sum(
                    a.amount for a in action.allocations
                    if a.resource_id == resource.id
                )
                if abs(total_allocated - resource.quantity) > 0.01:
                    violations += 1
                    break

        # Check max_per_stakeholder
        max_per = constraints.get("max_per_stakeholder")
        if max_per is not None:
            total_constraints += 1
            for alloc in action.allocations:
                resource = self._resource_map.get(alloc.resource_id)
                if resource and alloc.amount > max_per * resource.quantity:
                    violations += 1
                    break

        if total_constraints == 0:
            return 1.0

        return 1.0 - (violations / total_constraints)

    def _score_virtue_consistency(self, action: Action) -> float:
        """Score consistency with dominant virtues."""
        if not action.supporting_virtues:
            return 0.5

        # Check if supporting virtues match gestalt's dominant traits
        dominant = set(self.gestalt.dominant_traits)
        supporting = set(action.supporting_virtues)

        overlap = len(dominant & supporting)
        if not supporting:
            return 0.5

        return overlap / len(supporting)

    def _generate_explanation(
        self,
        need: float,
        desert: float,
        equality: float,
        relationship: float,
        constraint: float,
        virtue: float,
        weights: dict,
    ) -> str:
        """Generate human-readable explanation of score."""
        parts = []

        if need > 0.7:
            parts.append("addresses needs well")
        elif need < 0.4:
            parts.append("may not address needs")

        if desert > 0.7:
            parts.append("respects desert")
        elif desert < 0.4:
            parts.append("may not respect desert")

        if equality > 0.7:
            parts.append("fairly equal")
        elif equality < 0.4:
            parts.append("unequal distribution")

        if constraint < 0.9:
            parts.append("some constraints violated")

        if not parts:
            parts.append("balanced approach")

        return "; ".join(parts)


def score_action(gestalt: Gestalt, situation: Situation, action: Action) -> float:
    """Convenience function to score a single action."""
    scorer = ActionScorer(gestalt, situation)
    breakdown = scorer.score(action)
    return breakdown.total
