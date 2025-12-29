# Knowledge Forge — Unified Backend Architecture

## Overview

Design a unified backend that handles orchestration, streaming, API contracts, state sync, and persistence — structured for parallel implementation via git worktrees.

---

## Architecture Diagram

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                              FRONTEND                                        │
│  React + Zustand + API Client                                               │
│                                                                             │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐        │
│  │ JourneyIntake│  │ ChatInput   │  │ Mode Tabs   │  │ Panels      │        │
│  └──────┬──────┘  └──────┬──────┘  └──────┬──────┘  └──────┬──────┘        │
│         │                │                │                │                │
│         └────────────────┴────────────────┴────────────────┘                │
│                                   │                                         │
│                          ┌────────┴────────┐                                │
│                          │   API Client    │  (fetch + SSE EventSource)     │
│                          │   + Stream      │                                │
│                          │   Handlers      │                                │
│                          └────────┬────────┘                                │
└───────────────────────────────────┼─────────────────────────────────────────┘
                                    │ HTTP + SSE
                                    ▼
┌───────────────────────────────────────────────────────────────────────────────┐
│                              BACKEND (FastAPI)                                │
│                                                                               │
│  ┌─────────────────────────────────────────────────────────────────────────┐ │
│  │                         API LAYER (Routes)                              │ │
│  │                                                                         │ │
│  │  POST /api/journey/analyze    → JourneyDesignBrief                     │ │
│  │  POST /api/journey/confirm    → Initialize session                      │ │
│  │  GET  /api/journey/stream     → SSE stream (agent events)              │ │
│  │  POST /api/chat               → User message → agent response          │ │
│  │  GET  /api/session/:id        → Load session state                     │ │
│  │  POST /api/session/:id/save   → Persist session                        │ │
│  └──────────────────────────────────┬──────────────────────────────────────┘ │
│                                     │                                        │
│  ┌──────────────────────────────────┴──────────────────────────────────────┐ │
│  │                         ORCHESTRATOR                                    │ │
│  │                                                                         │ │
│  │  • Analyzes questions (work backwards from ideal answer)               │ │
│  │  • Routes to appropriate mode agent                                    │ │
│  │  • Manages mode transitions (Research → Build returns)                 │ │
│  │  • Coordinates Build phases (Grounding → Making)                       │ │
│  │  • Emits events to SSE stream                                          │ │
│  └──────────────────────────────────┬──────────────────────────────────────┘ │
│                                     │                                        │
│         ┌───────────────────────────┼───────────────────────────┐           │
│         │                           │                           │           │
│         ▼                           ▼                           ▼           │
│  ┌─────────────┐           ┌─────────────┐            ┌─────────────┐       │
│  │  RESEARCH   │           │ UNDERSTAND  │            │   BUILD     │       │
│  │   AGENT     │           │   AGENT     │            │   AGENT     │       │
│  │             │           │             │            │             │       │
│  │ • Decompose │           │ • Surface   │            │ • Anchor    │       │
│  │ • Answer    │           │ • Distinguish│            │ • Scaffold  │       │
│  │ • Rise Above│           │ • Integrate │            │ • Construct │       │
│  │ • Expand    │           │ • Discard   │            │ • Verify    │       │
│  └──────┬──────┘           └──────┬──────┘            └──────┬──────┘       │
│         │                         │                          │              │
│         └─────────────────────────┴──────────────────────────┘              │
│                                   │                                         │
│                          ┌────────┴────────┐                                │
│                          │  Claude API     │  (anthropic SDK)               │
│                          │  (streaming)    │                                │
│                          └────────┬────────┘                                │
│                                   │                                         │
│                          ┌────────┴────────┐                                │
│                          │  PERSISTENCE    │  (file-based MVP)              │
│                          │                 │                                │
│                          │ sessions/       │                                │
│                          │ learner-profiles/│                               │
│                          └─────────────────┘                                │
└───────────────────────────────────────────────────────────────────────────────┘
```

---

## Design Decisions

| Decision | Choice | Rationale |
|----------|--------|-----------|
| Backend Language | Python + FastAPI | Matches user's existing patterns (epic-business-regression-showcase) |
| Streaming | Server-Sent Events (SSE) | Simpler than WebSocket, one-way server→client, native browser support |
| Claude SDK | Claude Agent SDK | Official agent framework with tool use, streaming, proper agent patterns |
| Documentation | Context7 MCP | Real-time docs lookup for libraries during Research agent execution |
| Persistence | File-based JSON | Matches skill spec outputs, simple MVP, upgrade to DB later |
| Type Sharing | Pydantic ↔ TypeScript | Generate TypeScript from Pydantic or maintain parallel definitions |
| Session State | Server-side with client sync | Server is source of truth, client receives updates via SSE |

---

## Module Breakdown (Parallel Worktrees)

### Module 1: API Layer
**Path**: `server/api/`
**Can build independently**: Yes (mock agent responses)

```
server/
├── api/
│   ├── __init__.py
│   ├── main.py              # FastAPI app, CORS, middleware
│   ├── routes/
│   │   ├── journey.py       # /api/journey/* endpoints
│   │   ├── chat.py          # /api/chat endpoint
│   │   └── session.py       # /api/session/* endpoints
│   └── streaming.py         # SSE event emitter utilities
```

### Module 2: Orchestrator
**Path**: `server/orchestrator/`
**Depends on**: API Layer (for event emission), Agent interfaces

```
server/
├── orchestrator/
│   ├── __init__.py
│   ├── orchestrator.py      # Main orchestration logic
│   ├── router.py            # Question → Mode routing
│   ├── journey_designer.py  # Work backwards → JourneyDesignBrief
│   └── phase_manager.py     # Build phase transitions
```

### Module 3: Research Agent
**Path**: `server/agents/research/`
**Can build independently**: Yes (given interface contract)

```
server/
├── agents/
│   ├── base.py              # BaseAgent interface
│   └── research/
│       ├── __init__.py
│       ├── agent.py         # ResearchAgent class
│       ├── decomposer.py    # Topic → Questions
│       ├── answerer.py      # Question → Answer + Sources
│       ├── synthesizer.py   # Rise above → Category insights
│       └── expander.py      # Answered → Adjacent questions
```

### Module 4: Understand Agent
**Path**: `server/agents/understand/`
**Can build independently**: Yes

```
server/
├── agents/
│   └── understand/
│       ├── __init__.py
│       ├── agent.py         # UnderstandAgent class
│       ├── prober.py        # Triple calibration probes
│       ├── diagnostician.py # Knowledge state tracking
│       ├── teacher.py       # Generous teaching moments
│       └── tracker.py       # Mastery counters, exit conditions
```

### Module 5: Build Agent
**Path**: `server/agents/build/`
**Can build independently**: Yes

```
server/
├── agents/
│   └── build/
│       ├── __init__.py
│       ├── agent.py         # BuildAgent class
│       ├── anchor_finder.py # Anchor discovery
│       ├── scaffolder.py    # Scaffold delivery
│       ├── constructor.py   # Construction verification
│       └── memory.py        # Three-layer memory management
```

### Module 6: Frontend Integration
**Path**: `app/src/api/`
**Can build independently**: Yes (mock server responses)

```
app/src/
├── api/
│   ├── client.ts            # Fetch wrapper, error handling
│   ├── streaming.ts         # SSE EventSource handler
│   ├── types.ts             # API request/response types
│   └── hooks.ts             # useJourneyAnalysis, useChat, etc.
├── store/
│   └── useStore.ts          # Add async actions
```

### Module 7: Persistence Layer
**Path**: `server/persistence/`
**Can build independently**: Yes

```
server/
├── persistence/
│   ├── __init__.py
│   ├── session_store.py     # Session CRUD
│   └── file_backend.py      # JSON file read/write
├── data/
│   └── sessions/            # {session_id}.json
```

**Note**: Learner profiles deferred to future auth integration. Sessions identified by session ID only.

---

## API Contract

### Types (Shared between Frontend/Backend)

```typescript
// ============= Journey Intake =============

