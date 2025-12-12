# Gap Analysis: Soul Kiln ↔ Student Ambassador Platform

## Overview

This document maps capabilities between the existing soul_kiln virtue basin system and the requirements of the Student Ambassador Platform (as one example application).

---

## Soul Kiln: What Exists

### Graph Layer
| Component | Status | Description |
|-----------|--------|-------------|
| VirtueAnchor | ✓ | 19 virtue basins of attraction |
| Agent | ✓ | Entities that evolve through the kiln |
| Concept | ✓ | Ideas that connect to virtues |
| Trajectory | ✓ | Paths agents take toward virtues |
| Lesson | ✓ | Learnings preserved from dissolved agents |
| Pathway | ✓ | Knowledge routes between concepts |
| Warning | ✓ | Mercy system tracking |

### Dynamics
| Function | Status | Description |
|----------|--------|-------------|
| spawn | ✓ | Create new agents |
| dissolve | ✓ | Remove agents (with learning preservation) |
| spread | ✓ | Activation spreads through graph |
| decay | ✓ | Temporal decay of unused connections |
| heal | ✓ | Repair dead zones |
| perturb | ✓ | Random exploration |
| test_coherence | ✓ | Two-tier virtue evaluation |

### Mercy System
| Component | Status | Description |
|-----------|--------|-------------|
| judgment | ✓ | Empathetic failure evaluation |
| harm | ✓ | Trust violation detection |
| chances | ✓ | Warning system with expiry |
| lessons | ✓ | Learning extraction from failures |

### Evolution
| Component | Status | Description |
|-----------|--------|-------------|
| kiln loop | ✓ | Multi-generation evolution |
| selection | ✓ | Survivor selection strategies |
| coherence metrics | ✓ | Capture rate, coverage, dominance |

---

## Student Ambassador: What's Needed

### Multi-Agent Architecture
| Requirement | Soul Kiln Has | Gap |
|-------------|---------------|-----|
| Personal Ambassador per user | Agent node type | Need: 1:1 user binding, persistent identity |
| Specialist agents (Scout, Strategist, etc.) | Agent with types | Need: Agent specialization, tool binding |
| Agent-to-Agent communication | - | **GAP**: A2A protocol |
| Hierarchical delegation | - | **GAP**: Task delegation patterns |

### Knowledge Architecture
| Requirement | Soul Kiln Has | Gap |
|-------------|---------------|-----|
| Personal graph (on-device) | - | **GAP**: Sparksee Mobile integration |
| Commons graph (shared) | FalkorDB | Partial: needs anonymization layer |
| Temporal facts | - | **GAP**: Graphiti integration |
| Episodic memory | Trajectory | Partial: needs conversation threading |

### External Integrations
| Requirement | Soul Kiln Has | Gap |
|-------------|---------------|-----|
| Voice (Hume EVI) | - | **GAP**: Voice channel |
| SMS/RCS (Twilio) | - | **GAP**: Messaging channel |
| Banking (Greenlight) | - | **GAP**: Financial integration |
| Image gen (Nanobanana) | - | **GAP**: Visual generation |

### Domain Logic
| Requirement | Soul Kiln Has | Gap |
|-------------|---------------|-----|
| Scholarship matching | - | **GAP**: Domain-specific |
| Aid calculation | - | **GAP**: Domain-specific |
| Appeal drafting | - | **GAP**: Domain-specific |
| Deadline tracking | - | **GAP**: Domain-specific |

### Proactive Behavior
| Requirement | Soul Kiln Has | Gap |
|-------------|---------------|-----|
| Trigger → action | - | **GAP**: Event system |
| Scheduled checks | - | **GAP**: Cron/scheduler |
| User state monitoring | - | **GAP**: User session tracking |

---

## Alignment Analysis

### Strong Alignment (soul_kiln provides foundation)

**Virtue-Based Agents**
- Ambassador agents need trustworthiness, service, wisdom → soul_kiln's 19 virtues
- Coherence testing validates agent "character" → kiln loop
- Failed agents dissolve gracefully → mercy system

**Collective Learning**
- Commons graph shares patterns → soul_kiln's shared graph
- Lessons preserved from failures → Lesson nodes
- Pathways between concepts → Pathway nodes

**Evolutionary Improvement**
- Agents improve over time → kiln generations
- Bad patterns removed → dissolution with learning
- Good patterns reinforced → Hebbian learning, selection

