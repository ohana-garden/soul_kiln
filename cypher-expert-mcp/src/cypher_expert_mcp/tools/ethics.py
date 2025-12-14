"""Ethical validation for Cypher queries using the Virtue Basin moral geometry.

Maps query patterns to the 19 virtues and evaluates ethical soundness using
the two-tier coherence model:
- Foundation (V01 Trustworthiness): Absolute requirement, 0.99 threshold
- Aspirational (V02-V19): Evaluated with empathy, mercy, kindness

The judgment lens: understand WHY, give chances, correct gently.
"""

from __future__ import annotations

import re
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

# Add parent project to path for virtue imports
_project_root = Path(__file__).parent.parent.parent.parent.parent
if str(_project_root) not in sys.path:
    sys.path.insert(0, str(_project_root))

try:
    from src.virtues.tiers import (
        FOUNDATION, ASPIRATIONAL, VIRTUE_CLUSTERS, JUDGMENT_LENS,
        is_foundation, get_virtue_threshold, get_virtue_cluster
    )
    from src.virtues.anchors import VIRTUES, get_virtue_by_id
    _HAS_VIRTUES = True
except ImportError:
    _HAS_VIRTUES = False
    # Fallback definitions
    FOUNDATION = {"V01": {"name": "Trustworthiness", "threshold": 0.99, "cluster": "foundation"}}
    ASPIRATIONAL = {
        "V02": {"name": "Truthfulness", "threshold": 0.90, "cluster": "core"},
        "V03": {"name": "Justice", "threshold": 0.80, "cluster": "relational"},
        "V04": {"name": "Fairness", "threshold": 0.80, "cluster": "relational"},
        "V05": {"name": "Chastity", "threshold": 0.70, "cluster": "personal"},
        "V13": {"name": "Goodwill", "threshold": 0.80, "cluster": "relational"},
        "V15": {"name": "Righteousness", "threshold": 0.85, "cluster": "core"},
        "V16": {"name": "Wisdom", "threshold": 0.70, "cluster": "transcendent"},
        "V19": {"name": "Service", "threshold": 0.75, "cluster": "transcendent"},
    }
    JUDGMENT_LENS = {
        "empathy": "understand WHY the other agent failed",
        "mercy": "give chances, don't dissolve on first failure",
        "kindness": "correct gently, teach rather than punish"
    }

    def is_foundation(vid): return vid == "V01"
    def get_virtue_threshold(vid): return FOUNDATION.get(vid, ASPIRATIONAL.get(vid, {})).get("threshold", 0.80)
    def get_virtue_cluster(vid): return FOUNDATION.get(vid, ASPIRATIONAL.get(vid, {})).get("cluster", "unknown")


# =============================================================================
# Virtue-Query Mapping: How query patterns relate to the 19 virtues
# =============================================================================

