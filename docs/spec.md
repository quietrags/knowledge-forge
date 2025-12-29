# Knowledge Forge — Specification

**Version:** 0.3
**Date:** 2025-12-29

---

## What Is Knowledge Forge?

A learning platform with **layered learning modes**:

### The Layered Model

```
┌─────────────────────────────────────────────────────────────┐
│                         BUILD                               │
│        "What can we make?" (Applied understanding)          │
│                                                             │
│   ┌─────────────────────────────────────────────────────┐   │
│   │              UNDERSTAND                             │   │
│   │   "How should we think?" (Conceptual foundation)    │   │
│   └─────────────────────────────────────────────────────┘   │
│                                                             │
│   Build ALWAYS requires understanding first.                │
│   The understanding may be minimal (just enough to build)   │
│   or deep (comprehensive conceptual grounding).             │
└─────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────┐
│                      UNDERSTAND                             │
│        "How should we think?" (Pure conceptual)             │
│                                                             │
│   Understand CAN stand alone—not everything needs making.   │
│   Deep exploration of concepts, models, mental frameworks.  │
└─────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────┐
│                       RESEARCH                              │
│        "What do we need to know?" (Knowledge gathering)     │
│                                                             │
│   Supports BOTH understand and build.                       │
│   Can also be primary for pure fact-finding.                │
└─────────────────────────────────────────────────────────────┘
```

### Mode Relationships

| Mode | Nature | Stands Alone? | Relationship |
|------|--------|---------------|--------------|
| **/understand** | Conceptual development | Yes | Pure thinking |
| **/build** | Applied understanding | No | Always includes understanding phase |
| **/research** | Knowledge gathering | Yes* | Supports both; *can be primary for fact-finding |

**Key insight:** Build is a meta-outcome. You can't build without understanding something first. The question is: how much understanding is needed before making?

---

## Conceptual Model

```
┌─────────────────────────────────────────────────────────────────────────────────┐
│                              END GOALS                                          │
│  ┌─────────────────────────────────────┐  ┌─────────────────────────────────┐  │
│  │           UNDERSTAND                │  │            BUILD                │  │
│  │   "How should we think about this?" │  │      "What can we make?"        │  │
│  │                                     │  │                                 │  │
│  │ Assumption → Concept → Model        │  │ Construct → Decision → Capability│  │
│  └──────────────────┬──────────────────┘  └────────────────┬────────────────┘  │
│                     │    (when gaps arise)                 │                    │
│                     └──────────────┬───────────────────────┘                    │
│                                    ▼                                            │
│                     ┌──────────────────────────────┐                           │
│                     │         RESEARCH             │                           │
│                     │  "What do we need to know?"  │                           │
│                     │                              │                           │
│                     │ Question → Category → Adjacent│                           │
│                     └──────────────────────────────┘                           │
└─────────────────────────────────────────────────────────────────────────────────┘
```

---

## Journey Intake: Routing & Design

Users don't always know which mode they need. The system must **route questions intelligently** and **design journeys backwards** from the ideal answer.

### The Two Mechanisms

```
User asks a question
        │
        ▼
┌───────────────────────────────┐
│  MECHANISM 1: Quick Route     │
│  (Parse the question shape)   │
├───────────────────────────────┤
│  "How does X work?" → Research│
│  "Why does X happen?" → Understand
│  "How do I do X?" → Build     │
│  "What should I use?" → Research → Build
└───────────────────────────────┘
        │
        ▼ (if ambiguous or misaligned)
┌───────────────────────────────┐
│  MECHANISM 2: Work Backwards  │
│  (Design from ideal answer)   │
├───────────────────────────────┤
│  1. What would a great answer │
│     look like?                │
│  2. What must the journey     │
│     produce to get there?     │
│  3. Which mode fits?          │
│  4. What might they REALLY    │
│     be asking?                │
└───────────────────────────────┘
        │
        ▼
┌───────────────────────────────┐
│  CONFIRM with user            │
│  "It sounds like you want to  │
│   [do X / understand Y /      │
│    know Z]. Is that right?"   │
└───────────────────────────────┘
        │
        ▼
    Begin journey
```

### Question Shape → Mode Routing

