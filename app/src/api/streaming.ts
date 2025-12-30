/**
 * SSE Streaming Handler — EventSource wrapper with typed event handlers
 */

import { getStreamUrl } from './client'
import type {
  SSEEventType,
  SessionStartedPayload,
  SessionResumedPayload,
  AgentThinkingPayload,
  AgentSpeakingPayload,
  AgentCompletePayload,
  QuestionAddedPayload,
  QuestionUpdatedPayload,
  QuestionAnsweredPayload,
  CategoryAddedPayload,
  CategoryInsightPayload,
  KeyInsightAddedPayload,
  AdjacentQuestionAddedPayload,
  ConstructAddedPayload,
  DecisionAddedPayload,
  CapabilityAddedPayload,
  GroundingConceptAddedPayload,
  AssumptionSurfacedPayload,
  AssumptionDiscardedPayload,
  ConceptAddedPayload,
  ConceptDistinguishedPayload,
  ModelIntegratedPayload,
  NarrativeUpdatedPayload,
  PhaseChangedPayload,
  PathUpdatedPayload,
  ErrorPayload,
  // Build agent events (new)
  AnchorAddedPayload,
  PrimaryAnchorSetPayload,
  AnchorsConfirmedPayload,
  TopicTypePayload,
  ConstructionSLOAddedPayload,
  SLOsSelectedPayload,
  ConstructionSequencePayload,
  SequencesDesignedPayload,
  ConstructionRoundPayload,
  ScaffoldLevelPayload,
  ModeChangePayload,
  SurrenderStrategyPayload,
  ConstructionVerifiedPayload,
  SLOCompletePayload,
  SLOTransitionPayload,
  SessionInsightsPayload,
  ConsolidationCompletePayload,
  SessionCompletePayload,
  // Understand agent events (new)
  KnowledgeConfidencePayload,
  SessionConfigPayload,
  SLOAddedPayload,
  FacetUpdatedPayload,
  CalibrationCompletePayload,
  DiagnosticResultPayload,
  MasteryAchievedPayload,
  SLOSkippedPayload,
} from './types'

// ============================================================================
// Stream Handler Types
// ============================================================================

export interface StreamHandlers {
  // Session lifecycle
  onSessionStarted?: (payload: SessionStartedPayload) => void
  onSessionResumed?: (payload: SessionResumedPayload) => void
  onSessionEnded?: () => void

  // Agent activity
  onAgentThinking?: (payload: AgentThinkingPayload) => void
  onAgentSpeaking?: (payload: AgentSpeakingPayload) => void
  onAgentComplete?: (payload: AgentCompletePayload) => void

  // Research mode events
  onQuestionAdded?: (payload: QuestionAddedPayload) => void
  onQuestionUpdated?: (payload: QuestionUpdatedPayload) => void
  onQuestionAnswered?: (payload: QuestionAnsweredPayload) => void
  onCategoryAdded?: (payload: CategoryAddedPayload) => void
  onCategoryInsight?: (payload: CategoryInsightPayload) => void
  onKeyInsightAdded?: (payload: KeyInsightAddedPayload) => void
  onAdjacentQuestionAdded?: (payload: AdjacentQuestionAddedPayload) => void

  // Build mode events (legacy)
  onConstructAdded?: (payload: ConstructAddedPayload) => void
  onDecisionAdded?: (payload: DecisionAddedPayload) => void
  onCapabilityAdded?: (payload: CapabilityAddedPayload) => void
  onGroundingConceptAdded?: (payload: GroundingConceptAddedPayload) => void

  // Build mode events (new - from Build agent)
  onAnchorAdded?: (payload: AnchorAddedPayload) => void
  onPrimaryAnchorSet?: (payload: PrimaryAnchorSetPayload) => void
  onAnchorsConfirmed?: (payload: AnchorsConfirmedPayload) => void
  onTopicType?: (payload: TopicTypePayload) => void
  onConstructionSLOAdded?: (payload: ConstructionSLOAddedPayload) => void
  onSLOsSelected?: (payload: SLOsSelectedPayload) => void
  onConstructionSequence?: (payload: ConstructionSequencePayload) => void
  onSequencesDesigned?: (payload: SequencesDesignedPayload) => void
  onConstructionRound?: (payload: ConstructionRoundPayload) => void
  onScaffoldLevel?: (payload: ScaffoldLevelPayload) => void
  onModeChange?: (payload: ModeChangePayload) => void
  onSurrenderStrategy?: (payload: SurrenderStrategyPayload) => void
  onConstructionVerified?: (payload: ConstructionVerifiedPayload) => void
  onSLOComplete?: (payload: SLOCompletePayload) => void
  onSLOTransition?: (payload: SLOTransitionPayload) => void
  onSessionInsights?: (payload: SessionInsightsPayload) => void
  onConsolidationComplete?: (payload: ConsolidationCompletePayload) => void
  onSessionComplete?: (payload: SessionCompletePayload) => void

