import { useBuildData } from '../../store/useStore'
import styles from './AnswerableQuestionsTab.module.css'

export function AnswerableQuestionsTab() {
  const buildData = useBuildData()

  if (!buildData || buildData.questions.length === 0) {
    return (
      <div className={styles.empty}>
        No answerable questions yet. These are questions you can now answer after learning this topic.
      </div>
    )
  }

  return (
    <div className={styles.container}>
      <div className={styles.header}>
        <div className={styles.label}>Building</div>
        <h1 className={styles.title}>{buildData.narrative.title}</h1>
        <p className={styles.description}>
          Questions you can now answer—a self-check of your understanding and a reference for future you.
        </p>
      </div>

      <div className={styles.questions}>
        {buildData.questions.map((q, index) => (
          <div key={q.id} className={styles.question}>
            <div className={styles.number}>{index + 1}</div>
            <div className={styles.text}>{q.question}</div>
            <button className={styles.testBtn} title="Test yourself">
              ✓
            </button>
          </div>
        ))}
      </div>

      <button className={styles.addBtn}>+ Add question</button>
    </div>
  )
}