| Question Shape | Primary Signal | Routes To |
|----------------|----------------|-----------|
| "How does X work?" | Seeking facts/mechanism | **Research** |
| "What is X?" | Seeking definition/facts | **Research** |
| "Why does X happen?" | Seeking explanation/cause | **Understand** |
| "What's the difference between X and Y?" | Seeking distinction | **Understand** |
| "How do I do X?" | Seeking skill/capability | **Build** |
| "Help me create X" | Seeking artifact | **Build** |
| "What should I use for X?" | Seeking informed choice | **Research → Build** |
| "Compare X vs Y for doing Z" | Seeking decision support | **Research → Build** |

### Work Backwards: The Design Brief

Before starting any journey, the system generates a **design brief**:

```typescript
interface JourneyDesignBrief {
  originalQuestion: string

  // Mechanism 2: Work backwards
  idealAnswer: string           // 2-3 sentences: what would genuinely help?
  answerType: 'facts' | 'understanding' | 'skill'

  // Routing decision
  primaryMode: 'research' | 'understand' | 'build'
  secondaryMode?: 'research'    // if research is needed to support primary

  // Potential misalignment
  implicitQuestion?: string     // what they might REALLY be asking

  // Confirmation prompt
  confirmationMessage: string   // "It sounds like you want to..."
}
```

### Example: Detecting Misalignment

**User asks:** "How do I write better prompts?"

**Quick Route says:** "How do I" → Build ✓

**Work Backwards says:**
- **Ideal answer:** "5 concrete techniques with examples and when to use each"
- **Answer type:** skill
- **Routes to:** Build ✓

But if user had asked: "I want to understand how prompting works"

**Quick Route says:** "understand" → Understand

**Work Backwards says:**
- **Ideal answer:** "5 concrete techniques..." (same practical need!)
- **Answer type:** skill
- **Implicit question:** "How do I prompt better?" (skill, not understanding)
- **Confirmation:** "You said 'understand' but it sounds like you want to get better at prompting—learn techniques you can use. Is that right, or do you want to understand the underlying mechanics first?"

### When Research Is Primary

Research can be the **primary destination** (not just supporting tool) when:

1. **Fact-finding:** "What are the token limits for different Claude models?"
2. **Landscape survey:** "What approaches exist for prompt caching?"
3. **Comparison:** "How do OpenAI and Anthropic compare on function calling?"

In these cases, the user wants **knowledge gathered**, not understanding transformed or skill built.

```
Research as Primary:
  User gets → Questions answered, sources cited, key insights extracted
  Journey ends → Research Essay synthesizes findings

Research as Supporting:
  User gets → Specific facts needed for understand/build journey
  Journey continues → Returns to primary mode with knowledge
```

---

## The Three Modes: Definitions

### RESEARCH — "What do we need to know?"

| Element | Definition |
|---------|------------|
| **Question** | Atomic, improvable unit of inquiry |
| **Category Question** | Groups related questions; has synthesized insight |
| **Adjacent Question** | Frontier — what we don't yet know we need to know |

**Mechanisms:**
1. **DECOMPOSE** — Topic → Questions
2. **ANSWER** — Question + Sources → Answered Question
3. **RISE ABOVE** — Questions → Category insight (synthesis)
4. **EXPAND** — Answered Questions → Adjacent Questions (frontier)

