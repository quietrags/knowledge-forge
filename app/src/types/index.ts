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

export interface Boundary {
  id: string
  question: string
  answer: string
}

export interface Concept {
  id: string
  term: string
  definition: string
}

export interface AnswerableQuestion {
  id: string
  question: string
}

export interface BuildModeData {
  narrative: Narrative
  boundaries: Boundary[]
  concepts: Concept[]
  questions: AnswerableQuestion[]
}

// ============================================================================
// Understand Mode Types
// ============================================================================

export interface Misconception {
  id: string
  question: string
  answer: string
}

export interface Insight {
  id: string
  insight: string
  context: string
}

export interface UnderstandModeData {
  essay: Narrative // Similar structure to build narrative
  misconceptions: Misconception[]
  insights: Insight[]
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
  build: ['Knowledge Narrative', 'Boundaries', 'Concepts', 'Questions I Can Answer'],
  understand: ['Knowledge Essay', 'Misconceptions', 'Insights', 'Mental Model'],
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
