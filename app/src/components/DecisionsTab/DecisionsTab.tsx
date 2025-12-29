import { useBuildData, useForgeActions, useJourneyBrief } from '../../store/useStore'
import { InlineAdd } from '../InlineAdd/InlineAdd'
import styles from './DecisionsTab.module.css'

export function DecisionsTab() {
  const buildData = useBuildData()
  const { addDecision } = useForgeActions()
  const journeyBrief = useJourneyBrief()

  if (!buildData || buildData.decisions.length === 0) {
    return (
      <div className={styles.empty}>
        No decisions documented yet. Decisions capture why you chose one approach over another.
      </div>
    )
  }

  return (
    <div className={styles.container}>
      <div className={styles.header}>
        <div className={styles.label}>Building</div>
        <h1 className={styles.title}>{journeyBrief?.originalQuestion || 'Learning Journey'}</h1>
        <p className={styles.description}>
          Decisions document trade-offs—what you chose, what you didn't, and why.
        </p>
      </div>

      <div className={styles.decisions}>
        {buildData.decisions.map((decision) => (
          <div key={decision.id} className={styles.decision}>
            <div className={styles.choiceRow}>
              <span className={styles.choiceIcon}>✓</span>
              <span className={styles.choice}>{decision.choice}</span>
            </div>
            <div className={styles.alternativeRow}>
              <span className={styles.altIcon}>✗</span>
              <span className={styles.alternative}>{decision.alternative}</span>
            </div>
            <div className={styles.rationale}>
              <span className={styles.rationaleLabel}>Why:</span> {decision.rationale}
            </div>
          </div>
        ))}
      </div>

      <InlineAdd
        placeholder="Chosen approach..."
        buttonText="+ Add decision"
        secondPlaceholder="Alternative not chosen..."
        onAdd={() => {}}
        onAddTwo={(choice, alternative) => addDecision(choice, alternative)}
      />
    </div>
  )
}
