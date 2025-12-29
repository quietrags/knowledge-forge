import { useResearchData, useForgeActions } from '../../store/useStore'
import { InlineAdd } from '../InlineAdd/InlineAdd'
import styles from './FrontierTab.module.css'

export function FrontierTab() {
  const researchData = useResearchData()
  const { addAdjacentQuestion, promoteAdjacentQuestion } = useForgeActions()

  if (!researchData || researchData.adjacentQuestions.length === 0) {
    return (
      <div className={styles.empty}>
        No adjacent questions yet. These are the frontier—questions discovered during research that expand your inquiry.
      </div>
    )
  }

  // Get question text by ID for display
  const getQuestionText = (questionId: string) => {
    const question = researchData.questions.find((q) => q.id === questionId)
    return question?.question || questionId
  }

  // Group by discoveredFrom question
  const grouped = researchData.adjacentQuestions.reduce(
    (acc, aq) => {
      const sourceQuestion = getQuestionText(aq.discoveredFrom)
      if (!acc[sourceQuestion]) {
        acc[sourceQuestion] = []
      }
      acc[sourceQuestion].push(aq)
      return acc
    },
    {} as Record<string, typeof researchData.adjacentQuestions>
  )

  return (
    <div className={styles.container}>
      <div className={styles.header}>
        <div className={styles.label}>Research</div>
        <h1 className={styles.title}>{researchData.topic}</h1>
        <p className={styles.description}>
          Adjacent questions are the frontier—discovered during research, they expand your inquiry into new territory.
        </p>
      </div>

      <div className={styles.groups}>
        {Object.entries(grouped).map(([sourceQuestion, questions]) => (
          <div key={sourceQuestion} className={styles.group}>
            <div className={styles.groupHeader}>
              <span className={styles.groupIcon}>🔭</span>
              <span className={styles.groupName}>Discovered from: {sourceQuestion.slice(0, 50)}...</span>
            </div>
            <div className={styles.questions}>
              {questions.map((aq) => (
                <div key={aq.id} className={styles.question}>
                  <span className={styles.questionIcon}>?</span>
                  <span className={styles.questionText}>{aq.question}</span>
                  <button
                    className={styles.promoteBtn}
                    title="Promote to question tree"
                    onClick={() => {
                      // Promote to first category for now
                      const firstCategory = researchData.categories[0]
                      if (firstCategory) {
                        promoteAdjacentQuestion(aq.id, firstCategory.id)
                      }
                    }}
                  >
                    →
                  </button>
                </div>
              ))}
            </div>
          </div>
        ))}
      </div>

      <InlineAdd
        placeholder="Enter adjacent question..."
        buttonText="+ Add question"
        onAdd={(question) => addAdjacentQuestion(question, 'manual')}
      />
    </div>
  )
}
