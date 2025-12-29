import { useUnderstandData } from '../../store/useStore'
import styles from './InsightsTab.module.css'

export function InsightsTab() {
  const understandData = useUnderstandData()

  if (!understandData || understandData.insights.length === 0) {
    return (
      <div className={styles.empty}>
        No insights captured yet. Insights are key realizations that deepen understanding.
      </div>
    )
  }

  return (
    <div className={styles.container}>
      <div className={styles.header}>
        <div className={styles.label}>Understanding</div>
        <h1 className={styles.title}>{understandData.essay.title}</h1>
        <p className={styles.description}>
          Key insights and realizations—the "aha moments" that shift your mental model.
        </p>
      </div>

      <div className={styles.insights}>
        {understandData.insights.map((insight) => (
          <div key={insight.id} className={styles.insight}>
            <div className={styles.insightIcon}>💡</div>
            <div className={styles.insightContent}>
              <blockquote className={styles.quote}>{insight.insight}</blockquote>
              <div className={styles.context}>{insight.context}</div>
            </div>
          </div>
        ))}
      </div>

      <button className={styles.addBtn}>+ Add insight</button>
    </div>
  )
}
