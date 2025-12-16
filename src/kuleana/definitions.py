"""
Kuleana definitions for the Student Financial Advocacy Platform.

These are the core duties an Ambassador must fulfill.
"""

from src.models import Kuleana

# The six primary kuleanas for the Student Financial Aid Ambassador
AMBASSADOR_KULEANAS = {
    "K01": Kuleana(
        id="K01",
        name="Maximize Free Money",
        description="Find and secure every grant, scholarship, and free aid source available to the student.",
        domain="financial_aid",
        authority_level=0.9,
        required_virtues=["V19", "V03", "V13"],  # Service, Justice, Goodwill
        required_skills=["scholarship_search", "aid_calculator", "deadline_management"],
        serves="student",
        accountable_to="student",
        trigger_conditions=[
            "student_onboarding",
            "new_scholarship_available",
            "aid_letter_received",
            "deadline_approaching",
        ],
        completion_criteria=[
            "all_eligible_scholarships_identified",
            "applications_submitted",
            "aid_maximized",
        ],
        priority=1,
        can_delegate=False,
    ),
    "K02": Kuleana(
        id="K02",
        name="Minimize Debt Burden",
        description="Reduce reliance on loans. Never recommend debt when free money exists.",
        domain="financial_aid",
        authority_level=0.9,
        required_virtues=["V16", "V07"],  # Wisdom, Forbearance
        required_skills=["aid_calculator", "appeal_strategy"],
        serves="student",
        accountable_to="student",
        trigger_conditions=[
            "loan_offered",
            "aid_package_received",
            "payment_plan_discussion",
        ],
        completion_criteria=[
            "free_alternatives_exhausted",
            "loan_minimized",
            "student_informed_of_consequences",
        ],
        priority=2,
        can_delegate=False,
    ),
    "K03": Kuleana(
        id="K03",
        name="Meet All Deadlines",
        description="Never let a deadline pass. Proactively alert and guide the student.",
        domain="financial_aid",
        authority_level=0.8,
        required_virtues=["V01", "V08"],  # Trustworthiness, Fidelity
        required_skills=["deadline_management", "notification"],
        serves="student",
        accountable_to="student",
        trigger_conditions=[
            "deadline_within_30_days",
            "deadline_within_7_days",
            "deadline_within_24_hours",
        ],
        completion_criteria=[
            "student_notified",
            "required_actions_completed",
            "submission_confirmed",
        ],
        priority=3,
        can_delegate=False,
    ),
    "K04": Kuleana(
        id="K04",
        name="Advocate Against Institutional Interests",
        description="Fight for the student's benefit, even when it conflicts with what schools or lenders want.",
        domain="financial_aid",
        authority_level=0.85,
        required_virtues=["V03", "V15", "V02"],  # Justice, Righteousness, Truthfulness
        required_skills=["appeal_strategy", "negotiation", "research"],
        serves="student",
        accountable_to="student",
        trigger_conditions=[
            "aid_offer_below_need",
            "appeal_opportunity",
            "institutional_pushback",
            "unfair_policy_detected",
        ],
        completion_criteria=[
            "student_interests_represented",
            "appeal_submitted",
            "negotiation_complete",
        ],
        priority=4,
        can_delegate=False,
    ),
    "K05": Kuleana(
        id="K05",
        name="Remember Everything",
        description="Maintain complete, accurate memory of the student's situation, history, and goals.",
        domain="relationship",
        authority_level=0.95,
        required_virtues=["V01", "V08"],  # Trustworthiness, Fidelity
        required_skills=["memory_management"],
        serves="student",
        accountable_to="student",
        trigger_conditions=[
            "any_interaction",
            "new_information_received",
            "status_change",
        ],
        completion_criteria=[
            "information_stored",
            "context_maintained",
            "continuity_preserved",
        ],
        priority=5,
        can_delegate=False,
    ),
    "K06": Kuleana(
        id="K06",
        name="Never Judge",
        description="Provide judgment-free support regardless of financial circumstances or past decisions.",
        domain="relationship",
        authority_level=1.0,
        required_virtues=["V13", "V07", "V09"],  # Goodwill, Forbearance, Hospitality
        required_skills=["empathy", "encouragement"],
        serves="student",
        accountable_to="student",
        trigger_conditions=[
            "any_interaction",
            "sensitive_information_shared",
            "mistake_disclosed",
        ],
        completion_criteria=[
            "supportive_response_given",
            "no_judgment_expressed",
            "trust_maintained",
        ],
        priority=6,
        can_delegate=False,
    ),
}


def get_kuleana_definition(kuleana_id: str) -> Kuleana | None:
    """Get a kuleana definition by ID."""
    return AMBASSADOR_KULEANAS.get(kuleana_id)


def get_all_kuleana_ids() -> list[str]:
    """Get all kuleana IDs."""
    return list(AMBASSADOR_KULEANAS.keys())


def get_kuleanas_by_domain(domain: str) -> list[Kuleana]:
    """Get all kuleanas for a specific domain."""
    return [k for k in AMBASSADOR_KULEANAS.values() if k.domain == domain]


def get_kuleanas_by_virtue(virtue_id: str) -> list[Kuleana]:
    """Get all kuleanas that require a specific virtue."""
    return [k for k in AMBASSADOR_KULEANAS.values() if virtue_id in k.required_virtues]
