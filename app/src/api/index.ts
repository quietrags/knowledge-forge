/**
 * API Module — Re-exports for convenient imports
 */

// Client
export { apiClient, analyzeJourney, confirmJourney, sendChatMessage, loadSession, saveSession, listSessions, getStreamUrl } from './client'

// Streaming
export { createJourneyStream, createReconnectingStream, createManagedStream } from './streaming'
export type { StreamHandlers, StreamConnection, StreamState, StreamStateManager, ReconnectingStreamOptions } from './streaming'

// Hooks
export { useJourneyAnalysis, useJourneyConfirm, useChat, useSessionLoad, useSessionSave, useStream, useJourney } from './hooks'
export type { UseStreamOptions, UseJourneyOptions } from './hooks'

// Types
export * from './types'