  // Understand mode events (legacy)
  onAssumptionSurfaced?: (payload: AssumptionSurfacedPayload) => void
  onAssumptionDiscarded?: (payload: AssumptionDiscardedPayload) => void
  onConceptAdded?: (payload: ConceptAddedPayload) => void
  onConceptDistinguished?: (payload: ConceptDistinguishedPayload) => void
  onModelIntegrated?: (payload: ModelIntegratedPayload) => void

  // Understand mode events (new - from Understand agent)
  onKnowledgeConfidence?: (payload: KnowledgeConfidencePayload) => void
  onSessionConfig?: (payload: SessionConfigPayload) => void
  onSLOAdded?: (payload: SLOAddedPayload) => void
  onFacetUpdated?: (payload: FacetUpdatedPayload) => void
  onCalibrationComplete?: (payload: CalibrationCompletePayload) => void
  onDiagnosticResult?: (payload: DiagnosticResultPayload) => void
  onMasteryAchieved?: (payload: MasteryAchievedPayload) => void
  onSLOSkipped?: (payload: SLOSkippedPayload) => void

  // Shared events
  onNarrativeUpdated?: (payload: NarrativeUpdatedPayload) => void
  onPhaseChanged?: (payload: PhaseChangedPayload) => void
  onPathUpdated?: (payload: PathUpdatedPayload) => void
  onError?: (payload: ErrorPayload) => void

  // Connection events
  onOpen?: () => void
  onClose?: () => void
  onConnectionError?: (error: Event) => void
}

// ============================================================================
// Event Type to Handler Mapping
// ============================================================================

const EVENT_HANDLER_MAP: Record<SSEEventType, keyof StreamHandlers | null> = {
  // Session lifecycle
  'session.started': 'onSessionStarted',
  'session.resumed': 'onSessionResumed',
  'session.ended': 'onSessionEnded',
  // Agent activity
  'agent.thinking': 'onAgentThinking',
  'agent.speaking': 'onAgentSpeaking',
  'agent.complete': 'onAgentComplete',
  // Research mode
  'data.question.added': 'onQuestionAdded',
  'data.question.updated': 'onQuestionUpdated',
  'data.question.answered': 'onQuestionAnswered',
  'data.category.added': 'onCategoryAdded',
  'data.category.insight': 'onCategoryInsight',
  'data.key_insight.added': 'onKeyInsightAdded',
  'data.adjacent_question.added': 'onAdjacentQuestionAdded',
  // Build mode (legacy)
  'data.construct.added': 'onConstructAdded',
  'data.decision.added': 'onDecisionAdded',
  'data.capability.added': 'onCapabilityAdded',
  'data.grounding_concept.added': 'onGroundingConceptAdded',
  // Build mode (new - from Build agent)
  'data.anchor.added': 'onAnchorAdded',
  'data.primary_anchor_set': 'onPrimaryAnchorSet',
  'data.anchors_confirmed': 'onAnchorsConfirmed',
  'data.topic_type': 'onTopicType',
  'data.construction_slo.added': 'onConstructionSLOAdded',
  'data.slos_selected': 'onSLOsSelected',
  'data.construction_sequence': 'onConstructionSequence',
  'data.sequences_designed': 'onSequencesDesigned',
  'data.construction_round': 'onConstructionRound',
  'data.scaffold_level': 'onScaffoldLevel',
  'data.mode_change': 'onModeChange',
  'data.surrender_strategy': 'onSurrenderStrategy',
  'data.construction_verified': 'onConstructionVerified',
  'data.slo_complete': 'onSLOComplete',
  'data.slo_transition': 'onSLOTransition',
  'data.session_insights': 'onSessionInsights',
  'data.consolidation_complete': 'onConsolidationComplete',
  'data.session_complete': 'onSessionComplete',
  // Understand mode (legacy)
  'data.assumption.surfaced': 'onAssumptionSurfaced',
  'data.assumption.discarded': 'onAssumptionDiscarded',
  'data.concept.added': 'onConceptAdded',
  'data.concept.distinguished': 'onConceptDistinguished',
  'data.model.integrated': 'onModelIntegrated',
  // Understand mode (new - from Understand agent)
  'data.knowledge_confidence': 'onKnowledgeConfidence',
  'data.session_config': 'onSessionConfig',
  'data.slo.added': 'onSLOAdded',
  'data.facet_updated': 'onFacetUpdated',
  'data.calibration_complete': 'onCalibrationComplete',
  'data.diagnostic_result': 'onDiagnosticResult',
  'data.mastery_achieved': 'onMasteryAchieved',
  'data.slo_skipped': 'onSLOSkipped',
  // Shared
  'narrative.updated': 'onNarrativeUpdated',
  'phase.changed': 'onPhaseChanged',
  'path.updated': 'onPathUpdated',
  'error': 'onError',
}

