# Knowledge Forge — Tech Stack

**Version:** 0.1 (Frontend Only)
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
│   │   ├── ComponentsTab/
│   │   ├── DecisionsTab/
│   │   ├── CapabilitiesTab/
│   │   ├── DistinctionsTab/
│   │   ├── AssumptionsTab/
│   │   ├── NarrativeTab/
│   │   ├── MentalModelTab/
│   │   ├── KeyIdeasTab/
│   │   ├── EmergentQuestionsTab/
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
      addComponent: state.addComponent,
    }))
  )

// WRONG - causes infinite re-renders
export const useForgeActions = () =>
  useForgeStore((state) => ({
    setMode: state.setMode,  // New object every render!
  }))
```

---

## Commands

```bash
cd app
npm run dev      # Start dev server
npm run build    # Production build
npm run lint     # ESLint
```
