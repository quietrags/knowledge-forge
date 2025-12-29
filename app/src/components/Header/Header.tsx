import { useMode, useForgeActions } from '../../store/useStore'
import type { Mode } from '../../types'
import styles from './Header.module.css'

const modes: Mode[] = ['build', 'understand', 'research']

export function Header() {
  const currentMode = useMode()
  const { setMode } = useForgeActions()

  return (
    <header className={styles.header}>
      <div className={styles.logo}>Knowledge Forge</div>
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