// ============================================================================
// Stream Connection
// ============================================================================

export interface StreamConnection {
  close: () => void
  isConnected: () => boolean
}

/**
 * Create an SSE connection to the journey stream
 */
export function createJourneyStream(
  sessionId: string,
  handlers: StreamHandlers
): StreamConnection {
  const url = getStreamUrl(sessionId)
  const eventSource = new EventSource(url)

  let connected = false

  // Connection opened
  eventSource.onopen = () => {
    connected = true
    handlers.onOpen?.()
  }

  // Connection error
  eventSource.onerror = (event) => {
    connected = false
    handlers.onConnectionError?.(event)
  }

  // Register handlers for all event types
  for (const [eventType, handlerName] of Object.entries(EVENT_HANDLER_MAP)) {
    if (!handlerName) continue

    eventSource.addEventListener(eventType, (event: MessageEvent) => {
      try {
        // Parse the full event: {type, timestamp, payload}
        const eventData = JSON.parse(event.data)
        // Extract just the payload for handlers
        const handler = handlers[handlerName as keyof StreamHandlers]
        if (handler) {
          // eslint-disable-next-line @typescript-eslint/no-explicit-any
          ;(handler as (p: any) => void)(eventData.payload)
        }
      } catch (error) {
        console.error(`Failed to parse SSE event "${eventType}":`, error)
      }
    })
  }

  return {
    close: () => {
      connected = false
      eventSource.close()
      handlers.onClose?.()
    },
    isConnected: () => connected,
  }
}

// ============================================================================
// Reconnection Logic
// ============================================================================

export interface ReconnectingStreamOptions {
  maxRetries?: number
  retryDelayMs?: number
  onReconnecting?: (attempt: number) => void
  onReconnectFailed?: () => void
}

/**
 * Create an SSE connection with automatic reconnection
 */
export function createReconnectingStream(
  sessionId: string,
  handlers: StreamHandlers,
  options: ReconnectingStreamOptions = {}
): StreamConnection {
  const {
    maxRetries = 3,
    retryDelayMs = 1000,
    onReconnecting,
    onReconnectFailed,
  } = options

  let retryCount = 0
  let connection: StreamConnection | null = null
  let isManualClose = false

  const connect = () => {
    connection = createJourneyStream(sessionId, {
      ...handlers,
      onOpen: () => {
        retryCount = 0 // Reset on successful connection
        handlers.onOpen?.()
      },
      onConnectionError: (event) => {
        if (isManualClose) return

        if (retryCount < maxRetries) {
          retryCount++
          onReconnecting?.(retryCount)
          setTimeout(connect, retryDelayMs * retryCount)
        } else {
          onReconnectFailed?.()
          handlers.onConnectionError?.(event)
        }
      },
    })
  }

  connect()

  return {
    close: () => {
      isManualClose = true
      connection?.close()
    },
    isConnected: () => connection?.isConnected() ?? false,
  }
}

// ============================================================================
// Stream State Helpers
// ============================================================================

export type StreamState = 'disconnected' | 'connecting' | 'connected' | 'error' | 'reconnecting'

export interface StreamStateManager {
  state: StreamState
  connect: () => void
  disconnect: () => void
}

/**
 * Create a managed stream with state tracking
 * Useful for React hooks
 */
export function createManagedStream(
  sessionId: string,
  handlers: StreamHandlers,
  onStateChange: (state: StreamState) => void
): StreamStateManager {
  let connection: StreamConnection | null = null
  let currentState: StreamState = 'disconnected'

  const setState = (newState: StreamState) => {
    currentState = newState
    onStateChange(newState)
  }

  return {
    get state() {
      return currentState
    },

    connect() {
      if (connection?.isConnected()) return

      setState('connecting')

      connection = createReconnectingStream(
        sessionId,
        {
          ...handlers,
          onOpen: () => {
            setState('connected')
            handlers.onOpen?.()
          },
          onClose: () => {
            setState('disconnected')
            handlers.onClose?.()
          },
          onConnectionError: (error) => {
            setState('error')
            handlers.onConnectionError?.(error)
          },
        },
        {
          onReconnecting: () => setState('reconnecting'),
          onReconnectFailed: () => setState('error'),
        }
      )
    },

    disconnect() {
      connection?.close()
      connection = null
      setState('disconnected')
    },
  }
}
