"""
Temporal fact management for personas.

Implements the temporal validity pattern from Graphiti/Zep where
facts have valid_at/invalid_at timestamps, enabling:
- "Who they were vs who they are" queries
- Fact expiration and supersession
- Evolution tracking
- Point-in-time persona reconstruction
"""

import logging
import uuid
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple

from ..models import TemporalFact

logger = logging.getLogger(__name__)


class TemporalFactStore:
    """
    In-memory store for temporal facts.

    In production, this would be backed by the graph database.
    For now, provides the interface and logic for temporal fact management.
    """

    def __init__(self):
        """Initialize empty fact store."""
        self._facts: Dict[str, TemporalFact] = {}
        self._by_subject: Dict[str, List[str]] = {}  # subject -> [fact_ids]
        self._by_predicate: Dict[str, List[str]] = {}  # predicate -> [fact_ids]

    def add_fact(self, fact: TemporalFact) -> str:
        """
        Add a fact to the store.

        Args:
            fact: The temporal fact to add

        Returns:
            The fact's ID
        """
        self._facts[fact.id] = fact

        # Index by subject
        if fact.subject not in self._by_subject:
            self._by_subject[fact.subject] = []
        self._by_subject[fact.subject].append(fact.id)

        # Index by predicate
        if fact.predicate not in self._by_predicate:
            self._by_predicate[fact.predicate] = []
        self._by_predicate[fact.predicate].append(fact.id)

        return fact.id

    def get_fact(self, fact_id: str) -> Optional[TemporalFact]:
        """Get a fact by ID."""
        return self._facts.get(fact_id)

    def get_facts_for_subject(
        self,
        subject: str,
        at_time: Optional[datetime] = None,
        include_expired: bool = False,
    ) -> List[TemporalFact]:
        """
        Get all facts about a subject.

        Args:
            subject: The entity to get facts about
            at_time: Point in time to query (default: now)
            include_expired: Whether to include expired facts

        Returns:
            List of facts, filtered by validity
        """
        fact_ids = self._by_subject.get(subject, [])
        facts = [self._facts[fid] for fid in fact_ids if fid in self._facts]

        if not include_expired:
            facts = [f for f in facts if f.is_valid(at_time)]

        return facts

    def get_facts_by_predicate(
        self,
        predicate: str,
        at_time: Optional[datetime] = None,
    ) -> List[TemporalFact]:
        """Get all facts with a given predicate."""
        fact_ids = self._by_predicate.get(predicate, [])
        facts = [self._facts[fid] for fid in fact_ids if fid in self._facts]
        return [f for f in facts if f.is_valid(at_time)]

    def query(
        self,
        subject: Optional[str] = None,
        predicate: Optional[str] = None,
        object_value: Optional[str] = None,
        at_time: Optional[datetime] = None,
    ) -> List[TemporalFact]:
        """
        Query facts by subject, predicate, and/or object.

        Args:
            subject: Filter by subject
            predicate: Filter by predicate
            object_value: Filter by object value
            at_time: Point in time to query

        Returns:
            Matching facts
        """
        # Start with all facts
        candidates = list(self._facts.values())

        # Filter by subject
        if subject:
            candidates = [f for f in candidates if f.subject == subject]

        # Filter by predicate
        if predicate:
            candidates = [f for f in candidates if f.predicate == predicate]

        # Filter by object
        if object_value:
            candidates = [f for f in candidates if f.object == object_value]

        # Filter by validity
        candidates = [f for f in candidates if f.is_valid(at_time)]

        return candidates

    def expire_fact(
        self,
        fact_id: str,
        at_time: Optional[datetime] = None,
    ) -> bool:
        """
        Mark a fact as expired.

        Args:
            fact_id: ID of fact to expire
            at_time: When it expired (default: now)

        Returns:
            True if fact was found and expired
        """
        if fact_id not in self._facts:
            return False

        fact = self._facts[fact_id]
        fact.invalid_at = at_time or datetime.utcnow()
        return True

    def supersede_fact(
        self,
        old_fact_id: str,
        new_fact: TemporalFact,
    ) -> str:
        """
        Replace an old fact with a new one.

        The old fact is expired and linked to the new fact.

        Args:
            old_fact_id: ID of fact being replaced
            new_fact: The replacement fact

        Returns:
            ID of the new fact
        """
        # Expire old fact
        if old_fact_id in self._facts:
            old_fact = self._facts[old_fact_id]
            old_fact.invalid_at = new_fact.valid_at
            old_fact.superseded_by = new_fact.id
            new_fact.supersedes = old_fact_id

        # Add new fact
        return self.add_fact(new_fact)

    def get_fact_history(
        self,
        subject: str,
        predicate: str,
    ) -> List[TemporalFact]:
        """
        Get the history of a fact (all versions over time).

        Args:
            subject: The entity
            predicate: The relationship type

        Returns:
            List of facts ordered by valid_at (oldest first)
        """
        all_facts = self.get_facts_for_subject(subject, include_expired=True)
        relevant = [f for f in all_facts if f.predicate == predicate]
        return sorted(relevant, key=lambda f: f.valid_at)

    def get_persona_snapshot(
        self,
        agent_id: str,
        at_time: Optional[datetime] = None,
    ) -> Dict[str, str]:
        """
        Get a persona snapshot at a point in time.

        Returns dict of predicate -> object for all valid facts
        about the agent at that time.
        """
        facts = self.get_facts_for_subject(agent_id, at_time=at_time)

        # For each predicate, take the most recent valid fact
        snapshot = {}
        for fact in facts:
            key = fact.predicate
            if key not in snapshot:
                snapshot[key] = fact.object

        return snapshot


