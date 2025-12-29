# Knowledge Forge — Progress Log

## Session: 2025-12-29

### Summary
Completed comprehensive spec and design documentation for Knowledge Forge, a unified learning platform integrating /build, /understand, and /research modes.

### Decisions Made
1. **Architecture**: Orchestrator + Specialist Agents pattern (not single monolithic agent)
2. **Layout Direction**: Leaning toward IDE-style with persistent Knowledge Galaxy sidebar
3. **Key Insight**: Each mode needs 5+ distinct interface panels, not a simple 4-pane layout

### Work Done
- [x] Read all context files (seedidea.md, context.md, build-v1.md, understand-v3.md, research-v3.md)
- [x] Created `docs/spec.md` — Full system specification (architecture, data models, API contracts, MVP phases)
- [x] Created `docs/design.md` — UI/UX design with panel requirements per mode
- [x] Created `prototype/index.html` — Initial 4-pane interactive prototype
- [x] Enumerated interface elements needed for each mode (BUILD, UNDERSTAND, RESEARCH)

### Key Artifacts Created
```
knowledge-forge/
├── docs/
│   ├── spec.md          # 900+ line comprehensive spec
│   └── design.md        # UI/UX design with ASCII layouts
├── prototype/
│   └── index.html       # Interactive 4-pane mockup (needs revision)
├── CLAUDE.md            # Project instructions
├── seedidea.md          # Original vision
└── context.md           # Existing infrastructure context
```

### Learnings
- Simple 4-pane layout is insufficient — each mode has 5+ distinct interfaces
- Focus on substance (insights, doubts, assets) not metrics (progress bars, stats)
- Meta-layer connecting modes is critical for context preservation

### Blockers
None

### Next Session
1. Create 3 layout mockups (IDE-style, Dashboard, Focus-mode) for comparison
2. Get user feedback on layout direction
3. Initialize beads and create implementation issues
4. Revise prototype based on chosen layout

---

## Session: 2025-12-29 (continued)

### Summary
Iterated through 4 versions of the UI mockup based on user feedback. Moved from generic 4-pane layout to a focused, question/idea-centric design. Research mode completely redesigned around hierarchical question trees.

### Decisions
- **Hybrid layout over pure IDE/Cards/Focus**: Combines tabbed workspace (from IDE) + path bar (from cards) + slide-out contextual panels → best of each approach
- **Questions as unit of research**: Topic decomposes into question categories → questions → sub-questions. Everything (answers, sources, code) lives within the question tree → eliminates redundant tabs
- **Key Ideas vs Answers**: Answers live in question tree. "Key Ideas" tab captures concepts that help answer MULTIPLE questions → different purpose
- **Emergent Questions = Innovation Gaps**: Questions that arose during research, tagged with source → candidates for further investigation
- **Code/Canvas contextual to selected question**: Click a question, right panels update → focused context
- **Removed low-value elements**: Chronicle (user won't refer to it), Anchors (Claude's reference), Knowledge State (no value to user), separate Sources tab (inline per question), Notes tab (useless)

### Learnings
- **Focus on IDEAS not metadata**: Questions, insights, concepts are units of ideas. Chronicles, progress bars, stats are metadata about learning—not the learning itself
- **Unfolding knowledge narrative > log entries**: User wants a gradually building essay with prior + delta, not a timestamped journal
- **Boundaries = Q&A around neighboring concepts**: Automatically unfold as user journeys, delineating what's in vs out of scope
- **Research is iterative**: Initial question tree → research each question → capture answer + sources + emergent questions → user can add questions at any level

### Questions Resolved
- **What structure for research mode?**: Hierarchical question tree. Categories > Questions > Sub-questions. Each question contains answer, sources, sub-questions.
- **Where do sources belong?**: Inline per question, not in a separate tab. Sources support specific answers.
- **What are "findings" in research?**: Not answers (those are in question tree). Key Ideas are concepts that help answer multiple questions.

### Precious Context
- **User's mental model for value**: "Questions are units of ideas. Insights are units of ideas. Concepts are units of ideas." — everything should be idea-centric
- **Research flow**: Topic → agent generates question tree → research each question one-by-one → fill in answers + sources → emergent questions become frontier → user can add/modify questions at any level
- **Code panel purpose**: Show relevant library/pseudocode for the currently focused question, not just generic examples

