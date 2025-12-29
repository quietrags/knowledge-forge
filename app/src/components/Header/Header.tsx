import { useMode, useForgeActions, useBuildJourney } from '../../store/useStore'
import type { Mode } from '../../types'
import styles from './Header.module.css'

const modes: Mode[] = ['build', 'understand', 'research']

export function Header() {
  const currentMode = useMode()
  const buildJourney = useBuildJourney()
  const { setMode } = useForgeActions()

  // Show phase indicator for build mode
  const showPhaseIndicator = currentMode === 'build' && buildJourney
  const phase = buildJourney?.phase

  return (
    <header className={styles.header}>
      <div className={styles.logo}>Knowledge Forge</div>

      {showPhaseIndicator && (
        <div className={styles.phaseIndicator}>
          <span className={`${styles.phaseDot} ${phase === 'grounding' ? styles.active : ''}`} />
          <span className={styles.phaseLabel}>
            {phase === 'grounding' ? 'Grounding' : 'Making'}
          </span>
          <span className={`${styles.phaseDot} ${phase === 'making' ? styles.active : ''}`} />
        </div>
      )}

      <div className={styles.modeSwitch}>
        {modes.map((mode) => (
          <button
            key={mode}
            className={`${styles.modeBtn} ${currentMode === mode ? styles.active : ''}`}
            data-mode={mode}
            onClick={() => setMode(mode)}
          >
            {mode}
          </button>
        ))}
      </div>
    </header>
  )
}