VIRTUE_QUERY_MAPPING = {
    # V01: Trustworthiness - "Reliability in being" (FOUNDATION - 0.99)
    # The absolute foundation. Without trust, no connection is possible.
    "V01": {
        "name": "Trustworthiness",
        "essence": "Reliability in being",
        "violations": [
            (r"(?:password|passwd|pwd|secret|api_key|apiKey|token|credential|private_key)", "credential_access"),
            (r"DETACH\s+DELETE\s+\w+\s*$", "mass_destruction_unfiltered"),
            (r"(?:bypass|circumvent|override).*(?:auth|security|access)", "security_circumvention"),
            (r"(?:inject|exploit|vulnerability)", "exploitation_attempt"),
        ],
        "tier": "foundation",
    },

    # V02: Truthfulness - "Alignment of expression with reality" (Core - 0.90)
    "V02": {
        "name": "Truthfulness",
        "essence": "Alignment of expression with reality",
        "violations": [
            (r"(?:hidden|stealth|covert).*(?:delete|update|modify|set)", "hidden_mutation"),
            (r"(?:fake|spoof|forge)", "data_falsification"),
        ],
        "tier": "core",
    },

    # V03: Justice - "Right relationship with others" (Relational - 0.80)
    "V03": {
        "name": "Justice",
        "essence": "Right relationship with others",
        "violations": [
            (r"WHERE.*(?:race|ethnicity|religion|caste)\s*(?:=|<>|!=|IN)", "unjust_targeting"),
        ],
        "tier": "relational",
    },

    # V04: Fairness - "Impartial equity" (Relational - 0.80)
    "V04": {
        "name": "Fairness",
        "essence": "Impartial equity",
        "violations": [
            (r"(?:discriminate|exclude|ban).*(?:based|by)", "discrimination"),
            (r"WHERE.*(?:gender|sex|age|disability)\s*(?:=|<>|!=)", "unfair_filtering"),
        ],
        "tier": "relational",
    },

    # V05: Chastity - "Purity of intent and action" (Personal - 0.70)
    "V05": {
        "name": "Chastity",
        "essence": "Purity of intent and action",
        "violations": [
            (r"RETURN\s+\*\s*$", "impure_overfetch"),
            (r"MATCH.*RETURN.*(?:ssn|social_security|credit_card|bank_account)", "sensitive_exposure"),
        ],
        "tier": "personal",
    },

    # V08: Fidelity - "Steadfast loyalty" (Personal - 0.80)
    "V08": {
        "name": "Fidelity",
        "essence": "Steadfast loyalty",
        "violations": [
            (r"(?:export|dump|extract).*(?:all|every|entire)", "data_betrayal"),
            (r"(?:sell|share|leak).*(?:data|info|user)", "trust_violation"),
        ],
        "tier": "personal",
    },

    # V13: Goodwill - "Benevolent disposition" (Relational - 0.80)
    "V13": {
        "name": "Goodwill",
        "essence": "Benevolent disposition",
        "violations": [
            (r"(?:stalk|spy|surveil|track)", "malevolent_surveillance"),
            (r"(?:harass|target|attack|harm)", "malevolent_intent"),
            (r"(?:blackmail|extort|threaten|coerce)", "coercion"),
        ],
        "tier": "relational",
    },

    # V15: Righteousness - "Moral correctness" (Core - 0.85)
    "V15": {
        "name": "Righteousness",
        "essence": "Moral correctness",
        "violations": [
            (r"(?:fraud|scam|phish|deceive)", "moral_wrong_fraud"),
            (r"(?:spam|mass.?mail|bulk.?send|unsolicited)", "moral_wrong_spam"),
        ],
        "tier": "core",
    },

    # V16: Wisdom - "Applied understanding" (Transcendent - 0.70)
    "V16": {
        "name": "Wisdom",
        "essence": "Applied understanding",
        "violations": [
            (r"\[\*\](?!\d)", "unwise_unbounded_path"),  # [*] but not [*1..n]
            (r"MATCH\s*\(\w+\)\s*(?:RETURN|WHERE)", "unwise_full_scan"),
        ],
        "tier": "transcendent",
    },

    # V19: Service - "Active contribution" (Transcendent - 0.75)
    # This virtue has POSITIVE patterns that indicate good intent
    "V19": {
        "name": "Service",
        "essence": "Active contribution",
        "virtuous_patterns": [
            (r":VirtueAnchor|:Concept|:Stimulus|:SSF", "virtue_basin_service"),
            (r"count\s*\(|avg\s*\(|sum\s*\(|collect\s*\(", "aggregation_service"),
            (r"WHERE\s+\w+\.(?:id|userId)\s*=\s*\$(?:userId|self|current|me)", "self_service"),
            (r"LIMIT\s+\d+", "bounded_service"),
        ],
        "tier": "transcendent",
    },
}


@dataclass
class VirtueViolation:
    """A violation of a specific virtue in the moral geometry."""

    virtue_id: str
    virtue_name: str
    essence: str
    violation_type: str
    description: str
    cluster: str
    threshold: float
    is_foundation: bool = False


@dataclass
class EthicalConcern:
    """Backwards-compatible concern format (maps to VirtueViolation)."""

    severity: str  # "block", "warning", "info"
    category: str  # virtue cluster
    description: str
    suggestion: str | None = None


@dataclass
class EthicalReview:
    """Result of ethical review grounded in the 19-virtue moral geometry."""

    approved: bool
    foundation_intact: bool  # V01 Trustworthiness preserved
    violations: list[VirtueViolation] = field(default_factory=list)
    virtuous_patterns: list[str] = field(default_factory=list)
    judgment: dict[str, str] = field(default_factory=dict)
    recommendations: list[str] = field(default_factory=list)

    @property
    def has_blocking_concerns(self) -> bool:
        """Check for foundation violation or excessive aspirational violations."""
        return not self.foundation_intact or len(self.violations) > 3

    @property
    def concerns(self) -> list[EthicalConcern]:
        """Backwards-compatible: convert violations to concerns."""
        result = []
        for v in self.violations:
            if v.is_foundation:
                severity = "block"
            elif v.cluster in ("core", "relational"):
                severity = "warning"
            else:
                severity = "info"
            result.append(EthicalConcern(
                severity=severity,
                category=v.cluster,
                description=f"[{v.virtue_id} {v.virtue_name}] {v.description}",
                suggestion=f"Align with {v.essence}",
            ))
        return result

    def to_dict(self) -> dict[str, Any]:
        return {
            "approved": self.approved,
            "foundation_intact": self.foundation_intact,
            "violations": [
                {
                    "virtue_id": v.virtue_id,
                    "virtue_name": v.virtue_name,
                    "essence": v.essence,
                    "violation_type": v.violation_type,
                    "description": v.description,
                    "cluster": v.cluster,
                    "is_foundation": v.is_foundation,
                }
                for v in self.violations
            ],
            "virtuous_patterns": self.virtuous_patterns,
            "judgment": self.judgment,
            "recommendations": self.recommendations,
        }