### Work Done
- [x] Created mockup-a-ide.html (IDE-style with sidebar)
- [x] Created mockup-b-cards.html (Dashboard with cards)
- [x] Created mockup-c-focus.html (Focus mode with overlays)
- [x] Created mockup-d-hybrid.html (Combined best elements)
- [x] Created knowledge-forge-demo.html (Real content from output directories)
- [x] Created knowledge-forge-v2.html (Restructured: narrative focus, removed metadata)
- [x] Created knowledge-forge-v3.html (Question-centric research)
- [x] Created knowledge-forge-v4.html (Hierarchical question tree with categories)

### Key Artifacts
```
prototype/
├── mockup-a-ide.html         # Layout option A
├── mockup-b-cards.html       # Layout option B
├── mockup-c-focus.html       # Layout option C
├── mockup-d-hybrid.html      # Combined approach
├── knowledge-forge-demo.html # With real content
├── knowledge-forge-v2.html   # Narrative focus
├── knowledge-forge-v3.html   # Question-centric
└── knowledge-forge-v4.html   # Final: hierarchical questions ← CURRENT
```

### Blockers
- Beads not yet initialized (deferred to next session)

### Next Session
1. ~~Initialize beads: `bd init` and create implementation issues from v4 design~~ DONE
2. ~~Define data models for question tree structure~~ DONE
3. ~~Decide on tech stack for implementation~~ DONE (React + TypeScript + Zustand)
4. Start implementing the Question Tree component for research mode

---

## Session: 2025-12-29 (Implementation Start)

### Summary
Initialized Beads for project tracking and completed the foundation phase: React+TypeScript+Vite project setup, comprehensive TypeScript data models, and Zustand state management.

### Decisions
- **Zustand over Redux/Context**: Simpler API, optimized selectors prevent unnecessary re-renders, good fit for medium complexity state
- **Selector hooks pattern**: Created individual selector hooks (`useMode()`, `usePath()`, etc.) for optimized component re-renders
- **App structure in `/app`**: Placed React app in `/app` folder, keeping `/prototype` for HTML mockups and `/docs` for specs

### Learnings
- **Zustand getState() for initialization**: Use `useForgeStore.getState().updateCSSVariables(mode)` in useEffect for initialization logic without subscription
- **CSS variables for theming**: Dynamic accent colors via `document.documentElement.style.setProperty()` work well with React

### Questions Resolved
- **How to structure store?**: Single store with mode-specific data fields (buildData, understandData, researchData) + shared currentCode/currentCanvas
- **Selector pattern?**: Export individual `useX()` hooks wrapping `useForgeStore(state => state.x)` for optimal performance

### Precious Context
- **Type structure maps 1:1 to v4 modeData**: The TypeScript interfaces in `src/types/index.ts` mirror the JavaScript object structure from the prototype exactly

### Work Done
- [x] Initialized Beads (`bd init`)
- [x] Created 14 implementation issues with dependencies
- [x] Set up React + TypeScript + Vite in `/app`
- [x] Installed zustand, @monaco-editor/react, react-markdown
- [x] Created TypeScript interfaces in `src/types/index.ts`
- [x] Created Zustand store in `src/store/useStore.ts`
- [x] Updated App.tsx to use Zustand store
- [x] Verified build passes

### Blockers
None

### Beads Updates
- Closed: knowledge-forge-51o (project setup), knowledge-forge-ao9 (data models), knowledge-forge-y7n (state management)
- Open (P1): knowledge-forge-0ng, knowledge-forge-8k2, knowledge-forge-2h9, knowledge-forge-9rh, knowledge-forge-c7p
- Open (P2): knowledge-forge-to8, knowledge-forge-2lr, knowledge-forge-1iy, knowledge-forge-4i6, knowledge-forge-3nc, knowledge-forge-84l

### Next Session
1. ~~Implement P1 components (Header, PathBar, CodePanel, CanvasPanel)~~ DONE
2. ~~Create QuestionTree component for research mode (the most complex component)~~ DONE
3. ~~Add mock data to demonstrate full functionality~~ DONE

---

## Session: 2025-12-29 (P1 Components + Critical Bug Fix)

