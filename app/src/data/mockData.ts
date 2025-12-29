import type {
  ResearchModeData,
  BuildModeData,
  UnderstandModeData,
  PathData,
  CodeContent,
  CanvasContent,
} from '../types'

// ============================================================================
// Path Data
// ============================================================================

export const mockPathData: PathData = {
  nodes: [
    { id: 'llm-basics', name: 'LLM Basics', status: 'solid' },
    { id: 'prompting', name: 'Prompting', status: 'solid' },
    { id: 'agents', name: 'Agent Architectures', status: 'partial' },
  ],
  neighbors: ['Tool Use', 'Memory Systems'],
}

// ============================================================================
// Research Mode Data
// ============================================================================

export const mockResearchData: ResearchModeData = {
  topic: 'AI Coding Agent Economics',
  meta: 'Exploring key questions about billing, costs, and optimization',
  categories: [
    {
      id: 'billing',
      name: 'Billing Fundamentals',
      questions: [
        {
          id: 'q1',
          question: 'What is the fundamental billing model for AI coding agents?',
          status: 'answered',
          answer:
            'Token-based billing is the standard. Tokens (~4 characters) are the unit of compute. Every API call consumes tokens. Unlike traditional software with near-zero marginal cost, every inference requires real compute.',
          sources: [
            { title: 'Claude Code Usage Guide', credibility: 'primary' },
            {
              title: 'DX Pricing 2025',
              url: 'https://getdx.com/blog/ai-coding-assistant-pricing/',
              credibility: 'high',
            },
          ],
          subQuestions: [
            { id: 'sq1', question: 'How do caching mechanisms affect costs?', status: 'pending' },
            { id: 'sq2', question: 'Typical token count for agent workflows?', status: 'pending' },
          ],
          code: {
            file: 'tokens.py',
            content: `# Token estimation utility
def estimate_tokens(text: str) -> int:
    """Rough token count: ~4 chars per token"""
    return len(text) // 4

def calculate_cost(tokens: int, model: str) -> float:
    """Calculate cost in dollars"""
    rates = {
        "sonnet": {"input": 3, "output": 15},
        "opus": {"input": 15, "output": 75}
    }
    return tokens * rates[model]["output"] / 1_000_000`,
            language: 'python',
            library: {
              name: 'Anthropic SDK',
              url: 'https://docs.anthropic.com/en/api/client-sdks',
            },
          },
          canvas: {
            summary:
              '<h4>Key Points</h4><ul><li>Tokens ≈ 4 characters</li><li>Every API call = real compute cost</li><li>Output tokens cost 3-5x more than input</li></ul>',
            diagram:
              '<pre style="text-align:center;font-size:12px;">User Request\n     ↓\nInput Tokens (cheaper)\n     ↓\n  LLM Processing\n     ↓\nOutput Tokens (expensive)</pre>',
          },
        },
        {
          id: 'q2',
          question: 'Why do output tokens cost more than input?',
          status: 'answered',
          answer:
            'Generation is computationally harder. Input = single forward pass. Output = sequential passes with attention over all previous tokens. A 1000-token response requires 1000 forward passes.',
          sources: [{ title: 'IBM Context Window Guide', credibility: 'high' }],
          subQuestions: [
            { id: 'sq3', question: 'How does KV caching reduce this?', status: 'pending' },
          ],
          code: {
            file: 'pricing.py',
            content: `# Model pricing per million tokens
PRICING = {
    "claude-sonnet": {"input": 3, "output": 15},
    "claude-opus": {"input": 15, "output": 75},
    "gpt-4o": {"input": 5, "output": 15},
}

# Output costs 3-5x more due to autoregressive generation`,
            language: 'python',
          },
          canvas: {
            summary:
              '<p>Output costs 2-5x input due to <strong>autoregressive generation</strong>: each token requires a forward pass attending to all previous tokens.</p>',
          },
        },
      ],
    },
    {
      id: 'agents-vs-autocomplete',
      name: 'Agent vs Autocomplete',
      questions: [
        {
          id: 'q3',
          question: 'How do agents differ economically from autocomplete?',
          status: 'answered',
          answer:
            'Autocomplete: reactive, single suggestion, often flat-rate pricing. Agents: autonomous, 5-20 API calls per task, metered billing. Fundamentally different economics.',
          sources: [{ title: 'GoCodeo Analysis', credibility: 'high' }],
          subQuestions: [],
          code: {
            file: 'compare.py',
            content: `# Per-task cost comparison
autocomplete_cost = 0.001  # Single call
agent_cost = 0.15          # ~10-15 calls

# Agent tasks: planning + execution + verification
# Each step consumes tokens`,
            language: 'python',
          },
          canvas: {
            summary:
              '<p>Agents consume <strong>5-20x more tokens</strong> per task than autocomplete. Different cost model entirely.</p>',
          },
        },
      ],
    },
    {
      id: 'optimization',
      name: 'Cost Optimization',
      questions: [
        {
          id: 'q4',
          question: 'How does context window size affect costs?',
          status: 'researching',
          answer:
            'Attention scales O(n²) with context length. Longer context = quadratically more compute. This is why managing context is critical for cost control.',
          sources: [],
          subQuestions: [
            { id: 'sq4', question: 'Cost increase per context doubling?', status: 'pending' },
          ],
          code: {
            file: 'context.py',
            content: `# Context scaling impact
# Attention: O(n²) complexity

def attention_cost(context_length: int) -> float:
    """Relative compute cost"""
    return context_length ** 2

# 2x context = 4x compute
# 4x context = 16x compute`,
            language: 'python',
          },
          canvas: {
            summary: '<p>Context scales <strong>quadratically</strong>. Manage carefully.</p>',
          },
        },
        {
          id: 'q5',
          question: 'What are effective strategies for managing AI costs?',
          status: 'pending',
          answer: undefined,
          sources: [],
          subQuestions: [],
        },
      ],
    },
  ],
  keyIdeas: [
    {
      id: 'ki1',
      title: 'Marginal Cost Reality',
      description:
        'Unlike traditional software, every AI inference consumes real compute. This is why metered pricing dominates.',
      relevance: 'Answers: billing model, agent vs autocomplete',
    },
    {
      id: 'ki2',
      title: 'Autoregressive Generation',
      description:
        'Each output token requires a forward pass over all previous tokens. O(n) passes for n tokens.',
      relevance: 'Answers: why output costs more',
    },
    {
      id: 'ki3',
      title: 'Quadratic Attention',
      description: 'Attention mechanism scales O(n²) with context length.',
      relevance: 'Answers: context window costs',
    },
  ],
  emergentQuestions: [
    { id: 'eq1', question: 'How do caching mechanisms affect real-world costs?', sourceCategory: 'Billing Fundamentals' },
    { id: 'eq2', question: 'What is the actual token count for typical agent workflows?', sourceCategory: 'Billing Fundamentals' },
    { id: 'eq3', question: 'Cost increase per context doubling?', sourceCategory: 'Cost Optimization' },
    { id: 'eq4', question: 'Crossover point: subscription vs usage-based?', sourceCategory: 'Agent vs Autocomplete' },
  ],
}

