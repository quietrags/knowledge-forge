# Knowledge Forge: Unified Learning Platform

## The Problem

Current learning skills (/understand, /research, /build) run as isolated CLI sessions:
- No running knowledge synthesis visible during learning
- Code interaction is one-way (describe in prose, can't edit/run)
- Single-pane scrolling interface loses context
- Mode switching requires exiting and re-invoking
- Topic connections are manual

## Core Philosophy

```
┌─────────────────────────────────────────────────────────────┐
│                      END GOALS                              │
│  ┌────────────────────┐      ┌────────────────────┐        │
│  │   Understanding    │      │     Building       │        │
│  │  (Comprehension)   │      │   (Capability)     │        │
│  └─────────┬──────────┘      └──────────┬─────────┘        │
│            │                            │                   │
│            ▼                            ▼                   │
│  ┌────────────────────┐      ┌────────────────────┐        │
│  │      Outputs       │      │      Outputs       │        │
│  │  - Mental models   │      │  - Working code    │        │
│  │  - Articles        │      │  - Systems         │        │
│  │  - Explanations    │      │  - Capabilities    │        │
│  └────────────────────┘      └────────────────────┘        │
└─────────────────────────────────────────────────────────────┘
                          │
                          │ (when gaps arise)
                          ▼
              ┌───────────────────────┐
              │      Research         │
              │   (Tool, not goal)    │
              │                       │
              │  Invoked on-demand    │
              │  when questions arise │
              │  that block progress  │
              └───────────────────────┘
```

**The Two End Goals:**
- **Understanding** — Deep comprehension you can explain, apply, and teach
- **Building** — Working capability: code, systems, or skills

**Research is a Tool, Not a Destination:**
- Research supports understanding and building when gaps arise
- It is NOT always needed — sometimes you reason through or learn by doing
- When invoked, research answers specific questions then returns to the end goal

## The Vision

A unified web-based learning platform with two primary modes and one supporting tool:

**End Goals (Primary Modes):**
- **/understand** (Socratic) — Deep learning through questioning → mental models, articles
- **/build** (Constructivist) — Mastery through construction → working code, capabilities

**Supporting Tool (Invoked When Needed):**
- **/research** (Evidence-based) — Gather authoritative sources to unblock understanding or building

**Key principle:** Learning is non-linear. The app should support branching, returning, and connecting across topics. Research happens IN SERVICE of understanding or building, not as a standalone activity.

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

The flow always starts with an END GOAL (understand or build), never with research.

```
USER INTENT: "I want to learn X" or "I want to build Y"
                    │
        ┌───────────┴───────────┐
        ▼                       ▼
   /understand              /build
   (comprehension)          (capability)
        │                       │
        ├─► Gap: "I need evidence"  ──► Research (returns to understand)
        │                       │
        │                       ├─► Blocker: "How do others do this?" ──► Research (returns to build)
        │                       │
        ├─► "Let me try building" ──────► Switch to /build (anchors preserved)
        │                       │
        │   ◄── "Let me understand first" ◄──┤
        │                       │
        ├─► "This connects to topic-B" ──► Branch (new understand or build)
        │                       │
        └─► COMPLETE ──► Outputs (articles, code, mental models)
                        │
                        ▼
                   /blog-convert
```

**Key Flow Principles:**
1. **Start with end goal** — Never start with "research X", start with "understand X" or "build X"
2. **Research is invoked, not switched to** — It answers a specific question then returns
3. **Mode switching preserves context** — Anchors, knowledge state, and progress carry over
4. **Outputs flow from end goals** — Articles from understanding, code from building

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
