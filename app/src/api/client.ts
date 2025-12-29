/**
 * API Client — Fetch wrapper with error handling
 */

import {
  APIException,
  type JourneyAnalyzeRequest,
  type JourneyDesignBrief,
  type JourneyConfirmRequest,
  type SessionInitResponse,
  type ChatRequest,
  type SessionLoadResponse,
  type SessionSaveRequest,
  type SessionSaveResponse,
} from './types'

// ============================================================================
// Configuration
// ============================================================================

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000/api'

interface RequestOptions extends Omit<RequestInit, 'body'> {
  body?: unknown
}

// ============================================================================
// Core Fetch Wrapper
// ============================================================================

async function request<T>(endpoint: string, options: RequestOptions = {}): Promise<T> {
  const { body, headers: customHeaders, ...rest } = options

  const url = `${API_BASE_URL}${endpoint}`
  const headers: HeadersInit = {
    'Content-Type': 'application/json',
    ...customHeaders,
  }

  const config: RequestInit = {
    ...rest,
    headers,
  }

  if (body !== undefined) {
    config.body = JSON.stringify(body)
  }

  try {
    const response = await fetch(url, config)

    if (!response.ok) {
      let errorData: unknown
      try {
        errorData = await response.json()
      } catch {
        errorData = { message: response.statusText }
      }
      throw APIException.fromResponse(response.status, errorData)
    }

    // Handle 204 No Content
    if (response.status === 204) {
      return undefined as T
    }

    return await response.json()
  } catch (error) {
    if (error instanceof APIException) {
      throw error
    }
    // Network error or other fetch failure
    throw new APIException(0, 'NETWORK_ERROR', 'Unable to connect to the server')
  }
}

// ============================================================================
// Journey Intake API
// ============================================================================

/**
 * Analyze a user's question to determine the ideal journey
 */
export async function analyzeJourney(
  data: JourneyAnalyzeRequest
): Promise<JourneyDesignBrief> {
  return request<JourneyDesignBrief>('/journey/analyze', {
    method: 'POST',
    body: data,
  })
}

/**
 * Confirm journey design and initialize session
 */
export async function confirmJourney(
  data: JourneyConfirmRequest
): Promise<SessionInitResponse> {
  return request<SessionInitResponse>('/journey/confirm', {
    method: 'POST',
    body: data,
  })
}

/**
 * Get the SSE stream URL for a session
 */
export function getStreamUrl(sessionId: string): string {
  return `${API_BASE_URL}/journey/stream?sessionId=${encodeURIComponent(sessionId)}`
}

// ============================================================================
// Chat API
// ============================================================================

/**
 * Send a chat message (response streamed via SSE)
 * Returns 202 Accepted - actual response comes through stream
 */
export async function sendChatMessage(data: ChatRequest): Promise<void> {
  return request<void>('/chat', {
    method: 'POST',
    body: data,
  })
}

// ============================================================================
// Session API
// ============================================================================

/**
 * Load an existing session
 */
export async function loadSession(sessionId: string): Promise<SessionLoadResponse> {
  return request<SessionLoadResponse>(`/session/${encodeURIComponent(sessionId)}`)
}

/**
 * Save current session
 */
export async function saveSession(
  sessionId: string,
  data: SessionSaveRequest = {}
): Promise<SessionSaveResponse> {
  return request<SessionSaveResponse>(`/session/${encodeURIComponent(sessionId)}/save`, {
    method: 'POST',
    body: data,
  })
}

/**
 * List available sessions
 */
export async function listSessions(): Promise<Array<{ id: string; created: string; updated: string }>> {
  return request<Array<{ id: string; created: string; updated: string }>>('/sessions')
}

// ============================================================================
// Exported Client Object (for convenience)
// ============================================================================

export const apiClient = {
  // Journey
  analyzeJourney,
  confirmJourney,
  getStreamUrl,
  // Chat
  sendChatMessage,
  // Session
  loadSession,
  saveSession,
  listSessions,
}

export default apiClient
