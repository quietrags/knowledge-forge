import { useState, useCallback } from 'react'
import { useMode, useSessionId, useForgeActions } from '../../store/useStore'
import { useChat } from '../../api/hooks'
import styles from './ChatInput.module.css'

const MODE_PLACEHOLDERS = {
  build: 'Ask a question or request to build something...',
  understand: 'Ask to clarify or explore a concept...',
  research: 'Add a question or query findings...',
}

export function ChatInput() {
  const mode = useMode()
  const sessionId = useSessionId()
  const { setAgentThinking, setError, addConversationMessage, finalizeAgentMessage, setAwaitingInput } = useForgeActions()
  const { send, isSending, error: chatError } = useChat(sessionId)
  const [value, setValue] = useState('')

  const handleSubmit = useCallback(
    async (e: React.FormEvent) => {
      e.preventDefault()
      if (!value.trim() || isSending) return

      const message = value.trim()
      setValue('')

      // Finalize any current agent message before adding user message
      finalizeAgentMessage()

      // Add user message to conversation history
      addConversationMessage('user', message)

      // Clear awaiting input state - we're responding
      setAwaitingInput(false, null)

      // Set thinking state immediately for UI feedback
      setAgentThinking('Sending message...')

      const success = await send(message)
      if (!success) {
        setError(chatError?.message || 'Failed to send message')
        setAgentThinking(null)
      }
      // On success, SSE stream will handle updating agentThinking
    },
    [value, isSending, send, setAgentThinking, setError, chatError, addConversationMessage, finalizeAgentMessage, setAwaitingInput]
  )

  const handleKeyDown = useCallback(
    (e: React.KeyboardEvent) => {
      if (e.key === 'Enter' && !e.shiftKey) {
        e.preventDefault()
        handleSubmit(e)
      }
    },
    [handleSubmit]
  )

  // Don't render if no session yet
  if (!sessionId) {
    return (
      <div className={styles.container}>
        <div className={styles.inner}>
          <input
            type="text"
            className={styles.input}
            placeholder="Start a journey to begin chatting..."
            disabled
          />
        </div>
      </div>
    )
  }

  return (
    <div className={styles.container}>
      <form className={styles.inner} onSubmit={handleSubmit}>
        <input
          type="text"
          className={styles.input}
          placeholder={isSending ? 'Sending...' : MODE_PLACEHOLDERS[mode]}
          value={value}
          onChange={(e) => setValue(e.target.value)}
          onKeyDown={handleKeyDown}
          disabled={isSending}
        />
        <span className={styles.hint}>{isSending ? '...' : '↵'}</span>
      </form>
    </div>
  )
}