// ============================================================================
// Build Mode Data (placeholder)
// ============================================================================

export const mockBuildData: BuildModeData = {
  narrative: {
    label: 'Building',
    title: 'Document Intelligence Models',
    meta: 'Building on: tesseract_ocr, http_endpoints',
    content: `
      <div class="callout prior">
        You know HTTP endpoints. You've used Tesseract OCR—and experienced <strong>flat text with no structure</strong>.
      </div>
      <h2>Why Document Intelligence Models Exist</h2>
      <p>Tesseract reads left-to-right, top-to-bottom. Feed it a two-column document and column one mixes with column two. It doesn't understand structure.</p>
      <div class="callout insight">
        Modern models use a <strong>layout-first approach</strong>: detect regions, classify elements, determine reading order, <em>then</em> extract text.
      </div>
    `,
  },
  components: [
    {
      id: 'comp1',
      name: 'Layout Detection Model',
      description: 'Identifies semantic regions (headers, paragraphs, tables) before text extraction.',
      usage: 'First step in the pipeline—feeds region coordinates to the OCR step.',
    },
    {
      id: 'comp2',
      name: 'Reading Order Algorithm',
      description: 'Determines the sequence to read detected regions.',
      usage: 'Ensures multi-column documents are read top-to-bottom per column, not left-to-right.',
    },
  ],
  decisions: [
    {
      id: 'd1',
      choice: 'Layout-first approach',
      alternative: 'Direct OCR (Tesseract-style)',
      rationale: 'Direct OCR loses document structure. Layout-first preserves semantic meaning.',
    },
    {
      id: 'd2',
      choice: 'Markdown output format',
      alternative: 'DocTags format',
      rationale: 'Markdown is simpler for RAG pipelines. DocTags needed only when UI requires bounding boxes.',
    },
  ],
  capabilities: [
    {
      id: 'cap1',
      capability: 'Build a document-to-markdown pipeline',
      enabledBy: 'Understanding layout detection + reading order',
    },
    {
      id: 'cap2',
      capability: 'Choose the right output format for a use case',
      enabledBy: 'Understanding Markdown vs DocTags trade-offs',
    },
  ],
}

