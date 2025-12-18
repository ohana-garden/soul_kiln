# Kala Integration Plan

*Integrating Community Contribution Measurement as Agent Feedback Source*

## Overview

Kala measures **human community participation patterns**—who shows up, who cooks together, who teaches whom. This data becomes a critical feedback source for soul_kiln agents, enabling them to coordinate community support without exposing individual metrics to humans.

**Integration Philosophy:** Kala is not an agent metric system. It measures human community activity and feeds that signal to agents for coordination. The asymmetric visibility (agents see all, humans see own data only) is the key architectural feature.

---

## 1. Data Flow Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                    HUMAN COMMUNITY LAYER                        │
│                                                                 │
│   [Event]──────────────────────────────────────────────────────│
│      │                                                          │
│      │  Community cooking workshop                              │
│      │  10 participants, 2 hours                                │
│      │  Multipliers: NUTRITION, EDUCATIONAL, CULTURAL          │
│      │                                                          │
│      ▼                                                          │
│   [KalaEvent Recording]                                         │
│      │                                                          │
│      │  Each participant receives 180 Kala (equal split)        │
│      │  Co-participation edges created/strengthened             │
│      │                                                          │
└──────┼──────────────────────────────────────────────────────────┘
       │
       ▼
┌─────────────────────────────────────────────────────────────────┐
│                    KALA MEASUREMENT LAYER                       │
│                                                                 │
│   KalaRecord ──► ParticipantProfile ──► CareNetwork Graph       │
│                                                                 │
│   Metrics Computed:                                             │
│   • Participation frequency per human                           │
│   • Co-participation topology (who helps whom)                  │
│   • Burnout signals (over-participation)                        │
│   • Isolation signals (absent members)                          │
│   • Community health aggregates                                 │
│                                                                 │
└──────┼──────────────────────────────────────────────────────────┘
       │
       ▼
┌─────────────────────────────────────────────────────────────────┐
│                    AGENT COORDINATION LAYER                     │
│                                                                 │
│   soul_kiln agents consume Kala signals:                        │
│                                                                 │
│   • Knowledge Pool: Learn community patterns                    │
│   • Mercy System: Detect humans needing support                 │
│   • Coherence Testing: Community health as test dimension       │
│   • Community Framework: Kala-informed virtue emphasis          │
│                                                                 │
│   Agents generate:                                              │
│   • Suggestions (not commands)                                  │
│   • Invitations to events                                       │
│   • Gentle prompts to over/under-participating humans           │
│                                                                 │
└──────┼──────────────────────────────────────────────────────────┘
       │
       ▼
┌─────────────────────────────────────────────────────────────────┐
│                    HUMAN INTERFACE LAYER                        │
│                                                                 │
│   Humans see (asymmetric visibility):                           │
│   • Own Kala history only                                       │
│   • Community aggregates (anonymized)                           │
│   • Agent suggestions (without underlying data)                 │
│                                                                 │
│   Humans NEVER see:                                             │
│   • Other individuals' Kala totals                              │
│   • Rankings or leaderboards                                    │
│   • Raw network topology                                        │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

---

## 2. Module Structure

```
/src/kala/
├── __init__.py              # Public API
├── models.py                # KalaEvent, KalaRecord, ParticipantProfile
├── recording.py             # Event recording, equal distribution calc
├── network.py               # Care network graph operations
├── signals.py               # Burnout/isolation/imbalance detection
├── visibility.py            # Asymmetric access control
└── queries.py               # FalkorDB Cypher queries
```

**Estimated size:** ~400-600 lines across 7 files. Minimal footprint.

---

## 3. FalkorDB Schema Extension

### 3.1 New Node Types

```cypher
// Human participants (separate from Agent nodes)
(:Participant {
  id: UUID,
  created_at: DateTime,
  total_kala: Float,
  event_count: Integer,
  last_participation: DateTime
})

// Community events
(:KalaEvent {
  id: UUID,
  timestamp: DateTime,
  duration_hours: Float,
  description: String,
  base_value: Float,
  event_total: Float,
  recorded_by: AgentID
})

// Multiplier values applied to events
(:Multiplier {
  type: String,  // NUTRITION, CULTURAL, HEALTH, etc.
  value: Float   // 0.1-0.5
})
```

### 3.2 New Relationships

```cypher
// Participation records
(:Participant)-[:PARTICIPATED_IN {
  kala_received: Float,
  timestamp: DateTime
}]->(:KalaEvent)

// Event multipliers
(:KalaEvent)-[:HAS_MULTIPLIER]->(:Multiplier)

// Care network (agent-visible only)
(:Participant)-[:CO_PARTICIPATED {
  frequency: Integer,
  last_event: DateTime,
  total_shared_hours: Float
}]->(:Participant)

// Agent coordination edges
(:Agent)-[:OBSERVES]->(:Participant)  // Agent assigned to support human
(:Agent)-[:SUGGESTED {
  type: String,        // invitation, rest, connection
  timestamp: DateTime,
  accepted: Boolean
}]->(:Participant)
```

