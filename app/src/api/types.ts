/**
 * API Types — Request/Response contracts matching backend
 */

import type {
  Mode,
  BuildPhase,
  ResearchModeData,
  UnderstandModeData,
  BuildModeData,
  Narrative,
  JourneyDesignBrief,
  Question,
} from '../types'

// ============================================================================
// Journey Intake API
// ============================================================================

export interface JourneyAnalyzeRequest {
  question: string
  learnerContext?: string // Optional prior knowledge
}

// JourneyDesignBrief is re-exported from types
export type { JourneyDesignBrief }

export interface JourneyConfirmRequest {
  brief: JourneyDesignBrief
  confirmed: boolean
  alternativeMode?: Mode // If user picked different mode
}

export interface SessionInitResponse {
  sessionId: string
  mode: Mode
  initialData: ResearchModeData | UnderstandModeData | BuildModeData
}

// ============================================================================
// Chat API
// ============================================================================

export interface ChatRequest {
  sessionId: string
  message: string
  context?: {
    selectedQuestionId?: string
    activeTab?: number
  }
}

// Chat response is streamed via SSE

// ============================================================================
// Session API
// ============================================================================

export interface SessionLoadResponse {
  sessionId: string
  mode: Mode
  phase?: BuildPhase
  journeyBrief: JourneyDesignBrief
  modeData: ResearchModeData | UnderstandModeData | BuildModeData
}

export interface SessionSaveRequest {
  checkpoint?: string
}

export interface SessionSaveResponse {
  saved: boolean
  path: string
}

// ============================================================================
// SSE Event Types
// ============================================================================

export type SSEEventType =
  // Session lifecycle
  | 'session.started'
  | 'session.ended'
  // Agent activity
  | 'agent.thinking'
  | 'agent.speaking'
  | 'agent.complete'
  // Research mode data events
  | 'data.question.added'
  | 'data.question.answered'
  | 'data.category.added'
  | 'data.category.insight'
  | 'data.key_insight.added'
  | 'data.adjacent_question.added'
  // Build mode data events
  | 'data.construct.added'
  | 'data.decision.added'
  | 'data.capability.added'
  | 'data.grounding_concept.added'
  // Understand mode data events
  | 'data.assumption.surfaced'
  | 'data.assumption.discarded'
  | 'data.concept.distinguished'
  | 'data.model.integrated'
  // Shared events
  | 'narrative.updated'
  | 'phase.changed'
  | 'error'

export interface SSEEvent<T = unknown> {
  type: SSEEventType
  timestamp: string
  payload: T
}

// ============================================================================
// SSE Event Payloads
// ============================================================================

// Session events
export interface SessionStartedPayload {
  sessionId: string
  mode: Mode
}

// Agent events
export interface AgentThinkingPayload {
  message: string
}

export interface AgentSpeakingPayload {
  delta: string // Streaming text chunk
}

export interface AgentCompletePayload {
  summary: string
}

// Research data events
export interface QuestionAddedPayload {
  question: Question
  categoryId: string
}

export interface QuestionAnsweredPayload {
  questionId: string
  answer: string
  sources: Array<{
    title: string
    url?: string
    credibility: 'primary' | 'high' | 'medium' | 'low'
  }>
}

export interface CategoryAddedPayload {
  id: string
  category: string
}

export interface CategoryInsightPayload {
  categoryId: string
  insight: string
}

export interface KeyInsightAddedPayload {
  id: string
  title: string
  description: string
  relevance: string
}

export interface AdjacentQuestionAddedPayload {
  id: string
  question: string
  discoveredFrom: string
}

// Build data events
export interface ConstructAddedPayload {
  id: string
  name: string
  description: string
  usage: string
}

export interface DecisionAddedPayload {
  id: string
  choice: string
  alternative: string
  rationale: string
}

export interface CapabilityAddedPayload {
  id: string
  capability: string
  enabledBy: string[]
}

export interface GroundingConceptAddedPayload {
  id: string
  name: string
  distinction: string
}

// Understand data events
export interface AssumptionSurfacedPayload {
  id: string
  assumption: string
  surfaced: string
}

export interface AssumptionDiscardedPayload {
  assumptionId: string
}

export interface ConceptDistinguishedPayload {
  id: string
  name: string
  definition: string
  distinguishedFrom?: string
  isThreshold: boolean
}

export interface ModelIntegratedPayload {
  id: string
  name: string
  description: string
  conceptIds: string[]
}

// Shared events
export interface NarrativeUpdatedPayload {
  mode: Mode
  narrative: Narrative
  delta?: string // Incremental text for streaming display
}

export interface PhaseChangedPayload {
  from: BuildPhase
  to: BuildPhase
}

export interface ErrorPayload {
  code: string
  message: string
  details?: unknown
}

// ============================================================================
// API Error
// ============================================================================

export interface APIError {
  status: number
  code: string
  message: string
  details?: unknown
}

export class APIException extends Error {
  readonly status: number
  readonly code: string
  readonly details?: unknown

  constructor(status: number, code: string, message: string, details?: unknown) {
    super(message)
    this.name = 'APIException'
    this.status = status
    this.code = code
    this.details = details
  }

  static fromResponse(status: number, data: unknown): APIException {
    if (typeof data === 'object' && data !== null && 'message' in data) {
      const errorData = data as { code?: string; message: string; details?: unknown }
      return new APIException(
        status,
        errorData.code || 'UNKNOWN_ERROR',
        errorData.message,
        errorData.details
      )
    }
    return new APIException(status, 'UNKNOWN_ERROR', 'An unexpected error occurred')
  }
}
