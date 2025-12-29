// ============================================================================
// Core Types
// ============================================================================

export type Mode = 'build' | 'understand' | 'research'

export type QuestionStatus = 'open' | 'investigating' | 'answered'

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
// Research Mode Types (v0.2)
// ============================================================================

export interface Source {
  title: string
  url?: string
  credibility: SourceCredibility
}

export interface Question {
  id: string
  question: string
  status: QuestionStatus
  answer?: string
  sources: Source[]
  categoryId?: string
  code?: CodeContent
  canvas?: CanvasContent
}

export interface CategoryQuestion {
  id: string
  category: string
  insight?: string // "rise above" synthesis
  questionIds: string[]
}

export interface KeyInsight {
  id: string
  title: string
  description: string
  relevance: string // Which questions this helps answer
}

export interface AdjacentQuestion {
  id: string
  question: string
  discoveredFrom: string // Which question spawned this
}

export interface ResearchModeData {
  topic: string
  meta: string
  categories: CategoryQuestion[]
  questions: Question[]
  keyInsights: KeyInsight[]
  adjacentQuestions: AdjacentQuestion[]
}

// ============================================================================
// Build Mode Types (v0.2)
// ============================================================================

export interface Narrative {
  label: string
  title: string
  meta: string
  content: string // HTML/Markdown content
}

export interface Construct {
  id: string
  name: string
  description: string
  usage: string
  code?: string
}

export interface Decision {
  id: string
  choice: string
  alternative: string
  rationale: string
  constructIds: string[]
  producesId?: string
}

export interface Capability {
  id: string
  capability: string
  enabledBy: string[]
}

export interface BuildModeData {
  narrative: Narrative
  constructs: Construct[]
  decisions: Decision[]
  capabilities: Capability[]
}

// ============================================================================
// Understand Mode Types (v0.2)
// ============================================================================

export interface Assumption {
  id: string
  assumption: string
  surfaced: string
  status: 'active' | 'discarded'
}

export interface Concept {
  id: string
  name: string
  definition: string
  distinguishedFrom?: string
  isThreshold: boolean
  fromAssumptionId?: string
}

export interface Model {
  id: string
  name: string
  description: string
  conceptIds: string[]
  visualization?: string
}

export interface UnderstandModeData {
  essay: Narrative
  assumptions: Assumption[]
  concepts: Concept[]
  models: Model[]
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
  content: string
  language?: string
  library?: LibraryRef
}

export interface CanvasContent {
  summary?: string
  diagram?: string
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
  build: ['Build Narrative', 'Constructs', 'Decisions', 'Capabilities'],
  understand: ['Analysis Essay', 'Assumptions', 'Concepts', 'Model'],
  research: ['Questions', 'Key Insights', 'Frontier'],
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
