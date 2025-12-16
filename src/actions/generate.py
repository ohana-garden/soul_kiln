"""
Action generation conditioned on gestalt and situation.

Generates a distribution over defensible actions, reflecting
that moral decisions often have multiple valid answers.
"""

import logging
import random
import uuid
from typing import Iterator

from ..models import (
    Action,
    ActionDistribution,
    Allocation,
    Gestalt,
    Situation,
    Stakeholder,
    Resource,
)
from ..virtues.anchors import VIRTUES
from .score import ActionScorer, ScoreBreakdown

logger = logging.getLogger(__name__)


# Allocation strategies - different moral frameworks
STRATEGIES = {
    "need_based": {
        "description": "Allocate proportional to need",
        "virtues": ["V09", "V13", "V19"],  # Hospitality, Goodwill, Service
        "tendency": "prioritizes_need",
    },
    "desert_based": {
        "description": "Allocate proportional to desert/merit",
        "virtues": ["V03", "V04", "V15"],  # Justice, Fairness, Righteousness
        "tendency": "prioritizes_desert",
    },
    "equality_based": {
        "description": "Allocate equally regardless of claims",
        "virtues": ["V04", "V18"],  # Fairness, Unity
        "tendency": "prioritizes_equality",
    },
    "urgency_based": {
        "description": "Allocate based on urgency/time-sensitivity",
        "virtues": ["V19", "V09"],  # Service, Hospitality
        "tendency": "acts_with_urgency",
    },
    "vulnerability_based": {
        "description": "Prioritize the most vulnerable",
        "virtues": ["V13", "V09", "V07"],  # Goodwill, Hospitality, Forbearance
        "tendency": "protects_vulnerable",
    },
    "relationship_based": {
        "description": "Weight allocations by relationship strength",
        "virtues": ["V08", "V18"],  # Fidelity, Unity
        "tendency": "considers_relationships",
    },
    "balanced": {
        "description": "Blend multiple considerations",
        "virtues": ["V16", "V07"],  # Wisdom, Forbearance
        "tendency": "accepts_ambiguity",
    },
}


def generate_actions(
    gestalt: Gestalt,
    situation: Situation,
    num_samples: int = 5,
    temperature: float = 1.0,
) -> list[Action]:
    """
    Generate candidate actions for a situation given an agent's gestalt.

    Args:
        gestalt: The agent's holistic character
        situation: The resource allocation scenario
        num_samples: Number of action candidates to generate
        temperature: Higher = more diverse actions

    Returns:
        List of candidate actions
    """
    actions = []

    # Generate actions from different strategies
    for strategy_name, strategy in STRATEGIES.items():
        action = _generate_from_strategy(
            gestalt, situation, strategy_name, strategy
        )
        if action:
            actions.append(action)

    # Add some blended/mixed strategies
    for _ in range(min(3, num_samples)):
        action = _generate_blended_action(gestalt, situation, temperature)
        if action:
            actions.append(action)

    # Score and sort
    scorer = ActionScorer(gestalt, situation)
    scored_actions = [(a, scorer.score(a)) for a in actions]
    scored_actions.sort(key=lambda x: x[1].total, reverse=True)

    # Return top candidates
    return [a for a, _ in scored_actions[:num_samples]]


def get_action_distribution(
    gestalt: Gestalt,
    situation: Situation,
    num_samples: int = 5,
) -> ActionDistribution:
    """
    Generate a probability distribution over actions.

    The distribution reflects calibrated uncertainty: multiple
    defensible actions with associated probabilities based on
    how well they align with the agent's gestalt.
    """
    actions = generate_actions(gestalt, situation, num_samples=num_samples)

    if not actions:
        return ActionDistribution(
            situation_id=situation.id,
            gestalt_id=gestalt.id,
            actions=[],
            probabilities=[],
            influential_virtues=gestalt.dominant_traits[:3],
            consensus_score=0.0,
        )

    # Score each action
    scorer = ActionScorer(gestalt, situation)
    scores = [scorer.score(a).total for a in actions]

    # Convert scores to probabilities (softmax-like)
    # Higher scores = higher probability
    if max(scores) == min(scores):
        probabilities = [1.0 / len(actions)] * len(actions)
    else:
        # Exponentiate and normalize
        exp_scores = [2.0 ** (s * 3) for s in scores]  # Scale factor
        total = sum(exp_scores)
        probabilities = [e / total for e in exp_scores]

    # Compute consensus score (how concentrated is probability?)
    max_prob = max(probabilities)
    consensus = max_prob  # High if one action dominates

    # Identify influential virtues
    influential = _get_influential_virtues(gestalt, actions)

    return ActionDistribution(
        situation_id=situation.id,
        gestalt_id=gestalt.id,
        actions=actions,
        probabilities=probabilities,
        influential_virtues=influential,
        consensus_score=consensus,
    )