### Partial Alignment (needs extension)

**Memory**
- soul_kiln has Trajectory → needs conversation episodes
- soul_kiln has Lesson → needs temporal fact tracking
- soul_kiln has Warning → needs user-specific context

**Agent Identity**
- soul_kiln has Agent type → needs user binding
- soul_kiln has agent spawning → needs persistent identity
- soul_kiln has coherence → needs domain-specific metrics

### No Alignment (new capabilities needed)

**Channels**: Voice, SMS, Web, Email
**Integrations**: Greenlight, Hume, Nanobanana, Twilio
**Domain**: Scholarships, FAFSA, appeals, deadlines
**Privacy**: On-device graph, anonymization pipeline

---

## Integration Architecture (Proposed)

```
┌─────────────────────────────────────────────────────────────────────┐
│                      APPLICATION LAYER                              │
│  (Student Ambassador, or any domain)                                │
│                                                                     │
│  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐              │
│  │  Voice   │ │   SMS    │ │   Web    │ │  Domain  │              │
│  │ Channel  │ │ Channel  │ │ Channel  │ │  Logic   │              │
│  └────┬─────┘ └────┬─────┘ └────┬─────┘ └────┬─────┘              │
│       └────────────┴────────────┴────────────┘                     │
│                            │                                        │
│                    ┌───────▼───────┐                               │
│                    │  Application  │                               │
│                    │   Adapter     │                               │
│                    └───────┬───────┘                               │
└────────────────────────────┼────────────────────────────────────────┘
                             │
┌────────────────────────────┼────────────────────────────────────────┐
│                     SOUL KILN CORE                                  │
│                            │                                        │
│  ┌─────────────────────────▼─────────────────────────────────────┐ │
│  │                    Agent Manager                               │ │
│  │  - Spawn/dissolve agents                                       │ │
│  │  - Bind agents to users/domains                                │ │
│  │  - Coordinate A2A communication                                │ │
│  └────────────────────────┬──────────────────────────────────────┘ │
│                           │                                         │
│  ┌────────────┐  ┌────────▼────────┐  ┌──────────────┐            │
│  │   Kiln     │  │    Virtue       │  │    Mercy     │            │
│  │   Loop     │  │    Graph        │  │    System    │            │
│  │            │  │                 │  │              │            │
│  │ - Evolve   │  │ - 19 virtues    │  │ - Judgment   │            │
│  │ - Select   │  │ - Activation    │  │ - Warnings   │            │
│  │ - Test     │  │ - Hebbian       │  │ - Lessons    │            │
│  └────────────┘  └─────────────────┘  └──────────────┘            │
│                                                                     │
│  ┌─────────────────────────────────────────────────────────────┐   │
│  │                    Knowledge Layer                           │   │
│  │  - Pathways (shared learnings)                               │   │
│  │  - Lessons (preserved from failures)                         │   │
│  │  - Concepts (domain-agnostic ideas)                          │   │
│  └─────────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────────┘
```

---

## Recommended Build Sequence

### Phase 1A: Core Extensions (enable applications)
1. **Agent Manager** - User binding, persistent identity, A2A stub
2. **Event System** - Trigger → action patterns
3. **Memory Adapter** - Graphiti integration for temporal facts
4. **Anonymization Layer** - Privacy-preserving commons contribution

### Phase 1B: Application Scaffold (Student Ambassador)
1. **Channel Router** - Multi-channel message handling
2. **Domain Models** - Student, Scholarship, School, Deadline
3. **Tool Definitions** - scholarship_search, deadline_check, etc.
4. **Proactive Triggers** - Deadline alerts, match notifications

### Phase 1C: Integration (external services)
1. **Hume Voice** - Emotion-aware conversation
2. **Twilio SMS** - Messaging channel
3. **Greenlight** - Disbursement detection (or mock)
4. **Nanobanana** - Visual generation

---

## Open Questions

1. **Sparksee Mobile**: Is on-device graph essential for v1, or can we start server-only?
2. **A2A Protocol**: Custom or adopt existing (e.g., Google's A2A)?
3. **Graphiti**: Self-host or use Zep's service?
4. **Greenlight**: Partnership status? Mock for v1?
5. **Scope**: Full Student Ambassador or smaller proof-of-concept first?