// ============================================================================
// Understand Mode Data (placeholder)
// ============================================================================

export const mockUnderstandData: UnderstandModeData = {
  essay: {
    label: 'Analyzing',
    title: 'Agent Architectures',
    meta: 'Clarifying: failure modes, architecture selection',
    content: `
      <div class="callout prior">
        You know ReACT: think, act, observe, repeat. You know Reflexion adds self-critique. What's unclear: when does each fail?
      </div>
      <h2>ReACT: Power and Limits</h2>
      <p>ReACT is <strong>greedy</strong>—locally optimal decisions without lookahead. Failure modes:</p>
      <ul>
        <li>No natural stopping point</li>
        <li>Context overflow</li>
        <li>Tool fixation</li>
      </ul>
      <div class="callout insight">
        <strong>"ReACT needs external termination logic"</strong>—max iterations, token budgets, explicit "done" tools.
      </div>
    `,
  },
  distinctions: [
    {
      id: 'dist1',
      itemA: 'ReACT failure',
      itemB: 'Architecture mismatch',
      difference: 'ReACT failures are usually configuration issues (max iterations, tool design). Architecture mismatch is when the problem fundamentally needs planning or reflection.',
    },
    {
      id: 'dist2',
      itemA: 'Thought step',
      itemB: 'Logging',
      difference: 'Thought is active cognition that improves the next action. Logging is passive recording. Remove thought and quality degrades.',
    },
  ],
  assumptions: [
    {
      id: 'assum1',
      assumption: 'More sophisticated architecture = better results',
      surfaced: 'Simpler architectures often work better. Complexity adds failure modes. Start simple, add complexity only when needed.',
    },
    {
      id: 'assum2',
      assumption: 'Self-critique (Reflexion) is always beneficial',
      surfaced: 'External validation (tests, type checks) beats self-judgment. Use Reflexion only when external validation is unavailable.',
    },
  ],
  mentalModel: '<ul><li><strong>Structure problem</strong> → Planning</li><li><strong>Quality problem</strong> → Reflexion</li><li><strong>Speed problem</strong> → Simplify</li></ul>',
}

// ============================================================================
// Default Code/Canvas for modes
// ============================================================================

export const defaultBuildCode: CodeContent = {
  file: 'doc_pipeline.py',
  content: `import base64
from openai import OpenAI

def doc_to_markdown(image_path: str) -> str:
    with open(image_path, "rb") as f:
        data = base64.b64encode(f.read()).decode()

    client = OpenAI(base_url="http://localhost:8000/v1")
    resp = client.chat.completions.create(
        model="deepseek-ocr",
        messages=[{
            "role": "user",
            "content": [
                {"type": "image_url", "image_url": {"url": f"data:image/png;base64,{data}"}},
                {"type": "text", "text": "Convert to markdown."}
            ]
        }]
    )
    return resp.choices[0].message.content`,
  language: 'python',
  library: { name: 'DeepSeek-OCR', url: 'https://huggingface.co/deepseek-ai/DeepSeek-OCR' },
}

export const defaultUnderstandCode: CodeContent = {
  file: 'agent_loop.py',
  content: `def react_loop(agent, task, max_iter=10):
    for i in range(max_iter):
        thought = agent.think(task)
        action = agent.decide(thought)

        if action.type == "done":
            return action.result

        obs = agent.execute(action)
        task = agent.update(obs)

    raise TimeoutError("Max iterations")`,
  language: 'python',
  library: { name: 'Claude Agent SDK', url: 'https://docs.anthropic.com/en/docs/agents-and-tools' },
}

export const defaultBuildCanvas: CanvasContent = {
  summary: '<h4>Pipeline</h4><p>Image → Layout → Classification → Reading Order → Output</p>',
  diagram: '<pre style="font-size:11px;line-height:1.8;text-align:center;">Image\n  ↓\nLayout Detection\n  ↓\nStructured Output</pre>',
}

export const defaultUnderstandCanvas: CanvasContent = {
  summary: '<h4>Decision Tree</h4><ul><li>Structure → Planning</li><li>Quality → Reflexion</li><li>Speed → ReACT</li></ul>',
  diagram: '<pre style="font-size:11px;text-align:center;">Problem?\n  ↓\nStructure → Plan\nQuality → Reflect\nSpeed → ReACT</pre>',
}
