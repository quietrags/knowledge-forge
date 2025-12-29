/**
 * React Hooks — API integration hooks for components
 */

import { useState, useCallback, useEffect, useRef } from 'react'
import {
  analyzeJourney,
  confirmJourney,
  sendChatMessage,
  loadSession,
  saveSession,
} from './client'
import {
  createManagedStream,
  type StreamHandlers,
  type StreamState,
} from './streaming'
import type {
  JourneyAnalyzeRequest,
  JourneyDesignBrief,
  JourneyConfirmRequest,
  SessionInitResponse,
  ChatRequest,
  APIException,
} from './types'

// ============================================================================
// Generic Async State Hook
// ============================================================================

interface AsyncState<T> {
  data: T | null
  isLoading: boolean
  error: APIException | null
}

interface AsyncActions<TArgs extends unknown[], TResult> {
  execute: (...args: TArgs) => Promise<TResult | null>
  reset: () => void
}

function useAsyncAction<TArgs extends unknown[], TResult>(
  action: (...args: TArgs) => Promise<TResult>
): [AsyncState<TResult>, AsyncActions<TArgs, TResult>] {
  const [state, setState] = useState<AsyncState<TResult>>({
    data: null,
    isLoading: false,
    error: null,
  })

  const execute = useCallback(
    async (...args: TArgs): Promise<TResult | null> => {
      setState({ data: null, isLoading: true, error: null })
      try {
        const result = await action(...args)
        setState({ data: result, isLoading: false, error: null })
        return result
      } catch (error) {
        const apiError = error instanceof Error
          ? (error as APIException)
          : new Error('Unknown error') as unknown as APIException
        setState({ data: null, isLoading: false, error: apiError })
        return null
      }
    },
    [action]
  )

  const reset = useCallback(() => {
    setState({ data: null, isLoading: false, error: null })
  }, [])

  return [state, { execute, reset }]
}

// ============================================================================
// Journey Intake Hooks
// ============================================================================

/**
 * Hook for analyzing user questions during journey intake
 */
export function useJourneyAnalysis() {
  const [state, actions] = useAsyncAction(
    (data: JourneyAnalyzeRequest) => analyzeJourney(data)
  )

  const analyze = useCallback(
    (question: string, learnerContext?: string) =>
      actions.execute({ question, learnerContext }),
    [actions]
  )

  return {
    ...state,
    brief: state.data,
    analyze,
    reset: actions.reset,
  }
}

/**
 * Hook for confirming journey design
 */
export function useJourneyConfirm() {
  const [state, actions] = useAsyncAction(
    (data: JourneyConfirmRequest) => confirmJourney(data)
  )

  const confirm = useCallback(
    (brief: JourneyDesignBrief, confirmed: boolean = true, alternativeMode?: string) =>
      actions.execute({
        brief,
        confirmed,
        alternativeMode: alternativeMode as JourneyConfirmRequest['alternativeMode'],
      }),
    [actions]
  )

  return {
    ...state,
    session: state.data,
    confirm,
    reset: actions.reset,
  }
}

// ============================================================================
// Chat Hook
// ============================================================================

/**
 * Hook for sending chat messages
 * Note: Responses come through the SSE stream, not the API response
 */
export function useChat(sessionId: string | null) {
  const [isSending, setIsSending] = useState(false)
  const [error, setError] = useState<APIException | null>(null)

  const send = useCallback(
    async (message: string, context?: ChatRequest['context']) => {
      if (!sessionId) {
        setError(new Error('No session ID') as unknown as APIException)
        return false
      }

      setIsSending(true)
      setError(null)

      try {
        await sendChatMessage({ sessionId, message, context })
        setIsSending(false)
        return true
      } catch (err) {
        setError(err as APIException)
        setIsSending(false)
        return false
      }
    },
    [sessionId]
  )

  const reset = useCallback(() => {
    setIsSending(false)
    setError(null)
  }, [])

  return {
    send,
    isSending,
    error,
    reset,
  }
}

// ============================================================================
// Session Hooks
// ============================================================================

/**
 * Hook for loading an existing session
 */
export function useSessionLoad() {
  const [state, actions] = useAsyncAction(
    (sessionId: string) => loadSession(sessionId)
  )

  return {
    ...state,
    session: state.data,
    load: actions.execute,
    reset: actions.reset,
  }
}

/**
 * Hook for saving the current session
 */