interface JourneyAnalyzeRequest {
  question: string
  learnerContext?: string  // Optional prior knowledge
}

interface JourneyDesignBrief {
  originalQuestion: string
  idealAnswer: string
  answerType: 'facts' | 'understanding' | 'skill'
  primaryMode: 'research' | 'understand' | 'build'
  secondaryMode?: 'research'
  implicitQuestion?: string
  confirmationMessage: string
}

interface JourneyConfirmRequest {
  brief: JourneyDesignBrief
  confirmed: boolean
  alternativeMode?: Mode  // If user picked different mode
}

interface SessionInitResponse {
  sessionId: string
  mode: Mode
  initialData: ResearchModeData | UnderstandModeData | BuildModeData
}

// ============= Chat =============

interface ChatRequest {
  sessionId: string
  message: string
  context?: {
    selectedQuestionId?: string
    activeTab?: number
  }
}

// Response is streamed via SSE

// ============= SSE Events =============

type SSEEventType =
  | 'session.started'
  | 'agent.thinking'
  | 'agent.speaking'
  | 'data.question.added'
  | 'data.question.answered'
  | 'data.category.insight'
  | 'data.construct.added'
  | 'data.decision.added'
  | 'data.capability.added'
  | 'data.assumption.surfaced'
  | 'data.concept.distinguished'
  | 'data.model.integrated'
  | 'narrative.updated'
  | 'phase.changed'
  | 'agent.complete'
  | 'error'