**Pedagogical basis:** [Knowledge Building](https://ikit.org/fulltext/2006_KBTheory.pdf) (Scardamalia & Bereiter) — ideas as improvable objects, rise above, community knowledge.

---

### UNDERSTAND — "How should we think about this?"

| Element | Definition |
|---------|------------|
| **Assumption** | Background belief to surface and examine |
| **Concept** | Distinct idea that emerges from examining assumptions |
| **Distinction** | What a concept is NOT (A ≠ B) |
| **Threshold Concept** | Transformative concept that unlocks new thinking |
| **Model** | Integrated concepts forming a mental model |

**Mechanisms (Conceptual Change):**
1. **SURFACE** — Hidden belief → Explicit Assumption
2. **DISTINGUISH** — Assumption examined → Concept (what it IS vs what it's NOT)
3. **INTEGRATE** — Concepts combined → Model
4. **DISCARD** — Outdated belief → Removed

**Pedagogical basis:** [Conceptual Change Theory](https://www.ejmste.com/download/an-overview-of-conceptual-changetheories-4082.pdf), [Threshold Concepts](https://link.springer.com/article/10.1007/s10734-004-6779-5) (Meyer & Land).

---

### BUILD — "What can we make?"

| Element | Definition |
|---------|------------|
| **Construct** | External, shareable artifact (object-to-think-with) |
| **Decision** | Trade-off that combines constructs |
| **Capability** | What you can now do (enabled by constructs + decisions) |
| **System** | Capabilities composed into working whole |

**Mechanisms (Constructionism):**
1. **IDENTIFY** — Need → Construct (what building block?)
2. **DECIDE** — Construct + Construct → Decision (trade-off)
3. **COMBINE** — Decision → Larger Construct or Capability
4. **COMPOSE** — Capabilities → System

**Pedagogical basis:** [Constructionism](https://learning.media.mit.edu/content/publications/EA.Piaget%20_%20Papert.pdf) (Papert) — learning by making external artifacts.

**Build's Two Phases:**

Build is a meta-outcome that always includes understanding. Every Build journey has two phases:

```
BUILD JOURNEY
═════════════

Phase 1: GROUNDING (Minimal Understand)
─────────────────────────────────────────
  Goal: Just enough conceptual foundation to build well

  • What concepts do you need to grasp?
  • What assumptions might lead you astray?
  • What distinctions matter for this build?

  Output: Minimal viable understanding
  Depth: Shallow but sufficient

Phase 2: MAKING (Core Build)
─────────────────────────────────────────
  Goal: Apply understanding to create something

  • Identify constructs (building blocks)
  • Make decisions (trade-offs)
  • Develop capabilities (what you can now do)

  Output: Working artifact + transferable skill
  Depth: Deep practical application
```

**Example: "How do I write better prompts?"**

| Phase | What Happens |
|-------|--------------|
| **Grounding** | Grasp: tokens (not words), context window (not memory), attention (not uniform). Just enough to make informed decisions. |
| **Making** | Learn: few-shot technique, role assignment, scratchpad pattern. Decide: when to use each. Develop: ability to iterate when prompts fail. |

**Contrast with Pure Understand:**

| Question | Mode | Why |
|----------|------|-----|
| "How do I write better prompts?" | Build | Wants skill (techniques to apply) |
| "Why do LLMs sometimes hallucinate?" | Understand | Wants explanation (no making needed) |

---

## Parallel Structure

| Aspect | Research | Understand | Build |
|--------|----------|------------|-------|
| **Driving Question** | What do we need to know? | How should we think? | What can we make? |
| **Atomic Unit** | Question | Concept | Construct |
| **Background/Input** | Topic | Assumption | Need |
| **Composition Mechanism** | Rise Above | Integrate | Decide |
| **Emergent Structure** | Category Question | Model | Capability |
| **Frontier/Output** | Adjacent Questions | Transferred understanding | System |

---

## Agent Scripts

### Research Agent
```
1. DECOMPOSE: Take topic → generate question tree
2. ANSWER: For each question → find sources, synthesize answer
3. RISE ABOVE: When questions answered → extract category insight
4. EXPAND: From answers → identify adjacent questions (frontier)
```

### Understand Agent
```
1. SURFACE: Identify hidden assumptions about the topic
2. DISTINGUISH: For each assumption → what concept emerges?
                What is it NOT? (A vs B)
3. INTEGRATE: How do concepts relate? → Build model
4. DISCARD: What beliefs should be discarded?
```

### Build Agent
```
1. IDENTIFY: What constructs are needed for this goal?
2. DECIDE: When combining constructs → what trade-offs?
           Record: choice, alternative, rationale
3. COMBINE: Constructs + Decisions → Capabilities
4. COMPOSE: Capabilities → Working system
```

---

## Data Model

### Research Types

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
  discoveredFrom: string    // which answered question spawned this
}
```

### Understand Types

```typescript
interface Assumption {
  id: string
  assumption: string        // what was believed
  surfaced: string          // what is now understood
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

### Build Types

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
  constructIds: string[]    // which constructs this combines
  producesId?: string       // resulting construct or capability
}

interface Capability {
  id: string
  capability: string
  enabledBy: string[]       // construct/decision IDs
}
```

---

## Open Questions (For Next Iteration)

1. How should agents orchestrate the modes?
2. What's the API contract between frontend and backend?
3. How does Research "return" to calling mode with results?
4. Session persistence model?
5. Real-time communication (WebSocket vs polling)?

---

## Related Files

- `docs/design.md` — UI layout and interface elements
- `docs/tech-stack.md` — Frontend technologies
- `app/src/types/index.ts` — TypeScript interfaces
