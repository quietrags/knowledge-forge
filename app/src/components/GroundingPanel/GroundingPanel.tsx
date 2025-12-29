import { useBuildJourney, useForgeActions } from '../../store/useStore'
import { InlineAdd } from '../InlineAdd/InlineAdd'
import styles from './GroundingPanel.module.css'

export const GroundingPanel = () => {
  const buildJourney = useBuildJourney()
  const { addGroundingConcept, markGroundingReady } = useForgeActions()

  if (!buildJourney || buildJourney.phase !== 'grounding') {
    return null
  }

  const { concepts } = buildJourney.grounding

  const handleAddConcept = (name: string, distinction: string) => {
    addGroundingConcept(name, distinction)
  }

  return (
    <div className={styles.container}>
      <div className={styles.header}>
        <h3 className={styles.title}>Grounding: What you need to know</h3>
        <span className={styles.phase}>Phase 1 of 2</span>
      </div>

      <p className={styles.description}>
        Before building, let's establish the key concepts you'll need.
        This minimal understanding will inform your decisions.
      </p>

      <div className={styles.concepts}>
        {concepts.length === 0 ? (
          <p className={styles.empty}>No concepts yet. Add the first one below.</p>
        ) : (
          concepts.map((concept) => (
            <div key={concept.id} className={styles.conceptCard}>
              <div className={styles.conceptName}>{concept.name}</div>
              <div className={styles.distinction}>
                <span className={styles.arrow}>→</span>
                {concept.distinction}
              </div>
            </div>
          ))
        )}
      </div>

      <InlineAdd
        placeholder="Concept name"
        buttonText="+ Add Concept"
        onAdd={() => {}}
        secondPlaceholder="Distinction (e.g., 'Not X, but Y')"
        onAddTwo={handleAddConcept}
      />

      <div className={styles.footer}>
        <button
          className={styles.readyButton}
          onClick={markGroundingReady}
          disabled={concepts.length === 0}
        >
          Ready to build →
        </button>
        {concepts.length === 0 && (
          <p className={styles.hint}>Add at least one concept to continue</p>
        )}
      </div>
    </div>
  )
}
