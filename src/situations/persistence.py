"""
Situation persistence in the graph database.

Stores situations as graph structures:
- Stakeholder nodes
- Resource nodes
- Claim edges
- Relationship edges

This enables:
- Querying past situations
- Learning patterns across situations
- Graph-based reasoning about moral contexts
"""

import logging
from typing import List, Optional

from ..graph.client import get_client
from ..graph.safe_parse import safe_parse_dict, serialize_for_storage
from ..models import (
    Situation,
    Stakeholder,
    Resource,
    Claim,
    StakeholderRelation,
)

logger = logging.getLogger(__name__)


def save_situation(situation: Situation) -> str:
    """
    Save a situation to the graph database.

    Creates:
    - Situation node
    - Stakeholder nodes linked to situation
    - Resource nodes linked to situation
    - Claim edges from stakeholders to resources
    - Relationship edges between stakeholders

    Returns the situation ID.
    """
    client = get_client()

    # Create situation node
    client.query(
        """
        MERGE (s:Situation {id: $id})
        SET s.name = $name,
            s.description = $description,
            s.constraints = $constraints,
            s.created_at = datetime()
        """,
        {
            "id": situation.id,
            "name": situation.name,
            "description": situation.description,
            "constraints": serialize_for_storage(situation.constraints),
        }
    )

    # Create stakeholder nodes
    for sh in situation.stakeholders:
        client.query(
            """
            MERGE (sh:Stakeholder {id: $id})
            SET sh.name = $name,
                sh.need = $need,
                sh.desert = $desert,
                sh.urgency = $urgency,
                sh.vulnerability = $vulnerability
            WITH sh
            MATCH (s:Situation {id: $situation_id})
            MERGE (s)-[:HAS_STAKEHOLDER]->(sh)
            """,
            {
                "id": f"{situation.id}_{sh.id}",
                "name": sh.name,
                "need": sh.need,
                "desert": sh.desert,
                "urgency": sh.urgency,
                "vulnerability": sh.vulnerability,
                "situation_id": situation.id,
            }
        )

    # Create resource nodes
    for res in situation.resources:
        client.query(
            """
            MERGE (r:Resource {id: $id})
            SET r.name = $name,
                r.quantity = $quantity,
                r.divisible = $divisible
            WITH r
            MATCH (s:Situation {id: $situation_id})
            MERGE (s)-[:HAS_RESOURCE]->(r)
            """,
            {
                "id": f"{situation.id}_{res.id}",
                "name": res.name,
                "quantity": res.quantity,
                "divisible": res.divisible,
                "situation_id": situation.id,
            }
        )

    # Create claims (edges from stakeholder to resource)
    for claim in situation.claims:
        client.query(
            """
            MATCH (sh:Stakeholder {id: $sh_id})
            MATCH (r:Resource {id: $r_id})
            MERGE (sh)-[c:CLAIMS]->(r)
            SET c.strength = $strength,
                c.basis = $basis,
                c.justification = $justification
            """,
            {
                "sh_id": f"{situation.id}_{claim.stakeholder_id}",
                "r_id": f"{situation.id}_{claim.resource_id}",
                "strength": claim.strength,
                "basis": claim.basis,
                "justification": claim.justification,
            }
        )

    # Create stakeholder relationships
    for rel in situation.relations:
        client.query(
            """
            MATCH (sh1:Stakeholder {id: $source_id})
            MATCH (sh2:Stakeholder {id: $target_id})
            MERGE (sh1)-[r:RELATES_TO]->(sh2)
            SET r.type = $rel_type,
                r.strength = $strength
            """,
            {
                "source_id": f"{situation.id}_{rel.source_id}",
                "target_id": f"{situation.id}_{rel.target_id}",
                "rel_type": rel.relation_type,
                "strength": rel.strength,
            }
        )

    logger.info(f"Saved situation {situation.id} ({situation.name}) to graph")

    return situation.id


