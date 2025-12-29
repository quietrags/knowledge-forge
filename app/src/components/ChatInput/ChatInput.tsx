import { useState, useCallback } from 'react'
import { useMode } from '../../store/useStore'
import styles from './ChatInput.module.css'

const MODE_PLACEHOLDERS = {
  build: 'Ask a question or request to build something...',
  understand: 'Ask to clarify or explore a concept...',
  research: 'Add a question or query findings...',
}

export function ChatInput() {
  const mode = useMode()
  const [value, setValue] = useState('')

  const handleSubmit = useCallback(
    (e: React.FormEvent) => {
      e.preventDefault()
      if (!value.trim()) return

      // TODO: Implement actual submission logic
      console.log('Submit:', value)
      setValue('')
    },
    [value]
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

  return (
    <div className={styles.container}>
      <form className={styles.inner} onSubmit={handleSubmit}>
        <input
          type="text"
          className={styles.input}
          placeholder={MODE_PLACEHOLDERS[mode]}
          value={value}
          onChange={(e) => setValue(e.target.value)}
          onKeyDown={handleKeyDown}
        />
        <span className={styles.hint}>↵</span>
      </form>
    </div>
  )
}