interface SSEEvent<T = unknown> {
  type: SSEEventType
  timestamp: string
  payload: T
}

// Example payloads
interface QuestionAddedPayload {
  question: Question
  categoryId: string
}

interface NarrativeUpdatedPayload {
  mode: Mode
  narrative: Narrative
  delta?: string  // Incremental text for streaming display
}

interface PhaseChangedPayload {
  from: BuildPhase
  to: BuildPhase
}
```

### Endpoints

```
POST /api/journey/analyze
  Request: JourneyAnalyzeRequest
  Response: JourneyDesignBrief

POST /api/journey/confirm
  Request: JourneyConfirmRequest
  Response: SessionInitResponse

GET /api/journey/stream?sessionId={id}
  Response: SSE stream of SSEEvent

POST /api/chat
  Request: ChatRequest
  Response: 202 Accepted (results via SSE stream)

GET /api/session/{id}
  Response: SessionState

POST /api/session/{id}/save
  Request: { checkpoint?: string }
  Response: { saved: true, path: string }
```

---

## SSE Streaming Protocol

### Event Format
```
event: {type}
data: {json payload}

```

### Example Stream
```
event: session.started
data: {"sessionId": "abc123", "mode": "research"}

event: agent.thinking
data: {"message": "Decomposing your question into research areas..."}

event: data.question.added
data: {"question": {"id": "q1", "question": "What is X?", "status": "open"}, "categoryId": "cat1"}

event: agent.speaking
data: {"delta": "Let me start by exploring "}

event: agent.speaking
data: {"delta": "the core mechanisms..."}

event: data.question.answered
data: {"questionId": "q1", "answer": "X is...", "sources": [...]}

event: narrative.updated
data: {"mode": "research", "delta": "## Key Finding\n\nX works by..."}

event: agent.complete
data: {"summary": "Answered 5 questions, identified 3 adjacent areas"}
```

### Frontend Handler Pattern
```typescript
// app/src/api/streaming.ts

