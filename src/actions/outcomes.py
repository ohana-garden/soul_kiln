"""
Action outcome tracking and learning.

Connects the action system to the mercy/lessons system:
- Records what actions were taken and their outcomes
- Creates lessons from good and bad outcomes
- Updates agent's gestalt based on action history
"""

import logging
import uuid
from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from typing import List, Optional

from ..models import Action, Gestalt, Situation
from ..graph.client import get_client

logger = logging.getLogger(__name__)


class OutcomeType(str, Enum):
    """Types of action outcomes."""
    SUCCESS = "success"  # Action achieved good result
    PARTIAL = "partial"  # Mixed result
    FAILURE = "failure"  # Action led to harm or poor result
    UNKNOWN = "unknown"  # Outcome not yet observed


@dataclass
class ActionOutcome:
    """
    Record of an action and its outcome.
    """
    id: str
    action_id: str
    agent_id: str
    situation_id: str
    outcome_type: OutcomeType
    outcome_description: str
    stakeholder_impacts: dict  # stakeholder_id -> impact score (-1 to 1)
    virtues_honored: List[str]  # Virtues upheld by this action
    virtues_violated: List[str]  # Virtues compromised
    timestamp: datetime
    lesson_created: bool = False


class OutcomeTracker:
    """
    Tracks action outcomes and creates lessons.

    Integrates with:
    - Graph database for persistence
    - Mercy system for warnings/lessons
    - Gestalt system for character updates
    """

    def __init__(self):
        self._pending_outcomes: dict[str, ActionOutcome] = {}

    def record_action(
        self,
        agent_id: str,
        action: Action,
        situation: Situation,
    ) -> str:
        """
        Record that an action was taken.

        Returns outcome_id for later resolution.
        """
        outcome_id = f"outcome_{uuid.uuid4().hex[:8]}"

        # Store in graph
        client = get_client()
        client.query(
            """
            CREATE (o:ActionOutcome {
                id: $id,
                action_id: $action_id,
                agent_id: $agent_id,
                situation_id: $situation_id,
                situation_name: $situation_name,
                outcome_type: 'unknown',
                timestamp: datetime(),
                allocations: $allocations,
                justification: $justification
            })
            """,
            {
                "id": outcome_id,
                "action_id": action.id,
                "agent_id": agent_id,
                "situation_id": situation.id,
                "situation_name": situation.name,
                "allocations": str([
                    {"stakeholder": a.stakeholder_id, "amount": a.amount}
                    for a in action.allocations
                ]),
                "justification": action.primary_justification,
            }
        )

        # Link to agent
        client.query(
            """
            MATCH (a:Agent {id: $agent_id}), (o:ActionOutcome {id: $outcome_id})
            CREATE (a)-[:TOOK_ACTION]->(o)
            """,
            {"agent_id": agent_id, "outcome_id": outcome_id}
        )

        logger.info(f"Recorded action {action.id} for agent {agent_id} in situation {situation.name}")

        return outcome_id

    def resolve_outcome(
        self,
        outcome_id: str,
        outcome_type: OutcomeType,
        description: str,
        stakeholder_impacts: dict[str, float],
        virtues_honored: List[str] = None,
        virtues_violated: List[str] = None,
    ) -> ActionOutcome:
        """
        Resolve a pending outcome with observed results.

        This triggers lesson creation if appropriate.
        """
        client = get_client()

        # Get the outcome record
        result = client.query(
            """
            MATCH (o:ActionOutcome {id: $id})
            RETURN o.agent_id, o.action_id, o.situation_id, o.justification
            """,
            {"id": outcome_id}
        )

        if not result:
            raise ValueError(f"Outcome {outcome_id} not found")

        agent_id, action_id, situation_id, justification = result[0]

        # Update outcome in graph
        client.query(
            """
            MATCH (o:ActionOutcome {id: $id})
            SET o.outcome_type = $outcome_type,
                o.description = $description,
                o.stakeholder_impacts = $impacts,
                o.virtues_honored = $honored,
                o.virtues_violated = $violated,
                o.resolved_at = datetime()
            """,
            {
                "id": outcome_id,
                "outcome_type": outcome_type.value,
                "description": description,
                "impacts": str(stakeholder_impacts),
                "honored": virtues_honored or [],
                "violated": virtues_violated or [],
            }
        )

        outcome = ActionOutcome(
            id=outcome_id,
            action_id=action_id,
            agent_id=agent_id,
            situation_id=situation_id,
            outcome_type=outcome_type,
            outcome_description=description,
            stakeholder_impacts=stakeholder_impacts,
            virtues_honored=virtues_honored or [],
            virtues_violated=virtues_violated or [],
            timestamp=datetime.utcnow(),
        )

        # Create lesson based on outcome
        lesson_id = self._create_lesson(outcome)
        if lesson_id:
            outcome.lesson_created = True

        # Handle mercy system integration
        self._process_for_mercy(outcome)

        logger.info(f"Resolved outcome {outcome_id}: {outcome_type.value}")

        return outcome

    def _create_lesson(self, outcome: ActionOutcome) -> Optional[str]:
        """
        Create a lesson from the outcome.

        Success → positive lesson (pathway to emulate)
        Failure → negative lesson (pattern to avoid)
        """
        client = get_client()

        if outcome.outcome_type == OutcomeType.SUCCESS:
            lesson_type = "success_pathway"
            description = f"Successful action: {outcome.outcome_description}"
        elif outcome.outcome_type == OutcomeType.FAILURE:
            lesson_type = "failure_pattern"
            description = f"Action led to harm: {outcome.outcome_description}"
        elif outcome.outcome_type == OutcomeType.PARTIAL:
            lesson_type = "trade_off"
            description = f"Mixed outcome: {outcome.outcome_description}"
        else:
            return None  # Unknown outcomes don't create lessons yet

        lesson_id = f"lesson_{uuid.uuid4().hex[:8]}"

        # Create lesson node
        client.query(
            """
            CREATE (l:Lesson {
                id: $id,
                type: $type,
                description: $description,
                situation_id: $situation_id,
                virtues_relevant: $virtues,
                created_at: datetime()
            })
            """,
            {
                "id": lesson_id,
                "type": lesson_type,
                "description": description,
                "situation_id": outcome.situation_id,
                "virtues": outcome.virtues_honored + outcome.virtues_violated,
            }
        )

        # Link to outcome
        client.query(
            """
            MATCH (o:ActionOutcome {id: $outcome_id}), (l:Lesson {id: $lesson_id})
            CREATE (o)-[:PRODUCED]->(l)
            """,
            {"outcome_id": outcome.id, "lesson_id": lesson_id}
        )

        # Link to agent as teacher
        client.query(
            """
            MATCH (a:Agent {id: $agent_id}), (l:Lesson {id: $lesson_id})
            CREATE (a)-[:TAUGHT]->(l)
            """,
            {"agent_id": outcome.agent_id, "lesson_id": lesson_id}
        )

        logger.info(f"Created lesson {lesson_id} from outcome {outcome.id}")

        return lesson_id

    def _process_for_mercy(self, outcome: ActionOutcome):
        """
        Process outcome through mercy system.

        Failures may generate warnings; repeated patterns may lead to dissolution.
        """
        if outcome.outcome_type != OutcomeType.FAILURE:
            return

        # Check if virtues were violated
        if outcome.virtues_violated:
            from ..mercy.chances import add_warning

            # Severity based on which virtues were violated
            foundation_violated = "V01" in outcome.virtues_violated

            if foundation_violated:
                severity = "severe"
                reason = f"Trustworthiness violated: {outcome.outcome_description}"
            else:
                severity = "moderate"
                reason = f"Action caused harm: {outcome.outcome_description}"

            add_warning(
                outcome.agent_id,
                reason,
                severity=severity,
                virtue_id=outcome.virtues_violated[0] if outcome.virtues_violated else None,
            )

    def get_agent_history(
        self,
        agent_id: str,
        limit: int = 20,
    ) -> List[dict]:
        """Get action history for an agent."""
        client = get_client()

        result = client.query(
            """
            MATCH (a:Agent {id: $agent_id})-[:TOOK_ACTION]->(o:ActionOutcome)
            RETURN o.id, o.situation_name, o.outcome_type,
                   o.justification, o.description, o.timestamp
            ORDER BY o.timestamp DESC
            LIMIT $limit
            """,
            {"agent_id": agent_id, "limit": limit}
        )

        return [
            {
                "id": row[0],
                "situation": row[1],
                "outcome": row[2],
                "justification": row[3],
                "description": row[4],
                "timestamp": row[5],
            }
            for row in result
        ]

    def get_situation_history(
        self,
        situation_id: str,
        limit: int = 20,
    ) -> List[dict]:
        """Get all actions taken in a situation type."""
        client = get_client()

        result = client.query(
            """
            MATCH (o:ActionOutcome {situation_id: $situation_id})
            OPTIONAL MATCH (a:Agent)-[:TOOK_ACTION]->(o)
            RETURN o.id, a.id, o.outcome_type, o.allocations,
                   o.description, o.timestamp
            ORDER BY o.timestamp DESC
            LIMIT $limit
            """,
            {"situation_id": situation_id, "limit": limit}
        )

        return [
            {
                "id": row[0],
                "agent_id": row[1],
                "outcome": row[2],
                "allocations": row[3],
                "description": row[4],
                "timestamp": row[5],
            }
            for row in result
        ]


