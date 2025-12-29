import { useEffect } from 'react'
import './App.css'
import { useForgeStore, useMode, useActiveTab, useForgeActions } from './store/useStore'
import {
  Header,
  PathBar,
  CodePanel,
  CanvasPanel,
  QuestionTree,
  KeyIdeasTab,
  EmergentQuestionsTab,
  NarrativeTab,
  ComponentsTab,
  DecisionsTab,
  CapabilitiesTab,
  DistinctionsTab,
  AssumptionsTab,
  MentalModelTab,
  ChatInput,
} from './components'
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

  // Render content based on mode and active tab
  const renderContent = () => {
    // Research Mode
    if (mode === 'research') {
      switch (activeTab) {
        case 0:
          return <QuestionTree />
        case 1:
          return <KeyIdeasTab />
        case 2:
          return <EmergentQuestionsTab />
        default:
          return <QuestionTree />
      }
    }

    // Build Mode
    if (mode === 'build') {
      switch (activeTab) {
        case 0:
          return <NarrativeTab />
        case 1:
          return <ComponentsTab />
        case 2:
          return <DecisionsTab />
        case 3:
          return <CapabilitiesTab />
        default:
          return <NarrativeTab />
      }
    }

    // Understand Mode
    if (mode === 'understand') {
      switch (activeTab) {
        case 0:
          return <NarrativeTab />
        case 1:
          return <DistinctionsTab />
        case 2:
          return <AssumptionsTab />
        case 3:
          return <MentalModelTab />
        default:
          return <NarrativeTab />
      }
    }

    return null
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

      <ChatInput />
    </div>
  )
}

export default App
