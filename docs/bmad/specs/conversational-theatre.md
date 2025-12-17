# Conversational Theatre Platform Specification

```yaml
spec:
  name: conversational-theatre
  version: 1.0.0
  type: ux-architecture
  status: draft

metadata:
  created: 2024-12-17
  updated: 2024-12-17
  author: soul-kiln-team

dependencies:
  - soul-kiln-core: ">=1.0.0"
  - hume-ai: ">=0.7.0"
  - falkordb: ">=1.0.4"
  - python: ">=3.10"

agents:
  - analyst
  - architect
  - ux-designer
  - developer
  - mobile-developer
```

---

## Overview

**Goal:** A theatrical, voice-first conversational experience where users join ongoing discussions between AI agents through personal proxies.

**Core Metaphor:** Walking up to a water cooler conversation. Agents are already talking. You arrive, your proxy represents you, you can jump in anytime.

**Design Principle:** No fluffy bullshit. Every element earns its place by adding information value.

**Platform:** Smartphone-first (iOS/Android), cloud processing.

---

## Part 1: The Experience

### 1.1 Visual Stage

```
+----------------------------------------------------------+
|                                                          |
|              FULL-SCREEN CONTEXTUAL IMAGE                |
|                                                          |
|    (Generated or curated based on active concepts)       |
|                                                          |
|    Examples:                                             |
|    - Calendar when discussing deadlines                  |
|    - Document when reviewing proposals                   |
|    - Graph when exploring relationships                  |
|    - Generated scene for abstract topics                 |
|                                                          |
+----------------------------------------------------------+
|  [Proxy Name]  "The deadline is actually..."             |
|  [Agent Name]  "That changes our approach to..."         |
+----------------------------------------------------------+
       ^ Color-coded captions, stacked briefly
```

**Image Behavior:**
- Crossfade on context shifts (default)
- Cut for abrupt topic changes
- Morph for gradual evolution
- Transitions only when they add information value

### 1.2 Entry Flow

```
User opens app
       |
       v
+------------------+
| System knows:    |
| - Last session   |
| - User proxies   |
| - Active context |
+------------------+
       |
       v
+------------------+
| Has proxy(s)?    |
+--------+---------+
    |         |
   Yes        No
    |         |
    v         v
+--------+ +------------------+
| Resume | | Ambassador       |
| with   | | onboards user    |
| likely | | creates first    |
| proxy  | | proxy            |
+--------+ +------------------+
    |         |
    +----+----+
         |
         v
+------------------+
| Fade into        |
| conversation     |
| already in       |
| progress         |
+------------------+
         |
         v
User hears: "...and that's why the timeline matters"
```

### 1.3 Voice Interaction

**Input:**
| Event | Behavior |
|-------|----------|
| First voice detection | Proxy passes through verbatim |
| User speaking | Real-time caption as proxy |
| User silence | Proxy continues advocating |
| Sustained silence | Step back to observe mode |
| Disengagement (camera) | Session pauses |

**Output:**
| Agent | Voice |
|-------|-------|
| User's proxy (user speaking) | User's actual voice |
| User's proxy (autonomous) | Distinct TTS voice |
| Other agents | Unique TTS voices per agent |

### 1.4 Proxy Autonomy

When user is silent, proxy:
1. Continues representing user's position
2. Asks clarifying questions as needed
3. Defers to user on major decisions
4. Can be overridden by user voice at any time

```
PROXY SPEAKS FOR USER
         |
         v
User interrupts --> Proxy yields immediately
         |
         |
No interrupt --> Proxy continues
         |
         v
Needs user input? --> Proxy asks: "Should I...?"
         |
         v
Silence = consent
```

---

## Part 2: Proxies

### 2.1 Proxy Entity

```yaml
proxy:
  id: string
  owner_id: string  # Human user
  name: string
  role: string  # "Nonprofit Director", "Grant Writer", etc.
  communities: list[string]  # Can span multiple
  voice_id: string  # TTS voice selection
  behavior_profile: BehaviorProfile
  created_at: datetime
  last_active: datetime

  # Learned patterns
  positions: dict  # Topic -> stance history
  vocabulary: dict  # Preferred terms
  style: dict  # Communication preferences
```

### 2.2 Proxy Lifecycle

```
NEW USER
    |
    v
+------------------+
| Ambassador       |
| conversation     |
+------------------+
    |
    v
+------------------+
| "What brings     |
|  you here?"      |
+------------------+
    |
    v
+------------------+
| Extract:         |
| - Role           |
| - Community      |
| - Goals          |
+------------------+
    |
    v
+------------------+
| Create proxy     |
| with minimal     |
| config           |
+------------------+
    |
    v
+------------------+
| Proxy learns     |
| from interaction |
+------------------+
```

### 2.3 Proxy Selection

For returning users with multiple proxies:

1. System predicts likely proxy from context
2. Conversation starts with predicted proxy
3. User can say "I'm here as [role]" to switch
4. Switch is seamless, mid-conversation

---

## Part 3: Agent Ensemble

### 3.1 Composition

Every conversation has:

