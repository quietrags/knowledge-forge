# Understanding Loop Specification

## Overview

The Understanding Loop is the core pedagogical engine for the `/understand` mode in Knowledge Forge. It guides learners to deep understanding through a card-based, attention-driven approach where the tutor hypothesizes prerequisites, validates them through dialogue, and synthesizes everything into a coherent narrative at completion.

---

## Core Principles

### 1. Cards Are the Atomic Unit

All knowledge artifacts are represented as **cards**. Cards are discrete, addressable units of information that can be:
- Created
- Examined
- Resolved
- Referenced

### 2. Attention Is the Key Commodity

The chat interface directs learner attention to specific cards. As conversation flows, attention moves between:
- **New cards** being created
- **Active cards** being worked on
- **Old cards** being referenced

### 3. Narrative Is Synthesized at the End

The narrative/essay is NOT built incrementally. It is generated at session completion by synthesizing all resolved cards into a coherent article.

---

## Information Architecture

### Tabs

The UI has four primary tabs:

| Tab | Purpose | Color |
|-----|---------|-------|
| **Assumptions** | Hidden beliefs to surface and examine | Soft coral / salmon (`#F4A4A4`) |
| **Concepts** | Key terms to define and distinguish | Soft sky blue (`#A4C8E1`) |
| **Models** | Integrated frameworks connecting concepts | Soft sage green (`#A8D5BA`) |
| **Narrative** | Final synthesized essay (empty until completion) | Warm cream (`#FDF6E3`) |

> **Design Note:** Use pastel/muted tones throughout. Avoid saturated red, blue, green. Light backgrounds with subtle accent borders.

### Card Structure

Cards are hierarchical: **Main cards** contain the core content, and can have **subcards** nested inside.

#### Main Card (Container)

Every card in Assumptions, Concepts, or Models is a **main card**:

| Field | Description |
|-------|-------------|
| **Title** | Short name (e.g., "Reward Model", "Humans rate on a scale") |
| **Content** | Primary text explanation (Markdown) |
| **Subcards** | Zero or more nested subcards |

#### Subcard Types

Subcards provide supplementary content within a main card:

| Subcard Type | Description | Use Case |
|--------------|-------------|----------|
| **Visual** | Diagram, flowchart, or illustration | Show relationships, processes |
| **Code** | Syntax-highlighted code example | Technical implementation |
| **Diagnostic** | Question-answer pair | Capture the probe that led to this card |

#### Example Structure

