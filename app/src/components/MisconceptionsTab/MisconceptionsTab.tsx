import { useUnderstandData } from '../../store/useStore'
import styles from './MisconceptionsTab.module.css'

export function MisconceptionsTab() {
  const understandData = useUnderstandData()

  if (!understandData || understandData.misconceptions.length === 0) {
    return (
      <div className={styles.empty}>
        No misconceptions identified yet. These are common misunderstandings to watch out for.
      </div>
    )
  }

  return (
    <div className={styles.container}>
      <div className={styles.header}>
        <div className={styles.label}>Understanding</div>
        <h1 className={styles.title}>{understandData.essay.title}</h1>
        <p className={styles.description}>
          Common misconceptions and clarifications—pitfalls to avoid and myths to dispel.
        </p>
      </div>

      <div className={styles.misconceptions}>
        {understandData.misconceptions.map((m) => (
          <div key={m.id} className={styles.misconception}>
            <div className={styles.questionRow}>
              <span className={styles.icon}>✗</span>
              <span className={styles.question}>{m.question}</span>
            </div>
            <div className={styles.answer}>
              <span className={styles.checkIcon}>✓</span>
              <span className={styles.answerText}>{m.answer}</span>
            </div>
          </div>
        ))}
      </div>

      <button className={styles.addBtn}>+ Add misconception</button>
    </div>
  )
}
