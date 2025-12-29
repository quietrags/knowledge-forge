import { useUnderstandData } from '../../store/useStore'
import styles from './MentalModelTab.module.css'

export function MentalModelTab() {
  const understandData = useUnderstandData()

  if (!understandData || !understandData.mentalModel) {
    return (
      <div className={styles.empty}>
        No mental model defined yet. This is a high-level framework for thinking about the topic.
      </div>
    )
  }

  return (
    <div className={styles.container}>
      <div className={styles.header}>
        <div className={styles.label}>Understanding</div>
        <h1 className={styles.title}>{understandData.essay.title}</h1>
        <p className={styles.description}>
          Your mental model—a decision framework for applying what you've learned.
        </p>
      </div>

      <div className={styles.modelCard}>
        <div className={styles.modelIcon}>🧠</div>
        <div
          className={styles.modelContent}
          dangerouslySetInnerHTML={{ __html: understandData.mentalModel }}
        />
      </div>

      <div className={styles.actions}>
        <button className={styles.editBtn}>Edit mental model</button>
      </div>
    </div>
  )
}
