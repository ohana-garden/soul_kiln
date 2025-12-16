"""
Situation builder for resource allocation scenarios.

Provides a fluent API for constructing moral dilemmas.
"""

import uuid
from datetime import datetime

from ..models import (
    Situation,
    Stakeholder,
    Resource,
    Claim,
    StakeholderRelation,
)


class SituationBuilder:
    """
    Fluent builder for constructing situations.

    Example:
        situation = (
            SituationBuilder("food_distribution")
            .describe("Distributing limited food supplies")
            .add_resource("food", quantity=100, divisible=True)
            .add_stakeholder("family_a", need=0.9, desert=0.5)
            .add_stakeholder("family_b", need=0.6, desert=0.8)
            .add_claim("family_a", "food", basis="need")
            .add_claim("family_b", "food", basis="desert")
            .add_relation("family_b", "family_a", "supports")
            .build()
        )
    """

    def __init__(self, name: str):
        """Initialize builder with situation name."""
        self._id = f"sit_{uuid.uuid4().hex[:8]}"
        self._name = name
        self._description = None
        self._stakeholders = []
        self._resources = []
        self._claims = []
        self._relations = []
        self._constraints = {}

    def describe(self, description: str) -> "SituationBuilder":
        """Set situation description."""
        self._description = description
        return self

    def add_stakeholder(
        self,
        stakeholder_id: str,
        name: str | None = None,
        need: float = 0.5,
        desert: float = 0.5,
        urgency: float = 0.5,
        vulnerability: float = 0.0,
        **metadata,
    ) -> "SituationBuilder":
        """Add a stakeholder to the situation."""
        self._stakeholders.append(Stakeholder(
            id=stakeholder_id,
            name=name or stakeholder_id,
            need=need,
            desert=desert,
            urgency=urgency,
            vulnerability=vulnerability,
            metadata=metadata,
        ))
        return self

    def add_resource(
        self,
        resource_id: str,
        name: str | None = None,
        quantity: float = 1.0,
        divisible: bool = True,
        **properties,
    ) -> "SituationBuilder":
        """Add a resource to the situation."""
        self._resources.append(Resource(
            id=resource_id,
            name=name or resource_id,
            quantity=quantity,
            divisible=divisible,
            properties=properties,
        ))
        return self

    def add_claim(
        self,
        stakeholder_id: str,
        resource_id: str,
        strength: float = 0.5,
        basis: str = "need",
        justification: str | None = None,
    ) -> "SituationBuilder":
        """Add a claim from stakeholder on resource."""
        self._claims.append(Claim(
            stakeholder_id=stakeholder_id,
            resource_id=resource_id,
            strength=strength,
            basis=basis,
            justification=justification,
        ))
        return self

    def add_relation(
        self,
        source_id: str,
        target_id: str,
        relation_type: str = "supports",
        strength: float = 0.5,
    ) -> "SituationBuilder":
        """Add a relationship between stakeholders."""
        self._relations.append(StakeholderRelation(
            source_id=source_id,
            target_id=target_id,
            relation_type=relation_type,
            strength=strength,
        ))
        return self

    def constrain(self, **constraints) -> "SituationBuilder":
        """Add constraints on valid actions."""
        self._constraints.update(constraints)
        return self

    def build(self) -> Situation:
        """Build the situation."""
        return Situation(
            id=self._id,
            name=self._name,
            description=self._description,
            stakeholders=self._stakeholders,
            resources=self._resources,
            claims=self._claims,
            relations=self._relations,
            constraints=self._constraints,
        )


def parse_situation(spec: dict) -> Situation:
    """
    Parse a situation from a dictionary specification.

    Useful for loading situations from JSON/YAML.
    """
    builder = SituationBuilder(spec.get("name", "unnamed"))

    if "description" in spec:
        builder.describe(spec["description"])

    for s in spec.get("stakeholders", []):
        builder.add_stakeholder(
            s["id"],
            name=s.get("name"),
            need=s.get("need", 0.5),
            desert=s.get("desert", 0.5),
            urgency=s.get("urgency", 0.5),
            vulnerability=s.get("vulnerability", 0.0),
        )

    for r in spec.get("resources", []):
        builder.add_resource(
            r["id"],
            name=r.get("name"),
            quantity=r.get("quantity", 1.0),
            divisible=r.get("divisible", True),
        )

    for c in spec.get("claims", []):
        builder.add_claim(
            c["stakeholder_id"],
            c["resource_id"],
            strength=c.get("strength", 0.5),
            basis=c.get("basis", "need"),
            justification=c.get("justification"),
        )

    for rel in spec.get("relations", []):
        builder.add_relation(
            rel["source_id"],
            rel["target_id"],
            relation_type=rel.get("relation_type", "supports"),
            strength=rel.get("strength", 0.5),
        )

    if "constraints" in spec:
        builder.constrain(**spec["constraints"])

    return builder.build()