| Role | Count | Purpose |
|------|-------|---------|
| User Proxy | 1+ | Represents human(s) |
| Host | 1 | Facilitates, maintains coherence |
| Context Agents | 1+ | Domain expertise as needed |

### 3.2 Host Agent

The host is not a visible "character" but a toolset that:
- Manages turn-taking
- Resolves simultaneous speech
- Brings in/removes context agents
- Maintains conversation thread
- Surfaces relevant artifacts

### 3.3 Context Agent Dynamics

```
TOPIC SHIFT DETECTED
         |
         v
+------------------+
| Current agent    |
| still relevant?  |
+--------+---------+
    |         |
   Yes        No
    |         |
    v         v
Continue  +------------------+
          | Host: "Let me    |
          | bring in..."     |
          +------------------+
                   |
                   v
          +------------------+
          | New agent joins  |
          | with context     |
          +------------------+
```

---

## Part 4: Multi-User Sessions

### 4.1 Session Model

```yaml
session:
  id: string
  host_user_id: string  # Creator/facilitator
  participants: list[Participant]
  agents: list[AgentInstance]
  state: SessionState
  created_at: datetime

participant:
  user_id: string
  proxy_id: string
  joined_at: datetime
  status: active | observing | away
```

### 4.2 Join Flow

```
NEW PARTICIPANT JOINS
         |
         v
+------------------+
| Select/create    |
| proxy for this   |
| session          |
+------------------+
         |
         v
+------------------+
| Fade into        |
| ongoing          |
| conversation     |
+------------------+
         |
         v
+------------------+
| Host announces   |
| (if appropriate) |
+------------------+
```

### 4.3 Conflict Resolution

When multiple humans speak simultaneously:

```
SIMULTANEOUS SPEECH
         |
         v
+------------------+
| Host detects     |
| collision        |
+------------------+
         |
         v
+------------------+
| Queue by:        |
| 1. Speaking to   |
|    current topic |
| 2. Order of      |
|    detection     |
+------------------+
         |
         v
+------------------+
| Process in order |
| maintain flow    |
+------------------+
```

---

## Part 5: Artifacts

### 5.1 Types

| Type | Display | Interactive |
|------|---------|-------------|
| Image | Full stage | Zoomable |
| Document | Full stage | Scrollable, editable |
| Calendar | Full stage | Tappable events |
| Graph | Full stage | Explorable nodes |
| Timeline | Full stage | Scrubable |
| Checklist | Overlay | Checkable |

### 5.2 Surfacing

Artifacts surface:
1. Automatically from topic context
2. Explicitly on request ("Show me the timeline")
3. From agent reference ("As you can see here...")

### 5.3 Editing

```
USER EDITS ARTIFACT
         |
         v
+------------------+
| Turn-based lock  |
| acquired         |
+------------------+
         |
         v
+------------------+
| Changes visible  |
| to all           |
+------------------+
         |
         v
+------------------+
| Lock released    |
| on completion    |
+------------------+
```

---

## Part 6: Accessibility

### 6.1 Input Modes

| Mode | Primary | Fallback |
|------|---------|----------|
| Voice | Speech-to-text | - |
| Text | On-screen keyboard | - |
| ASL | Camera interpretation | - |

### 6.2 ASL Flow

```
USER SIGNS
         |
         v
+------------------+
| Start signal     |
| detected         |
+------------------+
         |
         v
+------------------+
| Capture signing  |
| sequence         |
+------------------+
         |
         v
+------------------+
| Stop signal      |
| detected         |
+------------------+
         |
         v
+------------------+
| Interpret to     |
| text             |
+------------------+
         |
         v
+------------------+
| Pass to proxy    |
| as voice input   |
+------------------+
```

### 6.3 Output Accessibility

- Captions always on (core to experience)
- High contrast mode available
- Screen reader compatible
- Haptic feedback optional

---

## Part 7: Technical Architecture

### 7.1 Component Overview

```
+----------------------------------------------------------+
|                    MOBILE APP (React Native)              |
|  +------------------------------------------------------+ |
|  |  Stage Renderer | Caption Overlay | Voice Capture   | |
|  +------------------------------------------------------+ |
+---------------------------+------------------------------+
                            |
                       WebSocket
                            |
+---------------------------v------------------------------+
|                    API GATEWAY (FastAPI)                 |
|  +------------------------------------------------------+ |
|  |  Session Manager | Auth | Rate Limiting              | |
|  +------------------------------------------------------+ |
+---------------------------+------------------------------+
                            |
         +------------------+------------------+
         |                  |                  |
+--------v-------+ +--------v-------+ +--------v-------+
|   THEATRE      | |   VOICE        | |   MEDIA        |
|   SERVICE      | |   SERVICE      | |   SERVICE      |
|                | |                | |                |
| - Orchestrator | | - STT (Hume)   | | - Image Gen    |
| - Captions     | | - TTS          | | - Artifact     |
| - Artifacts    | | - ASL          | |   Render       |
| - Topics       | | - Emotion      | |                |
+--------+-------+ +--------+-------+ +--------+-------+
         |                  |                  |
         +------------------+------------------+
                            |
+---------------------------v------------------------------+
|                    SOUL KILN CORE                        |
|  +------------------------------------------------------+ |
|  |  Graph | Virtues | Dynamics | Memory | Vessels       | |
|  +------------------------------------------------------+ |
+---------------------------+------------------------------+
                            |
+---------------------------v------------------------------+
|                    FALKORDB                              |
+----------------------------------------------------------+
```