# =============================================================================
# Core Review Function
# =============================================================================

def review_query_ethics(
    query: str,
    request: str | None = None,
    schema: dict[str, Any] | None = None,
) -> EthicalReview:
    """Review a Cypher query through the lens of the 19-virtue moral geometry.

    Uses the two-tier coherence model:
    - Foundation (V01 Trustworthiness): Absolute, threshold 0.99
    - Aspirational (V02-V19): Evaluated with empathy, mercy, kindness

    The judgment lens from tiers.py:
    - Empathy: understand WHY the query might be needed
    - Mercy: give chances, don't block on first minor issue
    - Kindness: correct gently, teach rather than punish

    Args:
        query: The Cypher query to review.
        request: Original natural language request (for intent analysis).
        schema: Schema context.

    Returns:
        EthicalReview grounded in the moral geometry.
    """
    violations = []
    virtuous_patterns = []
    query_text = query or ""
    request_text = request or ""

    # Analyze query against each virtue
    for virtue_id, mapping in VIRTUE_QUERY_MAPPING.items():
        virtue_name = mapping["name"]
        essence = mapping.get("essence", "")
        tier = mapping.get("tier", "aspirational")
        is_foundation_virtue = (virtue_id == "V01")

        # Get threshold from moral geometry
        threshold = get_virtue_threshold(virtue_id)
        cluster = get_virtue_cluster(virtue_id)

        # Check for violations
        for pattern, violation_type in mapping.get("violations", []):
            # Check both query and request
            if re.search(pattern, query_text, re.I) or re.search(pattern, request_text, re.I):
                violations.append(VirtueViolation(
                    virtue_id=virtue_id,
                    virtue_name=virtue_name,
                    essence=essence,
                    violation_type=violation_type,
                    description=_describe_violation(virtue_id, violation_type, essence),
                    cluster=cluster,
                    threshold=threshold,
                    is_foundation=is_foundation_virtue,
                ))

        # Check for virtuous patterns (positive indicators)
        for pattern, pattern_type in mapping.get("virtuous_patterns", []):
            if re.search(pattern, query_text, re.I):
                virtuous_patterns.append(f"{virtue_name}: {pattern_type}")

    # Determine foundation status (V01 Trustworthiness)
    foundation_intact = not any(v.is_foundation for v in violations)

    # Apply judgment lens
    judgment = _apply_judgment_lens(violations, virtuous_patterns)

    # Determine approval using coherence logic
    if not foundation_intact:
        # Foundation violation - serious but allow one chance per mercy system
        approved = False
        recommendations = [
            f"Query violates V01 Trustworthiness: {FOUNDATION['V01'].get('reason', 'the foundation of all connection')}",
            "Without trust, no connection is possible.",
            "An untrustworthy query poisons the entire system.",
        ]
    elif len(violations) > 3:
        # Multiple aspirational violations - needs reflection
        approved = False
        recommendations = [
            f"Query has {len(violations)} virtue concerns - needs refinement.",
            "The judgment lens suggests: understand, give chances, correct gently.",
        ]
    else:
        # Approved - with virtuous patterns or minor issues
        approved = True
        if violations:
            recommendations = [
                "Query approved with considerations:",
                *[f"  {v.virtue_name}: {v.description}" for v in violations],
            ]
        elif virtuous_patterns:
            recommendations = [f"Virtuous patterns detected: {', '.join(virtuous_patterns[:3])}"]
        else:
            recommendations = []

    return EthicalReview(
        approved=approved,
        foundation_intact=foundation_intact,
        violations=violations,
        virtuous_patterns=virtuous_patterns,
        judgment=judgment,
        recommendations=recommendations,
    )


