import { useUnderstandData, useForgeActions, useJourneyBrief } from '../../store/useStore'
import { InlineAdd } from '../InlineAdd/InlineAdd'
import styles from './AssumptionsTab.module.css'

export function AssumptionsTab() {
  const understandData = useUnderstandData()
  const { addAssumption } = useForgeActions()
  const journeyBrief = useJourneyBrief()

  if (!understandData || understandData.assumptions.length === 0) {
    return (
      <div className={styles.empty}>
        No assumptions surfaced yet. Assumptions are beliefs you held that deeper understanding has revised.
      </div>
    )
  }

  return (
    <div className={styles.container}>
      <div className={styles.header}>
        <div className={styles.label}>Understanding</div>
        <h1 className={styles.title}>{journeyBrief?.originalQuestion || 'Learning Journey'}</h1>
        <p className={styles.description}>
          Assumptions surfaced—beliefs you held before that deeper understanding has revised or nuanced.
        </p>
      </div>

      <div className={styles.assumptions}>
        {understandData.assumptions.map((assum) => (
          <div key={assum.id} className={styles.assumption}>
            <div className={styles.assumedRow}>
              <span className={styles.beforeIcon}>◯</span>
              <div className={styles.assumed}>
                <span className={styles.assumedLabel}>I assumed:</span>
                <span className={styles.assumedText}>{assum.assumption}</span>
              </div>
            </div>
            <div className={styles.surfacedRow}>
              <span className={styles.afterIcon}>●</span>
              <div className={styles.surfaced}>
                <span className={styles.surfacedLabel}>Now I understand:</span>
                <span className={styles.surfacedText}>{assum.surfaced}</span>
              </div>
            </div>
          </div>
        ))}
      </div>

      <InlineAdd
        placeholder="What I assumed..."
        buttonText="+ Add assumption"
        secondPlaceholder="What I now understand..."
        onAdd={() => {}}
        onAddTwo={(assumption, surfaced) => addAssumption(assumption, surfaced)}
      />
    </div>
  )
}
