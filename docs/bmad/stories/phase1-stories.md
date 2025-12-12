# Phase 1: Application Layer Stories

## Overview

Stories organized by dependency order. Each story follows BMAD format with clear acceptance criteria.

---

## Track A: Core Extensions

These extend soul_kiln to support any application layer.

### A1: Agent Identity & Binding

**As** an application developer
**I want** agents to have persistent identity bound to external entities
**So that** users get consistent agent relationships

**Tasks:**
- [ ] Add `external_id` and `binding_type` to Agent node schema
- [ ] Create `bind_agent(agent_id, external_id, binding_type)` function
- [ ] Create `get_agent_for(external_id, binding_type)` lookup
- [ ] Ensure agent persists across sessions (not dissolved by kiln)
- [ ] Add `agent_type` enum: `evolving`, `bound`, `specialist`

**Acceptance Criteria:**
- Given a user ID, can bind a new agent to that user
- Given a user ID, can retrieve their bound agent
- Bound agents survive kiln evolution cycles
- Bound agents still participate in coherence testing

**Dependencies:** None

---

### A2: Agent-to-Agent Communication (A2A Stub)

**As** a bound agent
**I want** to request help from specialist agents
**So that** complex tasks can be delegated

**Tasks:**
- [ ] Define A2A message schema: `{from, to, type, payload, context}`
- [ ] Create `send_request(from_agent, to_agent, request)` function
- [ ] Create `receive_response(request_id)` function
- [ ] Add message queue (in-memory for v1, Redis later)
- [ ] Implement request/response correlation

**Acceptance Criteria:**
- Agent A can send request to Agent B
- Agent B processes and returns response
- Agent A receives correlated response
- Failed requests surface as warnings (mercy system)

**Dependencies:** A1

---

### A3: Event System (Triggers)

**As** a bound agent
**I want** to respond to events automatically
**So that** I can be proactive, not just reactive

**Tasks:**
- [ ] Define event schema: `{type, source, timestamp, data}`
- [ ] Create event registry: `register_trigger(event_type, condition, action)`
- [ ] Create event emitter: `emit_event(event)`
- [ ] Implement condition evaluation (simple predicates)
- [ ] Connect to kiln loop (emit events on coherence changes)

**Acceptance Criteria:**
- Can register: "when deadline_approaching, if days < 7, send_reminder"
- Events trigger registered actions
- Actions execute as agent behaviors
- Failed actions create warnings

**Dependencies:** A1

---

### A4: Memory Adapter (Graphiti Integration)

**As** a bound agent
**I want** to remember conversations temporally
**So that** I have context across interactions

**Tasks:**
- [ ] Add graphiti-core dependency
- [ ] Create episode storage: `store_episode(agent_id, conversation)`
- [ ] Create fact extraction: `extract_facts(episode)` → temporal facts
- [ ] Create memory query: `recall(agent_id, query, time_context)`
- [ ] Connect episodes to agent's Trajectory nodes

**Acceptance Criteria:**
- Conversation stored as episode
- Facts extracted with valid_from/valid_to
- Can query "what did we discuss about X"
- Can query "what was true at time T"

**Dependencies:** A1

---

### A5: Anonymization Layer

**As** the system
**I want** to contribute learnings to commons without exposing PII
**So that** collective intelligence grows safely

**Tasks:**
- [ ] Define anonymization rules per field type
- [ ] Create `anonymize_profile(profile)` → AnonymizedProfile
- [ ] Create `anonymize_outcome(outcome)` → AnonymizedOutcome
- [ ] Add k-anonymity verification (min group size)
- [ ] Connect to Lesson creation (lessons are anonymized)

**Acceptance Criteria:**
- Profile fields bucketed (GPA → range, income → bracket)
- No reversible identifiers in anonymized data
- k-anonymity with k ≥ 5 verified
- Anonymized data flows to commons graph

**Dependencies:** None

---

## Track B: Application Scaffold

These are specific to the first application (Student Ambassador) but demonstrate patterns.

### B1: Domain Models

**As** the Student Ambassador application
**I want** domain-specific data models
**So that** I can represent students, scholarships, schools

**Tasks:**
- [ ] Create Student model (wraps Agent + domain fields)
- [ ] Create Scholarship model (graph node type)
- [ ] Create School model (graph node type)
- [ ] Create Deadline model (with event triggers)
- [ ] Create Application model (student → school relationship)

**Acceptance Criteria:**
- Student has: GPA, test scores, activities, financial info
- Scholarship has: criteria, amount, deadline, source
- School has: name, type, selectivity, behavior patterns
- Models map to FalkorDB nodes and relationships

**Dependencies:** A1

---

### B2: Channel Router

**As** a bound agent
**I want** to receive messages from multiple channels
**So that** users can interact via voice, SMS, or web

**Tasks:**
- [ ] Define channel interface: `send(message)`, `receive() → message`
- [ ] Create router: `route_message(channel, user_id, content)`
- [ ] Create SMS channel stub (Twilio later)
- [ ] Create Web channel (WebSocket)
- [ ] Create Voice channel stub (Hume later)