# Global store instance
_store: Optional[TemporalFactStore] = None


def get_store() -> TemporalFactStore:
    """Get or create the global fact store."""
    global _store
    if _store is None:
        _store = TemporalFactStore()
    return _store


def create_fact(
    subject: str,
    predicate: str,
    object_value: str,
    evidence_type: str = "inference",
    evidence_id: Optional[str] = None,
    confidence: float = 0.8,
) -> TemporalFact:
    """
    Create and store a new temporal fact.

    Args:
        subject: Entity the fact is about (usually agent_id)
        predicate: Relationship type (e.g., "has_value", "prefers")
        object_value: The value or target
        evidence_type: Source type (interaction, lesson, declaration, inference)
        evidence_id: Link to source evidence
        confidence: How confident we are in this fact

    Returns:
        The created fact

    Example:
        >>> fact = create_fact(
        ...     "agent_001",
        ...     "has_value",
        ...     "justice",
        ...     evidence_type="lesson",
        ...     evidence_id="lesson_123",
        ... )
    """
    fact = TemporalFact(
        id=f"fact_{uuid.uuid4().hex[:12]}",
        subject=subject,
        predicate=predicate,
        object=object_value,
        valid_at=datetime.utcnow(),
        evidence_type=evidence_type,
        evidence_id=evidence_id,
        confidence=confidence,
    )

    store = get_store()
    store.add_fact(fact)

    return fact


def update_fact(
    subject: str,
    predicate: str,
    new_value: str,
    evidence_type: str = "inference",
    evidence_id: Optional[str] = None,
    confidence: float = 0.8,
) -> Tuple[Optional[TemporalFact], TemporalFact]:
    """
    Update a fact by superseding the old value.

    Args:
        subject: Entity the fact is about
        predicate: Relationship type
        new_value: The new value
        evidence_type: Source type
        evidence_id: Link to source evidence
        confidence: Confidence in new fact

    Returns:
        Tuple of (old_fact or None, new_fact)

    Example:
        >>> old, new = update_fact("agent_001", "prefers", "equality_over_desert")
    """
    store = get_store()

    # Find existing fact
    existing = store.query(subject=subject, predicate=predicate)
    old_fact = existing[0] if existing else None

    # Create new fact
    new_fact = TemporalFact(
        id=f"fact_{uuid.uuid4().hex[:12]}",
        subject=subject,
        predicate=predicate,
        object=new_value,
        valid_at=datetime.utcnow(),
        evidence_type=evidence_type,
        evidence_id=evidence_id,
        confidence=confidence,
    )

    if old_fact:
        store.supersede_fact(old_fact.id, new_fact)
    else:
        store.add_fact(new_fact)

    return old_fact, new_fact