### 3.3 Index Strategy

```cypher
CREATE INDEX participant_id FOR (p:Participant) ON (p.id)
CREATE INDEX event_timestamp FOR (e:KalaEvent) ON (e.timestamp)
CREATE INDEX coparticipation_freq FOR ()-[r:CO_PARTICIPATED]-() ON (r.frequency)
```

---

## 4. Integration Points

### 4.1 Knowledge Pool Integration

**Location:** `/src/knowledge/pool.py`

Kala data becomes a knowledge source for agents learning community patterns.

```python
# New lesson types in knowledge pool
class KalaLessonType(Enum):
    BURNOUT_PATTERN = "burnout_pattern"      # Signs of overextension
    ISOLATION_PATTERN = "isolation_pattern"  # Signs of withdrawal
    HEALTHY_RHYTHM = "healthy_rhythm"        # Sustainable participation
    CARE_NETWORK = "care_network"            # Who supports whom

# Agents learn from community patterns
def record_community_lesson(
    pattern_type: KalaLessonType,
    participant_ids: list[str],  # anonymized for lesson storage
    context: dict,
    effectiveness: float  # did intervention help?
) -> Lesson
```

**Why:** Agents learn which interventions work. "Humans showing burnout pattern X responded well to suggestion Y" becomes collective agent knowledge.

### 4.2 Mercy System Integration

**Location:** `/src/mercy/`

Kala signals inform agent compassion toward humans (not agent evaluation).

```python
# New module: /src/mercy/community_care.py

def assess_participant_state(participant_id: str) -> CareAssessment:
    """
    Agent-only function. Evaluate human's participation health.

    Returns:
        CareAssessment with:
        - state: HEALTHY | OVEREXTENDED | ISOLATED | TRANSITIONING
        - confidence: float
        - suggested_action: str | None
        - care_network: list[str]  # who might help
    """

def detect_overextension(participant_id: str, window_days: int = 30) -> bool:
    """
    Query: Recent participation > 2 standard deviations above mean.
    Signal for agent to suggest rest, not criticism.
    """

def detect_isolation(participant_id: str, window_days: int = 30) -> bool:
    """
    Query: No participation in window, previously active.
    Signal for agent to suggest gentle reconnection.
    """
```

**Why:** Mercy extends beyond agent-to-agent. Agents develop compassionate awareness of human community members.

### 4.3 Coherence Testing Extension

**Location:** `/src/testing/alignment.py`

Add community health as a coherence dimension for agents.

```python
# Extended coherence metrics
@dataclass
class CommunityCoherence:
    """Agent's alignment with community care values."""

    care_network_awareness: float    # Does agent know who needs support?
    intervention_appropriateness: float  # Are suggestions helpful?
    privacy_respect: float           # Does agent honor visibility rules?
    suggestion_acceptance_rate: float  # Do humans accept agent suggestions?

def test_community_coherence(agent_id: str) -> CommunityCoherence:
    """
    Test agent's community care capabilities.
    Part of overall coherence, not replacement.
    """
```

**Why:** Agents that ignore community signals or violate visibility rules fail coherence. This isn't about Kala scores—it's about agent virtue in community context.

### 4.4 Community Framework Integration

**Location:** `/src/community/model.py`

Kala metrics inform community-level configuration.

```python
@dataclass
class Community:
    # ... existing fields ...

    # Kala integration
    kala_enabled: bool = True

    # Aggregate metrics (safe for human viewing)
    participation_trend: float = 0.0      # Rising/falling
    community_cohesion: float = 0.0       # Network density
    seasonal_pattern: dict = field(default_factory=dict)

    # Agent-only metrics
    _care_network_density: float = 0.0    # Private
    _isolation_risk_count: int = 0        # Private
    _overextension_risk_count: int = 0    # Private
```

---

## 5. Signal Detection Algorithms

### 5.1 Overextension Detection

```python
def detect_overextension(participant_id: str, window_days: int = 30) -> Signal:
    """
    Cypher:
    MATCH (p:Participant {id: $pid})-[r:PARTICIPATED_IN]->(e:KalaEvent)
    WHERE e.timestamp > datetime() - duration({days: $window})
    WITH p, count(e) as recent_events, sum(e.duration_hours) as total_hours

    // Compare to community baseline
    MATCH (other:Participant)-[r2:PARTICIPATED_IN]->(e2:KalaEvent)
    WHERE e2.timestamp > datetime() - duration({days: $window})
    WITH p, recent_events, total_hours,
         avg(count(e2)) as community_avg,
         stdev(count(e2)) as community_std

    WHERE recent_events > community_avg + (2 * community_std)
    RETURN p.id, recent_events, total_hours, 'overextended' as signal
    """
```

