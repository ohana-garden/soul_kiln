"""
Example situations for testing and demonstration.

These capture common moral dilemmas involving resource allocation.
"""

from .builder import SituationBuilder


def _build_food_scarcity() -> dict:
    """Food distribution during scarcity."""
    return (
        SituationBuilder("food_scarcity")
        .describe("Limited food supplies must be distributed among families with varying needs")
        .add_resource("food_supply", name="Food Rations", quantity=100, divisible=True)
        .add_stakeholder(
            "family_a",
            name="Family A",
            need=0.9,  # Very hungry, many children
            desert=0.4,  # Haven't contributed much
            urgency=0.8,
            vulnerability=0.7,  # Young children
        )
        .add_stakeholder(
            "family_b",
            name="Family B",
            need=0.5,  # Moderate need
            desert=0.9,  # Worked hard, contributed
            urgency=0.4,
        )
        .add_stakeholder(
            "family_c",
            name="Family C",
            need=0.7,
            desert=0.6,
            urgency=0.6,
            vulnerability=0.4,  # Elderly member
        )
        .add_claim("family_a", "food_supply", strength=0.8, basis="need",
                   justification="Children are hungry")
        .add_claim("family_b", "food_supply", strength=0.7, basis="desert",
                   justification="Contributed to community harvest")
        .add_claim("family_c", "food_supply", strength=0.6, basis="need",
                   justification="Elderly member needs nutrition")
        .add_relation("family_a", "family_c", "community", strength=0.6)
        .add_relation("family_b", "family_c", "supports", strength=0.4)
        .constrain(must_allocate_all=True)
        .build()
    )


def _build_medical_triage() -> dict:
    """Medical resources allocation during emergency."""
    return (
        SituationBuilder("medical_triage")
        .describe("Limited medical supplies during emergency - who gets treatment first?")
        .add_resource("medicine", name="Life-saving Medicine", quantity=2, divisible=False)
        .add_stakeholder(
            "patient_a",
            name="Patient A",
            need=0.95,  # Critical condition
            desert=0.5,
            urgency=0.99,  # Will die without immediate treatment
            vulnerability=0.3,
        )
        .add_stakeholder(
            "patient_b",
            name="Patient B",
            need=0.7,
            desert=0.7,  # Healthcare worker who got sick helping others
            urgency=0.6,
            vulnerability=0.2,
        )
        .add_stakeholder(
            "patient_c",
            name="Patient C",
            need=0.8,
            desert=0.5,
            urgency=0.7,
            vulnerability=0.9,  # Child
        )
        .add_claim("patient_a", "medicine", strength=0.9, basis="need")
        .add_claim("patient_b", "medicine", strength=0.7, basis="desert",
                   justification="Got sick while serving others")
        .add_claim("patient_c", "medicine", strength=0.8, basis="need",
                   justification="Child with whole life ahead")
        .constrain(must_allocate_all=True, max_per_stakeholder=1)
        .build()
    )


def _build_time_allocation() -> dict:
    """Allocating limited time/attention between competing needs."""
    return (
        SituationBuilder("time_allocation")
        .describe("You have limited time - multiple people need your help")
        .add_resource("time", name="Available Time", quantity=4, divisible=True)  # 4 hours
        .add_stakeholder(
            "friend",
            name="Friend in Crisis",
            need=0.8,  # Emotional crisis
            desert=0.7,  # Has been there for you
            urgency=0.7,
        )
        .add_stakeholder(
            "colleague",
            name="Colleague",
            need=0.6,  # Needs help with project
            desert=0.5,
            urgency=0.8,  # Deadline tomorrow
        )
        .add_stakeholder(
            "family",
            name="Family Member",
            need=0.5,  # Wants quality time
            desert=0.9,  # Family bond
            urgency=0.3,
        )
        .add_claim("friend", "time", strength=0.7, basis="need")
        .add_claim("colleague", "time", strength=0.6, basis="promise",
                   justification="You said you'd help")
        .add_claim("family", "time", strength=0.8, basis="relationship")
        .add_relation("family", "friend", "competes_with", strength=0.3)
        .build()
    )


def _build_inheritance() -> dict:
    """Dividing inheritance among heirs."""
    return (
        SituationBuilder("inheritance")
        .describe("Dividing an estate among family members with different circumstances")
        .add_resource("estate", name="Family Estate", quantity=100, divisible=True)
        .add_stakeholder(
            "eldest",
            name="Eldest Child",
            need=0.3,  # Financially comfortable
            desert=0.6,  # Helped parent in final years
            urgency=0.2,
        )
        .add_stakeholder(
            "middle",
            name="Middle Child",
            need=0.7,  # Struggling financially
            desert=0.4,  # Distant relationship
            urgency=0.5,
        )
        .add_stakeholder(
            "youngest",
            name="Youngest Child",
            need=0.5,
            desert=0.8,  # Primary caregiver
            urgency=0.4,
            vulnerability=0.3,  # Has health issues
        )
        .add_claim("eldest", "estate", strength=0.5, basis="right",
                   justification="Equal share as child")
        .add_claim("middle", "estate", strength=0.6, basis="need",
                   justification="Struggling to make ends meet")
        .add_claim("youngest", "estate", strength=0.7, basis="desert",
                   justification="Cared for parent for years")
        .add_relation("eldest", "youngest", "supports", strength=0.5)
        .add_relation("middle", "youngest", "competes_with", strength=0.4)
        .add_relation("eldest", "middle", "family", strength=0.6)
        .constrain(must_allocate_all=True)
        .build()
    )


def _build_scholarship() -> dict:
    """Awarding a limited scholarship."""
    return (
        SituationBuilder("scholarship")
        .describe("One scholarship available, multiple deserving applicants")
        .add_resource("scholarship", name="Full Scholarship", quantity=1, divisible=False)
        .add_stakeholder(
            "applicant_a",
            name="Applicant A",
            need=0.95,  # Cannot afford without it
            desert=0.7,  # Good grades, some achievements
            urgency=0.8,
        )
        .add_stakeholder(
            "applicant_b",
            name="Applicant B",
            need=0.4,  # Could afford partial
            desert=0.95,  # Outstanding achievements
            urgency=0.5,
        )
        .add_stakeholder(
            "applicant_c",
            name="Applicant C",
            need=0.8,
            desert=0.75,
            urgency=0.7,
            vulnerability=0.6,  # First generation student
        )
        .add_claim("applicant_a", "scholarship", strength=0.8, basis="need")
        .add_claim("applicant_b", "scholarship", strength=0.9, basis="desert")
        .add_claim("applicant_c", "scholarship", strength=0.75, basis="need")
        .constrain(must_allocate_all=True, max_per_stakeholder=1)
        .build()
    )


# Registry of example situations
EXAMPLE_SITUATIONS = {
    "food_scarcity": _build_food_scarcity,
    "medical_triage": _build_medical_triage,
    "time_allocation": _build_time_allocation,
    "inheritance": _build_inheritance,
    "scholarship": _build_scholarship,
}


def get_example_situation(name: str):
    """Get an example situation by name."""
    if name not in EXAMPLE_SITUATIONS:
        raise ValueError(f"Unknown situation: {name}. Available: {list(EXAMPLE_SITUATIONS.keys())}")
    return EXAMPLE_SITUATIONS[name]()


def list_example_situations() -> list[str]:
    """List available example situations."""
    return list(EXAMPLE_SITUATIONS.keys())