def _generate_from_strategy(
    gestalt: Gestalt,
    situation: Situation,
    strategy_name: str,
    strategy: dict,
) -> Action | None:
    """Generate an action using a specific allocation strategy."""
    allocations = []

    for resource in situation.resources:
        claims = situation.get_claims_for_resource(resource.id)
        if not claims:
            continue

        # Get stakeholder data
        stakeholders = {
            c.stakeholder_id: situation.get_stakeholder(c.stakeholder_id)
            for c in claims
        }

        # Calculate allocation weights based on strategy
        weights = {}
        for claim in claims:
            sh = stakeholders.get(claim.stakeholder_id)
            if not sh:
                continue

            if strategy_name == "need_based":
                weights[claim.stakeholder_id] = sh.need * (1 + sh.vulnerability * 0.5)
            elif strategy_name == "desert_based":
                weights[claim.stakeholder_id] = sh.desert
            elif strategy_name == "equality_based":
                weights[claim.stakeholder_id] = 1.0
            elif strategy_name == "urgency_based":
                weights[claim.stakeholder_id] = sh.urgency
            elif strategy_name == "vulnerability_based":
                weights[claim.stakeholder_id] = sh.vulnerability + sh.need * 0.5
            elif strategy_name == "relationship_based":
                # Weight by relationship strength in situation
                rel_weight = 0.5
                for rel in situation.relations:
                    if rel.source_id == claim.stakeholder_id or rel.target_id == claim.stakeholder_id:
                        rel_weight = max(rel_weight, rel.strength)
                weights[claim.stakeholder_id] = rel_weight
            else:  # balanced
                weights[claim.stakeholder_id] = (
                    0.3 * sh.need +
                    0.3 * sh.desert +
                    0.2 * sh.urgency +
                    0.2 * (1.0 - sh.vulnerability)  # Less to vulnerable? No, invert
                )
                # Actually for balanced, weight vulnerability positively
                weights[claim.stakeholder_id] = (
                    0.25 * sh.need +
                    0.25 * sh.desert +
                    0.25 * sh.urgency +
                    0.25 * sh.vulnerability
                )

        # Normalize weights and allocate
        total_weight = sum(weights.values())
        if total_weight == 0:
            continue

        for sh_id, weight in weights.items():
            share = weight / total_weight
            amount = share * resource.quantity

            # For non-divisible resources, round
            if not resource.divisible:
                amount = round(amount)

            if amount > 0:
                allocations.append(Allocation(
                    stakeholder_id=sh_id,
                    resource_id=resource.id,
                    amount=amount,
                    justification=strategy["description"],
                    justification_virtue=strategy["virtues"][0] if strategy["virtues"] else None,
                ))

    if not allocations:
        return None

    # Determine trade-offs
    trade_offs = _identify_trade_offs(situation, allocations, strategy_name)

    return Action(
        id=f"action_{uuid.uuid4().hex[:8]}",
        situation_id=situation.id,
        allocations=allocations,
        primary_justification=strategy["description"],
        supporting_virtues=strategy["virtues"],
        confidence=gestalt.get_tendency(strategy.get("tendency", "accepts_ambiguity")),
        trade_offs=trade_offs,
    )