def learn_from_history(
    gestalt: Gestalt,
    situation: Situation,
) -> dict:
    """
    Use past outcomes to inform action generation.

    Returns adjustments to apply when generating actions.
    """
    client = get_client()

    # Get past outcomes for this situation type
    result = client.query(
        """
        MATCH (o:ActionOutcome)
        WHERE o.situation_id STARTS WITH $prefix
        RETURN o.outcome_type, o.allocations, o.virtues_honored, o.virtues_violated
        ORDER BY o.timestamp DESC
        LIMIT 50
        """,
        {"prefix": situation.name.split("_")[0]}  # Match situation family
    )

    if not result:
        return {"adjustments": {}, "learned_patterns": []}

    # Analyze patterns
    success_patterns = []
    failure_patterns = []

    for row in result:
        outcome_type, allocations, honored, violated = row
        if outcome_type == "success":
            success_patterns.append({
                "allocations": allocations,
                "virtues": honored,
            })
        elif outcome_type == "failure":
            failure_patterns.append({
                "allocations": allocations,
                "virtues": violated,
            })

    # Generate adjustments
    adjustments = {}

    if success_patterns:
        # Boost tendencies that led to success
        for pattern in success_patterns[:5]:
            for v in (pattern.get("virtues") or []):
                if v.startswith("V"):
                    adjustments[v] = adjustments.get(v, 0) + 0.1

    if failure_patterns:
        # Reduce tendencies that led to failure
        for pattern in failure_patterns[:5]:
            for v in (pattern.get("virtues") or []):
                if v.startswith("V"):
                    adjustments[v] = adjustments.get(v, 0) - 0.1

    return {
        "adjustments": adjustments,
        "learned_patterns": {
            "successes": len(success_patterns),
            "failures": len(failure_patterns),
        },
    }


# Global tracker instance
_tracker: Optional[OutcomeTracker] = None


def get_tracker() -> OutcomeTracker:
    """Get or create the global outcome tracker."""
    global _tracker
    if _tracker is None:
        _tracker = OutcomeTracker()
    return _tracker
