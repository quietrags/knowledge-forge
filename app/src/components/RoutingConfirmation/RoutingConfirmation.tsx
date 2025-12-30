import { useState } from 'react'
import { useJourneyBrief, useForgeActions } from '../../store/useStore'
import { useJourneyConfirm } from '../../api/hooks'
import type { Mode } from '../../types'
import styles from './RoutingConfirmation.module.css'

const MODE_INFO: Record<Mode, { label: string; color: string; description: string }> = {
  build: {
    label: 'BUILD',
    color: '#059669',
    description: 'Learn techniques you can apply immediately',
  },
  understand: {
    label: 'UNDERSTAND',
    color: '#2563EB',
    description: 'Develop a mental model of how this works',
  },
  research: {
    label: 'RESEARCH',
    color: '#7C3AED',
    description: 'Survey what exists and understand the landscape',
  },
}

const ALTERNATIVE_MODES: Record<Mode, Mode[]> = {
  build: ['understand', 'research'],
  understand: ['build', 'research'],
  research: ['build', 'understand'],
}

export const RoutingConfirmation = () => {
  const journeyBrief = useJourneyBrief()
  const { confirmJourney, setJourneyBrief, resetJourney, setSessionId, setIsLoading, setError } = useForgeActions()
  const { confirm, error } = useJourneyConfirm()
  const [isConfirming, setIsConfirming] = useState(false)

  if (!journeyBrief) return null

  const primaryMode = journeyBrief.primaryMode
  const modeInfo = MODE_INFO[primaryMode]
  const alternatives = ALTERNATIVE_MODES[primaryMode]

  const handleConfirm = async () => {
    if (isConfirming) return
    setIsConfirming(true)
    setIsLoading(true)
    setError(null)

    try {
      const session = await confirm(journeyBrief, true)
      if (session) {
        // Store the session ID for later API calls
        setSessionId(session.sessionId)
        // Now trigger the local state transition
        confirmJourney()
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to start session')
    } finally {
      setIsConfirming(false)
      setIsLoading(false)
    }
  }

  const handleAlternative = async (mode: Mode) => {
    // Update brief with new mode, then confirm with that mode
    const updatedBrief = {
      ...journeyBrief,
      primaryMode: mode,
      confirmationMessage: MODE_INFO[mode].description,
    }
    setJourneyBrief(updatedBrief)
  }

  const handleBack = () => {
    resetJourney()
  }

  return (
    <div className={styles.container}>
      <div className={styles.content}>
        <p className={styles.question}>
          You asked: "{journeyBrief.originalQuestion}"
        </p>

        <div className={styles.card}>
          <p className={styles.confirmation}>{journeyBrief.confirmationMessage}</p>

          <div className={styles.modeInfo}>
            <span
              className={styles.modeLabel}
              style={{ backgroundColor: modeInfo.color }}
            >
              {modeInfo.label}
            </span>
            <span className={styles.modeDescription}>{modeInfo.description}</span>
          </div>

          <ul className={styles.helpList}>
            {primaryMode === 'build' && (
              <>
                <li>Identify key constructs (techniques)</li>
                <li>Make decisions about when to use each</li>
                <li>Build capabilities you can apply to your work</li>
              </>
            )}
            {primaryMode === 'understand' && (
              <>
                <li>Surface your current assumptions</li>
                <li>Develop precise concepts</li>
                <li>Build a mental model of how it works</li>
              </>
            )}
            {primaryMode === 'research' && (
              <>
                <li>Decompose into answerable questions</li>
                <li>Find and evaluate sources</li>
                <li>Synthesize findings into key insights</li>
              </>
            )}
          </ul>
        </div>

        <div className={styles.actions}>
          <button
            className={styles.primaryButton}
            onClick={handleConfirm}
            disabled={isConfirming}
          >
            {isConfirming ? 'Starting session...' : `Yes, let's ${primaryMode} →`}
          </button>
          {error && <p className={styles.error}>{error.message || 'Failed to start session'}</p>}
        </div>

        <div className={styles.alternatives}>
          <p className={styles.alternativesLabel}>Or choose a different approach:</p>
          <div className={styles.alternativeButtons}>
            {alternatives.map((mode) => (
              <button
                key={mode}
                className={styles.alternativeButton}
                onClick={() => handleAlternative(mode)}
              >
                Actually, I want to {mode}
              </button>
            ))}
          </div>
        </div>

        <button className={styles.backButton} onClick={handleBack}>
          ← Ask a different question
        </button>
      </div>
    </div>
  )
}
