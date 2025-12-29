import { useBuildData, useForgeActions } from '../../store/useStore'
import { InlineAdd } from '../InlineAdd/InlineAdd'
import styles from './ComponentsTab.module.css'

export function ComponentsTab() {
  const buildData = useBuildData()
  const { addComponent } = useForgeActions()

  if (!buildData || buildData.components.length === 0) {
    return (
      <div className={styles.empty}>
        No components identified yet. Components are the building blocks that make up what you're constructing.
      </div>
    )
  }

  return (
    <div className={styles.container}>
      <div className={styles.header}>
        <div className={styles.label}>Building</div>
        <h1 className={styles.title}>{buildData.narrative.title}</h1>
        <p className={styles.description}>
          Components are the building blocks—the parts you're combining to construct something new.
        </p>
      </div>

      <div className={styles.components}>
        {buildData.components.map((component) => (
          <div key={component.id} className={styles.component}>
            <div className={styles.componentHeader}>
              <span className={styles.icon}>⚙</span>
              <span className={styles.name}>{component.name}</span>
            </div>
            <div className={styles.description}>{component.description}</div>
            <div className={styles.usage}>
              <span className={styles.usageLabel}>Usage:</span> {component.usage}
            </div>
          </div>
        ))}
      </div>

      <InlineAdd
        placeholder="Component name..."
        buttonText="+ Add component"
        secondPlaceholder="Description..."
        onAdd={() => {}}
        onAddTwo={(name, description) => addComponent(name, description)}
      />
    </div>
  )
}
