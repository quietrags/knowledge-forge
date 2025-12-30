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

### Backend Stack

- **Python 3.12 + FastAPI** for API layer
- **Claude Agent SDK** for mode agents
- **SSE (Server-Sent Events)** for streaming
- **File-based JSON** for session persistence

### Mode Agents (Critical Pattern)

All three mode agents use identical Claude Agent SDK patterns:

```python
from claude_agent_sdk import tool, create_sdk_mcp_server, ClaudeSDKClient

# Tool definition pattern
@tool(
    "tool_name",
    "Tool description",
    {"param1": str, "param2": int}
)
async def tool_name(args: dict[str, Any]) -> dict[str, Any]:
    # ... implementation
    return {"content": [{"type": "text", "text": "Result"}]}

# MCP server creation
server = create_sdk_mcp_server(
    name="agent-name",
    version="1.0.0",
    tools=[tool1, tool2, ...]
)

# Tool naming convention: mcp__<server>__<tool_name>
allowed_tools = ["mcp__build__emit_anchor", "mcp__build__record_construction_round"]
```

**Agent Structure**:
```
server/agents/
├── base.py           # BaseForgeAgent, PhaseTransition
├── factory.py        # create_agent, get_or_create_agent, save_agent_state
├── research/         # DECOMPOSE → ANSWER → RISE_ABOVE → EXPAND
├── understand/       # SELF_ASSESS → CONFIGURE → CLASSIFY → CALIBRATE → DIAGNOSE
└── build/            # ANCHOR_DISCOVERY → CLASSIFY → SEQUENCE_DESIGN → CONSTRUCTION
```

**Agent Factory Usage** (in `server/api/routes/chat.py`):
```python
from server.agents import get_or_create_agent, save_agent_state

# Get or restore agent for session
agent = await get_or_create_agent(
    session=session,
    journey_brief=session.journey_brief,
    emit_event=emit_callback,  # async fn to emit SSE events
)

# Process message through agent's phase graph
async for event in agent.process_message(message, context):
    await emit_callback(event)

# Save agent state back to session
save_agent_state(session, agent)
store.save(session)
```

**Agent State Persistence**: Agent state is stored in `session.agent_state.counters` dict with keys:
- `current_phase`: Current phase value (e.g., "answer", "construction")
- `agent_type`: Agent type ("research", "understand", "build")
- `phase_context`: Phase-specific state (visit counts, triggers)
- `transition_history`: List of phase transitions

### Backend Commands

```bash
cd server
uv run pytest tests/ -v    # Run all tests
uv run pytest tests/test_build_agent.py -v  # Run specific test file
```

## Known Issues

### Circular Import with Agents

Due to circular dependencies between `api/routes/chat.py` and `agents/`, the agent imports must be done inside the function:

```python
# WRONG - causes circular import
from server.agents import get_or_create_agent, save_agent_state

async def process_chat_message(...):
    ...

# CORRECT - import inside function
async def process_chat_message(...):
    from server.agents import get_or_create_agent, save_agent_state
    ...
```

### `.gitignore` Conflict with `build/` Directory

`server/.gitignore` includes `build/` for Python build artifacts, but `server/agents/build/` is a legitimate module. Use `git add -f` when adding files to this directory:

```bash
git add -f server/agents/build/
```

### Test Fixtures Must Match Pydantic Models

When Pydantic models change, test fixtures must be updated. Example for `JourneyDesignBrief`:

```python
# WRONG - old fields
JourneyDesignBrief(
    original_question="...",
    clarified_question="...",  # Does not exist
    mode="build",              # Does not exist
    scope="...",               # Does not exist
)

# CORRECT - current required fields
JourneyDesignBrief(
    original_question="...",
    ideal_answer="...",
    answer_type="understanding",
    primary_mode="build",
    confirmation_message="...",
)
```

### SSE Connections Block Uvicorn Shutdown (SOLVED)

**Problem**: Ctrl-C hangs when SSE connections are active. Uvicorn waits indefinitely for connections to close.

**Root Cause** (deadlock):
1. Ctrl-C triggers uvicorn graceful shutdown
2. Uvicorn waits for SSE connections to close
3. SSE generators block on `queue.get()` waiting for events
4. Lifespan shutdown (which could signal queues) only runs AFTER connections close
5. Deadlock: connections wait for signal, lifespan waits for connections

**Solution** (in `server/api/main.py`):
- Register signal handlers via `loop.add_signal_handler()` during lifespan startup
- These handlers run IMMEDIATELY when SIGINT arrives (before uvicorn's wait)
- Handler calls `stream_manager.close_all_streams()` to unblock generators
- Handler removes itself and re-sends SIGINT for uvicorn to handle normally

**What doesn't work**:
- Lifespan shutdown handler: runs too late (after connections close)
- `asyncio.wait_for` timeout: uvicorn still waits for generator completion
- `--timeout-graceful-shutdown`: doesn't help if connections don't close

See detailed documentation in `server/api/main.py` lifespan function docstring.

## Related Resources

### Skill Specs (Reference)
- `~/Development/ClaudeProjects/content-pipeline/docs/build-v1.md`
- `~/Development/ClaudeProjects/content-pipeline/docs/understand-v3.md`
- `~/Development/ClaudeProjects/content-pipeline/docs/research-v3.md`

### Existing Output Examples
- `~/Documents/research-output/` — 18 research topics
- `~/Documents/build-output/` — Build outputs + learner profile
- `~/Documents/understanding-output/` — Understanding essays
