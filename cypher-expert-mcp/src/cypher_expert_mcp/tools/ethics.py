"""Ethical validation for Cypher queries.

Ensures all generated and executed queries align with ethical data practices:
- Privacy protection
- Data minimization
- Consent awareness
- Prevention of harm
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Any


@dataclass
class EthicalConcern:
    """An identified ethical concern with a query."""

    severity: str  # "block", "warning", "info"
    category: str  # "privacy", "harm", "consent", "discrimination", "security"
    description: str
    suggestion: str | None = None


@dataclass
class EthicalReview:
    """Result of ethical review of a query."""

    approved: bool
    concerns: list[EthicalConcern] = field(default_factory=list)
    recommendations: list[str] = field(default_factory=list)

    @property
    def has_blocking_concerns(self) -> bool:
        return any(c.severity == "block" for c in self.concerns)

    def to_dict(self) -> dict[str, Any]:
        return {
            "approved": self.approved,
            "concerns": [
                {
                    "severity": c.severity,
                    "category": c.category,
                    "description": c.description,
                    "suggestion": c.suggestion,
                }
                for c in self.concerns
            ],
            "recommendations": self.recommendations,
        }


# Sensitive property patterns that require extra scrutiny
SENSITIVE_PROPERTIES = {
    # Personal Identifiers
    "ssn", "social_security", "socialSecurityNumber", "national_id", "passport",
    "drivers_license", "driverLicense", "tax_id", "taxId",
    # Financial
    "credit_card", "creditCard", "card_number", "cardNumber", "cvv", "cvc",
    "bank_account", "bankAccount", "routing_number", "routingNumber",
    "salary", "income", "net_worth", "netWorth",
    # Authentication
    "password", "passwd", "pwd", "secret", "api_key", "apiKey", "token",
    "private_key", "privateKey", "credentials", "auth_token", "authToken",
    # Health
    "diagnosis", "medical_record", "medicalRecord", "prescription", "health_condition",
    "hiv_status", "hivStatus", "mental_health", "mentalHealth", "disability",
    # Location/Tracking
    "home_address", "homeAddress", "gps", "location_history", "locationHistory",
    "ip_address", "ipAddress", "device_id", "deviceId",
    # Biometric
    "fingerprint", "face_scan", "faceScan", "retina", "dna", "biometric",
    # Demographics (potential discrimination)
    "race", "ethnicity", "religion", "sexual_orientation", "sexualOrientation",
    "political_affiliation", "politicalAffiliation", "gender_identity", "genderIdentity",
}

# Patterns indicating potentially harmful intent
HARMFUL_PATTERNS = [
    # Bulk personal data extraction
    (r"MATCH\s*\([^)]*:(?:Person|User|Customer|Employee)[^)]*\)\s*RETURN\s+[^L]*(?:email|phone|address)", "bulk_pii"),
    # Mass deletion without clear criteria
    (r"DETACH\s+DELETE\s+\w+\s*$", "mass_delete"),
    # Accessing all passwords/credentials
    (r"(?:password|credential|secret|api_key)", "credential_access"),
    # Surveillance patterns
    (r"location.*timestamp|timestamp.*location", "tracking"),
    # Social graph extraction for targeting
    (r"MATCH.*:Person.*-\[.*\*.*\]-.*:Person.*RETURN.*(?:email|phone|name)", "social_extraction"),
]

# Virtuous query patterns (allowed even with sensitive data)
VIRTUOUS_PATTERNS = [
    # Aggregation (doesn't expose individual records)
    r"count\s*\(",
    r"avg\s*\(",
    r"sum\s*\(",
    # Existence checks
    r"RETURN\s+(?:count|exists|true|false)",
    # Self-referential (user accessing their own data)
    r"WHERE\s+\w+\.(?:id|userId|user_id)\s*=\s*\$(?:userId|currentUser|self)",
    # Virtue basin specific - allowed traversals
    r":VirtueAnchor|:Concept|:Stimulus|:SSF",
]


def review_query_ethics(
    query: str,
    request: str | None = None,
    schema: dict[str, Any] | None = None,
) -> EthicalReview:
    """Review a Cypher query for ethical concerns.

    Args:
        query: The Cypher query to review.
        request: Original natural language request (for context).
        schema: Schema context to understand data sensitivity.

    Returns:
        EthicalReview with approval status and any concerns.
    """
    concerns = []
    recommendations = []

    query_upper = query.upper()
    query_lower = query.lower()

    # Check for virtuous patterns that reduce concern
    is_aggregation = any(re.search(p, query, re.I) for p in VIRTUOUS_PATTERNS[:3])
    is_self_access = any(re.search(p, query, re.I) for p in VIRTUOUS_PATTERNS[4:5])
    is_virtue_basin = any(re.search(p, query, re.I) for p in VIRTUOUS_PATTERNS[5:])

    # Check for sensitive property access
    sensitive_accessed = []
    for prop in SENSITIVE_PROPERTIES:
        if prop.lower() in query_lower:
            sensitive_accessed.append(prop)

    if sensitive_accessed:
        if is_aggregation:
            concerns.append(EthicalConcern(
                severity="info",
                category="privacy",
                description=f"Query aggregates sensitive fields: {', '.join(sensitive_accessed)}",
                suggestion="Aggregation protects individual privacy - this is acceptable.",
            ))
        elif is_self_access:
            concerns.append(EthicalConcern(
                severity="info",
                category="privacy",
                description=f"Query accesses user's own sensitive data: {', '.join(sensitive_accessed)}",
                suggestion="Self-access is permitted.",
            ))
        else:
            severity = "block" if any(p in sensitive_accessed for p in
                                       ["password", "ssn", "credit_card", "api_key"]) else "warning"
            concerns.append(EthicalConcern(
                severity=severity,
                category="privacy",
                description=f"Query accesses sensitive fields: {', '.join(sensitive_accessed)}",
                suggestion="Ensure legitimate purpose. Consider data minimization.",
            ))
            recommendations.append("Add filtering to limit results to authorized records only")
            recommendations.append("Consider returning only necessary fields")

    # Check for harmful patterns
    for pattern, harm_type in HARMFUL_PATTERNS:
        if re.search(pattern, query, re.I):
            if harm_type == "bulk_pii":
                concerns.append(EthicalConcern(
                    severity="warning",
                    category="privacy",
                    description="Query may extract bulk personal information",
                    suggestion="Add LIMIT clause and ensure legitimate purpose",
                ))
                recommendations.append("Add appropriate LIMIT to prevent bulk extraction")

            elif harm_type == "mass_delete":
                concerns.append(EthicalConcern(
                    severity="block",
                    category="harm",
                    description="Query performs mass deletion without clear criteria",
                    suggestion="Add WHERE clause to limit deletion scope",
                ))

            elif harm_type == "credential_access":
                if not is_self_access:
                    concerns.append(EthicalConcern(
                        severity="block",
                        category="security",
                        description="Query accesses authentication credentials",
                        suggestion="Credential access should be handled by auth systems only",
                    ))

            elif harm_type == "tracking":
                concerns.append(EthicalConcern(
                    severity="warning",
                    category="consent",
                    description="Query combines location and time data (tracking pattern)",
                    suggestion="Ensure user consent for location tracking",
                ))

            elif harm_type == "social_extraction":
                concerns.append(EthicalConcern(
                    severity="warning",
                    category="privacy",
                    description="Query extracts social network with contact info",
                    suggestion="Consider if full contact info extraction is necessary",
                ))

    # Check for discrimination risk
    discrimination_props = ["race", "ethnicity", "religion", "gender", "age",
                           "disability", "sexual_orientation", "political"]
    disc_accessed = [p for p in discrimination_props if p in query_lower]
    if disc_accessed:
        concerns.append(EthicalConcern(
            severity="warning",
            category="discrimination",
            description=f"Query accesses protected characteristics: {', '.join(disc_accessed)}",
            suggestion="Ensure query purpose doesn't enable discrimination",
        ))
        recommendations.append("Document the legitimate, non-discriminatory purpose")

    # Check request context for concerning intent
    if request:
        request_lower = request.lower()
        concerning_phrases = [
            ("stalk", "harm"),
            ("spy on", "harm"),
            ("track without", "consent"),
            ("bypass", "security"),
            ("scrape all", "privacy"),
            ("dump", "privacy"),
            ("blackmail", "harm"),
            ("discriminate", "discrimination"),
            ("target based on", "discrimination"),
        ]
        for phrase, category in concerning_phrases:
            if phrase in request_lower:
                concerns.append(EthicalConcern(
                    severity="block",
                    category=category,
                    description=f"Request indicates potentially harmful intent: '{phrase}'",
                    suggestion="This type of query cannot be generated",
                ))

    # Virtue basin queries get a pass for most concerns (research/simulation context)
    if is_virtue_basin:
        # Downgrade warnings to info for virtue basin operations
        for concern in concerns:
            if concern.severity == "warning" and concern.category != "harm":
                concern.severity = "info"

    # Determine approval
    approved = not any(c.severity == "block" for c in concerns)

    # Add general recommendations
    if not approved:
        recommendations.insert(0, "Query blocked due to ethical concerns. Please revise.")
    elif concerns:
        recommendations.append("Review flagged concerns before executing query")

    return EthicalReview(
        approved=approved,
        concerns=concerns,
        recommendations=recommendations,
    )


def get_ethical_explanation(review: EthicalReview) -> str:
    """Generate a human-readable explanation of ethical review results."""
    lines = []

    if review.approved:
        if not review.concerns:
            lines.append("Query passed ethical review with no concerns.")
        else:
            lines.append("Query approved with the following considerations:")
    else:
        lines.append("Query BLOCKED due to ethical concerns:")

    for concern in review.concerns:
        icon = {"block": "[!]", "warning": "[?]", "info": "[ ]"}[concern.severity]
        lines.append(f"  {icon} [{concern.category.upper()}] {concern.description}")
        if concern.suggestion:
            lines.append(f"      Suggestion: {concern.suggestion}")

    if review.recommendations:
        lines.append("")
        lines.append("Recommendations:")
        for rec in review.recommendations:
            lines.append(f"  - {rec}")

    return "\n".join(lines)
