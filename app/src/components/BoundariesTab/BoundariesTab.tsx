import { useBuildData, useForgeActions } from '../../store/useStore'
import { InlineAdd } from '../InlineAdd/InlineAdd'
import styles from './BoundariesTab.module.css'

export function BoundariesTab() {
  const buildData = useBuildData()
  const { addBoundary } = useForgeActions()

  if (!buildData || buildData.boundaries.length === 0) {
    return (
      <div className={styles.empty}>
        No boundaries defined yet. Boundaries clarify the edges of your learning topic.
      </div>
    )
  }

  return (
    <div className={styles.container}>
      <div className={styles.header}>
        <div className={styles.label}>Building</div>
        <h1 className={styles.title}>{buildData.narrative.title}</h1>
        <p className={styles.description}>
          Boundaries answer questions about what's in scope vs. out of scope—the edges where your topic meets neighboring concepts.
        </p>
      </div>

      <div className={styles.boundaries}>
        {buildData.boundaries.map((boundary) => (
          <div key={boundary.id} className={styles.boundary}>
            <div className={styles.question}>
              <span className={styles.icon}>↔</span>
              <span className={styles.questionText}>{boundary.question}</span>
            </div>
            <div className={styles.answer}>{boundary.answer}</div>
          </div>
        ))}
      </div>

      <InlineAdd
        placeholder="Boundary question..."
        buttonText="+ Add boundary question"
        secondPlaceholder="Answer..."
        onAdd={() => {}}
        onAddTwo={(question, answer) => addBoundary(question, answer)}
      />
    </div>
  )
}