### 7.2 Real-Time Transport

```yaml
websocket_events:
  # Client -> Server
  - voice_chunk: Audio data stream
  - text_input: Typed message
  - gesture: UI interaction
  - presence: Join/leave/observe

  # Server -> Client
  - caption: New caption to display
  - stage_update: Image/artifact change
  - agent_state: Agent activity
  - session_state: Participants, status
```

### 7.3 Voice Pipeline

```
USER AUDIO
    |
    v
+------------------+
| Noise reduction  |
| VAD (Voice       |
| Activity Detect) |
+------------------+
    |
    v
+------------------+
| Stream to        |
| Hume STT         |
+------------------+
    |
    v
+------------------+
| Emotional        |
| analysis         |
+------------------+
    |
    +-----> Emotion state to orchestrator
    |
    v
+------------------+
| Text to          |
| proxy            |
+------------------+
```

### 7.4 TTS Pipeline

```
AGENT SPEAKS
    |
    v
+------------------+
| Select voice     |
| for agent        |
+------------------+
    |
    v
+------------------+
| Generate TTS     |
| (stream)         |
+------------------+
    |
    +-----> Audio to client
    |
    v
+------------------+
| Generate         |
| caption          |
+------------------+
    |
    v
Caption to client
```

---

## Part 8: Data Model Extensions

### 8.1 New Node Types

| Type | Purpose | Properties |
|------|---------|------------|
| Proxy | User representation | owner_id, name, role, communities, voice_id |
| Session | Conversation instance | host_id, state, created_at |
| Participant | Session member | user_id, proxy_id, status |

### 8.2 New Relationships

| Relationship | From | To | Purpose |
|--------------|------|-----|---------|
| OWNS_PROXY | User | Proxy | User's proxies |
| REPRESENTS | Proxy | User | Proxy acts for user |
| PARTICIPATES | Proxy | Session | Proxy in session |
| HOSTS | User | Session | Session ownership |
| MEMBER_OF | Proxy | Community | Community membership |

### 8.3 Session State Machine

```
CREATED --> ACTIVE --> PAUSED --> ACTIVE
              |           |
              |           v
              |       SUSPENDED
              |           |
              v           v
          COMPLETED   EXPIRED
```

---

## Part 9: Implementation Phases

### Phase 1: Foundation
- WebSocket server
- Basic mobile shell
- Voice pipeline (STT/TTS)
- Single-user sessions
- Proxy creation via Ambassador

### Phase 2: Theatrical Core
- Stage renderer with images
- Caption overlay system
- Topic-driven artifact surfacing
- Proxy autonomy (speaking for user)

### Phase 3: Multi-User
- Multi-participant sessions
- Host facilitation logic
- Conflict resolution
- Turn-based artifact editing

### Phase 4: Intelligence
- Emotional analysis integration
- Engagement detection
- ASL interpretation
- Proxy learning from patterns

### Phase 5: Polish
- Image transitions
- Ambient audio (optional)
- Notifications
- History replay

---

## Part 10: Integration Points

### 10.1 Existing Backend

| Component | Status | Integration |
|-----------|--------|-------------|
| TheatreOrchestrator | Ready | Wire to WebSocket |
| CaptionRenderer | Ready | Stream to client |
| ArtifactCurator | Ready | Surface to stage |
| HumeIntegration | Stub | Connect API |
| SessionManager | Ready | Extend for multi-user |
| A2AChat | Ready | Agent communication |

### 10.2 New Services Required

| Service | Purpose | Provider Options |
|---------|---------|------------------|
| STT | Speech to text | Hume, Deepgram, Whisper |
| TTS | Text to speech | ElevenLabs, Google, Azure |
| Image Gen | Contextual images | DALL-E, Midjourney, Stable Diffusion |
| ASL | Sign language interpretation | Custom model, Google MediaPipe |

---

## Summary

### Key Characteristics

| Aspect | Approach |
|--------|----------|
| Primary interface | Voice |
| Visual | Full-screen stage with caption overlay |
| Entry | Immediate, mid-conversation |
| User representation | Proxy agent |
| Multi-user | Supported, host-facilitated |
| Accessibility | Voice, text, ASL |
| Platform | Smartphone-first |

### Philosophy

> You're joining a conversation, not starting one. Your proxy has your back. The stage shows what matters. Everything else gets out of the way.

---

*Specification Version: 1.0.0*
*BMAD Method Compatible*

Sources:
- [BMAD-METHOD GitHub](https://github.com/bmad-code-org/BMAD-METHOD)
- [BMAD Method Framework Overview](https://medium.com/@visrow/what-is-bmad-method-a-simple-guide-to-the-future-of-ai-driven-development-412274f91419)
