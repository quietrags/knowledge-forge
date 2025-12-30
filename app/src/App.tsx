import { useEffect, useMemo } from 'react'
import './App.css'
import {
  useForgeStore,
  useMode,
  useActiveTab,
  useForgeActions,
  useJourneyState,
  useBuildJourney,
  useSessionId,
  useAgentThinking,
  useStreamHandlers,
} from './store/useStore'
import { useStream } from './api/hooks'
import type { StreamHandlers } from './api/streaming'
import {
  Header,
  PathBar,
  CodePanel,
  CanvasPanel,
  QuestionTree,
  KeyInsightsTab,
  FrontierTab,
  NarrativeTab,
  ConstructsTab,
  DecisionsTab,
  CapabilitiesTab,
  AssumptionsTab,
  ConceptsTab,
  ModelTab,
  ChatInput,
  JourneyIntake,
  RoutingConfirmation,
  GroundingPanel,
} from './components'
import { MODE_TABS } from './types'
import {
  defaultBuildCode,
  defaultUnderstandCode,
  defaultBuildCanvas,
  defaultUnderstandCanvas,
} from './data/mockData'

function App() {
  const mode = useMode()
  const activeTab = useActiveTab()
  const journeyState = useJourneyState()
  const buildJourney = useBuildJourney()
  const sessionId = useSessionId()
  const agentThinking = useAgentThinking()
  const {
    setActiveTab,
    setAgentThinking,
    setStreamState,
    setError,
  } = useForgeActions()

  // SSE event handlers (separate hook to keep useForgeActions smaller)
  const {
    handleNarrativeUpdated,
    handleQuestionAdded,
    handleQuestionAnswered,
    handleCategoryAdded,
    handleCategoryInsight,
    handleKeyInsightAdded,
    handleAdjacentQuestionAdded,
    handleConstructAdded,
    handleDecisionAdded,
    handleCapabilityAdded,
    handleGroundingConceptAdded,
    handleAssumptionSurfaced,
    handleConceptDistinguished,
    handleModelIntegrated,
    handlePhaseChanged,
  } = useStreamHandlers()

  // Create stable stream handlers
  const streamHandlers: StreamHandlers = useMemo(
    () => ({
      // Connection events
      onOpen: () => {
        console.log('[SSE] Connected')
        setStreamState('connected')
      },
      onClose: () => {
        console.log('[SSE] Disconnected')
        setStreamState('disconnected')
      },
      onConnectionError: (error) => {
        console.error('[SSE] Connection error:', error)
        setStreamState('error')
      },

      // Agent activity
      onAgentThinking: (payload) => {
        console.log('[SSE] Agent thinking:', payload.message)
        setAgentThinking(payload.message)
      },
      onAgentSpeaking: (payload) => {
        console.log('[SSE] Agent speaking:', payload.delta?.substring(0, 50) + '...')
        // Speaking events contain the response - could update narrative or display
      },
      onAgentComplete: () => {
        console.log('[SSE] Agent complete')
        setAgentThinking(null)
      },

      // Narrative updates
      onNarrativeUpdated: (payload) => {
        console.log('[SSE] Narrative updated for mode:', payload.mode)
        handleNarrativeUpdated(payload.mode, payload.narrative, payload.delta)
      },

      // Research mode events
      onQuestionAdded: (payload) => {
        console.log('[SSE] Question added:', payload.question.question)
        handleQuestionAdded(payload.question, payload.categoryId)
      },
      onQuestionAnswered: (payload) => {
        console.log('[SSE] Question answered:', payload.questionId)
        handleQuestionAnswered(payload.questionId, payload.answer, payload.sources)
      },
      onCategoryAdded: (payload) => {
        console.log('[SSE] Category added:', payload.category)
        handleCategoryAdded(payload.id, payload.category)
      },
      onCategoryInsight: (payload) => {
        console.log('[SSE] Category insight:', payload.categoryId)
        handleCategoryInsight(payload.categoryId, payload.insight)
      },
      onKeyInsightAdded: (payload) => {
        console.log('[SSE] Key insight added:', payload.title)
        handleKeyInsightAdded(payload.id, payload.title, payload.description, payload.relevance)
      },
      onAdjacentQuestionAdded: (payload) => {
        console.log('[SSE] Adjacent question added:', payload.question)
        handleAdjacentQuestionAdded(payload.id, payload.question, payload.discoveredFrom)
      },

      // Build mode events
      onConstructAdded: (payload) => {
        console.log('[SSE] Construct added:', payload.name)
        handleConstructAdded(payload.id, payload.name, payload.description, payload.usage)
      },
      onDecisionAdded: (payload) => {
        console.log('[SSE] Decision added:', payload.choice)
        handleDecisionAdded(payload.id, payload.choice, payload.alternative, payload.rationale)
      },
      onCapabilityAdded: (payload) => {
        console.log('[SSE] Capability added:', payload.capability)
        handleCapabilityAdded(payload.id, payload.capability, payload.enabledBy)
      },
      onGroundingConceptAdded: (payload) => {
        console.log('[SSE] Grounding concept added:', payload.name)
        handleGroundingConceptAdded(payload.id, payload.name, payload.distinction)
      },

      // Understand mode events
      onAssumptionSurfaced: (payload) => {
        console.log('[SSE] Assumption surfaced:', payload.assumption)
        handleAssumptionSurfaced(payload.id, payload.assumption, payload.surfaced)
      },
      onConceptDistinguished: (payload) => {
        console.log('[SSE] Concept distinguished:', payload.name)
        handleConceptDistinguished(payload.id, payload.name, payload.definition, payload.distinguishedFrom, payload.isThreshold)
      },
      onModelIntegrated: (payload) => {
        console.log('[SSE] Model integrated:', payload.name)
        handleModelIntegrated(payload.id, payload.name, payload.description, payload.conceptIds)
      },

      // Phase changes
      onPhaseChanged: (payload) => {
        console.log('[SSE] Phase changed:', payload.from, '->', payload.to)
        handlePhaseChanged(payload.from, payload.to)
      },

      // Errors
      onError: (payload) => {
        console.error('[SSE] Error:', payload.message)
        setError(payload.message)
        setAgentThinking(null)
      },
    }),
    [
      setStreamState,
      setAgentThinking,
      setError,
      handleNarrativeUpdated,
      handleQuestionAdded,
      handleQuestionAnswered,
      handleCategoryAdded,
      handleCategoryInsight,
      handleKeyInsightAdded,
      handleAdjacentQuestionAdded,
      handleConstructAdded,
      handleDecisionAdded,
      handleCapabilityAdded,
      handleGroundingConceptAdded,
      handleAssumptionSurfaced,
      handleConceptDistinguished,
      handleModelIntegrated,
      handlePhaseChanged,
    ]
  )

  // Connect to SSE stream when session is active
  const { connect, isConnected } = useStream(sessionId, {
    autoConnect: true,
    handlers: streamHandlers,
  })

  // Reconnect when sessionId changes
  useEffect(() => {
    if (sessionId && !isConnected) {
      console.log('[App] Connecting to SSE stream for session:', sessionId)
      connect()
    }
  }, [sessionId, isConnected, connect])

  // Initialize CSS variables on mount (removed mock data initialization)
  useEffect(() => {
    const store = useForgeStore.getState()
    store.updateCSSVariables(store.mode)
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
    // Research Mode: Research Essay, Questions, Key Insights, Frontier
    if (mode === 'research') {
      switch (activeTab) {
        case 0:
          return <NarrativeTab />
        case 1:
          return <QuestionTree />
        case 2:
          return <KeyInsightsTab />
        case 3:
          return <FrontierTab />
        default:
          return <NarrativeTab />
      }
    }

    // Build Mode: Build Narrative, Constructs, Decisions, Capabilities
    if (mode === 'build') {
      switch (activeTab) {
        case 0:
          return <NarrativeTab />
        case 1:
          return <ConstructsTab />
        case 2:
          return <DecisionsTab />
        case 3:
          return <CapabilitiesTab />
        default:
          return <NarrativeTab />
      }
    }

    // Understand Mode: Analysis Essay, Assumptions, Concepts, Model
    if (mode === 'understand') {
      switch (activeTab) {
        case 0:
          return <NarrativeTab />
        case 1:
          return <AssumptionsTab />
        case 2:
          return <ConceptsTab />
        case 3:
          return <ModelTab />
        default:
          return <NarrativeTab />
      }
    }

    return null
  }

  // Show journey intake flow
  if (journeyState === 'intake') {
    return <JourneyIntake />
  }

  if (journeyState === 'confirming') {
    return <RoutingConfirmation />
  }

  // Check if we're in build grounding phase
  const isGrounding = mode === 'build' && buildJourney?.phase === 'grounding'

  return (
    <div className="app">
      <Header />
      <PathBar />

      <main className="main">
        <div className="knowledge-area">
          {/* Show grounding panel in build mode during grounding phase */}
          {isGrounding && <GroundingPanel />}

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

      {/* Agent thinking indicator */}
      {agentThinking && (
        <div className="agent-thinking">
          <span className="thinking-dot"></span>
          <span className="thinking-text">{agentThinking}</span>
        </div>
      )}

      <ChatInput />
    </div>
  )
}

export default App
