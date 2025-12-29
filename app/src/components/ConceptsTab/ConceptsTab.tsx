import { useUnderstandData, useForgeActions } from '../../store/useStore'
import { InlineAdd } from '../InlineAdd/InlineAdd'
import styles from './ConceptsTab.module.css'

export function ConceptsTab() {
  const understandData = useUnderstandData()
  const { addConcept } = useForgeActions()

  if (!understandData || understandData.concepts.length === 0) {
    return (
      <div className={styles.empty}>
        No concepts identified yet. Concepts emerge from examining assumptions—they're the building blocks of understanding.
      </div>
    )
  }

  // Get assumption text by ID for display
  const getAssumptionText = (assumptionId?: string) => {
    if (!assumptionId) return null
    const assumption = understandData.assumptions.find((a) => a.id === assumptionId)
    return assumption?.assumption
  }

  return (
    <div className={styles.container}>
      <div className={styles.header}>
        <div className={styles.label}>Understanding</div>
        <h1 className={styles.title}>{understandData.essay.title}</h1>
        <p className={styles.description}>
          Concepts are precise distinctions that emerge from examining assumptions. Threshold concepts transform how you see the domain.
        </p>
      </div>

      <div className={styles.concepts}>
        {understandData.concepts.map((concept) => (
          <div
            key={concept.id}
            className={`${styles.concept} ${concept.isThreshold ? styles.threshold : ''}`}
          >
            <div className={styles.conceptHeader}>
              <span className={styles.conceptIcon}>{concept.isThreshold ? '⚡' : '💡'}</span>
              <span className={styles.conceptName}>{concept.name}</span>
              {concept.isThreshold && <span className={styles.thresholdBadge}>Threshold</span>}
            </div>
            <p className={styles.definition}>{concept.definition}</p>
            {concept.distinguishedFrom && (
              <div className={styles.distinction}>
                <span className={styles.distinctionLabel}>Not to be confused with:</span>
                <span className={styles.distinctionText}>{concept.distinguishedFrom}</span>
              </div>
            )}
            {concept.fromAssumptionId && (
              <div className={styles.source}>
                <span className={styles.sourceLabel}>Emerged from:</span>
                <span className={styles.sourceText}>
                  {getAssumptionText(concept.fromAssumptionId)}
                </span>
              </div>
            )}
          </div>
        ))}
      </div>

      <InlineAdd
        placeholder="Concept name..."
        buttonText="+ Add concept"
        secondPlaceholder="Definition..."
        onAdd={() => {}}
        onAddTwo={(name, definition) => addConcept(name, definition)}
      />
    </div>
  )
}
