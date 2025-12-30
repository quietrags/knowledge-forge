import { useState } from 'react'
import { useForgeActions } from '../../store/useStore'
import { useJourneyAnalysis } from '../../api/hooks'
import styles from './JourneyIntake.module.css'

export const JourneyIntake = () => {
  const [question, setQuestion] = useState('')
  const { setJourneyBrief, setIsLoading, setError } = useForgeActions()
  const { analyze, isLoading, error } = useJourneyAnalysis()

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!question.trim() || isLoading) return

    setIsLoading(true)
    setError(null)

    try {
      const brief = await analyze(question.trim())
      if (brief) {
        setJourneyBrief(brief)
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to analyze question')
    } finally {
      setIsLoading(false)
    }
  }

  return (
    <div className={styles.container}>
      <div className={styles.content}>
        <h1 className={styles.title}>What do you want to explore?</h1>

        <form onSubmit={handleSubmit} className={styles.form}>
          <textarea
            className={styles.input}
            value={question}
            onChange={(e) => setQuestion(e.target.value)}
            placeholder="Ask a question, describe what you want to learn, or explain what you want to build..."
            rows={3}
            autoFocus
          />
          <button
            type="submit"
            className={styles.button}
            disabled={!question.trim() || isLoading}
          >
            {isLoading ? 'Analyzing...' : 'Begin Journey →'}
          </button>
          {error && <p className={styles.error}>{error.message || 'Analysis failed'}</p>}
        </form>

        <div className={styles.examples}>
          <p className={styles.examplesLabel}>Examples:</p>
          <ul className={styles.examplesList}>
            <li onClick={() => setQuestion('How do I write better prompts?')}>
              "How do I write better prompts?" → Build
            </li>
            <li onClick={() => setQuestion('Why do LLMs hallucinate?')}>
              "Why do LLMs hallucinate?" → Understand
            </li>
            <li onClick={() => setQuestion('What approaches exist for prompt caching?')}>
              "What approaches exist for prompt caching?" → Research
            </li>
          </ul>
        </div>
      </div>
    </div>
  )
}