export function createJourneyStream(sessionId: string, handlers: StreamHandlers) {
  const eventSource = new EventSource(`/api/journey/stream?sessionId=${sessionId}`)

  eventSource.addEventListener('data.question.added', (e) => {
    const payload = JSON.parse(e.data) as QuestionAddedPayload
    handlers.onQuestionAdded(payload)
  })

  eventSource.addEventListener('narrative.updated', (e) => {
    const payload = JSON.parse(e.data) as NarrativeUpdatedPayload
    handlers.onNarrativeUpdated(payload)
  })

  eventSource.addEventListener('error', (e) => {
    handlers.onError(e)
  })

  return () => eventSource.close()
}
```

---

## Agent Interface Contract

Built using **Claude Agent SDK** for proper agent patterns, tool use, and streaming.

```python
# server/agents/base.py

from abc import ABC, abstractmethod
from typing import AsyncGenerator
from claude_agent_sdk import Agent, Tool
from .events import SSEEvent

class BaseForgeAgent(ABC):
    """
    Base interface for all mode agents.
    Built on Claude Agent SDK for tool use, streaming, and agent patterns.
    """

    def __init__(self, session_state, event_emitter):
        self.state = session_state
        self.emit = event_emitter
        self.agent = self._create_agent()

    @abstractmethod
    def _create_agent(self) -> Agent:
        """Create the Agent SDK agent with appropriate tools and system prompt."""
        pass

    @abstractmethod
    def _get_tools(self) -> list[Tool]:
        """Define tools available to this agent."""
        pass

    @abstractmethod
    async def initialize(self, journey_brief: JourneyDesignBrief) -> None:
        """Set up initial state for the journey."""
        pass

    @abstractmethod
    async def process_message(self, message: str, context: dict) -> AsyncGenerator[SSEEvent, None]:
        """Process user message, yield SSE events as work progresses."""
        pass

    @abstractmethod
    async def get_state(self) -> dict:
        """Return current agent state for persistence."""
        pass

    @abstractmethod
    async def restore_state(self, state: dict) -> None:
        """Restore agent from persisted state."""
        pass
```

### Research Agent Tools (with Context7)

```python
# server/agents/research/tools.py

from claude_agent_sdk import Tool

# Context7 integration for real-time documentation lookup
context7_resolve = Tool(
    name="resolve_library_id",
    description="Resolve a library name to Context7 ID for documentation lookup",
    # Calls Context7 MCP: resolve-library-id
)

context7_query = Tool(
    name="query_docs",
    description="Query up-to-date documentation for a library",
    # Calls Context7 MCP: query-docs
)

web_search = Tool(
    name="web_search",
    description="Search the web for current information",
    # Uses Claude's built-in web search
)

# Research agent has access to:
RESEARCH_TOOLS = [
    context7_resolve,  # Resolve library names → Context7 IDs
    context7_query,    # Get latest docs from Context7
    web_search,        # General web search for sources
]
```

### Build/Understand Agent Tools

```python
# These agents are more conversational, fewer tools needed

BUILD_TOOLS = [
    # Code execution for examples (optional)
    # File write for artifacts (optional)
]

UNDERSTAND_TOOLS = [
    # Primarily conversational - diagnostic probes
    # May use web_search for clarifying examples
]
```

---

## State Management Integration

### Frontend Store Extensions

```typescript
// Extend useStore.ts

interface ForgeState {
  // ... existing state ...

  // API state
  sessionId: string | null
  isConnected: boolean
  isLoading: boolean
  error: string | null

  // Stream state
  agentThinking: string | null
  streamingNarrative: string

  // API actions
  analyzeJourney: (question: string) => Promise<JourneyDesignBrief>
  confirmJourney: (brief: JourneyDesignBrief) => Promise<void>
  sendMessage: (message: string) => Promise<void>
  connectStream: () => void
  disconnectStream: () => void
}
```

### Update Flow

```
User types in ChatInput
       │
       ▼
sendMessage(text)
       │
       ▼
POST /api/chat ────────────────────┐
       │                           │
       ▼                           ▼
Returns 202 Accepted         Server processes
       │                           │
       ▼                           ▼
