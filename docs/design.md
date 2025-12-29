# Knowledge Forge — UI Design

**Version:** 0.3
**Date:** 2025-12-29

---

## Journey Intake (Onboarding Flow)

Before entering a mode, users go through an **intake flow** that routes their question:

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                                                                             │
│                         What do you want to explore?                        │
│                                                                             │
│  ┌───────────────────────────────────────────────────────────────────────┐  │
│  │                                                                       │  │
│  │  [                                                                  ] │  │
│  │                                                                       │  │
│  └───────────────────────────────────────────────────────────────────────┘  │
│                                                                             │
│                              [Begin Journey →]                              │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

### Routing Confirmation

After analyzing the question, the system presents a confirmation:

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                                                                             │
│  You asked: "How do I write better prompts?"                               │
│                                                                             │
│  ┌───────────────────────────────────────────────────────────────────────┐  │
│  │                                                                       │  │
│  │  It sounds like you want to BUILD a prompting skill—learn            │  │
│  │  techniques you can apply immediately.                               │  │
│  │                                                                       │  │
│  │  I'll help you:                                                      │  │
│  │  • Identify key prompting constructs (techniques)                    │  │
│  │  • Make decisions about when to use each                             │  │
│  │  • Build capabilities you can apply to your work                     │  │
│  │                                                                       │  │
│  └───────────────────────────────────────────────────────────────────────┘  │
│                                                                             │
│        [Yes, let's build →]     [Actually, I want to understand first]     │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

### Alternative Route Option

If user chooses "Actually, I want to understand first":

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                                                                             │
│  Got it. Let's UNDERSTAND how prompting works first.                       │
│                                                                             │
│  I'll help you:                                                            │
│  • Surface your current assumptions about prompting                        │
│  • Develop precise concepts (like tokens, context, attention)              │
│  • Build a mental model of how LLMs actually process prompts               │
│                                                                             │
│  This understanding will inform better prompting later.                    │
│                                                                             │
│                         [Begin Understanding →]                             │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

### Research as Primary

For research-shaped questions:

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                                                                             │
│  You asked: "What approaches exist for prompt caching?"                    │
│                                                                             │
│  ┌───────────────────────────────────────────────────────────────────────┐  │
│  │                                                                       │  │
│  │  This is a RESEARCH question—you want to survey what exists          │  │
│  │  and understand the landscape.                                       │  │
│  │                                                                       │  │
│  │  I'll help you:                                                      │  │
│  │  • Decompose this into answerable questions                          │  │
│  │  • Find and evaluate sources                                         │  │
│  │  • Synthesize findings into key insights                             │  │
│  │                                                                       │  │
│  └───────────────────────────────────────────────────────────────────────┘  │
│                                                                             │
│  [Begin Research →]   [I actually want to build something with this →]     │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## Layout

```
┌─────────────────────────────────────────────────────────────────────────────┐
│  Knowledge Forge                          [build] [understand] [research]   │
├─────────────────────────────────────────────────────────────────────────────┤
│  PATH  ● Topic A → ● Topic B → ◐ Current Topic                 [Neighbors] │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  ┌──────────────────────────────────────────────┐  ┌─────────────────────┐  │
│  │ [Tab 1] [Tab 2] [Tab 3]                      │  │ CODE                │  │
│  │                                              │  │                     │  │
│  │  KNOWLEDGE AREA                              │  │ Syntax-highlighted  │  │
│  │  (Tab content varies by mode)                │  │ code panel          │  │
│  │                                              │  │                     │  │
│  │                                              │  ├─────────────────────┤  │
│  │                                              │  │ CANVAS              │  │
│  │                                              │  │                     │  │
│  │                                              │  │ [Summary] [Diagram] │  │
│  │                                              │  │                     │  │
│  └──────────────────────────────────────────────┘  └─────────────────────┘  │
│                                                                              │
│  ┌──────────────────────────────────────────────────────────────────────────┐
│  │ [Chat input...]                                                          │
│  └──────────────────────────────────────────────────────────────────────────┘
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## Mode Tabs & Interface Elements

### Research Mode (Purple: #7C3AED)

| Tab | Purpose | Elements |
|-----|---------|----------|
| **Research Essay** | Synthesis narrative | Integrates findings into coherent story |
| **Questions** | Core work | Tree: Category > Questions (expandable) |
| **Key Insights** | Rise-above synthesis | Insights answering multiple questions |
| **Frontier** | What's next | Adjacent questions discovered |

**Question Tree Structure:**
```
Category Question: "How does X work?"
  ├─ [insight]: "Key insight synthesized from answers"
  ├─ Question 1 (answered) ✓
  │    └─ Answer + Sources
  ├─ Question 2 (investigating) ◐
  └─ Question 3 (open) ○
```

**Actions:**
- `+ Add Question` — Add question to category
- `+ Add Category` — Create new category
- `↑ Rise Above` — Synthesize category insight
- `→ Refine` — Improve question wording

---

### Understand Mode (Blue: #2563EB)

| Tab | Purpose | Elements |
|-----|---------|----------|
| **Analysis Essay** | Synthesis narrative | Integrates understanding into coherent story |
| **Assumptions** | Background surfaced | Believed → Now understand |
| **Concepts** | Atomic units | Name, definition, distinguished-from |
| **Model** | Integrated view | Concept relationships |

**Concept Card:**
```
┌─────────────────────────────────────┐
│ CONCEPT NAME              [⚡ threshold]
│ ─────────────────────────────────── │
│ Definition: What this concept means │
│                                     │
│ Distinguished from: What it's NOT   │
│ From assumption: #assumption-id     │
└─────────────────────────────────────┘
```

**Assumption Card:**
```
┌─────────────────────────────────────┐
│ ✗ Assumed: "What was believed"      │
│ ↓                                   │
│ ✓ Now understand: "What is true"    │
│                        [active|discarded]
└─────────────────────────────────────┘
```

**Actions:**
- `+ Surface Assumption` — Identify hidden belief
- `+ Add Concept` — Define new concept
- `→ Distinguish` — Clarify A vs B
- `⚡ Mark Threshold` — Flag as transformative
- `✗ Discard` — Mark assumption as outdated

---

### Build Mode (Green: #059669)

**Build is a layered journey** with two phases:

```
Phase 1: GROUNDING          Phase 2: MAKING
(Minimal understanding)     (Apply to create)
────────────────────────    ────────────────────────
Concepts needed             Constructs (techniques)
Assumptions to check        Decisions (trade-offs)
Distinctions that matter    Capabilities (skills)
```

| Tab | Purpose | Elements |
|-----|---------|----------|
| **Build Narrative** | Synthesis story | Integrates journey into coherent narrative |
| **Constructs** | Building blocks | Name, description, usage, code |
| **Decisions** | Trade-offs | Choice ✓, Alternative ✗, Rationale |
| **Capabilities** | What you can do | Capability, enabled-by |

**Grounding Panel (Phase 1):**

During the grounding phase, Build mode shows a condensed understanding panel:

```
┌─────────────────────────────────────┐
│ GROUNDING: What you need to know    │
│ ─────────────────────────────────── │
│ Concept: Token                      │
│   → Not words, not characters       │
│                                     │
│ Concept: Context Window             │
│   → Not memory, fixed buffer        │
│                                     │
│ Concept: Attention                  │
│   → Not uniform, edges matter       │
│                                     │
│ [Ready to build →]                  │
└─────────────────────────────────────┘
```

This is minimal—just enough to inform the making phase.

**Construct Card:**
```
┌─────────────────────────────────────┐
│ CONSTRUCT NAME                      │
│ ─────────────────────────────────── │
│ Description: What this construct is │
│ Usage: How to use it                │
│ Code: [link to code panel]          │
└─────────────────────────────────────┘
```

**Decision Card:**
```
┌─────────────────────────────────────┐
│ ✓ Choice: "What we chose"           │
│ ✗ Alternative: "What we didn't"     │
│ ─────────────────────────────────── │
│ Rationale: Why this trade-off       │
│ Combines: [construct-1, construct-2]│
│ Produces: [capability-id]           │
└─────────────────────────────────────┘
```

**Capability Card:**
```
┌─────────────────────────────────────┐
│ CAPABILITY                          │
│ ─────────────────────────────────── │
│ Enabled by: [construct/decision IDs]│
└─────────────────────────────────────┘
```

**Actions:**
- `+ Add Construct` — Identify building block
- `⚖ Decide` — Record trade-off
- `+ Add Capability` — Define what you can now do

---

## Theming

Mode switching updates CSS variables:

| Mode | `--accent` | `--accent-bg` |
|------|------------|---------------|
| Build | #059669 | #ECFDF5 |
| Understand | #2563EB | #EFF6FF |
| Research | #7C3AED | #F3E8FF |

---

## Component List

| Component | Purpose |
|-----------|---------|
| Header | Mode switcher with accent colors |
| PathBar | Learning path + neighbor topics |
| CodePanel | Syntax highlighting (prism-react-renderer) |
| CanvasPanel | Summary/Diagram tabs |
| QuestionTree | Expandable categories/questions |
| ConceptsTab | Concept cards with distinctions |
| AssumptionsTab | Before/after belief cards |
| ModelTab | Concept relationship view |
| ConstructsTab | Build constructs list |
| DecisionsTab | Trade-off cards |
| CapabilitiesTab | Capability list |
| ChatInput | Mode-specific placeholder |
| InlineAdd | Reusable add form |

---

## Status Indicators

| Icon | Meaning |
|------|---------|
| ○ | Open / Not started |
| ◐ | In progress / Investigating |
| ● | Complete / Answered |
| ✓ | Chosen / Affirmed |
| ✗ | Rejected / Discarded |
| ⚡ | Threshold (transformative) |
