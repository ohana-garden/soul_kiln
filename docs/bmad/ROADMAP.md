# Soul Kiln Development Roadmap

## Three-Phase Strategy

```
┌─────────────────────────────────────────────────────────────────────────┐
│  PHASE 1: Application Layer                                             │
│  Build a complete application on soul_kiln to prove the architecture    │
│  Example: Student Ambassador (or other domain)                          │
├─────────────────────────────────────────────────────────────────────────┤
│  PHASE 2: Core Evolution                                                │
│  Feed learnings back into soul_kiln - new dynamics, better coherence    │
│  testing, richer virtue interactions discovered through real use        │
├─────────────────────────────────────────────────────────────────────────┤
│  PHASE 3: Platform/SDK                                                  │
│  Abstract patterns into reusable primitives for any domain              │
│  soul_kiln becomes infrastructure, not just one implementation          │
└─────────────────────────────────────────────────────────────────────────┘
```

---

## Phase 1: Application Layer

**Goal:** Build one complete, deployed application that uses soul_kiln's virtue basin architecture.

**Why first:**
- Proves the architecture works in practice
- Reveals gaps in the current implementation
- Creates concrete user value
- Generates learnings for Phase 2

**Candidate Application:** Student Ambassador Platform
- AI advocates for students navigating college/financial aid
- Natural fit for virtue-based agents (trustworthiness, service, wisdom)
- Multi-agent coordination maps to specialist agents
- Privacy-first architecture aligns with on-device graph vision

**BMAD Artifacts Needed:**
- [x] Project Brief (provided as context)
- [ ] Gap Analysis: soul_kiln ↔ Student Ambassador requirements
- [ ] Integration Architecture: how virtue basins power ambassador agents
- [ ] Implementation Stories: prioritized backlog

---

## Phase 2: Core Evolution

**Goal:** Strengthen soul_kiln based on Phase 1 learnings.

**Expected Evolution Areas:**
- Virtue dynamics under real load
- Coherence testing with actual agent behavior
- Mercy system refinement (harm detection, lessons learned)
- Knowledge pool patterns (what gets shared, what stays private)
- Performance at scale

**BMAD Artifacts Needed:**
- [ ] Retrospective: what worked, what didn't
- [ ] Core Enhancement PRD
- [ ] Architecture Evolution Document
- [ ] Technical Stories

---

## Phase 3: Platform/SDK

**Goal:** Make soul_kiln a foundation others can build on.

**Platform Components:**
- Graph primitives (virtue anchors, activation spread, Hebbian learning)
- Agent lifecycle (spawn, evolve, test coherence, dissolve)
- Mercy framework (harm tracking, chances, judgment)
- Integration patterns (how applications connect)
- Multi-tenancy (multiple applications, shared learnings)

**BMAD Artifacts Needed:**
- [ ] Platform Vision Document
- [ ] SDK Architecture
- [ ] Developer Experience Design
- [ ] API Specification

---

## Current Status

| Phase | Status | Next Action |
|-------|--------|-------------|
| 1 - Application | Starting | Gap analysis |
| 2 - Core | Waiting | Depends on Phase 1 learnings |
| 3 - Platform | Waiting | Depends on Phase 1 + 2 patterns |

---

## Open Questions

1. **Application choice:** Is Student Ambassador the right first application, or is there a simpler/faster domain to prove the architecture?

2. **Scope for Phase 1:** Full feature set or MVP slice?

3. **Timeline pressure:** Is there external timing that affects prioritization?

4. **Team/resources:** Solo development or collaboration expected?
