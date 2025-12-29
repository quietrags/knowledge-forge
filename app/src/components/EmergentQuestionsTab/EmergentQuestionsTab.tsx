import { useResearchData, useForgeActions } from '../../store/useStore'
import { InlineAdd } from '../InlineAdd/InlineAdd'
import styles from './EmergentQuestionsTab.module.css'

export function EmergentQuestionsTab() {
  const researchData = useResearchData()
  const { addEmergentQuestion, promoteEmergentQuestion } = useForgeActions()

  if (!researchData || researchData.emergentQuestions.length === 0) {
    return (
      <div className={styles.empty}>
        No emergent questions yet. These arise during research and represent new areas to explore.
      </div>
    )
  }

  // Group by source category
  const grouped = researchData.emergentQuestions.reduce(
    (acc, eq) => {
      if (!acc[eq.sourceCategory]) {
        acc[eq.sourceCategory] = []
      }
      acc[eq.sourceCategory].push(eq)
      return acc
    },
    {} as Record<string, typeof researchData.emergentQuestions>
  )

  return (
    <div className={styles.container}>
      <div className={styles.header}>
        <div className={styles.label}>Research</div>
        <h1 className={styles.title}>{researchData.topic}</h1>
        <p className={styles.description}>
          Emergent questions arose during research. They represent the frontier of your inquiry—candidates for deeper investigation.
        </p>
      </div>

      <div className={styles.groups}>
        {Object.entries(grouped).map(([category, questions]) => (
          <div key={category} className={styles.group}>
            <div className={styles.groupHeader}>
              <span className={styles.groupIcon}>🌱</span>
              <span className={styles.groupName}>From: {category}</span>
            </div>
            <div className={styles.questions}>
              {questions.map((eq) => (
                <div key={eq.id} className={styles.question}>
                  <span className={styles.questionIcon}>?</span>
                  <span className={styles.questionText}>{eq.question}</span>
                  <button
                    className={styles.promoteBtn}
                    title="Promote to question tree"
                    onClick={() => {
                      // Promote to first category for now
                      const firstCategory = researchData.categories[0]
                      if (firstCategory) {
                        promoteEmergentQuestion(eq.id, firstCategory.id)
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
        placeholder="Enter emergent question..."
        buttonText="+ Add emergent question"
        onAdd={(question) => addEmergentQuestion(question, 'Manual Entry')}
      />
    </div>
  )
}
