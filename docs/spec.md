# Knowledge Forge — System Specification

**Version:** 1.0 (Draft)
**Author:** Anurag Sahay
**Date:** 2025-12-28

---

## Table of Contents

1. [Executive Summary](#1-executive-summary)
2. [Problem Analysis](#2-problem-analysis)
3. [Design Principles](#3-design-principles)
4. [System Architecture](#4-system-architecture)
5. [Data Models](#5-data-models)
6. [UI/UX Specification](#6-uiux-specification)
7. [Agent Architecture](#7-agent-architecture)
8. [Mode Integration](#8-mode-integration)
9. [API Contracts](#9-api-contracts)
10. [MVP Phases](#10-mvp-phases)
11. [Open Questions](#11-open-questions)

---

## 1. Executive Summary

### What

Knowledge Forge is a unified web-based learning platform that weaves together three pedagogical approaches:

| Mode | Pedagogy | Core Mechanism |
|------|----------|----------------|
| **/build** | Constructivist | Find anchors in prior knowledge, scaffold construction |
| **/understand** | Socratic | Diagnose gaps through questioning, then teach |
| **/research** | Evidence-based | Gather authoritative sources, synthesize knowledge |

### Why

Current learning skills run as isolated CLI sessions with critical limitations:

1. **Context loss** — Mode switching requires exiting and re-invoking
2. **No synthesis visibility** — Knowledge being built isn't visible during learning
3. **Linear interface** — Single-pane scrolling loses earlier context
4. **Manual connections** — Topic relationships must be discovered manually
5. **Code friction** — Code interaction is one-way (describe in prose, can't edit/run)

### Key Insight

**Learning is non-linear.** A learner exploring database indexes might:
- Start in /understand to build mental model
- Switch to /research when they need authoritative sources
- Jump to /build when they want to solidify through construction
- Branch to "query optimization" when a connection emerges
- Return to complete partial understanding

The platform must support this fluid movement **without losing context**.

---

## 2. Problem Analysis

### 2.1 Current State Pain Points

| Pain Point | Impact | Root Cause |
|------------|--------|------------|
| Mode switching requires restart | Lost context, repeated work | CLI sessions are isolated |
| Can't see what's being learned | Reduced metacognition | Knowledge synthesis is internal |
| Long sessions lose early context | Incomplete learning | No persistent state across modes |
| Code examples can't be edited | Reduced experimentation | One-way code delivery |
| Topic connections are manual | Missed learning opportunities | No knowledge graph |
| Learner profile is build-only | Inconsistent personalization | Modes don't share state |

### 2.2 What Must Change

| From | To |
|------|-----|
| Isolated CLI sessions | Unified web platform |
| Mode = separate invocation | Mode = tab switch with context preservation |
| Internal knowledge synthesis | Live Knowledge panel |
| Prose-only code examples | Interactive Code Sandbox |
| Linear topic exploration | Knowledge Galaxy graph |
| Build-only learner profile | Unified profile enriched by all modes |

### 2.3 Success Criteria

1. **Zero-friction mode switching** — Switch in <1s with full context preserved
2. **Visible learning** — Current state always visible in Live Knowledge panel
3. **Knowledge persistence** — Cross-session memory with unified learner profile
4. **Topic discovery** — Auto-suggested connections based on learned content
5. **Code integration** — Edit, run, and save code during learning
6. **Compatible outputs** — Artifacts match existing directory structures

---

## 3. Design Principles

### 3.1 Core Principles

| Principle | Implication |
|-----------|-------------|
| **Learning is non-linear** | Support branching, returning, connecting across topics and modes |
| **Knowledge isn't transmitted, it's constructed** | Even in /understand and /research, learner must actively engage |
| **Context is precious** | Never lose context on mode switch, session end, or topic branch |
| **Show the work** | Make learning progress visible (Live Knowledge panel) |
| **Code is a first-class citizen** | Not just examples — editable, runnable, saveable |

### 3.2 Pedagogical Integrity

Each mode retains its pedagogical approach. The platform unifies **infrastructure**, not pedagogy:

| Mode | Pedagogy Preserved |
|------|-------------------|
| /build | Anchor discovery, scaffolding (never transmit), surrender recovery |
| /understand | Triple calibration, diagnostic loops, generous teaching moments |
| /research | Source authority tiers, question architecture, evidence-based synthesis |

### 3.3 Compatibility Constraints

Outputs must remain compatible with existing directories:

```
~/Documents/understanding-output/{topic}/   → index.html, mental-model.md, ...
~/Documents/research-output/{topic}/        → index.html, deck.html, narrative.md, ...
~/Documents/build-output/{topic}/           → construction-log.md, mental-model.md, ...
~/Documents/build-output/.learner-profiles/ → {learner-id}.json
```

The platform **wraps** this structure with a richer UI, not replaces it.

---

## 4. System Architecture

### 4.1 High-Level Architecture

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                           FRONTEND (React + TypeScript)                      │
│  ┌─────────────────────┐  ┌─────────────────────┐  ┌─────────────────────┐  │
│  │   Knowledge Galaxy  │  │   Active Session    │  │   Live Knowledge    │  │
│  │       (D3.js)       │  │  (Chat + Mode Tabs) │  │      (Dynamic)      │  │
│  └─────────────────────┘  └─────────────────────┘  └─────────────────────┘  │
│  ┌───────────────────────────────────────────────────────────────────────┐  │
│  │                    Code Sandbox (Monaco Editor)                        │  │
│  └───────────────────────────────────────────────────────────────────────┘  │
└────────────────────────────────────┬────────────────────────────────────────┘
                                     │ WebSocket (bidirectional)
┌────────────────────────────────────┴────────────────────────────────────────┐
│                           BACKEND (FastAPI + Python)                         │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │  Session Manager                                                     │    │
│  │  - WebSocket connection handling                                     │    │
│  │  - Message routing (user ↔ agent)                                    │    │
│  │  - Mode state management                                             │    │
│  │  - UI update dispatch                                                │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │  Knowledge Store (SQLite + JSON files)                               │    │
│  │  - Learner profiles                                                  │    │
│  │  - Session state                                                     │    │
│  │  - Topic graph                                                       │    │
│  │  - Artifact management                                               │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
└────────────────────────────────────┬────────────────────────────────────────┘
                                     │
┌────────────────────────────────────┴────────────────────────────────────────┐
│                         AGENT LAYER (Claude Agent SDK)                       │
│                                                                              │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │  Orchestrator Agent                                                  │    │
│  │  - Session lifecycle                                                 │    │
│  │  - Mode switching with context transfer                              │    │
│  │  - Learner profile management                                        │    │
│  │  - Delegates to specialist agents                                    │    │
│  └──────────────────────────────┬──────────────────────────────────────┘    │
│                 ┌───────────────┼───────────────┐                           │
│                 ▼               ▼               ▼                           │
│  ┌─────────────────┐ ┌─────────────────┐ ┌─────────────────┐               │
│  │  Build Agent    │ │ Understand Agent│ │ Research Agent  │               │
│  │  (Constructiv.) │ │   (Socratic)    │ │  (Evidence)     │               │
│  │                 │ │                 │ │                 │               │
│  │  - Anchors      │ │  - Calibration  │ │  - Questions    │               │
│  │  - Scaffolds    │ │  - Diagnostics  │ │  - Sources      │               │
│  │  - Surrender    │ │  - Teaching     │ │  - Synthesis    │               │
│  └─────────────────┘ └─────────────────┘ └─────────────────┘               │
│                                                                              │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │  Shared Tools (available to all agents)                              │    │
│  │  - update_live_knowledge()     - update_knowledge_graph()            │    │
│  │  - set_code_scaffold()         - read_code_sandbox()                 │    │
│  │  - send_message()              - get_learner_profile()               │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
└─────────────────────────────────────────────────────────────────────────────┘
```

### 4.2 Technology Stack

| Layer | Technology | Rationale |
|-------|------------|-----------|
| **Frontend** | React 18 + TypeScript | Component-based, strong typing |
| **State Management** | Zustand | Lightweight, hooks-based |
| **Graph Visualization** | D3.js | Flexible, industry standard |
| **Code Editor** | Monaco Editor | VS Code engine, full-featured |
| **Styling** | Tailwind CSS | Utility-first, consistent |
| **Backend** | FastAPI (Python 3.11+) | Async, WebSocket support, Python ecosystem |
| **Database** | SQLite | Simple, file-based, portable |
| **Agent SDK** | Claude Agent SDK | Official Anthropic SDK |
| **Communication** | WebSocket | Bidirectional, real-time |

### 4.3 Communication Flow

```
User types message
       │
       ▼
┌─────────────────┐
│  Frontend       │ ──WebSocket──▶ ┌─────────────────┐
│  (React)        │                │  Backend        │
└─────────────────┘                │  (FastAPI)      │
       ▲                           └────────┬────────┘
       │                                    │
       │                                    ▼
       │                           ┌─────────────────┐
       │                           │  Orchestrator   │
       │                           │  Agent          │
       │                           └────────┬────────┘
       │                                    │
       │                                    ▼
       │                           ┌─────────────────┐
       │                           │  Specialist     │
       │                           │  Agent (mode)   │
       │                           └────────┬────────┘
       │                                    │
       │     Tool calls for UI updates      │
       └────────────────────────────────────┘

UI Update Tools:
  - update_live_knowledge(content) → Live Knowledge panel
  - update_knowledge_graph(action) → Knowledge Galaxy
  - set_code_scaffold(code)        → Code Sandbox
  - send_message(content)          → Active Session chat
```

### 4.4 Directory Structure

```
knowledge-forge/
├── frontend/
│   ├── src/
│   │   ├── components/
│   │   │   ├── KnowledgeGalaxy/    # D3.js graph visualization
│   │   │   ├── ActiveSession/       # Chat + mode tabs
│   │   │   ├── LiveKnowledge/       # Dynamic status panel
│   │   │   ├── CodeSandbox/         # Monaco editor wrapper
│   │   │   └── common/              # Shared components
│   │   ├── stores/                  # Zustand state stores
│   │   ├── hooks/                   # Custom React hooks
│   │   ├── types/                   # TypeScript types
│   │   └── utils/                   # Utility functions
│   ├── package.json
│   └── vite.config.ts
│
├── backend/
│   ├── app/
│   │   ├── main.py                  # FastAPI app entry
│   │   ├── routers/
│   │   │   ├── sessions.py          # Session endpoints
│   │   │   ├── websocket.py         # WebSocket handler
│   │   │   └── learner.py           # Profile endpoints
│   │   ├── models/                  # Pydantic models
│   │   ├── services/
│   │   │   ├── session_manager.py
│   │   │   ├── knowledge_store.py
│   │   │   └── agent_bridge.py      # Agent SDK integration
│   │   └── db/                      # SQLite operations
│   ├── agents/
│   │   ├── orchestrator.py          # Main orchestrator agent
│   │   ├── build_agent.py           # /build specialist
│   │   ├── understand_agent.py      # /understand specialist
│   │   ├── research_agent.py        # /research specialist
│   │   └── tools/                   # Shared tool definitions
│   └── pyproject.toml
│
├── docs/
│   ├── spec.md                      # This document
│   ├── design.md                    # Design decisions
│   └── api.md                       # API documentation
│
└── CLAUDE.md                        # Project instructions
```

---

## 5. Data Models

### 5.1 Core Entities

#### LearnerProfile (Unified, Cross-Session)

The single source of truth for learner state, enriched by all modes.

```typescript
interface LearnerProfile {
  learner_id: string;
  created_at: ISO8601;
  last_session: ISO8601;
  sessions_completed: number;

  // From /build
  anchor_inventory: {
    strong: Anchor[];
    medium: Anchor[];
    weak: Anchor[];
  };

  // Unified from all modes
  learning_patterns: {
    preferred_mode: "building" | "questioning" | "researching";
    preferred_style: "code_examples" | "scenarios" | "theory_first" | "visual";
    scaffold_preference: "start_light" | "start_medium" | "start_heavy";
    avg_rounds_per_concept: number;
    surrender_frequency: "none" | "low" | "medium" | "high";
    effective_recovery_strategies: string[];
    ineffective_strategies: string[];
  };

  // Mastery across all learning
  concept_mastery: ConceptMastery[];

  // Preferences
  preferences: {
    pace: "focused" | "standard" | "thorough";
    code_language: "python" | "typescript" | "go" | "multiple";
    theme: "paper-ink" | "modern-blue" | "minimal";
  };

  // Free-form observations
  notes: string[];
}

interface Anchor {
  anchor: string;
  description: string;
  used_in: string[];  // topic slugs
  success_rate: number;
  last_used: ISO8601;
}

interface ConceptMastery {
  topic: string;
  concepts: string[];
  status: "explored" | "partial" | "solid";
  learned_via: "build" | "understand" | "research";
  date: ISO8601;
}
```

#### Session (Single Learning Session)

```typescript
interface Session {
  session_id: string;
  learner_id: string;
  topic_id: string;

  current_mode: "build" | "understand" | "research";

  // Mode-specific state (only active mode is "hot")
  mode_states: {
    build: BuildState | null;
    understand: UnderstandState | null;
    research: ResearchState | null;
  };

  // Shared across modes
  shared_context: {
    established_concepts: string[];      // Things we know the learner knows
    active_questions: string[];          // Open questions across modes
    code_artifacts: CodeArtifact[];      // Code created during session
    discovered_connections: TopicEdge[]; // New topic relationships
  };

  messages: Message[];

  created_at: ISO8601;
  updated_at: ISO8601;
  status: "active" | "paused" | "completed";
}

interface Message {
  id: string;
  role: "user" | "assistant" | "system";
  content: string;
  mode: "build" | "understand" | "research";
  timestamp: ISO8601;
  metadata?: {
    tool_calls?: ToolCall[];
    ui_updates?: UIUpdate[];
  };
}
```

#### BuildState (Constructivist Mode)

```typescript
interface BuildState {
  // Phase tracking
  phase: "anchor_discovery" | "mlo_planning" | "construction" | "consolidation";

  // From Phase 0
  anchor_map: {
    strong: AnchorEvidence[];
    medium: AnchorEvidence[];
    weak: AnchorEvidence[];
    unexplored: string[];
  };
  primary_anchor: string | null;

  // From Phase 1
  mlo: SLO[];
  current_slo_index: number;

  // Working memory (current SLO)
  working_memory: {
    slo: SLO;
    round: number;
    scaffold_level: "heavy" | "medium" | "light" | "none";
    mode: "normal" | "surrender_recovery" | "code";
    construction_log: ConstructionRound[];
    last_scaffold: Scaffold;
  };

  // Session memory (completed SLOs)
  session_memory: {
    constructed_concepts: ConstructedConcept[];
    effective_scaffolds: string[];
    surrender_history: SurrenderEvent[];
    patterns_observed: string[];
  };
}

interface SLO {
  id: string;
  statement: string;
  frame: "BUILD" | "CONNECT" | "TRANSFER" | "DISTINGUISH" | "DEBUG";
  anchor: string;
  in_scope: string[];
  out_of_scope: string[];
  code_mode_likely: boolean;
  estimated_rounds: number;
  status: "pending" | "in_progress" | "constructed" | "partial" | "skipped";
}

interface ConstructedConcept {
  concept: string;
  anchor_used: string;
  bridge: string;
  breakthrough_moment: string;
  rounds: number;
  surrenders: number;
  code_mode_used: boolean;
  scaffold_exit_level: string;
  status: "solid" | "partial";
}
```

#### UnderstandState (Socratic Mode)

```typescript
interface UnderstandState {
  // Configuration
  preferences: {
    pace: "standard" | "thorough" | "focused";
    style: "balanced" | "example-heavy" | "theory-first" | "visual";
    context: string;
  };

  // Phase tracking
  phase: "configuration" | "calibration" | "diagnostic" | "completion";

  // SLO tracking
  mlo: SLO[];
  current_slo_index: number;

  // Knowledge state for current SLO
  knowledge_state_map: {
    vocabulary: FacetState;
    mental_model: FacetState;
    practical_grasp: FacetState;
    boundary_conditions: FacetState;
    transfer: FacetState;
  };

  // Diagnostic loop counters
  counters: {
    total_rounds: number;
    consecutive_passes: number;
    transfer_passes: number;
    facet_rounds: Record<string, number>;
  };

  // Round history
  rounds: DiagnosticRound[];
}

interface FacetState {
  status: "missing" | "shaky" | "solid";
  evidence: string;
  source_probe: string;
  rounds_spent: number;
  last_result: "pass" | "fail" | null;
}

interface DiagnosticRound {
  round_number: number;
  target_facet: string;
  diagnostic_question: string;
  learner_response: string;
  evaluation: "strong" | "partial" | "weak" | "missing";
  teaching_moment: string | null;
  check_question: string | null;
  check_result: "pass" | "fail" | null;
}
```

#### ResearchState (Evidence-Based Mode)

```typescript
interface ResearchState {
  // Configuration
  config: {
    mode: "quick" | "standard" | "deep";
    focus: "practical" | "conceptual" | "comparative" | "comprehensive";
    source_preference: "cutting-edge" | "established" | "academic" | "mixed";
    code_language: string;
  };

  // Intention
  intention: {
    topic: string;
    refined_topic: string;
    goal: string;
    audience: string;
    research_type: "CODE_FOCUSED" | "CONCEPT_FOCUSED" | "COMPARATIVE" | "ECOSYSTEM";
  };

  // Questions
  questions: ResearchQuestion[];

  // Sources
  sources: Source[];

  // Libraries (for CODE_FOCUSED)
  libraries: Library[];

  // Coverage
  coverage: {
    strong: string[];    // question IDs
    adequate: string[];
    weak: string[];
    unanswered: string[];
  };

  // Phase
  phase: "configuration" | "questions" | "research" | "synthesis" | "complete";
}

interface ResearchQuestion {
  id: string;
  question: string;
  frame: "WHAT" | "WHY" | "HOW" | "WHEN" | "CODE" | "PITFALL";
  concept_layer: "core" | "adjacent" | "neighboring";
  priority: "high" | "medium" | "low";
  story_order: number;
  requires_code: boolean;
  sources: string[];  // source IDs that answer this
  status: "pending" | "answered" | "weak" | "dropped";
}

interface Source {
  id: string;
  url: string;
  title: string;
  tier: 1 | 2 | 3 | 4 | 5;
  authority_score: number;
  recency_factor: number;
  final_score: number;
  questions_answered: string[];
  key_quotes: string[];
  accessed_at: ISO8601;
}
```

#### Topic (Knowledge Galaxy Node)

```typescript
interface Topic {
  topic_id: string;
  title: string;
  slug: string;

  mastery: {
    level: "none" | "explored" | "partial" | "solid";
    last_session: ISO8601;
    total_sessions: number;
    modes_used: ("build" | "understand" | "research")[];
  };

  // Sub-concepts within topic
  concepts: {
    name: string;
    status: "unexplored" | "partial" | "solid";
    learned_via: string;  // session_id
  }[];

  // Artifact locations
  artifacts: {
    build?: string;      // path to build-output
    understand?: string; // path to understanding-output
    research?: string;   // path to research-output
  };

  // Metadata
  created_at: ISO8601;
  updated_at: ISO8601;
  tags: string[];
}

interface TopicEdge {
  id: string;
  source_topic_id: string;
  target_topic_id: string;

  edge_type: "prerequisite" | "related" | "builds_on" | "contrasts" | "example_of";

  // How this connection was discovered
  created_by: "user" | "system" | "agent";
  discovered_in: string;  // session_id

  strength: number;  // 0-1, how strong the connection

  created_at: ISO8601;
}
```

### 5.2 Entity Relationships

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                           ENTITY RELATIONSHIPS                               │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  LearnerProfile (1) ◄─────────────────────────────────► (*) Session          │
│       │                                                        │             │
│       │ has                                              has   │             │
│       ▼                                                        ▼             │
│  anchor_inventory                                    mode_states             │
│  concept_mastery                                          │                  │
│  learning_patterns                          ┌─────────────┼─────────────┐   │
│                                             ▼             ▼             ▼   │
│                                       BuildState   UnderstandState  ResearchState
│                                                                              │
│  Topic (*) ◄────────────────────────────────────────────► (*) Topic          │
│       │                    TopicEdge                           │             │
│       │                                                        │             │
│       │ has sessions                                           │             │
│       ▼                                                        │             │
│  Session (*) ─────────────────────────────────────────────────►│             │
│                                                                              │
│  Topic (1) ◄───────────────────────────────────────────► (*) Artifact        │
│                         has outputs                                          │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## 6. UI/UX Specification

### 6.1 Four-Pane Layout

```
┌─────────────────────────────────────────────────────────────────────────────┐
│  ◉ Knowledge Forge                                    [Anurag] [Settings]   │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  ┌─────────────────────────────┐  ┌──────────────────────────────────────┐  │
│  │                             │  │                                      │  │
│  │    KNOWLEDGE GALAXY         │  │     ACTIVE SESSION                   │  │
│  │                             │  │                                      │  │
│  │    [Interactive D3 graph]   │  │  [build] [understand] [research]     │  │
│  │                             │  │  ─────────────────────────────────   │  │
│  │    ● = solid                │  │                                      │  │
│  │    ◐ = partial              │  │  [Chat messages here]                │  │
│  │    ○ = explored             │  │                                      │  │
│  │                             │  │                                      │  │
│  │    Click to navigate        │  │  ┌──────────────────────────────┐   │  │
│  │                             │  │  │ Type your message...    [→]  │   │  │
│  │                             │  │  └──────────────────────────────┘   │  │
│  │  Height: 40%                │  │  Height: 40%                        │  │
│  └─────────────────────────────┘  └──────────────────────────────────────┘  │
│                                                                              │
│  ┌─────────────────────────────┐  ┌──────────────────────────────────────┐  │
│  │                             │  │                                      │  │
│  │    LIVE KNOWLEDGE           │  │     CODE SANDBOX                     │  │
│  │                             │  │                                      │  │
│  │    [Mode-specific panel]    │  │  [Monaco Editor]                     │  │
│  │                             │  │                                      │  │
│  │    - Current progress       │  │  Language: Python ▼                  │  │
│  │    - State indicators       │  │                                      │  │
│  │    - Available resources    │  │  [Run] [Save] [Clear]                │  │
│  │                             │  │                                      │  │
│  │  Height: 60%                │  │  Height: 60%                         │  │
│  └─────────────────────────────┘  └──────────────────────────────────────┘  │
│                                                                              │
│  Left column: 35%                 Right column: 65%                          │
└─────────────────────────────────────────────────────────────────────────────┘
```

### 6.2 Pane Specifications

#### Knowledge Galaxy (Top-Left)

**Purpose:** Visual map of all topics/concepts with mastery indicators and connections.

**Components:**
- D3.js force-directed graph
- Nodes = Topics (sized by importance, colored by mastery)
- Edges = Relationships (styled by type)
- Current topic highlighted
- Zoom/pan controls
- Click to navigate

**Interactions:**
| Action | Result |
|--------|--------|
| Click node | Navigate to topic (prompts if unsaved) |
| Hover node | Show topic summary tooltip |
| Drag node | Rearrange graph |
| Double-click empty | Create new topic |
| Right-click node | Context menu (delete, rename, connect) |
| Scroll | Zoom in/out |

**Visual Encoding:**
| Element | Meaning |
|---------|---------|
| Node size | Concept count / importance |
| Node color (solid green) | Mastery: solid |
| Node color (half green) | Mastery: partial |
| Node color (outline) | Mastery: explored |
| Node color (gray) | Mastery: none |
| Edge solid | Prerequisite |
| Edge dashed | Related |
| Edge dotted | Builds on |

#### Active Session (Top-Right)

**Purpose:** Primary conversation interface with mode-switching tabs.

**Components:**
- Mode tabs: [build] [understand] [research]
- Active tab indicator (highlighted, possibly different color per mode)
- Message list (scrollable)
- Message input with send button
- Typing indicator when agent is responding

**Mode Tab Behavior:**
| Switch | Context Transfer |
|--------|------------------|
| Any → build | Established concepts become potential anchors |
| Any → understand | Create SLOs from current focus |
| Any → research | Current questions become research questions |

**Message Types:**
| Type | Styling |
|------|---------|
| User message | Right-aligned, blue background |
| Assistant message | Left-aligned, gray background |
| System message | Centered, italic, muted |
| Code block | Syntax highlighted, copy button |
| Question with options | Radio/checkbox buttons |

#### Live Knowledge (Bottom-Left)

**Purpose:** Real-time display of learning state, mode-specific.

**Build Mode Content:**
```
┌─────────────────────────────────┐
│ CURRENTLY BUILDING              │
│ ► [SLO statement]               │
│   Round 3 of ~5 | Medium scaffold│
│                                 │
│ ─────────────────────────────── │
│ USING ANCHORS                   │
│ ● print_debugging (strong)      │
│ ◐ recipe_following (trying)     │
│                                 │
│ ─────────────────────────────── │
│ CONSTRUCTED TODAY               │
│ ✓ agent_reasoning_visibility    │
│ ✓ react_loop_structure          │
│ ◐ failure_modes (partial)       │
│                                 │
│ ─────────────────────────────── │
│ FROM YOUR PROFILE               │
│ Strong: HTTP endpoints,         │
│         sklearn workflow        │
│ Medium: Tesseract OCR           │
└─────────────────────────────────┘
```

**Understand Mode Content:**
```
┌─────────────────────────────────┐
│ KNOWLEDGE STATE                 │
│                                 │
│ Vocabulary    [████░] Solid     │
│ Mental Model  [██░░░] Shaky     │
│ Boundaries    [░░░░░] Missing   │
│ Transfer      [░░░░░] Untested  │
│                                 │
│ ─────────────────────────────── │
│ SESSION PROGRESS                │
│ Round 4/7+ | Passes: 2/3        │
│ Facet focus: Mental Model       │
│                                 │
│ ─────────────────────────────── │
│ CURRENT SLO                     │
│ "Explain what database indexes  │
│  do to a junior developer"      │
│                                 │
│ ─────────────────────────────── │
│ REMAINING SLOs                  │
│ ○ Query optimization            │
│ ○ Index trade-offs              │
└─────────────────────────────────┘
```

**Research Mode Content:**
```
┌─────────────────────────────────┐
│ RESEARCH PROGRESS               │
│                                 │
│ Questions: ████████░░░░ 8/12    │
│                                 │
│ ─────────────────────────────── │
│ SOURCE QUALITY                  │
│ Tier 1 (Official):     4        │
│ Tier 2 (Engineering):  6        │
│ Tier 3+ (Other):       3        │
│                                 │
│ ─────────────────────────────── │
│ LIBRARIES DISCOVERED            │
│ ● langgraph    ★5.2k  Active    │
│ ● crewai       ★12k   Active    │
│ ○ autogen      ★8k    Stale?    │
│                                 │
│ ─────────────────────────────── │
│ NEEDS ATTENTION                 │
│ ⚠ "When to use X vs Y"          │
│ ⚠ "Production considerations"   │
│                                 │
│ ─────────────────────────────── │
│ PHASE: Gathering sources        │
└─────────────────────────────────┘
```

#### Code Sandbox (Bottom-Right)

**Purpose:** Interactive code editing, viewing, and execution.

**Components:**
- Monaco Editor instance
- Language selector dropdown
- Toolbar: [Run] [Save to Project] [Copy] [Clear]
- Output panel (collapsible, below editor)
- Diff view toggle (compare with scaffold)

**Behavior:**
| Trigger | Action |
|---------|--------|
| Agent calls `set_code_scaffold()` | Populate editor with code |
| User edits | Track changes, agent can call `read_code_sandbox()` |
| User clicks Run | Execute code, show output |
| User clicks Save | Save to project directory |

**Editor Features:**
- Syntax highlighting (via Monaco)
- Auto-completion (basic)
- Line numbers
- Error highlighting
- Read-only mode (when displaying scaffolds for examination)

### 6.3 Responsive Behavior

| Viewport | Layout |
|----------|--------|
| Desktop (>1200px) | 4-pane as shown |
| Tablet (768-1200px) | 2-column, panes stack vertically |
| Mobile (<768px) | Single column, tabs to switch panes |

### 6.4 Theme

Following user preference: **Light backgrounds always.**

| Element | Color |
|---------|-------|
| Background | #FAFAFA |
| Primary text | #1A1A1A |
| Secondary text | #666666 |
| Build mode accent | #10B981 (green) |
| Understand mode accent | #3B82F6 (blue) |
| Research mode accent | #8B5CF6 (purple) |
| Borders | #E5E5E5 |
| Code background | #F5F5F5 |

---

## 7. Agent Architecture

### 7.1 Agent Hierarchy

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                              ORCHESTRATOR AGENT                              │
│                                                                              │
│  Responsibilities:                                                           │
│  - Session lifecycle management                                              │
│  - Mode switching with context transfer                                      │
│  - Learner profile access and updates                                        │
│  - Delegation to specialist agents                                           │
│  - Topic graph management                                                    │
│                                                                              │
│  Does NOT do:                                                                │
│  - Actual teaching (delegates to specialists)                                │
│  - Source research (delegates to research agent)                             │
│  - Scaffold generation (delegates to build agent)                            │
└─────────────────────────────────────────────────────────────────────────────┘
                                    │
                                    │ delegates based on current_mode
                                    │
         ┌──────────────────────────┼──────────────────────────┐
         ▼                          ▼                          ▼
┌─────────────────┐      ┌─────────────────┐      ┌─────────────────┐
│  BUILD AGENT    │      │ UNDERSTAND AGENT│      │ RESEARCH AGENT  │
│                 │      │                 │      │                 │
│  Pedagogy:      │      │  Pedagogy:      │      │  Pedagogy:      │
│  Constructivist │      │  Socratic       │      │  Evidence-based │
│                 │      │                 │      │                 │
│  Phases:        │      │  Phases:        │      │  Phases:        │
│  - Anchor disc. │      │  - Config       │      │  - Config       │
│  - MLO planning │      │  - Calibration  │      │  - Questions    │
│  - Construction │      │  - Diagnostic   │      │  - Research     │
│  - Consolidate  │      │  - Completion   │      │  - Synthesis    │
│                 │      │                 │      │                 │
│  Special modes: │      │  Special modes: │      │  Special modes: │
│  - Surrender    │      │  - Teaching     │      │  - Library disc │
│  - Code mode    │      │    moments      │      │  - arXiv handle │
└─────────────────┘      └─────────────────┘      └─────────────────┘
```

### 7.2 Tool Definitions

#### Orchestrator Tools

```python
# Session Management
def create_session(learner_id: str, topic: str) -> Session:
    """Create a new learning session for a topic."""

def get_session_state(session_id: str) -> Session:
    """Get current session state including mode states."""

def end_session(session_id: str, summary: str) -> None:
    """End session, persist state, generate artifacts."""

# Mode Switching
def switch_mode(
    target_mode: Literal["build", "understand", "research"],
    context_transfer: ContextTransfer
) -> None:
    """Switch to target mode, transferring relevant context."""

# Learner Profile
def get_learner_profile(learner_id: str) -> LearnerProfile:
    """Get learner profile with anchors, patterns, mastery."""

def update_learner_profile(
    learner_id: str,
    updates: ProfileUpdate
) -> LearnerProfile:
    """Update learner profile with new information."""

# Topic Graph
def add_topic(topic: Topic) -> Topic:
    """Add new topic to knowledge galaxy."""

def connect_topics(
    source_id: str,
    target_id: str,
    edge_type: str
) -> TopicEdge:
    """Create connection between topics."""

def update_topic_mastery(
    topic_id: str,
    mastery: MasteryLevel
) -> Topic:
    """Update mastery level for a topic."""
```

#### Shared UI Tools (All Agents)

```python
def update_live_knowledge(content: LiveKnowledgeContent) -> None:
    """Update the Live Knowledge panel with mode-specific content.

    Content structure varies by mode:
    - build: current_slo, anchors, constructed_concepts
    - understand: knowledge_state_map, counters, current_slo
    - research: coverage, sources, libraries, phase
    """

def update_knowledge_graph(action: GraphAction) -> None:
    """Update the Knowledge Galaxy visualization.

    Actions:
    - add_node: Add new topic node
    - update_node: Update node properties (mastery, size)
    - add_edge: Connect topics
    - highlight: Highlight current topic
    """

def set_code_scaffold(
    code: str,
    language: str,
    instructions: str,
    read_only: bool = False
) -> None:
    """Set code in the Code Sandbox.

    Use for:
    - Code examples to examine
    - Scaffolds to complete
    - Code to debug
    """

def read_code_sandbox() -> CodeSandboxState:
    """Read current state of Code Sandbox.

    Returns:
    - current_code: What's in the editor
    - language: Selected language
    - has_changes: Whether user modified scaffold
    - execution_output: Last run output (if any)
    """

def send_message(
    content: str,
    message_type: Literal["text", "question", "code", "system"]
) -> None:
    """Send message to Active Session chat."""

def ask_user(
    question: str,
    options: List[Option],
    multi_select: bool = False
) -> UserResponse:
    """Present question with options to user."""
```

#### Build Agent Tools

```python
def discover_anchors(
    topic: str,
    existing_profile: LearnerProfile
) -> AnchorMap:
    """Discover learner's existing knowledge that connects to topic.

    Uses profile's existing anchors + asks probing questions.
    """

def create_slo(
    statement: str,
    frame: SLOFrame,
    anchor: str,
    code_mode_likely: bool
) -> SLO:
    """Create a Session Learning Objective."""

def create_scaffold(
    slo: SLO,
    level: ScaffoldLevel,
    scaffold_type: ScaffoldType
) -> Scaffold:
    """Create a scaffold for the current SLO.

    Types: question, scenario, code_complete, code_examine, code_debug
    Levels: heavy, medium, light, none
    """

def evaluate_construction(
    learner_response: str,
    expected_construction: str
) -> ConstructionResult:
    """Evaluate whether learner constructed the concept.

    Returns: CONSTRUCTED, PARTIAL, STUCK, SURRENDERED, UNEXPECTED
    """

def execute_surrender_recovery(
    strategy: SurrenderStrategy,
    context: SurrenderContext
) -> Scaffold:
    """Execute surrender recovery protocol.

    Strategies: heavier_scaffold, different_anchor, decompose_leap,
                code_mode, partial_answer
    """

def checkpoint_construction(
    slo: SLO,
    construction_log: List[ConstructionRound]
) -> CompressedConstruction:
    """Compress construction transcript for session memory."""
```

#### Understand Agent Tools

```python
def run_calibration_probe(
    probe_type: Literal["feynman", "minimal_example", "misconception"],
    slo: SLO
) -> CalibrationResult:
    """Run one of three calibration probes for Triple Calibration."""

def evaluate_facet(
    response: str,
    facet: Facet,
    rubric: EvaluationRubric
) -> FacetEvaluation:
    """Evaluate learner response against facet rubric."""

def generate_teaching_moment(
    gap: Gap,
    style: TeachingStyle,
    pace: Pace
) -> TeachingMoment:
    """Generate generous teaching moment for revealed gap.

    Includes: reflection, core explanation, examples (3),
              visual (optional), key insight, common traps
    """

def update_knowledge_state(
    facet: Facet,
    status: FacetStatus,
    evidence: str
) -> KnowledgeStateMap:
    """Update knowledge state map for current SLO."""

def check_exit_conditions(
    counters: DiagnosticCounters,
    knowledge_state: KnowledgeStateMap
) -> ExitCheck:
    """Check if SLO exit conditions are met.

    Conditions: rounds >= 7, all facets >= 2 rounds,
                consecutive_passes >= 3, transfer_passes >= 2,
                no facet is Missing
    """
```

#### Research Agent Tools

```python
def generate_questions(
    topic: str,
    intention: Intention,
    mode: ResearchMode
) -> List[ResearchQuestion]:
    """Generate research questions for topic.

    Frames: WHAT, WHY, HOW, WHEN, CODE, PITFALL
    """

def search_sources(
    query: str,
    tier_filter: Optional[List[int]] = None
) -> List[Source]:
    """Search for authoritative sources.

    Uses AI-specific source authority tiers.
    """

def evaluate_source(
    url: str,
    questions: List[str]
) -> SourceEvaluation:
    """Evaluate source authority and relevance.

    Calculates: tier, authority_score, recency_factor,
                questions_answered
    """

def research_library(
    library_name: str
) -> LibraryEvaluation:
    """Research a GitHub library/repo.

    Checks: stars, last_commit, contributors, documentation,
            tests, license, endorsements
    """

def check_coverage(
    questions: List[ResearchQuestion],
    sources: List[Source]
) -> CoverageReport:
    """Check source coverage for questions.

    Categories: strong (2+ Tier 1-2), adequate (1 Tier 1-2),
                weak (Tier 3+ only), none
    """

def synthesize_content(
    questions: List[ResearchQuestion],
    sources: List[Source],
    output_type: Literal["narrative", "reference", "deck"]
) -> SynthesizedContent:
    """Synthesize sources into output content."""
```

### 7.3 Agent Prompts (Summarized)

Each specialist agent has a detailed system prompt based on the existing skill specs:

| Agent | Base Spec | Key Adaptations |
|-------|-----------|-----------------|
| Build Agent | `/build-v1.md` | Add UI update tools, integrate with session state |
| Understand Agent | `/understand-v3.md` | Add UI update tools, share learner profile |
| Research Agent | `/research-v3.md` | Add UI update tools, integrate with topic graph |

---

## 8. Mode Integration

### 8.1 Context Transfer Matrix

When switching modes, context must be transferred appropriately:

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                         CONTEXT TRANSFER MATRIX                              │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  FROM ╲ TO │    BUILD         │    UNDERSTAND     │    RESEARCH            │
│  ──────────┼───────────────────┼───────────────────┼────────────────────────│
│            │                   │                   │                        │
│  BUILD     │        —          │ Constructed       │ Current SLO →          │
│            │                   │ concepts →        │ high-priority question │
│            │                   │ "Solid" facets    │                        │
│            │                   │                   │ Gaps → research seeds  │
│  ──────────┼───────────────────┼───────────────────┼────────────────────────│
│            │                   │                   │                        │
│  UNDERSTAND│ Solid facets →    │        —          │ Research seeds →       │
│            │ potential anchors │                   │ questions              │
│            │                   │                   │                        │
│            │ Shaky/Missing →   │                   │ Missing facets →       │
│            │ concepts to build │                   │ high-priority Qs       │
│  ──────────┼───────────────────┼───────────────────┼────────────────────────│
│            │                   │                   │                        │
│  RESEARCH  │ Key findings →    │ Answered Qs →     │        —               │
│            │ new anchors       │ pre-populate      │                        │
│            │                   │ knowledge state   │                        │
│            │ Code examples →   │                   │                        │
│            │ scaffolds         │ Gaps → SLOs       │                        │
│            │                   │                   │                        │
└─────────────────────────────────────────────────────────────────────────────┘
```

### 8.2 Transfer Implementations

#### BUILD → UNDERSTAND

```python
def transfer_build_to_understand(build_state: BuildState) -> UnderstandState:
    """Transfer context from build to understand mode."""

    # Constructed concepts become pre-validated knowledge
    pre_validated = {
        facet: "solid"
        for concept in build_state.session_memory.constructed_concepts
        if concept.status == "solid"
    }

    # Current SLO becomes first understand SLO
    understand_slos = [
        SLO(
            statement=f"Verify understanding of {build_state.working_memory.slo.statement}",
            frame="EXPLAIN"
        )
    ]

    return UnderstandState(
        knowledge_state_map=initialize_with_prevalidated(pre_validated),
        mlo=understand_slos,
        # Skip calibration for pre-validated facets
    )
```

#### UNDERSTAND → BUILD

```python
def transfer_understand_to_build(understand_state: UnderstandState) -> BuildState:
    """Transfer context from understand to build mode."""

    # Solid facets become potential anchors
    new_anchors = [
        Anchor(
            anchor=facet_name,
            description=f"Verified understanding from /understand session",
            strength="medium"  # Promote to strong if used successfully
        )
        for facet_name, state in understand_state.knowledge_state_map.items()
        if state.status == "solid"
    ]

    # Shaky/missing become concepts to construct
    concepts_to_build = [
        facet_name
        for facet_name, state in understand_state.knowledge_state_map.items()
        if state.status in ("shaky", "missing")
    ]

    return BuildState(
        anchor_map=merge_anchors(existing_anchors, new_anchors),
        mlo=generate_slos_for_concepts(concepts_to_build)
    )
```

#### ANY → RESEARCH

```python
def transfer_to_research(
    source_state: Union[BuildState, UnderstandState],
    source_mode: str
) -> ResearchState:
    """Transfer context to research mode."""

    questions = []

    if source_mode == "build":
        # Current SLO becomes high-priority question
        questions.append(ResearchQuestion(
            question=f"How does {source_state.working_memory.slo.statement}?",
            priority="high",
            frame="HOW"
        ))

        # Gaps from anchors become questions
        for anchor in source_state.anchor_map.weak:
            questions.append(ResearchQuestion(
                question=f"What is {anchor.anchor} and how does it connect?",
                priority="medium"
            ))

    elif source_mode == "understand":
        # Missing/shaky facets become questions
        for facet, state in source_state.knowledge_state_map.items():
            if state.status in ("missing", "shaky"):
                questions.append(ResearchQuestion(
                    question=f"What is the {facet} of this concept?",
                    priority="high"
                ))

    return ResearchState(
        questions=questions,
        phase="questions"  # Skip to question review
    )
```

### 8.3 Shared Context

Some context is shared across all modes and persists throughout the session:

```typescript
interface SharedContext {
  // Concepts we KNOW the learner understands
  // (from any mode's verification)
  established_concepts: string[];

  // Open questions that haven't been fully answered
  // (across all modes)
  active_questions: string[];

  // Code artifacts created during session
  // (available to all modes)
  code_artifacts: CodeArtifact[];

  // Topic connections discovered during session
  // (added to Knowledge Galaxy)
  discovered_connections: TopicEdge[];

  // Current focus/goal (natural language)
  current_focus: string;
}
```

---

## 9. API Contracts

### 9.1 REST Endpoints

#### Sessions

```
POST   /api/sessions
       Create new session
       Body: { learner_id, topic, initial_mode }
       Returns: Session

GET    /api/sessions/{session_id}
       Get session state
       Returns: Session

PUT    /api/sessions/{session_id}
       Update session (mode switch, etc.)
       Body: { current_mode?, status? }
       Returns: Session

DELETE /api/sessions/{session_id}
       End and archive session
       Returns: { artifacts_generated: string[] }
```

#### Learner Profiles

```
GET    /api/learners/{learner_id}/profile
       Get learner profile
       Returns: LearnerProfile

PUT    /api/learners/{learner_id}/profile
       Update learner profile
       Body: Partial<LearnerProfile>
       Returns: LearnerProfile
```

#### Topics

```
GET    /api/topics
       List all topics
       Query: ?mastery=solid|partial|explored
       Returns: Topic[]

POST   /api/topics
       Create new topic
       Body: { title, slug }
       Returns: Topic

GET    /api/topics/{topic_id}
       Get topic with edges
       Returns: { topic: Topic, edges: TopicEdge[] }

POST   /api/topics/{topic_id}/edges
       Connect topics
       Body: { target_id, edge_type }
       Returns: TopicEdge
```

### 9.2 WebSocket Protocol

#### Connection

```
WS /ws/session/{session_id}

On connect: Server sends current session state
On disconnect: Server persists session state
```

#### Message Types

```typescript
// Client → Server
interface ClientMessage {
  type: "user_message" | "mode_switch" | "code_update" | "command";
  payload: {
    content?: string;       // For user_message
    target_mode?: string;   // For mode_switch
    code?: string;          // For code_update
    command?: string;       // For command (/pause, /status, etc.)
  };
}

// Server → Client
interface ServerMessage {
  type: "assistant_message" | "ui_update" | "state_change" | "error";
  payload: {
    content?: string;              // For assistant_message
    update_type?: string;          // For ui_update
    update_data?: any;             // For ui_update
    new_state?: Partial<Session>;  // For state_change
    error?: string;                // For error
  };
}

// UI Update Types
type UIUpdateType =
  | "live_knowledge"      // Update Live Knowledge panel
  | "knowledge_graph"     // Update Knowledge Galaxy
  | "code_sandbox"        // Update Code Sandbox
  | "mode_indicator"      // Update mode tabs
  | "typing_indicator";   // Show/hide typing
```

#### Example Flow

```
1. User sends message:
   { type: "user_message", payload: { content: "I want to learn about agents" } }

2. Server acknowledges, shows typing:
   { type: "ui_update", payload: { update_type: "typing_indicator", update_data: true } }

3. Agent processes, sends UI updates:
   { type: "ui_update", payload: {
     update_type: "live_knowledge",
     update_data: { phase: "anchor_discovery", ... }
   }}

4. Agent sends response:
   { type: "assistant_message", payload: {
     content: "Before we explore agents, what's your background with..."
   }}

5. Server hides typing:
   { type: "ui_update", payload: { update_type: "typing_indicator", update_data: false } }
```

---

## 10. MVP Phases

### Phase 1: Core Loop (Build Mode Only)

**Goal:** Working 4-pane UI with /build functionality.

**Scope:**
- [ ] React frontend with 4-pane layout
- [ ] FastAPI backend with session management
- [ ] WebSocket communication
- [ ] Agent SDK with Build Agent only
- [ ] Live Knowledge panel (build-specific)
- [ ] Code Sandbox (display + read, no execution)
- [ ] Basic learner profile (read from existing)
- [ ] SQLite session storage

**Not in Scope:**
- Understand/Research modes
- Knowledge Galaxy visualization
- Code execution
- Mode switching
- Topic graph persistence

**Success Criteria:**
- Complete a /build session through web UI
- Live Knowledge updates in real-time
- Code scaffolds appear in sandbox
- Session state persists across page refresh

**Estimated Effort:** Foundation

---

### Phase 2: Multi-Mode

**Goal:** All three modes working with context-preserving switching.

**Scope:**
- [ ] Understand Agent implementation
- [ ] Research Agent implementation
- [ ] Mode switching with context transfer
- [ ] Mode-specific Live Knowledge panels
- [ ] Unified learner profile (write back)
- [ ] Mode tabs in Active Session

**Dependencies:** Phase 1 complete

**Success Criteria:**
- Switch between all three modes without losing context
- Learner profile updated by all modes
- Each mode has appropriate Live Knowledge display

**Estimated Effort:** Moderate

---

### Phase 3: Knowledge Galaxy

**Goal:** Visual topic graph with navigation.

**Scope:**
- [ ] D3.js force-directed graph component
- [ ] Topic CRUD operations
- [ ] Edge creation (manual + auto-suggested)
- [ ] Mastery visualization
- [ ] Click-to-navigate
- [ ] Topic persistence (SQLite)

**Dependencies:** Phase 2 complete

**Success Criteria:**
- Visual graph shows all topics
- Mastery indicators reflect actual state
- Can navigate between topics via graph
- System suggests connections

**Estimated Effort:** Moderate

---

### Phase 4: Full Integration

**Goal:** Complete platform with all features.

**Scope:**
- [ ] Code execution in sandbox (sandboxed Python/JS)
- [ ] Save to project functionality
- [ ] Export to existing directories
- [ ] Blog conversion integration
- [ ] Source library persistence
- [ ] Multi-session memory
- [ ] Mobile responsive design

**Dependencies:** Phase 3 complete

**Success Criteria:**
- Execute code in sandbox safely
- Artifacts appear in expected directories
- Blog conversion works from research output
- Works on tablet/mobile

**Estimated Effort:** Significant

---

### Phase Summary

| Phase | Focus | Key Deliverable |
|-------|-------|-----------------|
| 1 | Foundation | Working /build in web UI |
| 2 | Multi-mode | All modes with context transfer |
| 3 | Visualization | Interactive Knowledge Galaxy |
| 4 | Polish | Execution, export, mobile |

---

## 11. Open Questions

### 11.1 Technical

1. **Code Execution Security**
   - How to sandbox code execution safely?
   - Options: Pyodide (in-browser), Docker container, external service
   - Decision needed before Phase 4

2. **Agent SDK Conversation Management**
   - How to maintain conversation context across mode switches?
   - Option A: Single long-running conversation with mode as context
   - Option B: Separate conversations per mode, orchestrator manages handoff

3. **Real-time Sync**
   - What if user has multiple tabs open?
   - Need conflict resolution strategy

### 11.2 UX

4. **Mode Switch Confirmation**
   - Should mode switch require confirmation?
   - Could lose in-progress work if not careful

5. **Mobile Experience**
   - Is 4-pane layout viable on mobile?
   - May need fundamentally different mobile UX

6. **Session Length**
   - What happens when sessions get very long?
   - Context window limits in Agent SDK

### 11.3 Pedagogical

7. **Cross-Mode Consistency**
   - Should /understand respect /build's "never transmit" principle?
   - Current specs have different approaches

8. **Automatic Mode Suggestions**
   - Should the agent suggest mode switches?
   - "This might be easier to research first..."

9. **Learner Profile Cold Start**
   - First session has no profile
   - How aggressive should anchor discovery be?

---

## Appendix A: Existing Skill Specs

Referenced specifications:
- `/build-v1.md` — Constructivist Learning System
- `/understand-v3.md` — Socratic Learning System
- `/research-v3.md` — Deep Research Pipeline

These specs define the pedagogical approaches and should be consulted for detailed agent behavior.

---

## Appendix B: Glossary

| Term | Definition |
|------|------------|
| **Anchor** | Prior knowledge that new concepts can be connected to |
| **SLO** | Session Learning Objective — bounded learning goal |
| **MLO** | Multi-Learning Objectives — set of SLOs for a session |
| **Scaffold** | Support structure that helps learner construct understanding |
| **Facet** | Dimension of understanding (vocabulary, mental model, etc.) |
| **Construction** | Active building of understanding (vs. passive reception) |
| **Surrender** | Learner indicating they're stuck ("I don't know") |
| **Triple Calibration** | Three probes to assess starting knowledge |
| **Knowledge State Map** | Status of understanding across facets |
| **Tier** | Source authority level (1=official, 5=community) |