def expire_fact(
    subject: str,
    predicate: str,
) -> bool:
    """
    Expire a fact (mark it as no longer valid).

    Args:
        subject: Entity the fact is about
        predicate: Relationship type to expire

    Returns:
        True if a fact was found and expired
    """
    store = get_store()
    existing = store.query(subject=subject, predicate=predicate)

    if existing:
        return store.expire_fact(existing[0].id)
    return False


def get_fact_at_time(
    subject: str,
    predicate: str,
    at_time: datetime,
) -> Optional[TemporalFact]:
    """
    Get what a fact's value was at a specific point in time.

    Args:
        subject: Entity to query
        predicate: Relationship type
        at_time: Point in time

    Returns:
        The fact that was valid at that time, or None
    """
    store = get_store()

    # Get full history
    history = store.get_fact_history(subject, predicate)

    # Find the fact that was valid at the given time
    for fact in reversed(history):  # Start from most recent
        if fact.is_valid(at_time):
            return fact

    return None


def compare_persona_over_time(
    agent_id: str,
    time_a: datetime,
    time_b: datetime,
) -> Dict[str, Tuple[Optional[str], Optional[str]]]:
    """
    Compare an agent's persona at two points in time.

    Args:
        agent_id: Agent to compare
        time_a: First point in time
        time_b: Second point in time (usually later)

    Returns:
        Dict of predicate -> (value_at_a, value_at_b)
        Only includes predicates where values differ
    """
    store = get_store()

    snapshot_a = store.get_persona_snapshot(agent_id, time_a)
    snapshot_b = store.get_persona_snapshot(agent_id, time_b)

    # Find all predicates
    all_predicates = set(snapshot_a.keys()) | set(snapshot_b.keys())

    # Compare
    changes = {}
    for pred in all_predicates:
        val_a = snapshot_a.get(pred)
        val_b = snapshot_b.get(pred)
        if val_a != val_b:
            changes[pred] = (val_a, val_b)

    return changes


def record_value_change(
    agent_id: str,
    virtue_id: str,
    old_activation: float,
    new_activation: float,
    lesson_id: Optional[str] = None,
) -> TemporalFact:
    """
    Record that an agent's virtue activation changed.

    This is a convenience function for the common case of
    tracking value changes from lessons/experiences.

    Args:
        agent_id: The agent
        virtue_id: Which virtue changed
        old_activation: Previous activation level
        new_activation: New activation level
        lesson_id: Optional lesson that caused the change

    Returns:
        The fact recording this change
    """
    predicate = f"virtue_activation:{virtue_id}"

    _, new_fact = update_fact(
        subject=agent_id,
        predicate=predicate,
        new_value=str(new_activation),
        evidence_type="lesson" if lesson_id else "inference",
        evidence_id=lesson_id,
        confidence=0.9,
    )

    logger.info(
        f"Recorded value change for {agent_id}: "
        f"{virtue_id} {old_activation:.2f} -> {new_activation:.2f}"
    )

    return new_fact


def record_tendency_change(
    agent_id: str,
    tendency_name: str,
    new_strength: float,
    evidence_id: Optional[str] = None,
) -> TemporalFact:
    """
    Record that an agent's tendency changed.

    Args:
        agent_id: The agent
        tendency_name: Which tendency changed
        new_strength: New tendency strength
        evidence_id: Optional evidence for the change

    Returns:
        The fact recording this change
    """
    predicate = f"tendency:{tendency_name}"

    _, new_fact = update_fact(
        subject=agent_id,
        predicate=predicate,
        new_value=str(new_strength),
        evidence_type="lesson" if evidence_id else "inference",
        evidence_id=evidence_id,
        confidence=0.85,
    )

    return new_fact