### Summary
Implemented all 5 P1 components and discovered/fixed a critical Zustand infinite re-render bug caused by `useForgeActions()` returning new object references on every render.

### Decisions
- **useShallow for action hooks**: Action hooks that return object literals MUST use `useShallow` from `zustand/react/shallow` to prevent infinite re-renders
- **CSS Modules per component**: Each component gets its own `*.module.css` file for scoped styling, sharing CSS variables from `index.css`
- **Mock data in separate file**: Created `src/data/mockData.ts` with comprehensive sample data for all three modes
- **prism-react-renderer over raw Prism**: Provides React-native syntax highlighting with themeable output

### Learnings
- **Zustand selector anti-pattern**: `useForgeStore((state) => ({ action: state.action }))` creates NEW object on every render → causes infinite loop. Must wrap with `useShallow()` or select primitives directly
- **React DevTools hides real errors**: Console showed "An error occurred in \<Header\>" but no stack trace. Had to isolate by removing code incrementally to find root cause
- **Vite HMR masks errors**: Build passes but runtime crashes silently. Screenshot + console inspection required to debug blank screen issues

### Questions Resolved
- **Why was app showing blank screen after brief flicker?**: `useForgeActions()` created new object reference on every render → infinite re-render → React bailed out. Fixed with `useShallow`.
- **Which component was breaking?**: Used binary search (simplify App → add components one by one) to isolate Header as the culprit, then identified `useForgeActions()` call.

### Precious Context
- **Zustand useShallow is REQUIRED for object selectors**: Any selector returning `{ key: value }` needs `useShallow()` or will cause infinite loops. This is NOT obvious from Zustand docs and took significant debugging to discover. Pattern documented in CLAUDE.md.
- **Debugging blank React screens**: When React shows blank screen with no error overlay: 1) Check console for React DevTools warnings, 2) Simplify to minimal App, 3) Add components back one by one, 4) Check for infinite render loops

### Work Done
- [x] Header component with mode switcher (knowledge-forge-0ng)
- [x] PathBar component with learning path breadcrumb (knowledge-forge-8k2)
- [x] CodePanel with prism-react-renderer syntax highlighting (knowledge-forge-2h9)
- [x] CanvasPanel with Summary/Diagram tabs (knowledge-forge-9rh)
- [x] QuestionTree with categories, expandable questions, sources, sub-questions (knowledge-forge-c7p)
- [x] Mock data for all three modes
- [x] Fixed critical useShallow bug in useForgeActions
- [x] Updated CLAUDE.md with architecture and critical patterns
- [x] Initialized git repo and committed all work

### Beads Updates
- Closed: knowledge-forge-0ng, knowledge-forge-8k2, knowledge-forge-2h9, knowledge-forge-9rh, knowledge-forge-c7p (all P1 components)
- Remaining P2: knowledge-forge-to8, knowledge-forge-2lr, knowledge-forge-1iy, knowledge-forge-4i6, knowledge-forge-3nc, knowledge-forge-84l

