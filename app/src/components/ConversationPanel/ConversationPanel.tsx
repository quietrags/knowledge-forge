import { useEffect, useRef } from 'react'
import { useStreamingText, useAgentThinking, useJourneyBrief, useConversationMessages, useAwaitingInput, useInputPrompt } from '../../store/useStore'
import styles from './ConversationPanel.module.css'

export function ConversationPanel() {
  const conversationMessages = useConversationMessages()
  const streamingText = useStreamingText()
  const agentThinking = useAgentThinking()
  const journeyBrief = useJourneyBrief()
  const awaitingInput = useAwaitingInput()
  const inputPrompt = useInputPrompt()
  const messagesEndRef = useRef<HTMLDivElement>(null)

  // Auto-scroll to bottom when new messages arrive
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [conversationMessages, streamingText, agentThinking])

  // Show empty state if no content at all
  const hasContent = conversationMessages.length > 0 || streamingText || agentThinking
  if (!hasContent) {
    return (
      <div className={styles.container}>
        <div className={styles.header}>
          <h3 className={styles.title}>Conversation</h3>
        </div>
        <div className={styles.empty}>
          Start a session to begin the learning conversation.
        </div>
      </div>
    )
  }

  return (
    <div className={styles.container}>
      <div className={styles.header}>
        <h3 className={styles.title}>Learning Dialogue</h3>
        {journeyBrief && (
          <span className={styles.topic}>{journeyBrief.originalQuestion}</span>
        )}
      </div>

      <div className={styles.messages}>
        {/* Render conversation history */}
        {conversationMessages.map((msg) => (
          <div
            key={msg.id}
            className={msg.role === 'tutor' ? styles.agentMessage : styles.userMessage}
          >
            <div className={styles.messageHeader}>
              <span className={styles.sender}>{msg.role === 'tutor' ? 'Tutor' : 'You'}</span>
            </div>
            <div className={styles.messageContent}>
              {msg.content}
            </div>
          </div>
        ))}

        {/* Show current streaming text (tutor's in-progress message) */}
        {streamingText && (
          <div className={styles.agentMessage}>
            <div className={styles.messageHeader}>
              <span className={styles.sender}>Tutor</span>
            </div>
            <div className={styles.messageContent}>
              {streamingText}
            </div>
          </div>
        )}

        {/* Show thinking indicator */}
        {agentThinking && (
          <div className={styles.thinkingIndicator}>
            <span className={styles.dot}></span>
            <span className={styles.thinkingText}>{agentThinking}</span>
          </div>
        )}

        {/* Show awaiting input prompt - this is the key UX indicator */}
        {awaitingInput && (
          <div className={styles.awaitingInput}>
            <div className={styles.awaitingIcon}>💬</div>
            <div className={styles.awaitingContent}>
              <span className={styles.awaitingLabel}>Your turn</span>
              {inputPrompt && (
                <span className={styles.awaitingPrompt}>{inputPrompt}</span>
              )}
            </div>
          </div>
        )}

        {/* Scroll anchor */}
        <div ref={messagesEndRef} />
      </div>

      <div className={styles.hint}>
        {awaitingInput ? '↓ Type your response below ↓' : 'Type your response in the input below'}
      </div>
    </div>
  )
}
