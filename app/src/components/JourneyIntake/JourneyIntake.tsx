import { useState } from 'react'
import { useForgeActions } from '../../store/useStore'
import styles from './JourneyIntake.module.css'

export const JourneyIntake = () => {
  const [question, setQuestion] = useState('')
  const { setJourneyBrief } = useForgeActions()

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault()
    if (!question.trim()) return

    // For now, use simple heuristics to route the question
    // In production, this would call an LLM to analyze the question
    const brief = analyzeQuestion(question.trim())
    setJourneyBrief(brief)
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
            disabled={!question.trim()}
          >
            Begin Journey →
          </button>
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

// Simple heuristic-based question routing
// In production, this would be replaced with LLM analysis
function analyzeQuestion(question: string) {
  const lowerQ = question.toLowerCase()

  // Build signals
  if (
    lowerQ.startsWith('how do i') ||
    lowerQ.startsWith('help me') ||
    lowerQ.startsWith('i want to') ||
    lowerQ.includes('create') ||
    lowerQ.includes('build') ||
    lowerQ.includes('implement') ||
    lowerQ.includes('make a')
  ) {
    return {
      originalQuestion: question,
      idealAnswer: 'Techniques and constructs you can apply immediately',
      answerType: 'skill' as const,
      primaryMode: 'build' as const,
      confirmationMessage: `It sounds like you want to BUILD—learn techniques you can apply immediately.`,
    }
  }

  // Understand signals
  if (
    lowerQ.startsWith('why') ||
    lowerQ.startsWith('what is the difference') ||
    lowerQ.includes('understand') ||
    lowerQ.includes('explain') ||
    lowerQ.includes('how does') ||
    lowerQ.includes('concept')
  ) {
    return {
      originalQuestion: question,
      idealAnswer: 'A mental model that clarifies how things work',
      answerType: 'understanding' as const,
      primaryMode: 'understand' as const,
      confirmationMessage: `It sounds like you want to UNDERSTAND—develop a mental model of how this works.`,
    }
  }

  // Default to Research
  return {
    originalQuestion: question,
    idealAnswer: 'Answers to your questions with sources and key insights',
    answerType: 'facts' as const,
    primaryMode: 'research' as const,
    confirmationMessage: `This looks like a RESEARCH question—you want to survey what exists and understand the landscape.`,
  }
}
