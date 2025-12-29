# Knowledge Forge — Specification

**Version:** 0.1 (Frontend Only)
**Date:** 2025-12-29

---

## What Is Knowledge Forge?

A learning platform with two **end goals** and one **supporting tool**:

### End Goals (Primary Modes)

| Mode | Purpose | Outputs |
|------|---------|---------|
| **/understand** | Analytical — taking apart | Mental models, articles |
| **/build** | Synthetic — putting together | Working code, systems |

### Supporting Tool

| Tool | Purpose | When Used |
|------|---------|-----------|
| **/research** | Evidence gathering | Invoked FROM understand/build when gaps arise |

**Key insight:** Research is NOT a destination. Users start with "I want to understand X" or "I want to build Y", never "Research X".

---

## Conceptual Model

```
┌─────────────────────────────────────────────────────────────────────────────────┐
│                              END GOALS                                          │
│  ┌─────────────────────────────────────┐  ┌─────────────────────────────────┐  │
│  │           UNDERSTAND                │  │            BUILD                │  │
│  │     (Analytical - Taking Apart)     │  │   (Synthetic - Putting Together)│  │
│  │                                     │  │                                 │  │
│  │ Distinctions ─ What's different?    │  │ Components ─ Building blocks    │  │
│  │ Assumptions ── What did I believe?  │  │ Decisions ── Trade-offs         │  │
│  │ Mental Model ─ How do I think now?  │  │ Capabilities ─ What can I do?   │  │
│  └──────────────────┬──────────────────┘  └────────────────┬────────────────┘  │
│                     │    (when gaps arise)                 │                    │
│                     └──────────────┬───────────────────────┘                    │
│                                    ▼                                            │
│                     ┌──────────────────────────────┐                           │
│                     │         RESEARCH             │                           │
│                     │   (Tool, NOT destination)    │                           │
│                     │                              │                           │
│                     │ Returns to calling end goal  │                           │
│                     └──────────────────────────────┘                           │
└─────────────────────────────────────────────────────────────────────────────────┘
```

---

## What's Been Built (Frontend v0.1)

### Data Model

**Build Mode:**
- `Component` — name, description, usage
- `Decision` — choice, alternative, rationale
- `Capability` — capability, enabledBy

**Understand Mode:**
- `Distinction` — itemA, itemB, difference
- `Assumption` — assumption, surfaced
- `MentalModel` — HTML content

**Research Mode:**
- `Question` — question, status, answer, sources, subQuestions, code, canvas
- `KeyIdea` — title, description, relevance
- `EmergentQuestion` — question, sourceCategory

### UI Components

- Mode switcher (Header)
- Learning path breadcrumb (PathBar)
- Tab-based content per mode
- Code panel with syntax highlighting
- Canvas panel with Summary/Diagram tabs
- Inline add forms for CRUD

---

## Open Questions (For Next Iteration)

1. How should agents orchestrate the modes?
2. What's the API contract between frontend and backend?
3. How does Research "return" to calling mode?
4. Session persistence model?
5. Real-time communication (WebSocket vs polling)?

---

## Related Files

- `docs/design.md` — Current UI layout
- `docs/tech-stack.md` — Frontend technologies
- `app/src/types/index.ts` — TypeScript interfaces
