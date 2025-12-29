import { useUnderstandData, useForgeActions } from '../../store/useStore'
import { InlineAdd } from '../InlineAdd/InlineAdd'
import styles from './DistinctionsTab.module.css'

export function DistinctionsTab() {
  const understandData = useUnderstandData()
  const { addDistinction } = useForgeActions()

  if (!understandData || understandData.distinctions.length === 0) {
    return (
      <div className={styles.empty}>
        No distinctions identified yet. Distinctions clarify the differences between similar concepts.
      </div>
    )
  }

  return (
    <div className={styles.container}>
      <div className={styles.header}>
        <div className={styles.label}>Understanding</div>
        <h1 className={styles.title}>{understandData.essay.title}</h1>
        <p className={styles.description}>
          Distinctions separate what seems similar—the key differences that matter.
        </p>
      </div>

      <div className={styles.distinctions}>
        {understandData.distinctions.map((dist) => (
          <div key={dist.id} className={styles.distinction}>
            <div className={styles.versus}>
              <span className={styles.itemA}>{dist.itemA}</span>
              <span className={styles.vs}>vs</span>
              <span className={styles.itemB}>{dist.itemB}</span>
            </div>
            <div className={styles.difference}>
              <span className={styles.diffIcon}>↔</span>
              <span className={styles.diffText}>{dist.difference}</span>
            </div>
          </div>
        ))}
      </div>

      <InlineAdd
        placeholder="First thing (e.g., 'ReACT failure')..."
        buttonText="+ Add distinction"
        secondPlaceholder="Second thing (e.g., 'Architecture mismatch')..."
        onAdd={() => {}}
        onAddTwo={(itemA, itemB) => addDistinction(itemA, itemB)}
      />
    </div>
  )
}