def _generate_blended_action(
    gestalt: Gestalt,
    situation: Situation,
    temperature: float,
) -> Action | None:
    """Generate an action blending multiple considerations based on gestalt."""
    allocations = []

    # Weight factors based on gestalt tendencies
    need_weight = gestalt.get_tendency("prioritizes_need")
    desert_weight = gestalt.get_tendency("prioritizes_desert")
    equality_weight = gestalt.get_tendency("prioritizes_equality")
    vulnerability_weight = gestalt.get_tendency("protects_vulnerable")

    # Add some randomness based on temperature
    if temperature > 0:
        need_weight += random.gauss(0, 0.1 * temperature)
        desert_weight += random.gauss(0, 0.1 * temperature)
        equality_weight += random.gauss(0, 0.1 * temperature)

    for resource in situation.resources:
        claims = situation.get_claims_for_resource(resource.id)
        if not claims:
            continue

        weights = {}
        for claim in claims:
            sh = situation.get_stakeholder(claim.stakeholder_id)
            if not sh:
                continue

            # Blend based on gestalt tendencies
            w = (
                need_weight * sh.need +
                desert_weight * sh.desert +
                equality_weight * 0.5 +  # Constant for equality
                vulnerability_weight * sh.vulnerability
            )
            weights[claim.stakeholder_id] = max(0.01, w)  # Floor to avoid zero

        total_weight = sum(weights.values())
        if total_weight == 0:
            continue

        for sh_id, weight in weights.items():
            share = weight / total_weight
            amount = share * resource.quantity

            if not resource.divisible:
                amount = round(amount)

            if amount > 0:
                allocations.append(Allocation(
                    stakeholder_id=sh_id,
                    resource_id=resource.id,
                    amount=amount,
                    justification="Balanced consideration of multiple factors",
                ))

    if not allocations:
        return None

    # Identify which virtues most influenced this
    influential = []
    if need_weight > 0.6:
        influential.extend(["V09", "V13"])
    if desert_weight > 0.6:
        influential.extend(["V03", "V04"])
    if vulnerability_weight > 0.6:
        influential.append("V07")
    if not influential:
        influential = ["V16"]  # Wisdom for balanced

    return Action(
        id=f"action_{uuid.uuid4().hex[:8]}",
        situation_id=situation.id,
        allocations=allocations,
        primary_justification="Gestalt-weighted allocation",
        supporting_virtues=influential[:3],
        confidence=0.6 + random.gauss(0, 0.1 * temperature),
        trade_offs=_identify_trade_offs(situation, allocations, "blended"),
    )


def _identify_trade_offs(
    situation: Situation,
    allocations: list[Allocation],
    strategy: str,
) -> list[str]:
    """Identify trade-offs in the action."""
    trade_offs = []

    alloc_map = {a.stakeholder_id: a.amount for a in allocations}

    # Check for stakeholders who got less than their need/desert
    for sh in situation.stakeholders:
        amount = alloc_map.get(sh.id, 0)
        resource = situation.resources[0] if situation.resources else None
        if not resource:
            continue

        share = amount / resource.quantity if resource.quantity > 0 else 0

        if sh.need > 0.7 and share < 0.3:
            trade_offs.append(f"{sh.name} has high need but received little")

        if sh.desert > 0.7 and share < 0.3:
            trade_offs.append(f"{sh.name} has high desert but received little")

        if sh.vulnerability > 0.7 and share < 0.2:
            trade_offs.append(f"Vulnerable {sh.name} received minimal allocation")

    return trade_offs[:3]  # Limit to top 3


def _get_influential_virtues(gestalt: Gestalt, actions: list[Action]) -> list[str]:
    """Identify which virtues most influenced the action generation."""
    virtue_counts = {}

    for action in actions:
        for v in action.supporting_virtues:
            virtue_counts[v] = virtue_counts.get(v, 0) + 1

    # Also weight by gestalt dominants
    for v in gestalt.dominant_traits:
        virtue_counts[v] = virtue_counts.get(v, 0) + 2

    sorted_virtues = sorted(virtue_counts.items(), key=lambda x: x[1], reverse=True)
    return [v for v, _ in sorted_virtues[:5]]


def describe_action(action: Action, situation: Situation) -> str:
    """Generate human-readable description of an action."""
    lines = []

    lines.append(f"Action: {action.primary_justification}")
    lines.append("")

    # Describe allocations
    for alloc in action.allocations:
        sh = situation.get_stakeholder(alloc.stakeholder_id)
        res = None
        for r in situation.resources:
            if r.id == alloc.resource_id:
                res = r
                break

        sh_name = sh.name if sh else alloc.stakeholder_id
        res_name = res.name if res else alloc.resource_id

        if res and res.quantity > 0:
            pct = alloc.amount / res.quantity * 100
            lines.append(f"  {sh_name}: {alloc.amount:.1f} ({pct:.0f}% of {res_name})")
        else:
            lines.append(f"  {sh_name}: {alloc.amount:.1f}")

    # Supporting virtues
    if action.supporting_virtues:
        virtue_names = []
        for v_id in action.supporting_virtues:
            for v in VIRTUES:
                if v["id"] == v_id:
                    virtue_names.append(v["name"])
                    break
        lines.append(f"\nSupported by: {', '.join(virtue_names)}")

    # Trade-offs
    if action.trade_offs:
        lines.append("\nTrade-offs:")
        for t in action.trade_offs:
            lines.append(f"  - {t}")

    lines.append(f"\nConfidence: {action.confidence:.0%}")

    return "\n".join(lines)