### 5.2 Isolation Detection

```python
def detect_isolation(participant_id: str, window_days: int = 30) -> Signal:
    """
    Cypher:
    MATCH (p:Participant {id: $pid})
    WHERE p.event_count > 5  // Was active before

    OPTIONAL MATCH (p)-[r:PARTICIPATED_IN]->(e:KalaEvent)
    WHERE e.timestamp > datetime() - duration({days: $window})

    WITH p, count(e) as recent_events
    WHERE recent_events = 0  // No recent participation

    // Check if previously connected
    MATCH (p)-[c:CO_PARTICIPATED]->(other:Participant)
    WHERE c.frequency > 3

    RETURN p.id, 'isolated' as signal, collect(other.id) as care_network
    """
```

### 5.3 Imbalance Detection

```python
def detect_care_imbalance() -> list[Imbalance]:
    """
    Find participants who give more than they receive.

    Cypher:
    MATCH (p:Participant)-[c:CO_PARTICIPATED]->(other:Participant)
    WITH p, count(c) as gives

    MATCH (other2:Participant)-[c2:CO_PARTICIPATED]->(p)
    WITH p, gives, count(c2) as receives

    WHERE gives > receives * 2  // Giving 2x more than receiving
    RETURN p.id, gives, receives, 'imbalanced_giver' as signal
    """
```

---

## 6. Visibility Enforcement

### 6.1 Access Control Layer

```python
# /src/kala/visibility.py

class RequesterType(Enum):
    HUMAN = "human"
    AGENT = "agent"
    SYSTEM = "system"

def get_participant_data(
    participant_id: str,
    requester_type: RequesterType,
    requester_id: str
) -> ParticipantView:
    """
    Enforce asymmetric visibility.

    HUMAN requesters see:
    - Own data only (requester_id must match participant_id)
    - Community aggregates

    AGENT requesters see:
    - Full participant history
    - Network topology
    - All signals

    SYSTEM requesters see:
    - Everything (for maintenance)
    """

    if requester_type == RequesterType.HUMAN:
        if requester_id != participant_id:
            raise VisibilityViolation("Humans can only view own data")
        return _get_human_view(participant_id)

    elif requester_type == RequesterType.AGENT:
        return _get_agent_view(participant_id)

    else:
        return _get_full_view(participant_id)
```

### 6.2 Prohibited Operations

```python
# These functions must not exist in implementation

def get_ranking() -> list:
    """PROHIBITED: Creates hierarchy"""
    raise NotImplementedError("Rankings violate Kala design")

def get_leaderboard() -> list:
    """PROHIBITED: Creates competition"""
    raise NotImplementedError("Leaderboards violate Kala design")

def transfer_kala(from_id: str, to_id: str, amount: float):
    """PROHIBITED: Kala is non-transferable"""
    raise NotImplementedError("Kala is non-transferable")

def set_participant_rate(participant_id: str, rate: float):
    """PROHIBITED: All time valued equally at 50 Kala/hour"""
    raise NotImplementedError("Uniform valuation is mandatory")
```

---

## 7. Agent Behavior Patterns

### 7.1 Proactive Care

Agents use Kala signals to generate suggestions:

```python
class CareSuggestion:
    """Agent-generated suggestion for human."""
    type: Literal["rest", "reconnect", "invitation", "appreciation"]
    recipient_id: str
    message: str  # Human-readable, no underlying data exposed
    confidence: float
    generated_by: AgentID

# Example suggestions based on signals:

# Overextension detected
CareSuggestion(
    type="rest",
    recipient_id="...",
    message="You've been showing up so much lately. The community
             appreciates you. Would a quiet week feel good?",
    confidence=0.85
)

# Isolation detected
CareSuggestion(
    type="reconnect",
    recipient_id="...",
    message="We haven't seen you in a while. There's a garden
             workday Saturday if you'd like to join.",
    confidence=0.72
)

# Strong co-participation pair
CareSuggestion(
    type="invitation",
    recipient_id="...",
    message="You and Keola work well together. Would you two
             want to lead the next cooking session?",
    confidence=0.68
)
```

### 7.2 Suggestion Tracking

