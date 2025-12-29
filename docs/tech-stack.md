# Knowledge Forge — Tech Stack

**Version:** 1.0
**Date:** 2025-12-29

---

## Overview

Knowledge Forge is a web-based learning platform with a React frontend and (planned) Python backend with agent orchestration.

---

## Frontend Stack (Implemented)

### Core Framework

| Technology | Version | Purpose |
|------------|---------|---------|
| **React** | 19.x | UI component library |
| **TypeScript** | 5.x | Type safety and developer experience |
| **Vite** | 7.x | Build tool and dev server |

### State Management

| Technology | Purpose | Pattern |
|------------|---------|---------|
| **Zustand** | Global state | Single store with selector hooks |

**Critical Pattern:** Use `useShallow` from `zustand/react/shallow` for any selector returning object literals to prevent infinite re-renders.

```typescript
// CORRECT - uses useShallow
export const useForgeActions = () =>
  useForgeStore(
    useShallow((state) => ({
      setMode: state.setMode,
      addComponent: state.addComponent,
    }))
  )

// WRONG - causes infinite re-renders
export const useForgeActions = () =>
  useForgeStore((state) => ({
    setMode: state.setMode,  // New object on every render!
  }))
```

### Styling

| Technology | Purpose |
|------------|---------|
| **CSS Modules** | Scoped component styles (`*.module.css`) |
| **CSS Variables** | Theming and mode-specific colors |

**Theme Colors:**

| Mode | Accent | Background |
|------|--------|------------|
| Build | `#059669` (green) | `#ECFDF5` |
| Understand | `#2563EB` (blue) | `#EFF6FF` |
| Research | `#7C3AED` (purple) | `#F3E8FF` |

### Code Display

| Technology | Purpose |
|------------|---------|
| **prism-react-renderer** | Syntax highlighting for code panels |

---

## Project Structure

```
app/
├── src/
│   ├── components/           # React components
│   │   ├── Header/          # Mode switcher
│   │   ├── PathBar/         # Learning path breadcrumb
│   │   ├── CodePanel/       # Syntax-highlighted code
│   │   ├── CanvasPanel/     # Summary/Diagram tabs
│   │   ├── QuestionTree/    # Research mode questions
│   │   ├── ComponentsTab/   # Build: components
│   │   ├── DecisionsTab/    # Build: decisions
│   │   ├── CapabilitiesTab/ # Build: capabilities
│   │   ├── DistinctionsTab/ # Understand: distinctions
│   │   ├── AssumptionsTab/  # Understand: assumptions
│   │   ├── NarrativeTab/    # Shared: narrative content
│   │   ├── MentalModelTab/  # Understand: mental model
│   │   ├── KeyIdeasTab/     # Research: key ideas
│   │   ├── EmergentQuestionsTab/ # Research: emergent questions
│   │   ├── ChatInput/       # User input component
│   │   ├── InlineAdd/       # Reusable inline add form
│   │   └── index.ts         # Barrel export
│   ├── store/
│   │   └── useStore.ts      # Zustand store + selector hooks
│   ├── types/
│   │   └── index.ts         # TypeScript interfaces
│   ├── data/
│   │   └── mockData.ts      # Development mock data
│   ├── App.tsx              # Root component
│   ├── App.css              # Global layout styles
│   └── index.css            # CSS variables and base styles
├── package.json
├── tsconfig.json
└── vite.config.ts
```

---

## Type System

### Core Types

```typescript
type Mode = 'build' | 'understand' | 'research'

// Build Mode
interface Component { id, name, description, usage }
interface Decision { id, choice, alternative, rationale }
interface Capability { id, capability, enabledBy }

// Understand Mode
interface Distinction { id, itemA, itemB, difference }
interface Assumption { id, assumption, surfaced }

// Research Mode
interface Question { id, question, status, answer?, sources, subQuestions, code?, canvas? }
interface KeyIdea { id, title, description, relevance }
interface EmergentQuestion { id, question, sourceCategory }
```

---

## Dependencies

```json
{
  "dependencies": {
    "react": "^19.x",
    "react-dom": "^19.x",
    "zustand": "^5.x",
    "prism-react-renderer": "^2.x"
  },
  "devDependencies": {
    "typescript": "~5.x",
    "vite": "^7.x",
    "@types/react": "^19.x",
    "@types/react-dom": "^19.x",
    "@vitejs/plugin-react": "^4.x",
    "eslint": "^9.x"
  }
}
```

---

## Backend Stack (Planned)

### Core Framework

| Technology | Purpose |
|------------|---------|
| **FastAPI** | Async Python web framework |
| **WebSocket** | Bidirectional real-time communication |
| **SQLite** | Session and profile storage |

### Agent Layer

| Technology | Purpose |
|------------|---------|
| **Claude Agent SDK** | Agent orchestration |
| **Anthropic API** | LLM inference |

### Agent Architecture

```
Orchestrator Agent
├── Build Agent (Constructivist pedagogy)
├── Understand Agent (Socratic pedagogy)
└── Research Agent (Evidence-based pedagogy)
```

---

## Development Commands

```bash
cd app

# Development
npm run dev          # Start Vite dev server (http://localhost:5173)

# Build
npm run build        # TypeScript check + production build

# Lint
npm run lint         # ESLint check

# Preview
npm run preview      # Preview production build
```

---

## Future Additions (Planned)

| Technology | Purpose | Phase |
|------------|---------|-------|
| **Monaco Editor** | Interactive code editing | Phase 2 |
| **D3.js** | Knowledge Galaxy visualization | Phase 3 |
| **Pyodide/Docker** | Code execution sandbox | Phase 4 |

---

## Notes

1. **No Tailwind:** Using CSS Modules + CSS Variables for simplicity and control
2. **No Redux:** Zustand provides simpler API with better performance for this scale
3. **No SSR:** Client-side only (learning sessions are inherently interactive)