**Acceptance Criteria:**
- Message from any channel reaches bound agent
- Agent response routes back to originating channel
- Channel metadata preserved (for voice emotion, RCS capabilities)
- Unknown channel falls back to simple text

**Dependencies:** A1

---

### B3: Ambassador Tools

**As** a bound Student Ambassador agent
**I want** domain-specific tools
**So that** I can search scholarships, track deadlines, draft appeals

**Tasks:**
- [ ] Define tool interface: `execute(agent_id, params) → result`
- [ ] Create `scholarship_search(criteria)` tool
- [ ] Create `deadline_check(user_id)` tool
- [ ] Create `aid_calculate(packages)` tool
- [ ] Create `appeal_draft(school, circumstances)` tool
- [ ] Create `web_research(query)` tool

**Acceptance Criteria:**
- scholarship_search returns matches from graph
- deadline_check returns sorted upcoming deadlines
- aid_calculate computes net cost comparisons
- appeal_draft generates letter using commons patterns
- Tools accessible via agent action vocabulary

**Dependencies:** B1, A2

---

### B4: Proactive Triggers (Domain-Specific)

**As** a Student Ambassador agent
**I want** domain-specific triggers configured
**So that** I proactively help students

**Tasks:**
- [ ] Register: deadline_within_7_days → send_reminder
- [ ] Register: deadline_within_24_hours → send_urgent
- [ ] Register: new_scholarship_match → queue_conversation
- [ ] Register: days_inactive > 5 → check_in
- [ ] Register: disbursement_detected → process_commission

**Acceptance Criteria:**
- Deadline approaching triggers reminder via appropriate channel
- New scholarship matches queued for next conversation
- Inactive users get gentle check-in
- Commission flow triggered on disbursement (when Greenlight ready)

**Dependencies:** A3, B1, B2

---

## Track C: Integrations

External service connections.

### C1: Twilio SMS Integration

**As** the system
**I want** to send/receive SMS via Twilio
**So that** students can interact via text

**Tasks:**
- [ ] Set up Twilio account and phone number
- [ ] Create incoming webhook handler
- [ ] Create outgoing message sender
- [ ] Handle delivery receipts
- [ ] Implement rate limiting

**Acceptance Criteria:**
- Incoming SMS routes to user's bound agent
- Agent responses send as SMS
- Delivery failures surface as warnings
- Rate limits prevent abuse

**Dependencies:** B2

---

### C2: Hume Voice Integration

**As** a Student Ambassador agent
**I want** emotion-aware voice conversations
**So that** I can adapt to student emotional state

**Tasks:**
- [ ] Set up Hume account and API key
- [ ] Create WebSocket connection for streaming
- [ ] Implement emotion detection handler
- [ ] Create response adaptation (pace, tone)
- [ ] Store emotion data in episode metadata

**Acceptance Criteria:**
- Voice session streams through Hume
- Emotions detected in real-time (anxiety, frustration, etc.)
- Agent response adapts within 500ms
- Emotion history stored in memory

**Dependencies:** B2, A4

---

### C3: Nanobanana Visual Generation

**As** a Student Ambassador agent
**I want** to generate shareable visuals
**So that** students can celebrate wins and understand data

**Tasks:**
- [ ] Set up Nanobanana API
- [ ] Create win_card generator
- [ ] Create debt_comparison generator
- [ ] Create school_comparison generator
- [ ] Deliver via RCS when available, URL otherwise

**Acceptance Criteria:**
- Win card shows scholarship name, amount, student name
- Debt comparison shows before/after projection
- Images deliverable via RCS or fallback URL
- Generation completes in <5 seconds

**Dependencies:** B3, C1

---

### C4: Greenlight Banking (Mock)

**As** the system
**I want** to detect aid disbursements
**So that** I can calculate and collect commissions

**Tasks:**
- [ ] Create mock Greenlight API for development
- [ ] Define disbursement webhook schema
- [ ] Create disbursement classifier (grant/loan/scholarship)
- [ ] Create commission calculator
- [ ] Create approval flow (student confirms)

**Acceptance Criteria:**
- Mock webhook simulates disbursement events
- Classifier correctly categorizes source type
- Commission calculated per rate table
- Student sees breakdown before approval

**Dependencies:** B1, B4

---

## Story Map

```
Week 1-2: Foundation
├── A1: Agent Identity ─────────────────┐
├── A5: Anonymization (parallel)        │
│                                       ▼
Week 3-4: Communication                 │
├── A2: A2A Communication ◄─────────────┤
├── A3: Event System ◄──────────────────┤
├── A4: Memory Adapter ◄────────────────┘
│
Week 5-6: Application
├── B1: Domain Models ◄─────────────────┐
├── B2: Channel Router                  │
│                                       │
Week 7-8: Functionality                 │
├── B3: Ambassador Tools ◄──────────────┤
├── B4: Proactive Triggers              │
│
Week 9-10: Integrations
├── C1: Twilio SMS
├── C2: Hume Voice
├── C3: Nanobanana
├── C4: Greenlight Mock
```

---

## Definition of Done (All Stories)

- [ ] Code complete with tests
- [ ] No regression in existing kiln functionality
- [ ] Documentation updated
- [ ] Mercy system handles failures gracefully
- [ ] Coherence metrics still meaningful
