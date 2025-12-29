# Knowledge Forge — UI Design

**Version:** 0.1 (Frontend Only)
**Date:** 2025-12-29

---

## Current Layout

```
┌─────────────────────────────────────────────────────────────────────────────┐
│  Knowledge Forge                          [build] [understand] [research]   │
├─────────────────────────────────────────────────────────────────────────────┤
│  PATH  ● LLM Basics → ● Prompting → ◐ Agent Architectures    [Neighbors]   │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  ┌──────────────────────────────────────────────┐  ┌─────────────────────┐  │
│  │ [Tab 1] [Tab 2] [Tab 3] [Tab 4]              │  │ CODE                │  │
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

## Mode Tabs

### Build Mode (Green: #059669)
| Tab | Content |
|-----|---------|
| Build Narrative | Knowledge essay with callouts |
| Components | Building blocks (name, description, usage) |
| Decisions | Trade-offs (choice ✓, alternative ✗, rationale) |
| Capabilities | What you can now do (capability, enabledBy) |

### Understand Mode (Blue: #2563EB)
| Tab | Content |
|-----|---------|
| Analysis Essay | Knowledge narrative |
| Distinctions | A vs B comparisons (itemA, itemB, difference) |
| Assumptions | Surfaced beliefs (assumed → now understand) |
| Mental Model | Decision framework |

### Research Mode (Purple: #7C3AED)
| Tab | Content |
|-----|---------|
| Question Tree | Hierarchical questions with expand/collapse |
| Key Ideas | Concepts that answer multiple questions |
| Emergent Questions | Questions that arose during research |

---

## Implemented Components

| Component | Purpose |
|-----------|---------|
| Header | Mode switcher with accent colors |
| PathBar | Learning path + neighbor topics |
| CodePanel | Syntax highlighting (prism-react-renderer) |
| CanvasPanel | Summary/Diagram tabs |
| QuestionTree | Expandable categories/questions |
| ComponentsTab | Build components list |
| DecisionsTab | Trade-off cards |
| CapabilitiesTab | Capability list |
| DistinctionsTab | A vs B comparison cards |
| AssumptionsTab | Before/after belief cards |
| NarrativeTab | HTML content rendering |
| MentalModelTab | Framework display |
| KeyIdeasTab | Ideas with relevance |
| EmergentQuestionsTab | Grouped by source |
| ChatInput | Mode-specific placeholder |
| InlineAdd | Reusable add form |

---

## Theming

Mode switching updates CSS variables:
- `--accent` — Primary color
- `--accent-bg` — Background tint

| Mode | Accent | Background |
|------|--------|------------|
| Build | #059669 | #ECFDF5 |
| Understand | #2563EB | #EFF6FF |
| Research | #7C3AED | #F3E8FF |
