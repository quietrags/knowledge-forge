# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Knowledge Forge is a unified learning platform integrating three pedagogical approaches:
- **/build** (Constructivist) - Learn by building projects
- **/understand** (Socratic) - Learn through guided questioning
- **/research** (Evidence-based) - Learn through investigation

## Development Commands

All commands run from the `app/` directory:

```bash
cd app
npm run dev      # Start dev server (Vite)
npm run build    # TypeScript check + production build
npm run lint     # ESLint
npm run preview  # Preview production build
```

## Architecture

### Frontend Stack
- **React 19 + TypeScript** with Vite
- **Zustand** for state management
- **CSS Modules** for component styling
- **prism-react-renderer** for syntax highlighting

### State Management (Critical Pattern)

The Zustand store at `app/src/store/useStore.ts` uses selector hooks for optimized re-renders:

```typescript
// Individual state selectors (stable references)
export const useMode = () => useForgeStore((state) => state.mode)

// Action hooks MUST use useShallow to prevent infinite re-renders
export const useForgeActions = () =>
  useForgeStore(
    useShallow((state) => ({
      setMode: state.setMode,
      // ...
    }))
  )
```

**WARNING**: Never return object literals from Zustand selectors without `useShallow` - causes infinite re-render loops.

### Three-Mode Architecture

Each mode has distinct data types and UI components:

| Mode | Data Type | Primary Component | Accent Color |
|------|-----------|-------------------|--------------|
| build | `BuildModeData` | Knowledge Narrative | Green `#059669` |
| understand | `UnderstandModeData` | Essay/Misconceptions | Blue `#2563EB` |
| research | `ResearchModeData` | QuestionTree | Purple `#7C3AED` |

Mode switching updates CSS variables (`--accent`, `--accent-bg`) for theming.

### Component Structure

```
app/src/components/
├── Header/          # Mode switcher
├── PathBar/         # Learning path breadcrumb
├── CodePanel/       # Syntax-highlighted code display
├── CanvasPanel/     # Summary/Diagram tabs
└── QuestionTree/    # Research mode hierarchical questions
```

Components use CSS Modules (`*.module.css`) with shared CSS variables from `index.css`.

### Type System

Core types in `app/src/types/index.ts`:
- `Mode`: `'build' | 'understand' | 'research'`
- `Question`: Research mode with status, sources, sub-questions
- `CodeContent` / `CanvasContent`: Panel content types

## Related Resources

### Skill Specs (Reference)
- `~/Development/ClaudeProjects/content-pipeline/docs/build-v1.md`
- `~/Development/ClaudeProjects/content-pipeline/docs/understand-v3.md`
- `~/Development/ClaudeProjects/content-pipeline/docs/research-v3.md`

### Existing Output Examples
- `~/Documents/research-output/` — 18 research topics
- `~/Documents/build-output/` — Build outputs + learner profile
- `~/Documents/understanding-output/` — Understanding essays
