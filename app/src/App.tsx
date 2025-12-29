import { useEffect } from 'react'
import './App.css'
import { useForgeStore, useMode, useActiveTab, useForgeActions } from './store/useStore'
import { Header, PathBar, CodePanel, CanvasPanel, QuestionTree } from './components'
import { MODE_TABS } from './types'
import {
  mockResearchData,
  mockBuildData,
  mockUnderstandData,
  mockPathData,
  defaultBuildCode,
  defaultUnderstandCode,
  defaultBuildCanvas,
  defaultUnderstandCanvas,
} from './data/mockData'

function App() {
  const mode = useMode()
  const activeTab = useActiveTab()
  const { setActiveTab } = useForgeActions()

  // Initialize data and CSS variables on mount
  useEffect(() => {
    const store = useForgeStore.getState()
    store.updateCSSVariables(store.mode)
    store.setResearchData(mockResearchData)
    store.setBuildData(mockBuildData)
    store.setUnderstandData(mockUnderstandData)
    store.setPath(mockPathData)
    // Set initial code/canvas for build mode
    store.setCurrentCode(defaultBuildCode)
    store.setCurrentCanvas(defaultBuildCanvas)
  }, [])

  // Update code/canvas when mode changes (for non-research modes)
  useEffect(() => {
    const store = useForgeStore.getState()
    if (mode === 'build') {
      store.setCurrentCode(defaultBuildCode)
      store.setCurrentCanvas(defaultBuildCanvas)
    } else if (mode === 'understand') {
      store.setCurrentCode(defaultUnderstandCode)
      store.setCurrentCanvas(defaultUnderstandCanvas)
    } else if (mode === 'research') {
      // Clear panels - they get set when a question is selected
      store.setCurrentCode(null)
      store.setCurrentCanvas(null)
    }
  }, [mode])

  // Render content based on mode
  const renderContent = () => {
    if (mode === 'research' && activeTab === 0) {
      return <QuestionTree />
    }

    // Placeholder for other modes/tabs
    return (
      <>
        <div style={{ marginBottom: '24px' }}>
          <div
            style={{
              fontSize: '12px',
              color: 'var(--text-muted)',
              textTransform: 'uppercase',
              letterSpacing: '0.08em',
              marginBottom: '6px',
            }}
          >
            {mode === 'build' ? 'Building' : mode === 'understand' ? 'Understanding' : 'Research'}
          </div>
          <h1 className="font-display" style={{ fontSize: '30px', fontWeight: 600, lineHeight: 1.2 }}>
            {mode === 'research' ? 'AI Coding Agent Economics' : 'Agent Architectures'}
          </h1>
          <div style={{ marginTop: '6px', fontSize: '13px', color: 'var(--text-muted)' }}>
            {mode === 'build' && 'Building on: llm_basics, prompting'}
            {mode === 'understand' && 'Addressing: failure modes, architecture selection'}
            {mode === 'research' && 'Exploring key questions about billing, costs, and optimization'}
          </div>
        </div>
        <div className="font-serif" style={{ fontSize: '17px', lineHeight: 1.8 }}>
          <p style={{ marginBottom: '1.25em' }}>
            This is the <strong>{MODE_TABS[mode][activeTab]}</strong> tab for <strong>{mode}</strong>{' '}
            mode.
          </p>
          <p style={{ marginBottom: '1.25em' }}>
            The content here will be dynamically rendered based on the current mode and selected
            question or topic.
          </p>
        </div>
      </>
    )
  }

  return (
    <div className="app">
      <Header />
      <PathBar />

      <main className="main">
        <div className="knowledge-area">
          <div className="content-tabs">
            {MODE_TABS[mode].map((tab, i) => (
              <button
                key={tab}
                className={`content-tab ${activeTab === i ? 'active' : ''}`}
                onClick={() => setActiveTab(i)}
              >
                {tab}
              </button>
            ))}
          </div>
          <div className="content-body">{renderContent()}</div>
        </div>

        <CodePanel />
        <CanvasPanel />
      </main>

      <div className="chat">
        <div className="chat-inner">
          <input
            type="text"
            className="chat-input"
            placeholder={mode === 'research' ? 'Add a question or query findings...' : 'Continue...'}
          />
          <span className="chat-hint">↵</span>
        </div>
      </div>
    </div>
  )
}

export default App