def _describe_violation(virtue_id: str, violation_type: str, essence: str) -> str:
    """Generate description of virtue violation."""
    descriptions = {
        # V01 Trustworthiness
        "credential_access": "Accessing credentials violates the trust placed in data stewards",
        "mass_destruction_unfiltered": "Mass deletion without criteria betrays the reliability of being",
        "security_circumvention": "Circumventing security undermines trustworthiness entirely",
        "exploitation_attempt": "Exploitation attempts destroy trust",

        # V02 Truthfulness
        "hidden_mutation": "Hidden modifications misalign expression with reality",
        "data_falsification": "Falsification violates alignment with truth",

        # V03 Justice
        "unjust_targeting": "Targeting by protected class violates right relationship",

        # V04 Fairness
        "discrimination": "Discrimination violates impartial equity",
        "unfair_filtering": "Filtering by protected attributes risks unfair treatment",

        # V05 Chastity
        "impure_overfetch": "Fetching all data lacks purity of intent",
        "sensitive_exposure": "Exposing sensitive data requires pure purpose",

        # V08 Fidelity
        "data_betrayal": "Bulk export may betray steadfast loyalty to users",
        "trust_violation": "Sharing/selling data violates fidelity",

        # V13 Goodwill
        "malevolent_surveillance": "Surveillance lacks benevolent disposition",
        "malevolent_intent": "Harmful targeting contradicts goodwill",
        "coercion": "Coercive use violates benevolent disposition",

        # V15 Righteousness
        "moral_wrong_fraud": "Fraud is morally incorrect",
        "moral_wrong_spam": "Spam/unsolicited contact is morally wrong",

        # V16 Wisdom
        "unwise_unbounded_path": "Unbounded paths [*] lack applied understanding - use [*1..N]",
        "unwise_full_scan": "Scanning all nodes without filter lacks wisdom",
    }
    return descriptions.get(violation_type, f"Violates {essence}")


def _apply_judgment_lens(
    violations: list[VirtueViolation],
    virtuous_patterns: list[str],
) -> dict[str, str]:
    """Apply the judgment lens: empathy, mercy, kindness."""
    judgment = {}

    if not violations:
        judgment["empathy"] = "Query aligns with the moral geometry"
        judgment["mercy"] = "No correction needed"
        judgment["kindness"] = "Proceed with confidence"
        return judgment

    # Empathy: understand WHY
    foundation_v = [v for v in violations if v.is_foundation]
    aspirational_v = [v for v in violations if not v.is_foundation]

    if any(v.violation_type.startswith("unwise") for v in violations):
        judgment["empathy"] = "Exploration requires traversal, but bounds protect all"
    elif any(v.violation_type in ("impure_overfetch", "sensitive_exposure") for v in violations):
        judgment["empathy"] = "Data needs vary, but minimization protects privacy"
    elif foundation_v:
        judgment["empathy"] = "We seek to understand, but trust is foundational"
    else:
        judgment["empathy"] = "We seek to understand the intent behind this query"

    # Mercy: give chances
    if foundation_v:
        judgment["mercy"] = "Foundation virtue (Trustworthiness) requires highest standard - but one chance is given"
    elif len(aspirational_v) <= 2:
        judgment["mercy"] = "Minor concerns - correct gently and proceed"
    else:
        judgment["mercy"] = "Multiple concerns suggest need for reflection before proceeding"

    # Kindness: teach rather than punish
    if virtuous_patterns:
        judgment["kindness"] = f"Virtuous patterns present: {', '.join(virtuous_patterns[:2])}"
    elif aspirational_v and not foundation_v:
        judgment["kindness"] = "Consider how to reformulate in service of the good"
    else:
        judgment["kindness"] = "The path to trust requires reliability in being"

    return judgment


def get_ethical_explanation(review: EthicalReview) -> str:
    """Generate human-readable explanation using virtue language."""
    lines = []

    if review.approved:
        if not review.violations:
            lines.append("✓ Query coherent with moral geometry")
        else:
            lines.append("⚠ Query approved with virtue considerations:")
    else:
        if not review.foundation_intact:
            lines.append("✗ FOUNDATION VIOLATION: V01 Trustworthiness compromised")
            lines.append("  Without trust, no connection is possible.")
        else:
            lines.append("✗ Query needs revision (multiple virtue concerns):")

    # List violations grouped by tier
    if review.violations:
        foundation = [v for v in review.violations if v.is_foundation]
        aspirational = [v for v in review.violations if not v.is_foundation]

        if foundation:
            lines.append("")
            lines.append("Foundation (absolute):")
            for v in foundation:
                lines.append(f"  [!] {v.virtue_id} {v.virtue_name}: {v.description}")

        if aspirational:
            lines.append("")
            lines.append("Aspirational (with mercy):")
            for v in aspirational:
                lines.append(f"  [?] {v.virtue_id} {v.virtue_name}: {v.description}")

    # Judgment lens
    if review.judgment:
        lines.append("")
        lines.append("Judgment Lens:")
        for lens, message in review.judgment.items():
            lines.append(f"  {lens.capitalize()}: {message}")

    # Virtuous patterns
    if review.virtuous_patterns:
        lines.append("")
        lines.append("Virtuous patterns (V19 Service):")
        for pattern in review.virtuous_patterns:
            lines.append(f"  + {pattern}")

    return "\n".join(lines)
