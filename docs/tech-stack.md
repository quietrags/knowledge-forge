# Knowledge Forge — Tech Stack

**Version:** 0.2
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
│   │   ├── QuestionTree/
│   │   ├── ConceptsTab/
│   │   ├── AssumptionsTab/
│   │   ├── ModelTab/
│   │   ├── ConstructsTab/
│   │   ├── DecisionsTab/
│   │   ├── CapabilitiesTab/
│   │   ├── ChatInput/
│   │   ├── InlineAdd/
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

## Data Model (v0.2)

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