### Next Session
1. ~~Implement P2 Research Mode: Key Ideas tab (`knowledge-forge-to8`)~~ DONE
2. ~~Implement P2 Research Mode: Emergent Questions tab (`knowledge-forge-2lr`)~~ DONE
3. ~~Implement Build/Understand mode content panels~~ DONE
4. Add interactivity: clicking question should populate code/canvas panels (store action exists but UI doesn't trigger it)

---

## Session: 2025-12-29 (P2 Components Complete)

### Summary
Implemented all P2 tab components for all three modes. All 6 P2 beads issues closed. The app now has full UI for all tabs across Research, Build, and Understand modes.

### Work Done
- [x] **Research Mode Tabs**
  - KeyIdeasTab: Displays key ideas with titles, descriptions, and relevance to questions
  - EmergentQuestionsTab: Groups emergent questions by source category with promote action
- [x] **Build Mode Tabs**
  - NarrativeTab: Reusable component for Build/Understand knowledge narrative with HTML rendering
  - BoundariesTab: Q&A format boundary questions
  - ConceptsTab: Term/definition grid layout
  - AnswerableQuestionsTab: Numbered list with test-yourself action
- [x] **Understand Mode Tabs**
  - MisconceptionsTab: Wrong/right pattern with visual indicators
  - InsightsTab: Quote-style insight cards with context
  - MentalModelTab: Decision framework card with HTML content
- [x] **ChatInput Component**: Extracted from inline App.tsx with mode-specific placeholders
- [x] Wired all tabs in App.tsx renderContent() with proper switch statements

### Components Created (10 new)
```
app/src/components/
├── KeyIdeasTab/
├── EmergentQuestionsTab/
├── NarrativeTab/
├── BoundariesTab/
├── ConceptsTab/
├── AnswerableQuestionsTab/
├── MisconceptionsTab/
├── InsightsTab/
├── MentalModelTab/
└── ChatInput/
```

### Beads Updates
- Closed: knowledge-forge-to8, knowledge-forge-2lr, knowledge-forge-1iy, knowledge-forge-4i6, knowledge-forge-3nc, knowledge-forge-84l
- **All P2 issues complete** - no open issues remaining

### Next Session
1. ~~Add interactivity: clicking question should populate code/canvas panels~~ DONE
2. ~~Add button functionality~~ DONE
3. Re-plan remaining features (API integration, persistence, LLM interactions)

---

## Session: 2025-12-29 (Interactivity Complete)

### Summary
Completed interactivity features: question selection now updates code/canvas panels, and all add buttons are functional with inline input UI.

### Work Done
- [x] **Question selection fix**: Clicking question header now both expands AND selects, updating code/canvas panels
- [x] **Store CRUD actions**: Added 11 new actions for creating items across all modes
- [x] **InlineAdd component**: Reusable inline input with support for single and two-field inputs
- [x] **Wired all add buttons**: All "+ Add" buttons now functional across all 3 modes

### Components Modified
- QuestionTree: add questions, sub-questions, categories
- KeyIdeasTab, EmergentQuestionsTab: research mode adds + promote
- BoundariesTab, ConceptsTab, AnswerableQuestionsTab: build mode adds
- MisconceptionsTab, InsightsTab: understand mode adds

### Learnings
- **stopPropagation requires selection too**: When using `e.stopPropagation()` for expand toggle, must also call `onSelect()` or user expects click to select
- **Two-field pattern**: For items with paired data (term/definition, question/answer), the InlineAdd component supports `secondPlaceholder` + `onAddTwo` props

### Commits
- `10ed4c5` - feat: Add interactivity - question selection and inline add functionality

### Next Session
Re-plan remaining features:
1. API integration (real LLM calls for research/build/understand)
2. Persistence (save sessions, load previous work)
3. Edit/delete functionality for existing items
4. Context-aware chat input integration

---

## Session: 2025-12-29 (Conceptual Framework Redesign)

### Summary
Redesigned the Build and Understand mode conceptual frameworks based on user feedback. The new model provides clearer distinctions:
- **Build** = synthetic (Components + Decisions + Capabilities)
- **Understand** = analytical (Distinctions + Assumptions + Mental Model)
- **Research** = exploratory (Questions + Key Ideas + Emergent Questions)

### Decisions
- **Components over Concepts**: Components are building blocks you combine; concepts were too generic
- **Decisions over Boundaries**: Decisions capture trade-offs (choice vs alternative + rationale); boundaries were about scope
- **Capabilities over Answerable Questions**: Capabilities are what you can now do; questions were testing-focused
- **Distinctions over Misconceptions**: Distinctions clarify A vs B differences; misconceptions were negative-framed
- **Assumptions over Insights**: Assumptions surface beliefs revised by understanding; insights were too broad

### Work Done
- [x] Updated MODE_TABS labels in types/index.ts
- [x] Updated type definitions (Component, Decision, Capability, Distinction, Assumption)
- [x] Updated mock data with relevant examples for new framework
- [x] Created ComponentsTab (name, description, usage)
- [x] Created DecisionsTab (choice, alternative, rationale with visual checkmark/X)
- [x] Created CapabilitiesTab (capability, enabledBy)
- [x] Created DistinctionsTab (itemA vs itemB, difference)
- [x] Created AssumptionsTab (assumed → now understand pattern)
- [x] Updated store actions (addComponent, addDecision, addCapability, addDistinction, addAssumption)
- [x] Removed old components (BoundariesTab, ConceptsTab, AnswerableQuestionsTab, MisconceptionsTab, InsightsTab)
- [x] Verified all tabs render correctly in browser

### Commits
- `679b25e` - refactor: Replace Build/Understand mode tabs with new conceptual framework

### Learnings
- **Framing matters**: "Misconception" implies error; "Distinction" implies clarity. Same information, different pedagogical stance.
- **Synthetic vs Analytical**: Build combines (components + decisions); Understand separates (distinctions + assumptions). Clear mental model.

### Next Session
1. Re-plan remaining features with user
2. Consider adding edit/delete functionality for items
3. Plan API integration for LLM-powered content generation

---

## Session: 2025-12-29 (v0.3 — Journey Intake & Examples)

### Summary
Major conceptual framework update to v0.3. Added Journey Intake routing mechanism, clarified Build as layered meta-outcome requiring understanding, and documented complete journey examples for all three modes.

### Decisions
- **Journey Intake has two mechanisms**: Quick Route (question shape parsing) + Work Backwards (ideal answer design)
- **Build = Grounding + Making**: Build always requires understanding first; grounding phase provides minimal conceptual foundation before making phase
- **Research can be primary**: Not just supporting tool—can be destination for fact-finding questions
- **Flat question structure**: Questions have categoryId instead of being nested; CategoryQuestion tracks insight synthesis
- **Renamed concepts**: EmergentQuestions → AdjacentQuestions (frontier), Category → CategoryQuestion, Components → Constructs

### Work Done
- [x] Updated types for v0.2 (CategoryQuestion, Question with categoryId, AdjacentQuestion)
- [x] Fixed QuestionTree for flat structure (removed subQuestions, updated status icons)
- [x] Added Research Essay tab (NarrativeTab now handles all 3 modes)
- [x] Updated spec.md to v0.3 with Journey Intake, layered model, Build phases
- [x] Updated design.md to v0.3 with intake flow wireframes, grounding panel
- [x] Updated tech-stack.md to v0.3 with JourneyDesignBrief, BuildJourney interfaces
- [x] Created docs/examples.md with complete journey walkthroughs for all 3 modes

### Key Artifacts
```
docs/
├── spec.md          # v0.3 — Journey Intake, layered model
├── design.md        # v0.3 — Intake flow, grounding panel wireframes
├── tech-stack.md    # v0.3 — New interfaces
└── examples.md      # NEW — Complete journey examples (1080 lines)
```

### Learnings
- **Question shape heuristics**: "How do I" → Build, "Why does" → Understand, "What is" → Research
- **Misalignment detection**: User says "understand" but wants skill = route to Build with confirmation
- **Grounding is minimal understanding**: Just enough concepts/assumptions to make informed build decisions

### Commits
- `feat: Update frontend to v0.2 pedagogical framework`
- `feat: Add Research Essay tab for synthesis narrative`
- `docs: Add Journey Intake routing mechanism (v0.3)`
- `docs: Clarify Build as layered meta-outcome requiring understanding`
- `docs: Sync design.md and tech-stack.md with v0.3 spec`
- `docs: Add complete journey examples for all three modes`

### Next Session
1. ~~Implement Journey Intake UI (onboarding flow before entering mode)~~ DONE
2. ~~Add Grounding Panel UI for Build Phase 1~~ DONE
3. Consider edit/delete functionality for items
4. Plan API integration for LLM-powered content generation

---

## Session: 2025-12-29 (v0.3 Frontend Implementation)

### Summary
Implemented complete v0.3 Journey Intake and Build Phase system. Created 8 beads issues, all closed. Tested full flow in browser - all features working.

### Work Done
- [x] **Types**: JourneyDesignBrief, JourneyState, BuildJourney, GroundingConcept, BuildPhase
- [x] **Store**: journeyState, journeyBrief, buildJourney state + 6 new actions
- [x] **JourneyIntake component**: Full-screen question input with heuristic routing
- [x] **RoutingConfirmation component**: Mode suggestion with alternatives
- [x] **GroundingPanel component**: Build Phase 1 with concept cards
- [x] **Header phase indicator**: Shows GROUNDING/MAKING in build mode
- [x] **App.tsx integration**: Conditional rendering based on journeyState and buildPhase

### Components Created
```
app/src/components/
├── JourneyIntake/      # Question input + routing
├── RoutingConfirmation/ # Mode confirmation + alternatives
└── GroundingPanel/     # Build Phase 1 concepts
```

### Test Results (All Passed)
| Feature | Status |
|---------|--------|
| JourneyIntake screen | ✓ |
| Question routing heuristics | ✓ |
| RoutingConfirmation with alternatives | ✓ |
| Build Grounding Phase panel | ✓ |
| Header phase indicator | ✓ |
| Add grounding concept | ✓ |
| Phase transition (Grounding → Making) | ✓ |

### Beads Closed (8 issues)
- knowledge-forge-5ja: JourneyDesignBrief types
- knowledge-forge-a97: BuildJourney/GroundingConcept types
- knowledge-forge-ldo: Journey intake store state
- knowledge-forge-dz8: Build phase store state
- knowledge-forge-8qa: JourneyIntake component
- knowledge-forge-9sk: RoutingConfirmation component
- knowledge-forge-ncl: GroundingPanel component
- knowledge-forge-0si: Phase indicator in header

### Commits
- `feat: Implement v0.3 Journey Intake and Build Phase system`

### Configuration
- `journeyState: 'active'` for dev (skips intake)
- Change to `journeyState: 'intake'` to enable full flow

### Next Session
1. ~~Consider edit/delete functionality for items~~ (deferred)
2. ~~Plan API integration for LLM-powered content generation~~ DONE
3. ~~Add real question routing via LLM (replace heuristics)~~ (in architecture)
4. ~~Persist journey state across sessions~~ (in architecture)

---

## Session: 2025-12-29 (Backend Architecture Design)

### Summary
Designed comprehensive unified backend architecture for Knowledge Forge. Created 7 beads issues for parallel implementation via git worktrees. Architecture covers orchestration, streaming, API contracts, state sync, and persistence.

### Decisions
- **Backend**: Python + FastAPI (matches existing patterns)
- **Streaming**: Server-Sent Events (simpler than WebSocket)
- **Persistence**: File-based JSON sessions (no learner profiles yet)
- **Web Search**: Claude's built-in web search tool
- **Auth**: Deferred to later (sessions identified by ID only)
- **Hosting**: Local development only for now

### Work Done
- [x] Explored frontend structure, skill specs, and existing backend patterns
- [x] Designed unified architecture with 7 parallelizable modules
- [x] Defined API contract (TypeScript types, endpoints, SSE protocol)
- [x] Defined agent interface contract (Python BaseAgent)
- [x] Created `docs/backend-architecture.md` (730+ lines)
- [x] Created 7 beads issues with dependencies
- [x] Set up 7 git branches for worktree development

### Key Artifacts
```
docs/backend-architecture.md   # Complete architecture spec

Beads Issues (7):
├── knowledge-forge-751 [P1] Backend API Layer
├── knowledge-forge-3mn [P1] Backend Persistence
├── knowledge-forge-3fe [P1] Frontend API Integration
├── knowledge-forge-cm0 [P2] Backend Orchestrator (depends on API)
├── knowledge-forge-7x2 [P2] Research Agent (depends on Orchestrator)
├── knowledge-forge-614 [P2] Understand Agent (depends on Orchestrator)
└── knowledge-forge-b7h [P2] Build Agent (depends on Orchestrator)

Git Branches (7):
├── backend-api-layer
├── backend-persistence
├── frontend-api-integration
├── backend-orchestrator
├── backend-research-agent
├── backend-understand-agent
└── backend-build-agent
```

### Architecture Highlights
- **SSE Event Types**: 15+ event types for real-time UI updates
- **Agent Interface**: `initialize()`, `process_message()`, `get_state()`, `restore_state()`
- **Session Persistence**: JSON files in `server/data/sessions/`
- **Worktree Strategy**: 7 branches, merge order defined for integration

### Learnings
- Skill specs (build-v1, understand-v3, research-v3) define complete agent behaviors with phases, state tracking, and failure modes
- User's existing patterns favor FastAPI + Next.js API routes as proxy
- SSE is simpler than WebSocket for this use case (one-way server→client streaming)

### Next Session
1. Start implementing P1 modules (can parallelize):
   - `backend-api-layer` — FastAPI skeleton, routes, SSE
   - `backend-persistence` — Session store, file backend
   - `frontend-api-integration` — API client, stream handlers
2. After P1: Implement orchestrator, then agents
