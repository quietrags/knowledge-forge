import { useBuildData, useForgeActions, useJourneyBrief } from '../../store/useStore'
import { InlineAdd } from '../InlineAdd/InlineAdd'
import styles from './ConstructsTab.module.css'

export function ConstructsTab() {
  const buildData = useBuildData()
  const { addConstruct } = useForgeActions()
  const journeyBrief = useJourneyBrief()

  if (!buildData || buildData.constructs.length === 0) {
    return (
      <div className={styles.empty}>
        No constructs identified yet. Constructs are the building blocks—external, shareable artifacts you combine to build something.
      </div>
    )
  }

  return (
    <div className={styles.container}>
      <div className={styles.header}>
        <div className={styles.label}>Building</div>
        <h1 className={styles.title}>{journeyBrief?.originalQuestion || 'Learning Journey'}</h1>
        <p className={styles.description}>
          Constructs are objects-to-think-with—the parts you're combining to build something new.
        </p>
      </div>

      <div className={styles.constructs}>
        {buildData.constructs.map((construct) => (
          <div key={construct.id} className={styles.construct}>
            <div className={styles.constructHeader}>
              <span className={styles.icon}>⚙</span>
              <span className={styles.name}>{construct.name}</span>
            </div>
            <div className={styles.description}>{construct.description}</div>
            <div className={styles.usage}>
              <span className={styles.usageLabel}>Usage:</span> {construct.usage}
            </div>
          </div>
        ))}
      </div>

      <InlineAdd
        placeholder="Construct name..."
        buttonText="+ Add construct"
        secondPlaceholder="Description..."
        onAdd={() => {}}
        onAddTwo={(name, description) => addConstruct(name, description)}
      />
    </div>
  )
}
