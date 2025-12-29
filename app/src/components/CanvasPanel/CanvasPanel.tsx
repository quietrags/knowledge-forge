import { useState } from 'react'
import { useCurrentCanvas } from '../../store/useStore'
import styles from './CanvasPanel.module.css'

type CanvasTab = 'summary' | 'diagram'

export function CanvasPanel() {
  const canvas = useCurrentCanvas()
  const [activeTab, setActiveTab] = useState<CanvasTab>('summary')

  if (!canvas) {
    return (
      <div className={styles.panel}>
        <div className={styles.header}>
          <span className={styles.title}>Canvas</span>
        </div>
        <div className={styles.body}>
          <div className={styles.empty}>Select a question to view related content</div>
        </div>
      </div>
    )
  }

  const content = activeTab === 'summary' ? canvas.summary : canvas.diagram

  return (
    <div className={styles.panel}>
      <div className={styles.header}>
        <span className={styles.title}>Canvas</span>
      </div>
      <div className={styles.body}>
        <div className={styles.tabs}>
          <button
            className={`${styles.tab} ${activeTab === 'summary' ? styles.active : ''}`}
            onClick={() => setActiveTab('summary')}
          >
            Summary
          </button>
          <button
            className={`${styles.tab} ${activeTab === 'diagram' ? styles.active : ''}`}
            onClick={() => setActiveTab('diagram')}
            disabled={!canvas.diagram}
          >
            Diagram
          </button>
        </div>
        <div className={styles.content}>
          {content ? (
            <div dangerouslySetInnerHTML={{ __html: content }} />
          ) : (
            <div className={styles.noContent}>No {activeTab} available</div>
          )}
        </div>
      </div>
    </div>
  )
}