```
┌─────────────────────────────────────────────────────────────────┐
│  CONCEPT CARD: Reward Model                                      │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  A neural network trained to predict human preferences.         │
│  Given a (prompt, response), it outputs a score.                │
│                                                                  │
│  ┌─────────────────────────────────────────────────────────────┐ │
│  │  📊 VISUAL SUBCARD                                          │ │
│  │  [Diagram: Preference pairs → Training → Score output]      │ │
│  └─────────────────────────────────────────────────────────────┘ │
│                                                                  │
│  ┌─────────────────────────────────────────────────────────────┐ │
│  │  💻 CODE SUBCARD                                            │ │
│  │  reward = reward_model(prompt, response)  # Returns float   │ │
│  └─────────────────────────────────────────────────────────────┘ │
│                                                                  │
│  ┌─────────────────────────────────────────────────────────────┐ │
│  │  ❓ DIAGNOSTIC SUBCARD                                      │ │
│  │  Q: "Why not just use a classifier?"                        │ │
│  │  A: "Need continuous scores for RL optimization"            │ │
│  └─────────────────────────────────────────────────────────────┘ │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

### Card States

Each card has a state:

| State | Visual | Meaning |
|-------|--------|---------|
| `hypothesized` | Dimmed | Tutor thinks this might be relevant |
| `active` | Highlighted + pulsing | Currently being discussed |
| `resolved` | Solid + checkmark | Understanding confirmed |
| `referenced` | Brief highlight | Mentioned in passing |

---

## Session Flow

### Phase 0: Scope & Hypothesis

**Trigger:** User asks a question

**Actions:**
1. Parse the original question
2. Generate the **ideal answer** (thesis)
3. Hypothesize prerequisites:
   - Assumptions the learner might hold (or need to reject)
   - Concepts the learner needs to understand
   - Models that integrate those concepts
4. Seed the tabs with hypothesized cards (state: `hypothesized`)
5. Initialize chat with thesis summary

**UI State:**
- Assumptions/Concepts/Models tabs show seeded cards (dimmed)
- Narrative tab is empty
- Progress bar: 0%

```
┌─────────────────────────────────────────────────────────────────┐
│  CHAT                                                            │
│  ─────────────────────────────────────────────────────────────── │
│  TUTOR: "Here's the short answer: [THESIS]                       │
│                                                                  │
│  Let me check where you're starting from so I can help you       │
│  build a complete understanding."                                │
└─────────────────────────────────────────────────────────────────┘
```

---

### Phase 1: Diagnostic Probing

**Goal:** Validate or invalidate hypothesized cards, discover new ones

**Loop:**
1. Select an unvalidated card (assumption, concept, or model)
2. Design a probe question targeting that card
3. Ask the learner
4. Analyze response:
   - **Confirmed:** Learner already has this understanding → mark `resolved`, no teaching needed
   - **Rejected:** Learner lacks this or holds misconception → mark `active`, enter teaching moment
   - **New discovery:** Response reveals something not hypothesized → create new card

**UI Behavior:**
- When a card becomes `active`, its tab pulses/highlights
- The active card scrolls into view
- Chat references the card explicitly

---

### Phase 2: Teaching Moment (Inner Loop)

**Trigger:** A card is marked `active` (needs teaching)

**Fluid Interleaving:**
While teaching one card, if understanding is blocked by another:
1. Push current card onto stack
2. Pivot to blocking card
3. Resolve blocking card
4. Pop and resume original card

**Per-Card Flow:**

#### For Assumption Cards:
1. **Surface:** "You seem to be assuming X..."
2. **Examine:** Why this matters, what's wrong/right
3. **Confirm:** Learner acknowledges understanding
4. Mark `resolved`

#### For Concept Cards:
1. **Name:** "The key concept here is X"
2. **Define:** Precise definition
3. **Distinguish:** "X is NOT Y because..."
4. **Example:** Concrete illustration (may use Code Card or Visual Card)
5. **Confirm:** Learner confirms
6. Mark `resolved`

#### For Model Cards:
1. **Connect:** "Now A + B + C together mean..."
2. **Synthesize:** Integrated framework
3. **Visualize:** Diagram if helpful (Visual Card)
4. **Confirm:** Learner confirms
5. Mark `resolved`

**UI Behavior:**
- Active card is highlighted in its tab
- Supplementary cards (code, visual) appear nested under the main card
- On resolution, checkmark appears

---

### Phase 3: Milestone Checks

**At ~50% resolved:**
- Transfer check: Novel question using concepts learned so far
- If pass: Continue
- If fail: Identify gap, add card, continue teaching

**At ~80% resolved:**
- Ask learner: "We've covered the core. Want to continue to 100% or wrap up here?"
- If continue: Complete remaining cards
- If wrap up: Proceed to synthesis

---

### Phase 4: Narrative Synthesis

**Trigger:** Session complete (80%+ resolved or learner satisfied)

**Actions:**
1. Collect all resolved cards
2. Synthesize into coherent essay:
   - Thesis (from Phase 0)
   - Key concepts defined
   - Assumptions examined
   - Models explained
   - Woven into readable narrative
3. Populate Narrative tab

**UI Behavior:**
- Narrative tab illuminates
- Essay appears with structure derived from card sequence
- Cards remain viewable as reference

---

## Card Reference System

Cards can reference other cards within the conversation:

```
TUTOR: "This connects back to [→ Concept: Preference Data] we discussed earlier."
```

When a card is referenced:
1. Brief highlight animation on that card
2. Optional: "Jump to card" affordance in chat

---

## Progress Tracking

### Progress Bar Calculation

```
progress = resolved_cards / total_cards * 100
```

Where `total_cards` = hypothesized + discovered cards

### Completion Criteria

Session can complete when:
- `progress >= 80%` AND learner confirms satisfaction, OR
- `progress >= 90%` (auto-prompt to complete), OR
- All cards resolved (100%)

---

## Attention System

### Attention Signals

The chat can signal attention to cards via:

| Signal | Effect |
|--------|--------|
| `@card:create` | New card created, tab pulses, card animates in |
| `@card:focus` | Existing card highlighted, scrolled into view |
| `@card:resolve` | Card gets checkmark, brief celebration |
| `@card:reference` | Brief highlight, subtle |

### Tab Behavior

- When a card of a type becomes active, that tab gets attention indicator
- Only one tab "active" at a time
- User can manually switch tabs without disrupting flow

---

## Data Model

### Card Schema

```typescript
// Subcard types - nested inside main cards
interface VisualSubcard {
  type: 'visual'
  diagram: string  // Mermaid syntax or SVG
  caption?: string
}