export function useSessionSave(sessionId: string | null) {
  const [isSaving, setIsSaving] = useState(false)
  const [error, setError] = useState<APIException | null>(null)
  const [lastSaved, setLastSaved] = useState<string | null>(null)

  const save = useCallback(
    async (checkpoint?: string) => {
      if (!sessionId) {
        setError(new Error('No session ID') as unknown as APIException)
        return false
      }

      setIsSaving(true)
      setError(null)

      try {
        const result = await saveSession(sessionId, { checkpoint })
        setLastSaved(result.path)
        setIsSaving(false)
        return true
      } catch (err) {
        setError(err as APIException)
        setIsSaving(false)
        return false
      }
    },
    [sessionId]
  )

  return {
    save,
    isSaving,
    error,
    lastSaved,
  }
}

// ============================================================================
// SSE Stream Hook
// ============================================================================

export interface UseStreamOptions {
  autoConnect?: boolean
  handlers: StreamHandlers
}

/**
 * Hook for managing SSE stream connection
 */
export function useStream(sessionId: string | null, options: UseStreamOptions) {
  const { autoConnect = false, handlers } = options
  const [streamState, setStreamState] = useState<StreamState>('disconnected')

  // Keep handlers ref stable
  const handlersRef = useRef(handlers)
  handlersRef.current = handlers

  // Stream manager ref
  const managerRef = useRef<ReturnType<typeof createManagedStream> | null>(null)

  // Connect to stream
  const connect = useCallback(() => {
    if (!sessionId) return

    if (managerRef.current) {
      managerRef.current.disconnect()
    }

    managerRef.current = createManagedStream(
      sessionId,
      handlersRef.current,
      setStreamState
    )
    managerRef.current.connect()
  }, [sessionId])

  // Disconnect from stream
  const disconnect = useCallback(() => {
    managerRef.current?.disconnect()
    managerRef.current = null
  }, [])

  // Auto-connect when sessionId changes
  useEffect(() => {
    if (autoConnect && sessionId) {
      connect()
    }

    return () => {
      disconnect()
    }
  }, [sessionId, autoConnect, connect, disconnect])

  return {
    streamState,
    isConnected: streamState === 'connected',
    isConnecting: streamState === 'connecting',
    isReconnecting: streamState === 'reconnecting',
    hasError: streamState === 'error',
    connect,
    disconnect,
  }
}

// ============================================================================
// Combined Journey Hook
// ============================================================================

export interface UseJourneyOptions {
  onSessionStart?: (session: SessionInitResponse) => void
  streamHandlers: StreamHandlers
}

/**
 * Combined hook for the full journey flow: analyze -> confirm -> stream
 */
export function useJourney(options: UseJourneyOptions) {
  const { onSessionStart, streamHandlers } = options

  const analysis = useJourneyAnalysis()
  const confirmation = useJourneyConfirm()
  const [sessionId, setSessionId] = useState<string | null>(null)
  const stream = useStream(sessionId, { handlers: streamHandlers })

  // Handle session initialization
  useEffect(() => {
    if (confirmation.session) {
      setSessionId(confirmation.session.sessionId)
      onSessionStart?.(confirmation.session)
      // Connect to stream after session is confirmed
      stream.connect()
    }
  }, [confirmation.session])

  // Analyze question
  const analyze = useCallback(
    (question: string, learnerContext?: string) =>
      analysis.analyze(question, learnerContext),
    [analysis]
  )

  // Confirm with suggested mode
  const confirmSuggested = useCallback(
    () => {
      if (analysis.brief) {
        return confirmation.confirm(analysis.brief, true)
      }
      return Promise.resolve(null)
    },
    [analysis.brief, confirmation]
  )

  // Confirm with alternative mode
  const confirmAlternative = useCallback(
    (alternativeMode: string) => {
      if (analysis.brief) {
        return confirmation.confirm(analysis.brief, true, alternativeMode)
      }
      return Promise.resolve(null)
    },
    [analysis.brief, confirmation]
  )

  // Reset entire journey
  const reset = useCallback(() => {
    analysis.reset()
    confirmation.reset()
    stream.disconnect()
    setSessionId(null)
  }, [analysis, confirmation, stream])

  return {
    // Analysis state
    brief: analysis.brief,
    isAnalyzing: analysis.isLoading,
    analysisError: analysis.error,

    // Confirmation state
    session: confirmation.session,
    isConfirming: confirmation.isLoading,
    confirmError: confirmation.error,

    // Session state
    sessionId,

    // Stream state
    streamState: stream.streamState,
    isConnected: stream.isConnected,

    // Actions
    analyze,
    confirmSuggested,
    confirmAlternative,
    reset,
  }
}
