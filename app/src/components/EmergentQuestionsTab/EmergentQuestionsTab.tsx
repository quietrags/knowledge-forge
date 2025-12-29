import { useResearchData } from '../../store/useStore'
import styles from './EmergentQuestionsTab.module.css'

export function EmergentQuestionsTab() {
  const researchData = useResearchData()

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
                  <button className={styles.promoteBtn} title="Promote to question tree">
                    →
                  </button>
                </div>
              ))}
            </div>
          </div>
        ))}
      </div>

      <button className={styles.addBtn}>+ Add emergent question</button>
    </div>
  )
}
