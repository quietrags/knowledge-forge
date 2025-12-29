import { useBuildData, useForgeActions } from '../../store/useStore'
import { InlineAdd } from '../InlineAdd/InlineAdd'
import styles from './CapabilitiesTab.module.css'

export function CapabilitiesTab() {
  const buildData = useBuildData()
  const { addCapability } = useForgeActions()

  if (!buildData || buildData.capabilities.length === 0) {
    return (
      <div className={styles.empty}>
        No capabilities documented yet. Capabilities are what you can now do or build with this knowledge.
      </div>
    )
  }

  return (
    <div className={styles.container}>
      <div className={styles.header}>
        <div className={styles.label}>Building</div>
        <h1 className={styles.title}>{buildData.narrative.title}</h1>
        <p className={styles.description}>
          Capabilities are what you can now do—the practical outcomes of what you've built or learned.
        </p>
      </div>

      <div className={styles.capabilities}>
        {buildData.capabilities.map((cap, index) => (
          <div key={cap.id} className={styles.capability}>
            <div className={styles.capabilityHeader}>
              <span className={styles.number}>{index + 1}</span>
              <span className={styles.capabilityText}>{cap.capability}</span>
            </div>
            <div className={styles.enabledBy}>
              <span className={styles.enabledLabel}>Enabled by:</span> {cap.enabledBy}
            </div>
          </div>
        ))}
      </div>

      <InlineAdd
        placeholder="What you can now do..."
        buttonText="+ Add capability"
        secondPlaceholder="What enables this..."
        onAdd={() => {}}
        onAddTwo={(capability, enabledBy) => addCapability(capability, enabledBy)}
      />
    </div>
  )
}
