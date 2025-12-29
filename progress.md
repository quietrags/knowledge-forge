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
1. Implement P1 components (Header, PathBar, CodePanel, CanvasPanel)
2. Create QuestionTree component for research mode (the most complex component)
3. Add mock data to demonstrate full functionality
