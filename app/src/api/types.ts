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
  | 'session.resumed'
  | 'session.ended'
  // Agent activity
  | 'agent.thinking'
  | 'agent.speaking'
  | 'agent.complete'
  | 'agent.awaiting_input'
  // Research mode data events
  | 'data.question.added'
  | 'data.question.updated'
  | 'data.question.answered'
  | 'data.category.added'
  | 'data.category.insight'
  | 'data.key_insight.added'
  | 'data.adjacent_question.added'
  // Build mode data events (legacy - kept for backwards compatibility)
  | 'data.construct.added'
  | 'data.decision.added'
  | 'data.capability.added'
  | 'data.grounding_concept.added'
  // Build mode data events (new - from Build agent)
  | 'data.anchor.added'
  | 'data.primary_anchor_set'
  | 'data.anchors_confirmed'
  | 'data.topic_type'
  | 'data.construction_slo.added'
  | 'data.slos_selected'
  | 'data.construction_sequence'
  | 'data.sequences_designed'
  | 'data.construction_round'
  | 'data.scaffold_level'
  | 'data.mode_change'
  | 'data.surrender_strategy'
  | 'data.construction_verified'
  | 'data.slo_complete'
  | 'data.slo_transition'
  | 'data.session_insights'
  | 'data.consolidation_complete'
  | 'data.session_complete'
  // Understand mode data events (legacy - kept for backwards compatibility)
  | 'data.assumption.surfaced'
  | 'data.assumption.discarded'
  | 'data.concept.added'
  | 'data.concept.distinguished'
  | 'data.model.integrated'
  // Understand mode data events (new - from Understand agent)
  | 'data.knowledge_confidence'
  | 'data.session_config'
  | 'data.slo.added'
  | 'data.facet_updated'
  | 'data.calibration_complete'
  | 'data.diagnostic_result'
  | 'data.mastery_achieved'
  | 'data.slo_skipped'
  // Shared events
  | 'narrative.updated'
  | 'phase.changed'
  | 'phase.checkpoint'
  | 'path.updated'
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

export interface SessionResumedPayload {
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

export interface AgentAwaitingInputPayload {
  prompt: string
  phase?: string
}

// Research data events
export interface QuestionAddedPayload {
  question: Question
  categoryId: string
}

export interface QuestionUpdatedPayload {
  questionId: string
  status?: 'open' | 'investigating' | 'answered'
  answer?: string
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

export interface ConceptAddedPayload {
  id: string
  name: string
  definition: string
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

// Build agent data events (new)
export interface AnchorAddedPayload {
  id: string
  concept: string
  strength: 'strong' | 'moderate' | 'weak'
  evidence: string
}

export interface PrimaryAnchorSetPayload {
  anchorId: string
}

export interface AnchorsConfirmedPayload {
  anchorIds: string[]
  primaryId: string
}

export interface TopicTypePayload {
  topicType: 'vocabulary' | 'mental_model' | 'skill' | 'disposition'
}

export interface ConstructionSLOAddedPayload {
  id: string
  statement: string
  frame: string
  inScope: string[]
  outOfScope: string[]
  estimatedRounds: number
}

export interface SLOsSelectedPayload {
  sloIds: string[]
  sequence: string[]
}

export interface ConstructionSequencePayload {
  sloId: string
  sequence: Array<{
    phase: string
    description: string
  }>
}

export interface SequencesDesignedPayload {
  ready: boolean
}

export interface ConstructionRoundPayload {
  sloId: string
  round: number
  totalRounds: number
  result: 'pass' | 'fail' | 'partial'
  feedback: string
}

export interface ScaffoldLevelPayload {
  level: number
  direction: 'increased' | 'decreased' | 'maintained'
}

export interface ModeChangePayload {
  from: 'doing' | 'teaching' | 'watching'
  to: 'doing' | 'teaching' | 'watching'
  reason: string
}

export interface SurrenderStrategyPayload {
  strategy: string
  reason: string
}

export interface ConstructionVerifiedPayload {
  sloId: string
  verified: boolean
  evidence: string
}

export interface SLOCompletePayload {
  sloId: string
  success: boolean
  rounds: number
}

export interface SLOTransitionPayload {
  fromSloId: string
  toSloId: string
  reason: string
}

export interface SessionInsightsPayload {
  insights: string[]
}

export interface ConsolidationCompletePayload {
  summary: string
}

export interface SessionCompletePayload {
  totalSLOs: number
  completedSLOs: number
  summary: string
}

// Understand agent data events (new)
export interface KnowledgeConfidencePayload {
  level: 'high' | 'medium' | 'low' | 'unknown'
  evidence: string
}

export interface SessionConfigPayload {
  targetMastery: number
  maxRounds: number
}

export interface SLOAddedPayload {
  id: string
  statement: string
  frame: string
  inScope: string[]
  outOfScope: string[]
  estimatedRounds: number
}

export interface FacetUpdatedPayload {
  sloId: string
  facet: 'vocabulary' | 'mental_model' | 'practical_grasp' | 'boundary_conditions' | 'transfer'
  status: 'not_tested' | 'missing' | 'shaky' | 'solid'
  evidence: string
}

export interface CalibrationCompletePayload {
  sloId: string
  facets: Record<string, string>
}

export interface DiagnosticResultPayload {
  sloId: string
  round: number
  result: 'pass' | 'fail'
  feedback: string
}

export interface MasteryAchievedPayload {
  sloId: string
  rounds: number
}

export interface SLOSkippedPayload {
  sloId: string
  reason: string
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

export interface PhaseCheckpointPayload {
  id: string
  message: string
  options: string[]
  requiresApproval: boolean
}

export interface PathUpdatedPayload {
  nodes: Array<{
    id: string
    name: string
    status: 'solid' | 'partial' | 'empty'
  }>
  neighbors: string[]
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
