import DOMPurify from 'dompurify'
import { useBuildData, useUnderstandData, useResearchData, useMode, useJourneyBrief } from '../../store/useStore'
import type { Narrative, Mode } from '../../types'
import styles from './NarrativeTab.module.css'

// Mode-specific display labels
const MODE_LABELS: Record<Mode, string> = {
  build: 'Build Narrative',
  understand: 'Understanding Essay',
  research: 'Research Essay',
}

export function NarrativeTab() {
  const mode = useMode()
  const buildData = useBuildData()
  const understandData = useUnderstandData()
  const researchData = useResearchData()
  const journeyBrief = useJourneyBrief()

  // Get the narrative based on mode
  let narrative: Narrative | null = null
  if (mode === 'build' && buildData) {
    narrative = buildData.narrative
  } else if (mode === 'understand' && understandData) {
    narrative = understandData.essay
  } else if (mode === 'research' && researchData) {
    narrative = researchData.essay
  }

  // Only show if we have actual narrative content
  // Conversation/dialogue is shown in ConversationPanel, not here
  if (!narrative?.full) {
    return (
      <div className={styles.empty}>
        <p>No content available yet.</p>
        <p className={styles.hint}>
          The {MODE_LABELS[mode].toLowerCase()} will appear here as you progress through the learning session.
          Check the Conversation panel on the right to interact with your tutor.
        </p>
      </div>
    )
  }

  return (
    <div className={styles.container}>
      <div className={styles.header}>
        <div className={styles.label}>{MODE_LABELS[mode]}</div>
        <h1 className={styles.title}>{journeyBrief?.originalQuestion || 'Learning Journey'}</h1>
        <div className={styles.meta}>{journeyBrief?.confirmationMessage || ''}</div>
      </div>

      <div
        className={styles.content}
        dangerouslySetInnerHTML={{ __html: DOMPurify.sanitize(narrative.full) }}
      />
    </div>
  )
}
