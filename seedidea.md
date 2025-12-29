# Knowledge Forge: Unified Learning Platform

## The Problem

Current learning skills (/understand, /research, /build) run as isolated CLI sessions:
- No running knowledge synthesis visible during learning
- Code interaction is one-way (describe in prose, can't edit/run)
- Single-pane scrolling interface loses context
- Mode switching requires exiting and re-invoking
- Topic connections are manual

## The Vision

A unified web-based learning platform that weaves together:
- **/understand** (Socratic) — Personal deep learning through questioning
- **/research** (Evidence-based) — Authoritative content creation with sources
- **/build** (Constructivist) — Anchor-scaffolded mastery through building

**Key principle:** Learning is non-linear. The app should support branching, returning, and connecting across topics and modes.

---

## Core UI: Four Panes

```
┌─────────────────────────────────────────────────────────────────────────────────┐
│                           THE KNOWLEDGE FORGE                                    │
├─────────────────────────────────────────────────────────────────────────────────┤
│  ┌─────────────────────────────┐  ┌──────────────────────────────────────────┐  │
│  │    KNOWLEDGE GALAXY         │  │     ACTIVE SESSION                       │  │
│  │    (topic graph, mastery    │  │     (conversation + mode tabs)           │  │
│  │    indicators, connections) │  │     [understand] [research] [build]      │  │
│  └─────────────────────────────┘  └──────────────────────────────────────────┘  │
│  ┌─────────────────────────────┐  ┌──────────────────────────────────────────┐  │
│  │    LIVE KNOWLEDGE           │  │     CODE SANDBOX                         │  │
│  │    (running synthesis,      │  │     (edit, run, save)                    │  │
│  │    current SLO, anchors)    │  │                                          │  │
│  └─────────────────────────────┘  └──────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────────────────────┘
```

### 1. Knowledge Galaxy (Top-Left)
- Visual graph of all topics/concepts
- Mastery indicators (● mastered, ◐ partial, ○ explored)
- Click to resume or branch
- Auto-suggested connections

### 2. Active Session (Top-Right)
- Conversation with mode-switching tabs
- Context preserved when switching modes
- Inline scaffolds as interactive cards

### 3. Live Knowledge Panel (Bottom-Left)
- Currently building (active SLO)
- Constructed today (checklist)
- Available anchors from learner profile
- Gaps identified (seeds for future)

### 4. Code Sandbox (Bottom-Right)
- Monaco editor with syntax highlighting
- Run button with output display
- Save to project functionality
- Diff view from scaffold

---

## Non-Linear Learning Flow

```
Start exploring topic-A (/understand)
    │
    ├─► "I need sources" → switch to /research (context preserved)
    │
    ├─► "Let me build this" → switch to /build (anchors from /understand)
    │
    ├─► "This connects to topic-B" → branch (system pre-populates anchors)
    │
    └─► "Write a blog" → /blog-convert with full context
```

---

## Architecture

```
┌──────────────────┐
│     Frontend     │  React + Monaco Editor + D3.js
│   (Browser UI)   │  WebSocket for real-time updates
└────────┬─────────┘
         │
         ▼
┌──────────────────┐
│     Backend      │  FastAPI
│   (Orchestrator) │  Session management, mode switching, persistence
└────────┬─────────┘
         │
         ▼
┌──────────────────┐
│  Claude Agent    │  Agent SDK
│   (Learning AI)  │  Tools: update_live_knowledge, run_code, etc.
└────────┬─────────┘
         │
         ▼
┌──────────────────┐
│  Knowledge Store │  SQLite + JSON (compatible with existing outputs)
└──────────────────┘
```

---

## Agent SDK Tools

```python
tools = [
    # UI Updates
    "update_live_knowledge",      # Push to Live Knowledge panel
    "update_knowledge_graph",     # Add/connect nodes in galaxy
    "set_code_scaffold",          # Put code in sandbox
    "read_code_sandbox",          # Get learner's code edits

    # Mode Management
    "switch_mode",                # Change between understand/research/build
    "checkpoint_session",         # Save progress
    "load_prior_session",         # Resume

    # Artifact Generation
    "generate_mental_model",
    "generate_blog_draft",
    "export_code_to_project",

    # Knowledge Operations
    "find_anchors",
    "suggest_connections",
    "search_sources",
]
```

---

## MVP Phases

### Phase 1: Core Loop
- React frontend with 4 panes
- FastAPI backend with session management
- Agent SDK with /build logic only
- Live Knowledge panel
- Basic code sandbox (display only)

### Phase 2: Multi-Mode
- Add /understand and /research logic
- Mode switching
- Unified learner profile

### Phase 3: Knowledge Galaxy
- D3.js graph visualization
- Auto-connections
- Topic navigation

### Phase 4: Full Integration
- Code execution in sandbox
- Blog conversion
- Source library
- Export to existing directories

---

## Compatibility

Outputs should remain compatible with existing directories:
- `~/Documents/understanding-output/`
- `~/Documents/research-output/`
- `~/Documents/build-output/`
- `~/Development/ClaudeProjects/my-blog/_posts/`

The app wraps the existing artifact structure with a richer UI, not replaces it.