Wait for SSE events          Agent runs, emits events
       │                           │
       ▼                           ▼
Stream handlers ◄──────────── SSE events arrive
       │
       ▼
Update Zustand store
       │
       ▼
Components re-render
```

---

## Persistence Schema

### Session File Structure
```
server/data/sessions/{session_id}.json
```

```json
{
  "id": "session-abc123",
  "created": "2025-12-29T10:00:00Z",
  "updated": "2025-12-29T11:30:00Z",

  "journeyBrief": {
    "originalQuestion": "How do I write better prompts?",
    "idealAnswer": "...",
    "answerType": "skill",
    "primaryMode": "build",
    "confirmationMessage": "..."
  },

  "mode": "build",
  "phase": "making",

  "modeData": {
    "narrative": { "prior": "...", "delta": "...", "full": "..." },
    "constructs": [...],
    "decisions": [...],
    "capabilities": [...]
  },

  "agentState": {
    "anchorMap": {...},
    "sloProgress": [...],
    "memoryLayers": {...}
  },

  "path": {
    "nodes": [...],
    "neighbors": [...]
  }
}
```

**Note**: Learner profiles (cross-session memory, anchor inventory, learning patterns) deferred to future auth integration.

---

## Implementation Order

### Phase 1: Foundation (Can parallelize)
1. **API Layer** — FastAPI skeleton, routes, SSE infrastructure
2. **Frontend API Client** — Fetch wrapper, SSE handlers, store extensions
3. **Persistence Layer** — File-based session/profile storage

### Phase 2: Orchestration
4. **Orchestrator** — Question routing, journey design, phase management
   - Depends on: API Layer

### Phase 3: Agents (Can parallelize)
5. **Research Agent** — Implement DECOMPOSE, ANSWER, RISE ABOVE, EXPAND
6. **Understand Agent** — Implement probing, diagnostics, teaching moments
7. **Build Agent** — Implement anchoring, scaffolding, construction loops
   - All depend on: Orchestrator (for event emission interface)

### Phase 4: Integration
8. **End-to-end testing** — Full journey flows
9. **Polish** — Error handling, loading states, edge cases

---

## File Structure (Complete)

```
knowledge-forge/
├── app/                          # Frontend (existing)
│   └── src/
│       ├── api/                  # NEW: API integration
│       │   ├── client.ts
│       │   ├── streaming.ts
│       │   ├── types.ts
│       │   └── hooks.ts
│       ├── store/
│       │   └── useStore.ts       # Extend with API state
│       └── ...
│
├── server/                       # NEW: Backend
│   ├── api/
│   │   ├── __init__.py
│   │   ├── main.py
│   │   ├── routes/
│   │   │   ├── journey.py
│   │   │   ├── chat.py
│   │   │   └── session.py
│   │   └── streaming.py
│   │
│   ├── orchestrator/
│   │   ├── __init__.py
│   │   ├── orchestrator.py
│   │   ├── router.py
│   │   ├── journey_designer.py
│   │   └── phase_manager.py
│   │
│   ├── agents/
│   │   ├── __init__.py
│   │   ├── base.py
│   │   ├── research/
│   │   │   ├── __init__.py
│   │   │   ├── agent.py
│   │   │   ├── decomposer.py
│   │   │   ├── answerer.py
│   │   │   ├── synthesizer.py
│   │   │   └── expander.py
│   │   ├── understand/
│   │   │   ├── __init__.py
│   │   │   ├── agent.py
│   │   │   ├── prober.py
│   │   │   ├── diagnostician.py
│   │   │   ├── teacher.py
│   │   │   └── tracker.py
│   │   └── build/
│   │       ├── __init__.py
│   │       ├── agent.py
│   │       ├── anchor_finder.py
│   │       ├── scaffolder.py
│   │       ├── constructor.py
│   │       └── memory.py
│   │
│   ├── persistence/
│   │   ├── __init__.py
│   │   ├── session_store.py
│   │   └── file_backend.py
│   │
│   ├── data/
│   │   └── sessions/
│   │
│   ├── requirements.txt          # anthropic, claude-agent-sdk, fastapi, uvicorn
│   └── pyproject.toml
│
├── shared/                       # NEW: Shared type definitions
│   └── types/
│       ├── api.ts               # TypeScript API types
│       └── api.py               # Pydantic models (mirror)
│
├── scripts/
│   └── dev-server.py            # Concurrent server launcher
│
└── docs/
    ├── spec.md
    ├── design.md
    ├── tech-stack.md
    └── backend-architecture.md  # NEW: This design