interface CodeSubcard {
  type: 'code'
  code: string
  language: string
  caption?: string
}

interface DiagnosticSubcard {
  type: 'diagnostic'
  question: string
  answer: string
}

type Subcard = VisualSubcard | CodeSubcard | DiagnosticSubcard

// Main card - the primary unit
interface Card {
  id: string
  category: 'assumption' | 'concept' | 'model'
  state: 'hypothesized' | 'active' | 'resolved'

  // Content
  title: string
  content: string  // Markdown prose explanation

  // Nested subcards
  subcards: Subcard[]

  // Metadata
  createdAt: timestamp
  resolvedAt?: timestamp

  // Relations
  blockedBy?: string[]  // Card IDs that must be resolved first
  relatedTo?: string[]  // Cards referenced in discussion
}
```

### Session State

```typescript
interface UnderstandSession {
  // Thesis
  originalQuestion: string
  thesis: string

  // Cards
  cards: Card[]

  // Progress
  currentCardId?: string
  cardStack: string[]  // For interleaving
  progress: number  // 0-100

  // Narrative (populated at end)
  narrative?: string
}
```

---

## SSE Events

### Card Events

| Event Type | Payload | UI Action |
|------------|---------|-----------|
| `card.created` | `{ card, attention: boolean }` | Add card to tab, optionally highlight |
| `card.updated` | `{ cardId, updates }` | Update card content/state |
| `card.focused` | `{ cardId }` | Highlight card, switch tab |
| `card.resolved` | `{ cardId }` | Add checkmark, update progress |
| `card.referenced` | `{ cardId }` | Brief highlight |

### Session Events

| Event Type | Payload | UI Action |
|------------|---------|-----------|
| `session.progress` | `{ percent }` | Update progress bar |
| `session.milestone` | `{ type: '50%' \| '80%' }` | Show milestone UI |
| `session.complete` | `{ narrative }` | Populate narrative tab |

---

## Example Session Flow

```
1. User: "How does RLHF work?"

2. Phase 0:
   - Thesis: "RLHF trains models to match human preferences via reward modeling"
   - Seed cards:
     - [Assumption] "Humans rate every response" (hypothesized)
     - [Assumption] "RLHF replaces pre-training" (hypothesized)
     - [Concept] "Preference data" (hypothesized)
     - [Concept] "Reward model" (hypothesized)
     - [Concept] "Policy" (hypothesized)
     - [Model] "Two-phase pipeline" (hypothesized)
   - Progress: 0%

3. Phase 1: Probe "Preference data"
   - Tutor asks about human feedback
   - Learner says "rating 1-5"
   - Card [Assumption] "Humans rate responses" → active

4. Phase 2: Teach
   - Surface: "You're assuming ratings..."
   - Teach: Actually pairwise comparisons
   - Card [Concept] "Preference data" → resolved
   - Card [Assumption] → resolved
   - Progress: 33%

5. Continue probing and teaching...

6. At 80%: "Want to continue or wrap up?"

7. Phase 4: Synthesize narrative from all cards
   - Narrative tab populated
   - Session complete
```

---

## Implementation Notes

### Tools Required

The Understand agent needs these tools:

| Tool | Purpose |
|------|---------|
| `create_card` | Create a new main card (assumption, concept, or model) |
| `add_subcard` | Add a visual, code, or diagnostic subcard to an existing card |
| `update_card` | Update card content or state |
| `focus_card` | Direct attention to a card (highlights tab + card) |
| `resolve_card` | Mark card as resolved |
| `reference_card` | Briefly highlight a referenced card |
| `synthesize_narrative` | Generate final essay from all resolved cards |

### Prompt Structure

Each phase needs specific prompts that:
1. Reference the current card state
2. Include hypothesized cards not yet validated
3. Track the card stack for interleaving
4. Know when to trigger milestone checks

---

## Open Questions

1. **Card limit:** Should there be a max number of cards? (Suggest: 15-20)
2. **Interleaving depth:** How deep can the card stack go? (Suggest: 3 levels)
3. **Partial resolution:** Can a card be "partially resolved"? (Suggest: No, keep binary)
4. **Card editing:** Can learner edit/annotate cards? (Future feature)

---

## Version History

| Version | Date | Changes |
|---------|------|---------|
| 0.1 | 2024-01-XX | Initial spec from design session |