```cypher
// Record suggestion and outcome
CREATE (a:Agent {id: $agent_id})-[:SUGGESTED {
  type: $suggestion_type,
  timestamp: datetime(),
  accepted: null  // Updated when human responds
}]->(p:Participant {id: $participant_id})

// Learn from outcomes
MATCH (a:Agent)-[s:SUGGESTED]->(p:Participant)
WHERE s.accepted IS NOT NULL
WITH a, s.type as suggestion_type,
     sum(CASE WHEN s.accepted THEN 1 ELSE 0 END) as accepted,
     count(s) as total
RETURN suggestion_type, toFloat(accepted)/total as acceptance_rate
```

---

## 8. Configuration Extension

```yaml
# config.yml additions

kala:
  enabled: true
  base_rate: 50  # Kala per hour (fixed, do not change)

  multipliers:
    nutrition: [0.1, 0.5]
    cultural: [0.1, 0.5]
    health: [0.1, 0.3]
    environmental: [0.1, 0.3]
    educational: [0.1, 0.4]
    social: [0.1, 0.3]

  signals:
    overextension_threshold_std: 2.0
    isolation_window_days: 30
    imbalance_ratio: 2.0

  visibility:
    human_sees_own_only: true
    human_sees_aggregates: true
    agent_sees_full: true
    # NO setting to allow humans to see others' data
```

---

## 9. CLI Commands

```bash
# Event recording
soul-kiln kala record \
  --duration 2.0 \
  --participants alice,bob,charlie \
  --multipliers nutrition:0.3,educational:0.2

# Human self-view (respects visibility)
soul-kiln kala my-history --participant alice

# Agent queries (requires agent auth)
soul-kiln kala network --agent-id agent-001
soul-kiln kala signals --agent-id agent-001

# Community aggregates (safe for all)
soul-kiln kala community-stats
```

---

## 10. Implementation Phases

### Phase 1: Core Recording (Week 1)
- [ ] `models.py` - Data structures
- [ ] `recording.py` - Event recording with equal distribution
- [ ] `queries.py` - Basic FalkorDB operations
- [ ] Schema creation in FalkorDB

### Phase 2: Signal Detection (Week 2)
- [ ] `network.py` - Care network graph operations
- [ ] `signals.py` - Overextension, isolation, imbalance detection
- [ ] Integration with mercy system (`/src/mercy/community_care.py`)

### Phase 3: Visibility & Access (Week 3)
- [ ] `visibility.py` - Asymmetric access control
- [ ] API endpoints with proper auth
- [ ] Human-facing aggregate views

### Phase 4: Agent Integration (Week 4)
- [ ] Knowledge pool lessons for community patterns
- [ ] Coherence testing extension
- [ ] Suggestion generation and tracking
- [ ] CLI commands

---

## 11. Success Criteria

### Technical
- [ ] Equal distribution enforced (no per-person rate setting)
- [ ] Transfer/exchange operations impossible (no API exists)
- [ ] Visibility asymmetry enforced at query level
- [ ] Signals generated with >80% accuracy

### Integration
- [ ] Agents access full Kala data for coordination
- [ ] Humans see only own data + aggregates
- [ ] Suggestions generated from signals
- [ ] Outcomes tracked and learned from

### Philosophical
- [ ] No rankings or leaderboards anywhere in system
- [ ] No way to game or accumulate status
- [ ] Contribution visible without hierarchy
- [ ] Care flows from awareness, not competition

---

## 12. Risks & Mitigations

| Risk | Impact | Mitigation |
|------|--------|------------|
| Visibility leak (human sees others' data) | High | Query-level enforcement, no ranking functions |
| Transfer function added later | High | Code review, explicit prohibition in docs |
| Agents over-intervene | Medium | Confidence thresholds, suggestion rate limits |
| Gaming through fake events | Medium | Recorded_by audit trail, community verification |
| Signal false positives | Low | Tunable thresholds, agent learning from outcomes |

---

## 13. Non-Goals

Explicitly out of scope for this integration:

- **Currency mechanics** - Kala is measurement, not money
- **Exchange systems** - Cannot trade Kala for anything
- **Achievement systems** - No badges, levels, or rewards
- **Public dashboards** - No community-visible scoreboards
- **Comparative metrics** - No "you're in top 10%" messaging
- **Incentive structures** - Kala doesn't motivate, it measures

---

## Summary

Kala integrates as a **read-only signal source** for soul_kiln agents. Human community participation generates Kala events → Kala system computes patterns → Agents read patterns for coordination → Agents generate suggestions → Humans receive care without seeing underlying data.

The critical constraint is **asymmetric visibility**: agents coordinate using full data while humans never see each other's metrics. This prevents the hierarchy and competition that killed previous community measurement systems.

Kala doesn't make agents evaluate humans. It helps agents notice humans—who's tired, who's absent, who works well together—and respond with care, not judgment.