```

---

## Worktree Strategy

Create separate worktrees for parallel development:

```bash
# Main branch
git branch backend-api-layer
git branch backend-orchestrator
git branch backend-research-agent
git branch backend-understand-agent
git branch backend-build-agent
git branch frontend-api-integration
git branch backend-persistence

# Create worktrees
git worktree add ../kf-api-layer backend-api-layer
git worktree add ../kf-orchestrator backend-orchestrator
git worktree add ../kf-research-agent backend-research-agent
git worktree add ../kf-understand-agent backend-understand-agent
git worktree add ../kf-build-agent backend-build-agent
git worktree add ../kf-frontend-api frontend-api-integration
git worktree add ../kf-persistence backend-persistence
```

### Merge Order
1. `backend-persistence` → main
2. `backend-api-layer` → main
3. `frontend-api-integration` → main
4. `backend-orchestrator` → main
5. `backend-research-agent`, `backend-understand-agent`, `backend-build-agent` → main (parallel)

---

## Implementation Notes

### Using Agent SDK
When implementing agents, use the `/agent-sdk-dev:new-sdk-app` skill to bootstrap properly:
- Creates correct project structure
- Sets up Agent SDK dependencies
- Follows SDK best practices

After implementation, run `/agent-sdk-dev:agent-sdk-verifier-py` to verify the agent follows SDK patterns.

### Using Context7 for Documentation
The Research agent should use Context7 MCP for real-time documentation:
1. Call `resolve-library-id` to get the Context7 library ID
2. Call `query-docs` with specific questions about the library
3. Integrate responses into research answers with proper sourcing

Example flow:
```
User asks: "What caching strategies does LangChain support?"
  ↓
Research Agent calls: resolve-library-id("langchain", "caching strategies")
  ↓
Gets: "/langchain-ai/langchain"
  ↓
Calls: query-docs("/langchain-ai/langchain", "How to implement caching")
  ↓
Gets: Up-to-date documentation with code examples
  ↓
Synthesizes into answer with Context7 as source
```

### Dependencies
```
# server/requirements.txt
anthropic>=0.40.0
claude-agent-sdk>=0.1.0
fastapi>=0.115.0
uvicorn>=0.32.0
sse-starlette>=2.0.0
pydantic>=2.0.0
```

---

## Design Decisions (User Confirmed)

| Question | Decision | Implication |
|----------|----------|-------------|
| **Learner ID** | Defer to later auth | No learner profiles for MVP. Sessions identified by session ID only. Design hooks for future auth. |
| **Web Search** | Claude web search tool | Research agent uses Claude's built-in web search. Simpler integration. |
| **Session Resume** | Yes, persist sessions | Server-side session storage required. User can resume across browser restarts. |
| **Hosting** | Local development only | No cloud deployment concerns for now. Simple localhost setup. |

---

## Next Steps

After plan approval, create beads issues for each module:

1. `backend-api-layer` — FastAPI skeleton, routes, SSE streaming
2. `backend-persistence` — File-based session storage (no profiles yet)
3. `frontend-api-integration` — API client, SSE handlers, store extensions
4. `backend-orchestrator` — Question routing, journey design
5. `backend-research-agent` — With Claude web search integration
6. `backend-understand-agent` — Socratic probing, teaching moments
7. `backend-build-agent` — Anchoring, scaffolding, construction
