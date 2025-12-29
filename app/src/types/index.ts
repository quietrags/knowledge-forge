// ============================================================================
// Core Types
// ============================================================================

export type Mode = 'build' | 'understand' | 'research'

export type QuestionStatus = 'answered' | 'researching' | 'pending'

export type SourceCredibility = 'primary' | 'high' | 'medium' | 'low'

// ============================================================================
// Path / Learning Trail
// ============================================================================

export interface PathNode {
  id: string
  name: string
  status: 'solid' | 'partial' | 'empty'
}

export interface PathData {
  nodes: PathNode[]
  neighbors: string[]
}

// ============================================================================
// Research Mode Types
// ============================================================================

export interface Source {
  title: string
  url?: string
  credibility: SourceCredibility
}

export interface SubQuestion {
  id: string
  question: string
  status: QuestionStatus
  answer?: string
}

export interface Question {
  id: string
  question: string
  status: QuestionStatus
  answer?: string
  sources: Source[]
  subQuestions: SubQuestion[]
  code?: CodeContent
  canvas?: CanvasContent
}

export interface Category {
  id: string
  name: string
  questions: Question[]
}

export interface KeyIdea {
  id: string
  title: string
  description: string
  relevance: string // Which questions this helps answer
}

export interface EmergentQuestion {
  id: string
  question: string
  sourceCategory: string // Which category this emerged from
}

export interface ResearchModeData {
  topic: string
  meta: string
  categories: Category[]
  keyIdeas: KeyIdea[]
  emergentQuestions: EmergentQuestion[]
}

// ============================================================================
// Build Mode Types
// ============================================================================

export interface Narrative {
  label: string
  title: string
  meta: string
  content: string // HTML/Markdown content
}

export interface Component {
  id: string
  name: string
  description: string
  usage: string // How it's used in the build
}

export interface Decision {
  id: string
  choice: string // What was chosen
  alternative: string // What was not chosen
  rationale: string // Why this choice
}

export interface Capability {
  id: string
  capability: string // What you can now do/build
  enabledBy: string // What knowledge enables this
}

export interface BuildModeData {
  narrative: Narrative
  components: Component[]
  decisions: Decision[]
  capabilities: Capability[]
}

// ============================================================================
// Understand Mode Types
// ============================================================================

export interface Distinction {
  id: string
  itemA: string // First thing being distinguished
  itemB: string // Second thing being distinguished
  difference: string // The key difference
}

export interface Assumption {
  id: string
  assumption: string // What was assumed
  surfaced: string // What you now realize/understand
}

export interface UnderstandModeData {
  essay: Narrative // The analysis journey
  distinctions: Distinction[]
  assumptions: Assumption[]
  mentalModel: string // HTML/Markdown content
}

// ============================================================================
// Code & Canvas (shared across modes)
// ============================================================================

export interface LibraryRef {
  name: string
  url: string
}

export interface CodeContent {
  file: string
  content: string // Syntax-highlighted HTML or raw code
  language?: string
  library?: LibraryRef
}

export interface CanvasContent {
  summary?: string // HTML content
  diagram?: string // HTML/SVG content
}

// ============================================================================
// Session / App State
// ============================================================================

export interface ModeColors {
  accent: string
  accentBg: string
}

export const MODE_COLORS: Record<Mode, ModeColors> = {
  build: { accent: '#059669', accentBg: '#ECFDF5' },
  understand: { accent: '#2563EB', accentBg: '#EFF6FF' },
  research: { accent: '#7C3AED', accentBg: '#F3E8FF' },
}

export const MODE_TABS: Record<Mode, string[]> = {
  build: ['Build Narrative', 'Components', 'Decisions', 'Capabilities'],
  understand: ['Analysis Essay', 'Distinctions', 'Assumptions', 'Mental Model'],
  research: ['Question Tree', 'Key Ideas', 'Emergent Questions'],
}

// ============================================================================
// Full Session State
// ============================================================================

export interface SessionState {
  mode: Mode
  activeTab: number
  selectedQuestionId: string | null
  path: PathData

  // Mode-specific data
  build?: BuildModeData
  understand?: UnderstandModeData
  research?: ResearchModeData

  // Contextual panels
  currentCode?: CodeContent
  currentCanvas?: CanvasContent
}
