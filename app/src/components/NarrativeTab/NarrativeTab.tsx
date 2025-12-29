import DOMPurify from 'dompurify'
import { useBuildData, useUnderstandData, useResearchData, useMode } from '../../store/useStore'
import type { Narrative } from '../../types'
import styles from './NarrativeTab.module.css'

export function NarrativeTab() {
  const mode = useMode()
  const buildData = useBuildData()
  const understandData = useUnderstandData()
  const researchData = useResearchData()

  // Get the narrative based on mode
  let narrative: Narrative | null = null
  if (mode === 'build' && buildData) {
    narrative = buildData.narrative
  } else if (mode === 'understand' && understandData) {
    narrative = understandData.essay
  } else if (mode === 'research' && researchData) {
    narrative = researchData.essay
  }

  if (!narrative) {
    return (
      <div className={styles.empty}>
        No content available. Start a {mode} session to see the knowledge narrative.
      </div>
    )
  }

  return (
    <div className={styles.container}>
      <div className={styles.header}>
        <div className={styles.label}>{narrative.label}</div>
        <h1 className={styles.title}>{narrative.title}</h1>
        <div className={styles.meta}>{narrative.meta}</div>
      </div>

      <div
        className={styles.content}
        dangerouslySetInnerHTML={{ __html: DOMPurify.sanitize(narrative.content) }}
      />
    </div>
  )
}
