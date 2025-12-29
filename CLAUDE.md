# CLAUDE.md - Knowledge Forge Project

## Project Overview

Building a unified learning platform that integrates three pedagogical approaches:
- /understand (Socratic)
- /research (Evidence-based)
- /build (Constructivist)

Into a rich web UI with Claude Agent SDK backend.

## SESSION STARTUP - MANDATORY

Before starting work, read these files in order:

1. **seedidea.md** (this project) — The vision and architecture
2. **context.md** (this project) — Existing infrastructure context
3. **~/Development/ClaudeProjects/content-pipeline/docs/build-v1.md** — Build spec (constructivist)
4. **~/Development/ClaudeProjects/content-pipeline/docs/understand-v3.md** — Understand spec (Socratic)
5. **~/Development/ClaudeProjects/content-pipeline/docs/research-v3.md** — Research spec (evidence-based)

## Key Design Decisions

1. **Four-pane UI**: Knowledge Galaxy, Active Session, Live Knowledge, Code Sandbox
2. **Mode switching without context loss**: All three modes share session state
3. **Learner profile persistence**: Cross-session memory like /build
4. **Compatibility**: Output to existing artifact directories

## Tech Stack (Proposed)

- **Frontend**: React + TypeScript + Monaco Editor + D3.js
- **Backend**: FastAPI (Python)
- **Agent**: Claude Agent SDK
- **Storage**: SQLite + JSON files (compatible with existing outputs)

## Related Resources

### Existing Outputs (Examples)
- `~/Documents/understanding-output/` — 3 topics (agent-architectures, claude-code)
- `~/Documents/research-output/` — 18 topics (AI economics, security, agents)
- `~/Documents/build-output/` — 2 topics + learner profile

### Learner Profile Location
- `~/Documents/build-output/.learner-profiles/anurag.json`

### Skill Specs
- `~/Development/ClaudeProjects/content-pipeline/docs/understand-v3.md`
- `~/Development/ClaudeProjects/content-pipeline/docs/research-v3.md`
- `~/Development/ClaudeProjects/content-pipeline/docs/build-v1.md`

## Learner Preferences (from profile)

- **Preferred mode**: Building concrete projects
- **Scaffold preference**: Start medium
- **Effective**: Code examples, concrete scenarios
- **Pattern**: Constructs quickly once anchor connects, self-corrects when reasoning aloud

## Development Approach

Use /build methodology to construct this app — learn Agent SDK by building with it.
