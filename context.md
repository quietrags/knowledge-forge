# Context: Existing Learning Infrastructure

This document captures the existing infrastructure that Knowledge Forge will integrate with.

---

## 1. Understanding Outputs

**Location:** `~/Documents/understanding-output/`

**Structure per topic:**
```
topic-slug/
├── index.html          # Primary reference (styled, self-contained)
├── mental-model.md     # Condensed decision-making reference
├── research-seeds.md   # Future research directions
└── session-journal.md  # Learning journey (feeds /blog-convert)
```

**Existing topics:**
- agent-architectures (full 4-file set)
- claude-code-understanding.html (standalone)
- multi-session-claude-code-workflow.html (standalone)

**Design themes:**
- "Paper & Ink" (brown/cream, academic) for editorial content
- Blue technical theme for modern content
- Light backgrounds always (user preference)

---

## 2. Research Outputs

**Location:** `~/Documents/research-output/`

**Structure per topic:**
```
topic-slug/
├── index.html          # Primary article (25-53 KB)
├── narrative.md        # Content source
├── sources.json        # 20-31 sources with credibility scores
├── depth-check-report.json  # Quality validation
└── visuals/
    ├── *.mmd           # Mermaid diagrams
    └── index.json      # Diagram catalog
```

**Existing topics (18):**
- agent-design-patterns
- agentic-ai-frameworks-cto-guide (+ v2)
- ai-assisted-coding-workflows
- ai-coding-agent-economics
- ai-sdlc-coding-agents-cxo-adoption
- anthropic-agents-engineering-blog
- anthropic-claude-code-engineering-productivity
- claude-code-mastery
- code-indexes-embedding-storages-risks
- epam-ai-consulting
- gemini-cli-from-a-to-z
- github-speckit-and-spec-based-programming
- how-to-fine-tune-small-model-tinker-api
- practical-agent-engineering-deep-dive-tutorial
- scientific-skills-guide
- specification-based-development
- agent-built-with-claude-code-versus-claude-agent-sdk

**Source credibility tiers:**
- Tier 1: Official docs, original authors (1.0)
- Tier 2: Credible practitioners (0.9)
- Tier 3: Tech publications (0.7-0.8)
- Recency factor: 0.85-1.0

---

## 3. Build Outputs

**Location:** `~/Documents/build-output/`

**Structure:**
```
build-output/
├── .learner-profiles/
│   └── anurag.json         # Cross-session learner profile
└── topic-slug/
    ├── session-memory.json  # Detailed session transcript
    ├── mental-model.md      # Synthesized knowledge
    ├── construction-log.md  # Learning journey
    ├── code-examples.py     # Working code (when applicable)
    └── next-steps.md        # Future exploration
```

**Existing topics:**
- tool-use-function-calling-ai-agents (Dec 26)
- doc-intelligence-models (Dec 28)

**Learner Profile Schema:**
```json
{
  "learner_id": "anurag",
  "anchor_inventory": {
    "strong": [{"anchor": "...", "used_in": [...], "success_rate": 1.0}],
    "medium": [...],
    "weak": [...]
  },
  "learning_patterns": {
    "preferred_mode": "building_concrete_projects",
    "scaffold_preference": "start_medium",
    "avg_rounds_per_slo": 3.25,
    "surrender_frequency": "none"
  },
  "concept_mastery": [{
    "topic": "...",
    "concepts": [...],
    "status": "solid",
    "date": "..."
  }],
  "notes": [...]
}
```

---

## 4. Blog Output

**Location:** `~/Development/ClaudeProjects/my-blog/_posts/`

**Format:** `YYYY-MM-DD-slug.md` (Jekyll-compatible)

**Pipeline:** /understand or /research → /blog-convert → blog post

---

## 5. Skill Specs Summary

### /understand-v3 (Socratic)
- **Core:** Diagnose knowledge gaps through questioning, teach to gaps
- **Phases:** Self-assessment → Config → Diagnostic loop → SLO completion → Artifact generation
- **Key mechanism:** "Explain to 12-year-old" test, Triple Calibration
- **Output:** index.html + mental-model.md + research-seeds.md + session-journal.md

### /research-v3 (Evidence-based)
- **Core:** Gather authoritative sources, synthesize with quality validation
- **Phases:** Intention capture → Source research → Content synthesis
- **Key mechanism:** Authority tiers, depth checks, credibility scoring
- **Output:** index.html + deck.html + narrative.md + sources.json + visuals/

### /build-v1 (Constructivist)
- **Core:** Find anchors in prior knowledge, scaffold construction (never transmit)
- **Phases:** Anchor discovery → MLO breakdown → Construction loop → Consolidation → Artifacts
- **Key mechanism:** Surrender Recovery Protocol, Code Mode, Three-layer memory
- **Output:** construction-log.md + mental-model.md + session-memory.json + next-steps.md

---

## 6. Key Anchors (from Anurag's profile)

**Strong:**
- HTTP endpoint calling (URLs, methods, responses)

**Medium:**
- Tesseract OCR (experienced "flat text" limitation)
- sklearn/Keras workflow (model loading, inference)

**Patterns:**
- Learns best by building toward concrete projects
- Constructs quickly once anchor connects
- Self-corrects when reasoning aloud
- Zero surrenders — can handle medium scaffolds
- Code mode highly effective for technical topics

---

## 7. Integration Requirements

Knowledge Forge should:

1. **Read from** existing output directories (understand, research, build)
2. **Write to** same directories (maintain compatibility)
3. **Share** learner profile with /build
4. **Support** blog conversion pipeline
5. **Preserve** design themes (light backgrounds, Paper & Ink for academic)

---

## 8. HuggingFace Blog Reference

During the doc-intelligence /build session, this blog was used:
https://huggingface.co/blog/ocr-open-models

Key models covered:
- OlmOCR-2 (8B, English, highest accuracy)
- Nanonets-OCR2 (4B, handwriting/signatures)
- PaddleOCR-VL (0.9B, 109 languages, tiny)
- Granite-Docling (258M, smallest)
- DeepSeek-OCR (3B, multilingual, efficient)
- Chandra (9B, 40+ languages, high accuracy)
- dots.ocr (3B, grounding/coordinates)

This context is useful for understanding doc-intelligence topic depth.
