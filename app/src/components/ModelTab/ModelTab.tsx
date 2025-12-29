import { useUnderstandData, useForgeActions } from '../../store/useStore'
import { InlineAdd } from '../InlineAdd/InlineAdd'
import styles from './ModelTab.module.css'

export function ModelTab() {
  const understandData = useUnderstandData()
  const { addModel } = useForgeActions()

  if (!understandData || understandData.models.length === 0) {
    return (
      <div className={styles.empty}>
        No models defined yet. Models integrate concepts into coherent frameworks for understanding.
      </div>
    )
  }

  // Get concept names for display
  const getConceptNames = (conceptIds: string[]) => {
    return conceptIds
      .map((id) => understandData.concepts.find((c) => c.id === id)?.name)
      .filter(Boolean)
      .join(', ')
  }

  return (
    <div className={styles.container}>
      <div className={styles.header}>
        <div className={styles.label}>Understanding</div>
        <h1 className={styles.title}>{understandData.essay.title}</h1>
        <p className={styles.description}>
          Models integrate concepts into coherent frameworks—they're how you see the system as a whole.
        </p>
      </div>

      <div className={styles.models}>
        {understandData.models.map((model) => (
          <div key={model.id} className={styles.model}>
            <div className={styles.modelHeader}>
              <span className={styles.modelIcon}>🧠</span>
              <span className={styles.modelName}>{model.name}</span>
            </div>
            <p className={styles.modelDescription}>{model.description}</p>
            {model.conceptIds.length > 0 && (
              <div className={styles.concepts}>
                <span className={styles.conceptsLabel}>Integrates:</span>
                <span className={styles.conceptsList}>{getConceptNames(model.conceptIds)}</span>
              </div>
            )}
            {model.visualization && (
              <div className={styles.visualization}>
                <span className={styles.vizLabel}>Visualization:</span>
                <span className={styles.vizText}>{model.visualization}</span>
              </div>
            )}
          </div>
        ))}
      </div>

      <InlineAdd
        placeholder="Model name..."
        buttonText="+ Add model"
        secondPlaceholder="Description..."
        onAdd={() => {}}
        onAddTwo={(name, description) => addModel(name, description)}
      />
    </div>
  )
}
