import { useResearchData, useForgeActions } from '../../store/useStore'
import { InlineAdd } from '../InlineAdd/InlineAdd'
import styles from './KeyInsightsTab.module.css'

export function KeyInsightsTab() {
  const researchData = useResearchData()
  const { addKeyInsight } = useForgeActions()

  if (!researchData || researchData.keyInsights.length === 0) {
    return (
      <div className={styles.empty}>
        No key insights captured yet. Key insights are concepts that help answer multiple questions—the "rise above" synthesis.
      </div>
    )
  }

  return (
    <div className={styles.container}>
      <div className={styles.header}>
        <div className={styles.label}>Research</div>
        <h1 className={styles.title}>{researchData.topic}</h1>
        <p className={styles.description}>
          Key insights transcend individual questions—they're the synthesis that helps answer multiple parts of your research.
        </p>
      </div>

      <div className={styles.insights}>
        {researchData.keyInsights.map((insight) => (
          <div key={insight.id} className={styles.insight}>
            <div className={styles.insightIcon}>💡</div>
            <div className={styles.insightContent}>
              <h3 className={styles.insightTitle}>{insight.title}</h3>
              <p className={styles.insightDescription}>{insight.description}</p>
              <div className={styles.relevance}>
                <span className={styles.relevanceLabel}>Relevance:</span>
                <span className={styles.relevanceText}>{insight.relevance}</span>
              </div>
            </div>
          </div>
        ))}
      </div>

      <InlineAdd
        placeholder="Key insight title..."
        buttonText="+ Add insight"
        secondPlaceholder="Description..."
        onAdd={() => {}}
        onAddTwo={(title, description) => addKeyInsight(title, description)}
      />
    </div>
  )
}
