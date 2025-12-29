# Knowledge Forge — Example Journeys

**Version:** 0.3
**Date:** 2025-12-29

These examples illustrate complete journeys through each mode, showing how the system routes questions, surfaces assumptions, develops concepts, and builds capabilities.

---

## Table of Contents

1. [Build Example: Chrome Extension](#build-example-chrome-extension-that-summarizes-web-pages)
2. [Understand Example: LLM Hallucination](#understand-example-why-do-llms-hallucinate)
3. [Research Example: Local LLMs](#research-example-running-llms-locally)

---

## Build Example: Chrome Extension that Summarizes Web Pages

**User enters:** "I want to build a Chrome extension that summarizes web pages"

### Phase 0: Journey Intake

**Quick Route:** "I want to build" → **Build** ✓

**Work Backwards:**
- **Ideal answer:** Working extension code + understanding of the architecture + ability to extend/modify it
- **Answer type:** Skill (applied making)
- **Routes to:** Build

**Confirmation:**

```
┌─────────────────────────────────────────────────────────────────┐
│                                                                 │
│  You want to BUILD a Chrome extension for page summarization.  │
│                                                                 │
│  I'll help you:                                                │
│  • Ground yourself in the key concepts (extension architecture,│
│    LLM integration patterns)                                   │
│  • Identify the constructs you'll combine (manifest, scripts,  │
│    API calls)                                                  │
│  • Make key decisions (which model, where to process)          │
│  • Develop the capability to build and extend this             │
│                                                                 │
│              [Let's build →]                                   │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

---

### Phase 1: Grounding (Minimal Understanding)

**System:** "Before we start building, let's make sure you have the conceptual foundation. I'll keep this minimal—just enough to make good decisions."

#### Grounding Concept 1: Extension Architecture

**System:** "What do you think happens when a Chrome extension runs?"

**User:** "It... adds functionality to the browser? Like a plugin?"

**System:** "Close. Let me sharpen this."

```
┌─────────────────────────────────────────────────────────────────┐
│ CONCEPT: Extension Architecture                                 │
│ ─────────────────────────────────────────────────────────────── │
│                                                                 │
│ An extension is NOT a single program.                          │
│ It's multiple isolated scripts that communicate via messages:  │
│                                                                 │
│   ┌──────────────┐     messages     ┌──────────────┐           │
│   │ Content      │ ◄──────────────► │ Background   │           │
│   │ Script       │                  │ Service      │           │
│   │ (per tab)    │                  │ Worker       │           │
│   └──────────────┘                  └──────────────┘           │
│         ▲                                  ▲                    │
│         │                                  │                    │
│    page DOM                           API calls                 │
│                                                                 │
│ Content script: Can see the page, can't make API calls         │
│ Service worker: Can make API calls, can't see the page         │
│                                                                 │
│ ⚡ This is why you need message passing—they're isolated.      │
└─────────────────────────────────────────────────────────────────┘
```

#### Grounding Concept 2: Token Economics

**System:** "You'll be sending entire web pages to an LLM. What do you think that costs?"

*Quick research detour:*

| Model | Input (per 1M tokens) | Typical page (~4k tokens) |
|-------|----------------------|---------------------------|
| Claude Haiku | $0.25 | ~$0.001 |
| Claude Sonnet | $3.00 | ~$0.012 |
| GPT-4o-mini | $0.15 | ~$0.0006 |

```
┌─────────────────────────────────────────────────────────────────┐
│ CONCEPT: Token Economics                                        │
│ ─────────────────────────────────────────────────────────────── │
│                                                                 │
│ NOT "AI is free after you pay for the API key"                 │
│ IS "Every page summary has a real marginal cost"               │
│                                                                 │
│ Implications for your extension:                                │
│ • Use cheaper model (Haiku) for most summaries                 │
│ • Consider caching summaries for revisited pages               │
│ • Maybe offer "quick" vs "deep" summary options                │
└─────────────────────────────────────────────────────────────────┘
```

#### Grounding Concept 3: Content Extraction

```
┌─────────────────────────────────────────────────────────────────┐
│ CONCEPT: Content Extraction                                     │
│ ─────────────────────────────────────────────────────────────── │
│                                                                 │
│ Raw page HTML includes:                                         │
│ • Navigation, headers, footers (noise)                         │
│ • Ads, sidebars, related links (noise)                         │
│ • The actual article content (signal)                          │
│ • Scripts, styles (garbage)                                    │
│                                                                 │
│ NOT "just grab document.body.innerText"                        │
│ IS "extract the main content, ignore the chrome"               │
│                                                                 │
│ Options:                                                        │
│ • Mozilla Readability (extracts article content)               │
│ • Custom selectors (fragile)                                   │
│ • Send everything, let LLM figure it out (expensive)           │
└─────────────────────────────────────────────────────────────────┘
```

#### Grounding Check

```
┌─────────────────────────────────────────────────────────────────┐
│ GROUNDING COMPLETE                                              │
│ ─────────────────────────────────────────────────────────────── │
│                                                                 │
│ You now understand:                                             │
│ ✓ Extension architecture (content script ↔ service worker)     │
│ ✓ Token economics (~$0.001-0.01 per summary)                   │
│ ✓ Content extraction (signal vs noise)                         │
│                                                                 │
│ This is enough to make informed decisions.                      │
│                                                                 │
│                    [Begin making →]                             │
└─────────────────────────────────────────────────────────────────┘
```

---

### Phase 2: Making (Core Build)

#### Construct 1: Manifest

```
┌─────────────────────────────────────────────────────────────────┐
│ CONSTRUCT: manifest.json                                        │
│ ─────────────────────────────────────────────────────────────── │
│                                                                 │
│ The extension's configuration file. Declares:                  │
│ • Permissions (activeTab, storage)                             │
│ • Scripts (content script, service worker)                     │
│ • UI elements (popup, icon)                                    │
│                                                                 │
│ Usage: Required. Chrome won't load the extension without it.   │
└─────────────────────────────────────────────────────────────────┘
```

```json
{
  "manifest_version": 3,
  "name": "Page Summarizer",
  "version": "1.0",
  "permissions": ["activeTab", "storage"],
  "action": {
    "default_popup": "popup.html",
    "default_icon": "icon.png"
  },
  "background": {
    "service_worker": "background.js"
  },
  "content_scripts": [{
    "matches": ["<all_urls>"],
    "js": ["content.js"]
  }]
}
```

#### Construct 2: Content Script

```
┌─────────────────────────────────────────────────────────────────┐
│ CONSTRUCT: content.js                                           │
│ ─────────────────────────────────────────────────────────────── │
│                                                                 │
│ Runs in the context of each web page.                          │
│ Job: Extract content, send to service worker.                  │
│                                                                 │
│ Usage: Inject Readability, extract article, message background.│
└─────────────────────────────────────────────────────────────────┘
```

```javascript
// content.js
function extractContent() {
  const documentClone = document.cloneNode(true);
  const reader = new Readability(documentClone);
  const article = reader.parse();

  return {
    title: article?.title || document.title,
    content: article?.textContent || document.body.innerText,
    url: window.location.href
  };
}

chrome.runtime.onMessage.addListener((request, sender, sendResponse) => {
  if (request.action === 'extract') {
    sendResponse(extractContent());
  }
});
```

#### Construct 3: Service Worker

```
┌─────────────────────────────────────────────────────────────────┐
│ CONSTRUCT: background.js (Service Worker)                      │
│ ─────────────────────────────────────────────────────────────── │
│                                                                 │
│ Runs in the background, handles API calls.                     │
│ Job: Receive content, call Claude, return summary.             │
│                                                                 │
│ Usage: Message listener + Anthropic API integration.           │
└─────────────────────────────────────────────────────────────────┘
```

```javascript
// background.js
async function summarize(content, length = 'medium') {
  const lengthGuide = {
    short: '2-3 sentences',
    medium: '1 paragraph',
    long: '3-4 paragraphs with key points'
  };

  const response = await fetch('https://api.anthropic.com/v1/messages', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      'x-api-key': API_KEY,
      'anthropic-version': '2023-06-01'
    },
    body: JSON.stringify({
      model: 'claude-3-haiku-20240307',
      max_tokens: 500,
      messages: [{
        role: 'user',
        content: `Summarize this article in ${lengthGuide[length]}:\n\n${content}`
      }]
    })
  });

  const data = await response.json();
  return data.content[0].text;
}

chrome.runtime.onMessage.addListener((request, sender, sendResponse) => {
  if (request.action === 'summarize') {
    summarize(request.content, request.length)
      .then(summary => sendResponse({ summary }))
      .catch(error => sendResponse({ error: error.message }));
    return true;
  }
});
```

---

#### Decision 1: Which Model?

```
┌─────────────────────────────────────────────────────────────────┐
│ DECISION                                                        │
│ ─────────────────────────────────────────────────────────────── │
│                                                                 │
│ ✓ Choice: Claude Haiku for default summaries                   │
│ ✗ Alternative: Sonnet for all summaries                        │
│                                                                 │
│ Rationale: Haiku is 12x cheaper and summarization doesn't      │
│ require deep reasoning. Offer Sonnet as "deep analysis" option │
│ for complex articles.                                           │
│                                                                 │
│ Combines: [Service Worker, Token Economics understanding]       │
│ Produces: Cost-effective summarization capability               │
└─────────────────────────────────────────────────────────────────┘
```

#### Decision 2: Where to Store API Key?

```
┌─────────────────────────────────────────────────────────────────┐
│ DECISION                                                        │
│ ─────────────────────────────────────────────────────────────── │
│                                                                 │
│ ✓ Choice: User provides their own API key (stored in           │
│           chrome.storage.local)                                 │
│ ✗ Alternative: Bundle API key in extension / proxy server      │
│                                                                 │
│ Rationale: Bundling key is a security risk (can be extracted). │
│ Proxy server adds complexity and hosting cost. User-provided   │
│ key is safest and makes cost transparent.                      │
│                                                                 │
│ Combines: [Manifest permissions, Storage API]                   │
│ Produces: Secure, user-controlled billing                       │
└─────────────────────────────────────────────────────────────────┘
```

#### Decision 3: When to Summarize?

```
┌─────────────────────────────────────────────────────────────────┐
│ DECISION                                                        │
│ ─────────────────────────────────────────────────────────────── │
│                                                                 │
│ ✓ Choice: On-demand (user clicks button)                       │
│ ✗ Alternative: Auto-summarize every page                       │
│                                                                 │
│ Rationale: Auto-summarize burns tokens on pages user doesn't   │
│ care about. On-demand gives user control over cost.            │
│                                                                 │
│ Produces: Intentional, cost-conscious usage pattern            │
└─────────────────────────────────────────────────────────────────┘
```

---

#### Capabilities

```
┌─────────────────────────────────────────────────────────────────┐
│ CAPABILITY: Summarize any web page on demand                   │
│ ─────────────────────────────────────────────────────────────── │
│                                                                 │
│ Enabled by:                                                     │
│ • Manifest (permissions, script registration)                  │
│ • Content Script (extracts readable content)                   │
│ • Service Worker (calls Claude API)                            │
│ • Decision: Haiku for cost, on-demand for control              │
│                                                                 │
│ You can now:                                                    │
│ • Click extension icon on any page                             │
│ • Get a clean summary in seconds                               │
│ • Choose summary length (short/medium/long)                    │
│ • Know exactly what each summary costs                         │
└─────────────────────────────────────────────────────────────────┘
```

```
┌─────────────────────────────────────────────────────────────────┐
│ CAPABILITY: Extend the extension                               │
│ ─────────────────────────────────────────────────────────────── │
│                                                                 │
│ Because you understand the architecture, you can now:          │
│                                                                 │
│ • Add new features (save summaries, export to Notion)          │
│ • Change the prompt (bullet points, ELI5, translate)           │
│ • Add keyboard shortcuts                                        │
│ • Cache summaries for revisited pages                          │
│ • Add "deep analysis" mode with Sonnet                         │
│                                                                 │
│ The grounding concepts transfer to any extension you build.    │
└─────────────────────────────────────────────────────────────────┘
```

---

### Build Narrative

> **Building a Chrome Extension for Page Summarization**
>
> This extension combines three constructs: a manifest that declares permissions and scripts, a content script that extracts readable content from any page, and a service worker that calls Claude's API to generate summaries.
>
> Three key decisions shaped the design:
>
> **Model selection:** Haiku over Sonnet—summarization doesn't require deep reasoning, and 12x cost savings matter when summarizing frequently.
>
> **API key management:** User-provided keys stored locally, not bundled or proxied. This is the only secure approach for a client-side extension.
>
> **Trigger pattern:** On-demand, not automatic. Users control their costs by choosing what to summarize.
>
> The grounding phase revealed why these decisions matter: understanding extension architecture (isolated scripts communicating via messages) explains the content-script/service-worker split; understanding token economics justifies the model and trigger choices; understanding content extraction explains why we use Readability instead of raw innerHTML.
>
> With this foundation, extending the extension becomes straightforward—the same patterns apply to any new feature.

---

### Build Journey Summary

| Phase | What Happened |
|-------|---------------|
| **Intake** | Routed to Build, confirmed intent |
| **Grounding** | 3 concepts: extension architecture, token economics, content extraction |
| **Research detour** | Quick lookup on model pricing |
| **Constructs** | manifest.json, content.js, background.js |
| **Decisions** | Model (Haiku), API key (user-provided), trigger (on-demand) |
| **Capabilities** | Summarize any page, extend the extension |
| **Narrative** | Synthesized the journey into transferable knowledge |

**Key insight:** Everything in grounding served the building. We didn't explore token economics deeply—just enough to make the Haiku decision. We didn't study extension architecture exhaustively—just enough to structure the code.

---

## Understand Example: Why Do LLMs Hallucinate?

**User enters:** "Why do LLMs hallucinate?"

### Phase 0: Journey Intake

**Quick Route:** "Why does X happen?" → **Understand** ✓

**Work Backwards:**
- **Ideal answer:** A mental model that explains the mechanism behind hallucination, enabling the user to predict when it will happen and understand why it's intrinsic
- **Answer type:** Understanding (causal explanation)
- **Routes to:** Understand (pure conceptual—no making needed)

**Confirmation:**

```
┌─────────────────────────────────────────────────────────────────┐
│                                                                 │
│  You want to UNDERSTAND why LLMs hallucinate.                  │
│                                                                 │
│  I'll help you:                                                │
│  • Surface your current assumptions about how LLMs work        │
│  • Develop precise concepts that explain the phenomenon        │
│  • Build a mental model of why hallucination is intrinsic      │
│                                                                 │
│  This is about understanding, not fixing or working around.    │
│                                                                 │
│              [Let's understand →]                              │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

---

### Phase 1: Surface Assumptions

**System:** "Before we examine hallucination, let's surface what you currently believe. Complete these sentences honestly—there are no wrong answers:"

**User responds:**
- "When an LLM hallucinates, it's because *it doesn't have enough information*"
- "The LLM knows it's wrong when *it says 'I'm not sure'*"
- "Hallucination could be fixed by *training on more accurate data*"
- "The LLM's confidence means *it's more likely to be correct*"

**Assumptions surfaced:**

| # | Assumption | Belief Type |
|---|------------|-------------|
| A1 | Hallucination = information gap | Causal |
| A2 | LLM has self-knowledge of correctness | Metacognitive |
| A3 | More/better data = less hallucination | Solutionist |
| A4 | Confidence correlates with correctness | Probabilistic |

---

### Phase 2: Examine Assumptions & Develop Concepts

#### Examining A1: "Hallucination = information gap"

**System:** "If this were true, what would you expect to see?"

**User:** "It would hallucinate about obscure topics but be accurate about common ones?"

**System:** "Let's test that. Ask Claude who won the 1987 Academy Award for Best Picture."

Claude confidently says "The Last Emperor" ✓ (correct)

**System:** "Now ask who won the 2009 Guildford Chess Congress."

Claude confidently gives a name and result... but it's fabricated.

**System:** "Both questions have 'correct answers' in the training data somewhere. Why did one work and one fail?"

#### Concept 1: Statistical Prediction (Threshold Concept)

```
┌─────────────────────────────────────────────────────────────────┐
│ ⚡ CONCEPT: Statistical Prediction                              │
│ ─────────────────────────────────────────────────────────────── │
│                                                                 │
│ Definition:                                                     │
│ An LLM doesn't retrieve facts—it predicts the most likely      │
│ next token given the pattern of previous tokens. "Likely"      │
│ means "frequently followed this pattern in training data."     │
│                                                                 │
│ Distinguished from:                                             │
│ ✗ NOT retrieval (it's not looking things up)                   │
│ ✗ NOT reasoning (it's not deducing from premises)              │
│ ✗ NOT knowing (it has no concept of "true" vs "false")         │
│                                                                 │
│ ⚡ THRESHOLD: Once you see this, you can't unsee it.            │
│ The LLM isn't "wrong"—it's doing exactly what it was trained   │
│ to do: produce likely continuations. Sometimes likely ≠ true.  │
│                                                                 │
│ From assumption: A1 ("doesn't have enough information")        │
│ Status: DISCARDED                                               │
└─────────────────────────────────────────────────────────────────┘
```

---

#### Examining A2: "LLM knows when it's wrong"

**System:** "When Claude says 'I'm not sure,' what do you think is happening?"

**User:** "It's... checking its confidence? Recognizing uncertainty?"

**System:** "What makes YOU say 'I'm not sure'?"

**User:** "I notice a feeling of uncertainty. I'm aware I might be wrong."

**System:** "That requires two things: (1) a sense that there's a correct answer, and (2) awareness that your internal state doesn't match it. Does an LLM have either?"

#### Concept 2: Performed Uncertainty

```
┌─────────────────────────────────────────────────────────────────┐
│ CONCEPT: Performed Uncertainty                                  │
│ ─────────────────────────────────────────────────────────────── │
│                                                                 │
│ Definition:                                                     │
│ When an LLM says "I'm not sure" or "I might be wrong," it's   │
│ generating text that *resembles* uncertainty—not experiencing  │
│ or detecting actual uncertainty.                               │
│                                                                 │
│ Distinguished from:                                             │
│ ✗ NOT metacognition (no awareness of its own states)           │
│ ✗ NOT calibrated confidence (no correlation with correctness)  │
│ ✗ NOT humility (no sense of limitation)                        │
│                                                                 │
│ Implication:                                                    │
│ You cannot trust "I'm not sure" as a signal of actual         │
│ uncertainty. The model might be confidently wrong or          │
│ uncertainly correct—the words don't tell you which.           │
│                                                                 │
│ From assumption: A2 ("LLM knows when it's wrong")              │
│ Status: DISCARDED                                               │
└─────────────────────────────────────────────────────────────────┘
```

---

#### Examining A3: "Better data = fix"

**System:** "If we trained only on verified facts, would hallucination disappear?"

*Research detour:*

**Findings:**
- Models trained on Wikipedia + textbooks still hallucinate
- Hallucination rate decreases but never reaches zero
- Novel combinations of true facts can produce false statements
- The generation mechanism itself produces hallucinations

#### Concept 3: Generative Confabulation

```
┌─────────────────────────────────────────────────────────────────┐
│ CONCEPT: Generative Confabulation                              │
│ ─────────────────────────────────────────────────────────────── │
│                                                                 │
│ Definition:                                                     │
│ The act of producing coherent, plausible text that combines    │
│ elements in ways not grounded in any training example.         │
│ The model doesn't "make mistakes"—it generates novel           │
│ combinations that happen to not correspond to reality.         │
│                                                                 │
│ Distinguished from:                                             │
│ ✗ NOT errors (implies a correct process gone wrong)            │
│ ✗ NOT lies (implies intent to deceive)                         │
│ ✗ NOT guesses (implies awareness of uncertainty)               │
│                                                                 │
│ Why it can't be "fixed":                                       │
│ The same mechanism that produces creative, useful text         │
│ (novel combinations) also produces hallucinations.             │
│ You can't have one without the other.                          │
│                                                                 │
│ From assumption: A3 ("better data = fix")                      │
│ Status: DISCARDED                                               │
└─────────────────────────────────────────────────────────────────┘
```

---

#### Examining A4: "Confidence = correctness"

**System:** "When Claude states something without hedging, do you assume it's more likely to be true?"

**User:** "Yes, intuitively."

**System:** "The confidence is in the *text pattern*, not the *factual accuracy*."

#### Concept 4: Surface Confidence

```
┌─────────────────────────────────────────────────────────────────┐
│ CONCEPT: Surface Confidence                                    │
│ ─────────────────────────────────────────────────────────────── │
│                                                                 │
│ Definition:                                                     │
│ The stylistic quality of text that sounds certain. Determined  │
│ by training patterns (academic writing sounds confident,       │
│ hedging appears in certain contexts) not by factual accuracy.  │
│                                                                 │
│ Distinguished from:                                             │
│ ✗ NOT calibrated probability (no correlation with truth)       │
│ ✗ NOT model confidence scores (those exist but aren't shown)   │
│ ✗ NOT expertise (a model can sound confident about anything)   │
│                                                                 │
│ Why it's misleading:                                           │
│ Confident text patterns occur in training for TRUE statements. │
│ The model learns to produce confident style for all outputs,   │
│ regardless of whether the specific claim is accurate.          │
│                                                                 │
│ From assumption: A4 ("confidence = correctness")               │
│ Status: DISCARDED                                               │
└─────────────────────────────────────────────────────────────────┘
```

---

### Phase 3: Integrate into Model

```
┌─────────────────────────────────────────────────────────────────┐
│ MODEL: Why LLMs Hallucinate                                    │
│ ─────────────────────────────────────────────────────────────── │
│                                                                 │
│                    ┌─────────────────┐                         │
│                    │ Training Corpus │                         │
│                    │ (patterns, not  │                         │
│                    │  facts)         │                         │
│                    └────────┬────────┘                         │
│                             │                                   │
│                             ▼                                   │
│                    ┌─────────────────┐                         │
│                    │ Statistical     │                         │
│                    │ Prediction      │                         │
│                    │ "What token is  │                         │
│                    │  likely next?"  │                         │
│                    └────────┬────────┘                         │
│                             │                                   │
│              ┌──────────────┴──────────────┐                   │
│              ▼                              ▼                   │
│    ┌─────────────────┐            ┌─────────────────┐          │
│    │ Likely + True   │            │ Likely + False  │          │
│    │ (useful output) │            │ (hallucination) │          │
│    └─────────────────┘            └─────────────────┘          │
│                                                                 │
│    SAME MECHANISM ───────────────────────────► SAME MECHANISM  │
│                                                                 │
│    No internal signal distinguishes these two cases.           │
│    Surface confidence applied equally to both.                 │
│    Performed uncertainty uncorrelated with which is which.     │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘

CORE INSIGHT:
Hallucination is not a failure mode. It's the inevitable result of
statistical prediction applied to factual questions. The model has
no concept of "true"—only "likely." When likely ≠ true, you get
hallucination. When likely = true, you get useful output. Same process.
```

---

### Analysis Essay

> **Why LLMs Hallucinate**
>
> Hallucination isn't a bug—it's an intrinsic property of how large language models work. Understanding why requires discarding several intuitive but incorrect assumptions.
>
> **The core mechanism: Statistical Prediction**
>
> An LLM doesn't store facts and retrieve them. It predicts the most likely next token given the previous tokens. "Likely" means "frequently followed this pattern in training." This is fundamentally different from knowing, reasoning, or remembering.
>
> When you ask about the 1987 Best Picture winner, the pattern "1987 Best Picture" was strongly associated with "The Last Emperor" in training data—many articles, reviews, and lists reinforced this. The prediction aligns with truth.
>
> When you ask about an obscure chess tournament, there's no strong pattern. The model still produces confident text—because that's what it does—but the prediction doesn't align with any ground truth. Same mechanism, different outcome.
>
> **Why confidence is misleading**
>
> The style of confident assertion is itself a pattern learned from training. Academic papers, encyclopedia entries, and authoritative sources don't hedge on facts. The model learned to produce this style, regardless of whether the specific claim is accurate. Surface confidence is a text pattern, not a reliability signal.
>
> **Why uncertainty expressions don't help**
>
> When Claude says "I'm not sure," it's not experiencing uncertainty—it's producing text that resembles uncertainty. This happens when the context suggests hedging (e.g., after being challenged) not when the underlying "knowledge" is actually uncertain. You cannot use these phrases to gauge reliability.
>
> **Why it can't be "fixed"**
>
> The same generative capability that produces useful, creative, novel outputs—code that works, explanations that clarify, writing that engages—is the capability that produces hallucinations. Both are novel combinations of learned patterns. You cannot have a model that creatively combines ideas without sometimes combining them into false claims.
>
> **The transformed understanding**
>
> Stop asking "how do we make LLMs stop hallucinating?" Start asking "how do we work with systems that produce plausible text without regard for truth?" The first question has no answer. The second has many: verification, grounding, structured outputs, retrieval augmentation—but none eliminate hallucination, because hallucination isn't a failure. It's the system working exactly as designed.

---

### Assumptions Summary

| Assumption | Status | Replaced With |
|------------|--------|---------------|
| A1: Hallucination = information gap | ❌ Discarded | Statistical prediction—no "information" involved |
| A2: LLM knows when it's wrong | ❌ Discarded | Performed uncertainty—no metacognition |
| A3: Better data = fix | ❌ Discarded | Generative confabulation—intrinsic to the mechanism |
| A4: Confidence = correctness | ❌ Discarded | Surface confidence—text style, not reliability |

---

### Understand Journey Summary

| Phase | What Happened |
|-------|---------------|
| **Intake** | Routed to Understand (causal question, no making needed) |
| **Surface** | 4 assumptions identified through sentence completion |
| **Examine A1** | Tested with Oscar vs chess tournament examples |
| **Concept 1** | Statistical Prediction ⚡ (threshold concept) |
| **Examine A2** | Probed what "I'm not sure" actually means |
| **Concept 2** | Performed Uncertainty |
| **Examine A3** | Research detour on curated training data |
| **Concept 3** | Generative Confabulation |
| **Examine A4** | Tested confidence vs correctness correlation |
| **Concept 4** | Surface Confidence |
| **Integrate** | Mental model: same mechanism → useful or hallucination |
| **Essay** | Synthesized transformed understanding |

**Key insight:** There's no artifact. No code. No "how to deal with hallucination." The user now *understands* hallucination in a way that transforms how they think about LLMs—but if they wanted to *do* something about it, that would be a separate Build journey.

---

## Research Example: Running LLMs Locally

**User enters:** "What are the current options for running LLMs locally?"

### Phase 0: Journey Intake

**Quick Route:** "What are the options for X?" → **Research** ✓

**Work Backwards:**
- **Ideal answer:** A comprehensive landscape of local LLM options—models, runtimes, hardware requirements—organized and compared
- **Answer type:** Facts (survey/comparison)
- **Routes to:** Research (primary—user wants knowledge gathered)

**Confirmation:**

```
┌─────────────────────────────────────────────────────────────────┐
│                                                                 │
│  This is a RESEARCH question—you want to survey the landscape │
│  of local LLM options.                                         │
│                                                                 │
│  I'll help you:                                                │
│  • Decompose this into specific, answerable questions          │
│  • Find and evaluate sources for each                          │
│  • Synthesize findings into key insights                       │
│  • Identify adjacent questions for further exploration         │
│                                                                 │
│  [Begin Research →]    [I want to build something with this →] │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

---

### Phase 1: Decompose into Questions

```
┌─────────────────────────────────────────────────────────────────┐
│ TOPIC: Running LLMs Locally                                     │
│ ─────────────────────────────────────────────────────────────── │
│                                                                 │
│ 📂 Category: Available Models                                   │
│    ├─ ○ What open-source LLMs can run locally?                 │
│    ├─ ○ How do model sizes affect requirements?                │
│    └─ ○ What are quantized models?                             │
│                                                                 │
│ 📂 Category: Inference Runtimes                                 │
│    ├─ ○ What software runs local LLMs?                         │
│    └─ ○ How do llama.cpp, Ollama, and vLLM compare?           │
│                                                                 │
│ 📂 Category: Hardware Requirements                              │
│    ├─ ○ What GPU/RAM is needed for different model sizes?      │
│    └─ ○ Can you run LLMs on CPU only?                          │
│                                                                 │
│ 📂 Category: Comparison to Cloud                                │
│    ├─ ○ How does local quality compare to Claude/GPT-4?        │
│    └─ ○ What are the cost tradeoffs?                           │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

---

### Phase 2: Answer Questions

#### Category: Available Models

**Q: What open-source LLMs can run locally?**

| Model Family | Creator | Sizes | License |
|--------------|---------|-------|---------|
| Llama 3.1 | Meta | 8B, 70B, 405B | Llama 3.1 License |
| Mistral | Mistral AI | 7B, 8x7B (Mixtral) | Apache 2.0 |
| Qwen 2.5 | Alibaba | 0.5B - 72B | Apache 2.0 |
| Gemma 2 | Google | 2B, 9B, 27B | Gemma License |
| Phi-3 | Microsoft | 3.8B, 14B | MIT |

**Sources:** [HF Leaderboard: high] [LMSys Arena: high]

**Q: How do model sizes affect requirements?**

| Model Size | VRAM (FP16) | VRAM (Q4) | RAM (CPU) |
|------------|-------------|-----------|-----------|
| 7-8B | 16 GB | 4-6 GB | 8-16 GB |
| 13-14B | 28 GB | 8-10 GB | 16-32 GB |
| 30-35B | 70 GB | 20-24 GB | 64 GB |
| 70B | 140 GB | 40-48 GB | 128 GB |

**Sources:** [llama.cpp docs: primary] [Ollama: primary]

**Q: What are quantized models?**

Models compressed from 16-bit to 4/8-bit precision. Reduces VRAM 2-4x with ~1-3% quality loss. GGUF (llama.cpp) and AWQ/GPTQ are main formats.

**Rise Above:**
```
┌─────────────────────────────────────────────────────────────────┐
│ 📂 Category: Available Models                                   │
│ INSIGHT: The "Llama 3.1 8B quantized" sweet spot               │
│                                                                 │
│ For most local use cases, Llama 3.1 8B with Q4 quantization   │
│ hits the sweet spot: fits in 6GB VRAM (consumer GPU), performs │
│ close to GPT-3.5 on most tasks.                                │
└─────────────────────────────────────────────────────────────────┘
```

---

#### Category: Inference Runtimes

**Q: What software runs local LLMs?**

| Runtime | Type | Best For |
|---------|------|----------|
| llama.cpp | C++ inference | Maximum compatibility, CPU |
| Ollama | Wrapper + API | Easy setup, docker-like |
| vLLM | Python server | Production serving, batching |
| LM Studio | Desktop app | GUI, beginners |

**Q: How do llama.cpp, Ollama, and vLLM compare?**

| Aspect | llama.cpp | Ollama | vLLM |
|--------|-----------|--------|------|
| Setup | Compile | `brew install` | pip + GPU |
| Use Case | Tinkering, CPU | Personal use | Production |

**Rise Above:**
```
┌─────────────────────────────────────────────────────────────────┐
│ 📂 Category: Inference Runtimes                                 │
│ INSIGHT: The abstraction ladder                                 │
│                                                                 │
│ llama.cpp → Ollama → Your app                                  │
│ (engine)    (ease)   (integration)                             │
│                                                                 │
│ Start with Ollama. Drop to llama.cpp if you need control.     │
└─────────────────────────────────────────────────────────────────┘
```

---

#### Category: Hardware Requirements

**Q: What GPU/RAM is needed for different model sizes?**

| Setup | Can Run | Quality Level |
|-------|---------|---------------|
| M1/M2 Mac 16GB | 7B Q8, 13B Q4 | Good |
| RTX 3060 12GB | 7B Q8, 13B Q4 | Good, fast |
| RTX 4090 24GB | 30B Q4 | Excellent, fast |

**Q: Can you run LLMs on CPU only?**

Yes. llama.cpp does ~10-20 tok/s on CPU for 7B Q4. Usable for testing, too slow for real-time chat.

**Rise Above:**
```
┌─────────────────────────────────────────────────────────────────┐
│ 📂 Category: Hardware Requirements                              │
│ INSIGHT: The Mac surprise                                       │
│                                                                 │
│ Apple Silicon unified memory makes Macs competitive local LLM  │
│ platforms. An M2 Pro 32GB can run models that need expensive   │
│ discrete GPUs on Windows/Linux.                                │
└─────────────────────────────────────────────────────────────────┘
```

---

#### Category: Comparison to Cloud

**Q: How does local quality compare to Claude/GPT-4?**

| Model | Relative Quality |
|-------|------------------|
| GPT-4 / Claude 3.5 Sonnet | 100% (reference) |
| Llama 3.1 70B | ~80-85% |
| Llama 3.1 8B | ~60-70% |

**Q: What are the cost tradeoffs?**

Local is "free" per query after hardware cost. Break-even vs API at ~500K-2M tokens. But local models are weaker—you're trading quality for cost, plus you get privacy and no rate limits.

**Rise Above:**
```
┌─────────────────────────────────────────────────────────────────┐
│ 📂 Category: Comparison to Cloud                                │
│ INSIGHT: Different tools for different jobs                    │
│                                                                 │
│ Local isn't "cheaper Claude"—it's a different tool:           │
│ • Privacy (data never leaves your machine)                     │
│ • No rate limits                                               │
│ • Offline capability                                           │
│ • Customization (fine-tuning)                                  │
│                                                                 │
│ Use local for: bulk processing, privacy, experimentation.      │
│ Use cloud for: maximum quality, complex reasoning.             │
└─────────────────────────────────────────────────────────────────┘
```

---

### Phase 3: Key Insights

```
┌─────────────────────────────────────────────────────────────────┐
│ KEY INSIGHTS                                                    │
│ ─────────────────────────────────────────────────────────────── │
│                                                                 │
│ 💡 The Llama 3.1 8B Q4 sweet spot                              │
│    Best balance of capability/requirements for most users.     │
│                                                                 │
│ 💡 The abstraction ladder                                       │
│    llama.cpp → Ollama → Your app. Start with Ollama.          │
│                                                                 │
│ 💡 The Mac surprise                                             │
│    Apple Silicon is surprisingly competitive.                  │
│                                                                 │
│ 💡 Different tools for different jobs                          │
│    Local = privacy, no limits. Cloud = quality, reliability.  │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

---

### Phase 4: Frontier (Adjacent Questions)

```
┌─────────────────────────────────────────────────────────────────┐
│ FRONTIER: Adjacent Questions                                    │
│ ─────────────────────────────────────────────────────────────── │
│                                                                 │
│ 🔭 Discovered from "What are quantized models?"                │
│    ? How does quantization actually work (AWQ vs GPTQ)?        │
│    ? Can you quantize a model yourself?                        │
│                                                                 │
│ 🔭 Discovered from "How do runtimes compare?"                  │
│    ? How do you deploy a local LLM as an API?                  │
│    ? What's the Ollama Modelfile format?                       │
│                                                                 │
│ 🔭 Discovered from "Cost tradeoffs"                            │
│    ? Is fine-tuning local models practical?                    │
│    ? What about running on cloud GPUs you control?             │
│                                                                 │
│ 🔭 Discovered from "Quality comparison"                        │
│    ? Why do local models lag on reasoning tasks?               │
│    ? What's the state of local code models specifically?       │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

---

### Research Essay

> **Running LLMs Locally: A Landscape Survey**
>
> The local LLM ecosystem has matured rapidly. Where running your own model once required deep ML expertise, today anyone can run capable language models on consumer hardware with a single command.
>
> **The model landscape**
>
> Llama 3.1 from Meta dominates open-source. The 8B parameter version, when quantized to 4-bit precision, runs on a 6GB GPU while performing near GPT-3.5 levels. For those with more hardware, the 70B version approaches GPT-4 on many tasks.
>
> **The software stack**
>
> Most local LLM software builds on llama.cpp. Ollama wraps this in a Docker-like experience—`ollama run llama3.1` is all you need. For production serving, vLLM is the standard.
>
> **Hardware requirements**
>
> A 7B quantized model runs on a $300 GPU or 16GB Mac. Apple Silicon, with unified memory, has become surprisingly competitive—an M2 Pro can run models that would need expensive discrete GPUs elsewhere.
>
> **When to use local vs cloud**
>
> Local LLMs aren't "cheaper Claude"—they're different tools. Choose local for: privacy-sensitive data, bulk processing, offline use, experimentation. Choose cloud for: maximum quality, complex reasoning, simplicity.
>
> **The practical starting point**
>
> Install Ollama, run Llama 3.1 8B, see how far it gets you. The ecosystem has made the on-ramp gentle enough that experimentation costs almost nothing.

---

### Research Journey Summary

| Phase | What Happened |
|-------|---------------|
| **Intake** | Routed to Research (landscape survey question) |
| **Decompose** | Topic → 4 categories, 9 questions |
| **Answer** | Each question researched with sources |
| **Rise Above** | 4 category insights synthesized |
| **Key Insights** | Cross-cutting insights extracted |
| **Frontier** | 8 adjacent questions discovered |
| **Essay** | Synthesized findings into coherent narrative |

---

## Comparison: Three Modes

| Aspect | Research | Understand | Build |
|--------|----------|------------|-------|
| **Goal** | Gather knowledge | Transform thinking | Create capability |
| **Output** | Answered questions + synthesis | Concepts + mental model | Constructs + decisions |
| **Assumptions** | Not surfaced | Surfaced and examined | Minimal (grounding only) |
| **Artifacts** | None | None | Code/system |
| **"Rise above"** | Category insights | Model integration | Capability composition |
| **Frontier** | Adjacent questions | Transferred understanding | Extended system |

---

## What Comes Next

Each mode can lead to another:

**Research → Build:**
> "Now help me set up Ollama for my team"

**Research → Understand:**
> "Why do local models lag on reasoning?"

**Understand → Build:**
> "Now help me build guardrails for hallucination"

**Build → Research:**
> (During grounding) "What are the API rate limits?"

**Build → Understand:**
> (When stuck) "Why isn't the message passing working?"

The modes aren't isolated—they're a connected system for learning.