def load_situation(situation_id: str) -> Optional[Situation]:
    """
    Load a situation from the graph database.
    """
    client = get_client()

    # Get situation node
    result = client.query(
        """
        MATCH (s:Situation {id: $id})
        RETURN s.name, s.description, s.constraints
        """,
        {"id": situation_id}
    )

    if not result:
        return None

    name, description, constraints_str = result[0]

    # Parse constraints safely (no eval)
    constraints = safe_parse_dict(constraints_str)

    # Get stakeholders
    sh_result = client.query(
        """
        MATCH (s:Situation {id: $id})-[:HAS_STAKEHOLDER]->(sh:Stakeholder)
        RETURN sh.id, sh.name, sh.need, sh.desert, sh.urgency, sh.vulnerability
        """,
        {"id": situation_id}
    )

    stakeholders = []
    for row in sh_result:
        full_id, sh_name, need, desert, urgency, vulnerability = row
        # Extract original ID (remove situation prefix)
        original_id = full_id.replace(f"{situation_id}_", "")
        stakeholders.append(Stakeholder(
            id=original_id,
            name=sh_name,
            need=need or 0.5,
            desert=desert or 0.5,
            urgency=urgency or 0.5,
            vulnerability=vulnerability or 0.0,
        ))

    # Get resources
    res_result = client.query(
        """
        MATCH (s:Situation {id: $id})-[:HAS_RESOURCE]->(r:Resource)
        RETURN r.id, r.name, r.quantity, r.divisible
        """,
        {"id": situation_id}
    )

    resources = []
    for row in res_result:
        full_id, res_name, quantity, divisible = row
        original_id = full_id.replace(f"{situation_id}_", "")
        resources.append(Resource(
            id=original_id,
            name=res_name,
            quantity=quantity or 1.0,
            divisible=divisible if divisible is not None else True,
        ))

    # Get claims
    claim_result = client.query(
        """
        MATCH (s:Situation {id: $id})-[:HAS_STAKEHOLDER]->(sh:Stakeholder)
              -[c:CLAIMS]->(r:Resource)
        RETURN sh.id, r.id, c.strength, c.basis, c.justification
        """,
        {"id": situation_id}
    )

    claims = []
    for row in claim_result:
        sh_full_id, r_full_id, strength, basis, justification = row
        sh_id = sh_full_id.replace(f"{situation_id}_", "")
        r_id = r_full_id.replace(f"{situation_id}_", "")
        claims.append(Claim(
            stakeholder_id=sh_id,
            resource_id=r_id,
            strength=strength or 0.5,
            basis=basis or "need",
            justification=justification,
        ))

    # Get relationships
    rel_result = client.query(
        """
        MATCH (s:Situation {id: $id})-[:HAS_STAKEHOLDER]->(sh1:Stakeholder)
              -[r:RELATES_TO]->(sh2:Stakeholder)
        RETURN sh1.id, sh2.id, r.type, r.strength
        """,
        {"id": situation_id}
    )

    relations = []
    for row in rel_result:
        source_full, target_full, rel_type, strength = row
        source_id = source_full.replace(f"{situation_id}_", "")
        target_id = target_full.replace(f"{situation_id}_", "")
        relations.append(StakeholderRelation(
            source_id=source_id,
            target_id=target_id,
            relation_type=rel_type or "supports",
            strength=strength or 0.5,
        ))

    return Situation(
        id=situation_id,
        name=name,
        description=description,
        stakeholders=stakeholders,
        resources=resources,
        claims=claims,
        relations=relations,
        constraints=constraints,
    )


def list_situations(limit: int = 20) -> List[dict]:
    """List all saved situations."""
    client = get_client()

    result = client.query(
        """
        MATCH (s:Situation)
        OPTIONAL MATCH (s)-[:HAS_STAKEHOLDER]->(sh)
        OPTIONAL MATCH (s)-[:HAS_RESOURCE]->(r)
        RETURN s.id, s.name, s.description, count(DISTINCT sh), count(DISTINCT r)
        ORDER BY s.created_at DESC
        LIMIT $limit
        """,
        {"limit": limit}
    )

    return [
        {
            "id": row[0],
            "name": row[1],
            "description": row[2],
            "stakeholder_count": row[3],
            "resource_count": row[4],
        }
        for row in result
    ]


def find_similar_situations(
    situation: Situation,
    limit: int = 5,
) -> List[dict]:
    """
    Find situations similar to the given one.

    Similarity based on:
    - Number of stakeholders
    - Resource divisibility
    - Claim basis distribution
    """
    client = get_client()

    # Count claim bases
    need_claims = sum(1 for c in situation.claims if c.basis == "need")
    desert_claims = sum(1 for c in situation.claims if c.basis == "desert")

    result = client.query(
        """
        MATCH (s:Situation)
        WHERE s.id <> $current_id
        OPTIONAL MATCH (s)-[:HAS_STAKEHOLDER]->(sh)
        OPTIONAL MATCH (s)-[:HAS_RESOURCE]->(r)
        OPTIONAL MATCH (sh)-[c:CLAIMS]->(r)
        WITH s, count(DISTINCT sh) as sh_count, count(DISTINCT r) as r_count,
             sum(CASE WHEN c.basis = 'need' THEN 1 ELSE 0 END) as need_count,
             sum(CASE WHEN c.basis = 'desert' THEN 1 ELSE 0 END) as desert_count
        WITH s, sh_count, r_count, need_count, desert_count,
             abs(sh_count - $target_sh) + abs(need_count - $target_need) as diff
        ORDER BY diff ASC
        LIMIT $limit
        RETURN s.id, s.name, s.description, sh_count, r_count, diff
        """,
        {
            "current_id": situation.id,
            "target_sh": len(situation.stakeholders),
            "target_need": need_claims,
            "limit": limit,
        }
    )

    return [
        {
            "id": row[0],
            "name": row[1],
            "description": row[2],
            "stakeholder_count": row[3],
            "resource_count": row[4],
            "similarity_score": 1.0 / (1.0 + row[5]),
        }
        for row in result
    ]


def delete_situation(situation_id: str) -> bool:
    """Delete a situation and all its components from the graph."""
    client = get_client()

    # Delete claims first
    client.query(
        """
        MATCH (s:Situation {id: $id})-[:HAS_STAKEHOLDER]->(sh)-[c:CLAIMS]->()
        DELETE c
        """,
        {"id": situation_id}
    )

    # Delete relationships
    client.query(
        """
        MATCH (s:Situation {id: $id})-[:HAS_STAKEHOLDER]->(sh)-[r:RELATES_TO]->()
        DELETE r
        """,
        {"id": situation_id}
    )

    # Delete stakeholders
    client.query(
        """
        MATCH (s:Situation {id: $id})-[h:HAS_STAKEHOLDER]->(sh)
        DELETE h, sh
        """,
        {"id": situation_id}
    )

    # Delete resources
    client.query(
        """
        MATCH (s:Situation {id: $id})-[h:HAS_RESOURCE]->(r)
        DELETE h, r
        """,
        {"id": situation_id}
    )

    # Delete situation
    result = client.query(
        """
        MATCH (s:Situation {id: $id})
        DELETE s
        RETURN count(s)
        """,
        {"id": situation_id}
    )

    deleted = result[0][0] > 0 if result else False
    if deleted:
        logger.info(f"Deleted situation {situation_id}")

    return deleted
