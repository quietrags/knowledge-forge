# Knowledge Forge — Tech Stack

**Version:** 0.3
**Date:** 2025-12-29

---

## Frontend Stack

| Technology | Version | Purpose |
|------------|---------|---------|
| React | 19.x | UI components |
| TypeScript | 5.x | Type safety |
| Vite | 7.x | Build tool |
| Zustand | 5.x | State management |
| prism-react-renderer | 2.x | Syntax highlighting |
| CSS Modules | — | Scoped styling |

---

## Project Structure

```
app/
├── src/
│   ├── components/          # React components
│   │   ├── Header/
│   │   ├── PathBar/
│   │   ├── CodePanel/
│   │   ├── CanvasPanel/
│   │   │
│   │   │  # Shared
│   │   ├── NarrativeTab/     # Essay/narrative for all modes
│   │   ├── ChatInput/
│   │   ├── InlineAdd/
│   │   │
│   │   │  # Research Mode
│   │   ├── QuestionTree/
│   │   ├── KeyInsightsTab/
│   │   ├── FrontierTab/
│   │   │
│   │   │  # Understand Mode
│   │   ├── AssumptionsTab/
│   │   ├── ConceptsTab/
│   │   ├── ModelTab/
│   │   │
│   │   │  # Build Mode
│   │   ├── ConstructsTab/
│   │   ├── DecisionsTab/
│   │   ├── CapabilitiesTab/
│   │   │
│   │   └── index.ts
│   ├── store/
│   │   └── useStore.ts      # Zustand store
│   ├── types/
│   │   └── index.ts         # TypeScript interfaces
│   ├── data/
│   │   └── mockData.ts      # Development data
│   ├── App.tsx
│   ├── App.css
│   └── index.css            # CSS variables
├── package.json
└── vite.config.ts
```

---

## Critical Pattern: Zustand Selectors

**Always use `useShallow` for object selectors to prevent infinite re-renders:**

```typescript
// CORRECT
import { useShallow } from 'zustand/react/shallow'

export const useForgeActions = () =>
  useForgeStore(
    useShallow((state) => ({
      setMode: state.setMode,
      addConstruct: state.addConstruct,
    }))
  )

// WRONG - causes infinite re-renders
export const useForgeActions = () =>
  useForgeStore((state) => ({
    setMode: state.setMode,  // New object every render!
  }))
```

---

## Data Model (v0.3)

### Journey Intake

```typescript
// Routing and journey design
interface JourneyDesignBrief {
  originalQuestion: string

  // Work backwards from ideal answer
  idealAnswer: string           // What would genuinely help?
  answerType: 'facts' | 'understanding' | 'skill'

  // Routing decision
  primaryMode: 'research' | 'understand' | 'build'
  secondaryMode?: 'research'    // If research needed to support primary

  // Misalignment detection
  implicitQuestion?: string     // What they might REALLY be asking

  // Confirmation
  confirmationMessage: string   // "It sounds like you want to..."
}

// Build's two phases
interface BuildJourney {
  phase: 'grounding' | 'making'

  // Phase 1: Grounding (minimal understanding)
  grounding: {
    concepts: GroundingConcept[]
    ready: boolean
  }

  // Phase 2: Making (core build)
  making: {
    constructs: Construct[]
    decisions: Decision[]
    capabilities: Capability[]
  }
}

interface GroundingConcept {
  id: string
  name: string
  distinction: string   // "Not X, but Y"
  sufficient: boolean   // Enough to proceed?
}
```

### Research Mode

```typescript
interface Question {
  id: string
  question: string
  status: 'open' | 'investigating' | 'answered'
  answer?: string
  sources?: Source[]
  categoryId?: string
}

interface CategoryQuestion {
  id: string
  category: string
  insight?: string          // "rise above" synthesis
  questionIds: string[]
}

interface AdjacentQuestion {
  id: string
  question: string
  discoveredFrom: string
}
```

### Understand Mode

```typescript
interface Assumption {
  id: string
  assumption: string
  surfaced: string
  status: 'active' | 'discarded'
}

interface Concept {
  id: string
  name: string
  definition: string
  distinguishedFrom?: string
  isThreshold: boolean
  fromAssumptionId?: string
}

interface Model {
  id: string
  name: string
  description: string
  conceptIds: string[]
  visualization?: string
}
```

### Build Mode

```typescript
interface Construct {
  id: string
  name: string
  description: string
  usage: string
  code?: string
}

interface Decision {
  id: string
  choice: string
  alternative: string
  rationale: string
  constructIds: string[]
  producesId?: string
}

interface Capability {
  id: string
  capability: string
  enabledBy: string[]
}
```

---

## Commands

```bash
cd app
npm run dev      # Start dev server
npm run build    # Production build
npm run lint     # ESLint
```
