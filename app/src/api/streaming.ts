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

  // Build mode events
  onConstructAdded?: (payload: ConstructAddedPayload) => void
  onDecisionAdded?: (payload: DecisionAddedPayload) => void
  onCapabilityAdded?: (payload: CapabilityAddedPayload) => void
  onGroundingConceptAdded?: (payload: GroundingConceptAddedPayload) => void

  // Understand mode events
  onAssumptionSurfaced?: (payload: AssumptionSurfacedPayload) => void
  onAssumptionDiscarded?: (payload: AssumptionDiscardedPayload) => void
  onConceptAdded?: (payload: ConceptAddedPayload) => void
  onConceptDistinguished?: (payload: ConceptDistinguishedPayload) => void
  onModelIntegrated?: (payload: ModelIntegratedPayload) => void

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
  'session.started': 'onSessionStarted',
  'session.resumed': 'onSessionResumed',
  'session.ended': 'onSessionEnded',
  'agent.thinking': 'onAgentThinking',
  'agent.speaking': 'onAgentSpeaking',
  'agent.complete': 'onAgentComplete',
  'data.question.added': 'onQuestionAdded',
  'data.question.updated': 'onQuestionUpdated',
  'data.question.answered': 'onQuestionAnswered',
  'data.category.added': 'onCategoryAdded',
  'data.category.insight': 'onCategoryInsight',
  'data.key_insight.added': 'onKeyInsightAdded',
  'data.adjacent_question.added': 'onAdjacentQuestionAdded',
  'data.construct.added': 'onConstructAdded',
  'data.decision.added': 'onDecisionAdded',
  'data.capability.added': 'onCapabilityAdded',
  'data.grounding_concept.added': 'onGroundingConceptAdded',
  'data.assumption.surfaced': 'onAssumptionSurfaced',
  'data.assumption.discarded': 'onAssumptionDiscarded',
  'data.concept.added': 'onConceptAdded',
  'data.concept.distinguished': 'onConceptDistinguished',
  'data.model.integrated': 'onModelIntegrated',
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
