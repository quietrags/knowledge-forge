import { create } from 'zustand'
import { useShallow } from 'zustand/react/shallow'
import type {
  Mode,
  PathData,
  BuildModeData,
  UnderstandModeData,
  ResearchModeData,
  CodeContent,
  CanvasContent,
  Question,
  CategoryQuestion,
  KeyInsight,
  AdjacentQuestion,
  Construct,
  Decision,
  Capability,
  Concept,
  Model,
  Assumption,
  MODE_COLORS,
  JourneyState,
  JourneyDesignBrief,
  BuildJourney,
  BuildPhase,
  GroundingConcept,
  Narrative,
  Source,
  ConversationMessage,
  ConversationRole,
} from '../types'
import type { StreamState } from '../api/streaming'

// Helper to generate unique IDs
const generateId = () => `id-${Date.now()}-${Math.random().toString(36).substr(2, 9)}`

// ============================================================================
// Store State Interface
// ============================================================================

interface ForgeState {
  // Journey intake state
  journeyState: JourneyState
  journeyBrief: JourneyDesignBrief | null

  // Core state
  mode: Mode
  activeTab: number
  selectedQuestionId: string | null

  // Path data
  path: PathData

  // Build phase tracking
  buildJourney: BuildJourney | null

  // Mode-specific data
  buildData: BuildModeData | null
  understandData: UnderstandModeData | null
  researchData: ResearchModeData | null

  // Contextual panels
  currentCode: CodeContent | null
  currentCanvas: CanvasContent | null

  // API state
  sessionId: string | null
  streamState: StreamState
  isLoading: boolean
  error: string | null
  agentThinking: string | null
  streamingText: string
  conversationMessages: ConversationMessage[]
  awaitingInput: boolean
  inputPrompt: string | null

  // Journey intake actions
  setJourneyBrief: (brief: JourneyDesignBrief) => void
  confirmJourney: () => void
  resetJourney: () => void

  // Build phase actions
  setBuildPhase: (phase: BuildPhase) => void
  addGroundingConcept: (name: string, distinction: string) => void
  markGroundingReady: () => void

  // Core actions
  setMode: (mode: Mode) => void
  setActiveTab: (tab: number) => void
  selectQuestion: (questionId: string | null) => void
  setPath: (path: PathData) => void
  setBuildData: (data: BuildModeData) => void
  setUnderstandData: (data: UnderstandModeData) => void
  setResearchData: (data: ResearchModeData) => void
  setCurrentCode: (code: CodeContent | null) => void
  setCurrentCanvas: (canvas: CanvasContent | null) => void

  // Helpers
  getSelectedQuestion: () => Question | null
  updateCSSVariables: (mode: Mode) => void

  // Research Mode CRUD
  addQuestion: (categoryId: string, questionText: string) => void
  addCategory: (categoryName: string) => void
  addKeyInsight: (title: string, description: string) => void
  addAdjacentQuestion: (question: string, discoveredFrom: string) => void
  promoteAdjacentQuestion: (adjacentQuestionId: string, targetCategoryId: string) => void
  addCategoryInsight: (categoryId: string, insight: string) => void

  // Build Mode CRUD
  addConstruct: (name: string, description: string) => void
  addDecision: (choice: string, alternative: string) => void
  addCapability: (capability: string, enabledBy: string) => void

  // Understand Mode CRUD
  addAssumption: (assumption: string, surfaced: string) => void
  discardAssumption: (assumptionId: string) => void
  addConcept: (name: string, definition: string) => void
  addModel: (name: string, description: string) => void

  // API state actions
  setSessionId: (sessionId: string | null) => void
  setStreamState: (state: StreamState) => void
  setIsLoading: (loading: boolean) => void
  setError: (error: string | null) => void
  setAgentThinking: (message: string | null) => void
  appendStreamingText: (delta: string) => void
  clearStreamingText: () => void
  addConversationMessage: (role: ConversationRole, content: string) => void
  clearConversation: () => void
  finalizeAgentMessage: () => void
  setAwaitingInput: (awaiting: boolean, prompt?: string | null) => void

  // SSE event handlers (called from streaming handlers)
  handleQuestionAdded: (question: Question, categoryId: string) => void
  handleQuestionAnswered: (questionId: string, answer: string, sources: Source[]) => void
  handleCategoryAdded: (id: string, category: string) => void
  handleCategoryInsight: (categoryId: string, insight: string) => void
  handleKeyInsightAdded: (id: string, title: string, description: string, relevance: string) => void
  handleAdjacentQuestionAdded: (id: string, question: string, discoveredFrom: string) => void
  handleConstructAdded: (id: string, name: string, description: string, usage: string) => void
  handleDecisionAdded: (id: string, choice: string, alternative: string, rationale: string) => void
  handleCapabilityAdded: (id: string, capability: string, enabledBy: string[]) => void
  handleGroundingConceptAdded: (id: string, name: string, distinction: string) => void
  handleAssumptionSurfaced: (id: string, assumption: string, surfaced: string) => void
  handleConceptDistinguished: (id: string, name: string, definition: string, distinguishedFrom?: string, isThreshold?: boolean) => void
  handleModelIntegrated: (id: string, name: string, description: string, conceptIds: string[]) => void
  handleNarrativeUpdated: (mode: Mode, narrative: Narrative, delta?: string) => void
  handlePhaseChanged: (from: BuildPhase, to: BuildPhase) => void
}

// ============================================================================
// Mode Colors (matching types)
// ============================================================================

const modeColors: typeof MODE_COLORS = {
  build: { accent: '#059669', accentBg: '#ECFDF5' },
  understand: { accent: '#2563EB', accentBg: '#EFF6FF' },
  research: { accent: '#7C3AED', accentBg: '#F3E8FF' },
}

// ============================================================================
// Initial Mock Data
// ============================================================================

const initialPath: PathData = {
  nodes: [
    { id: 'llm-basics', name: 'LLM Basics', status: 'solid' },
    { id: 'prompting', name: 'Prompting', status: 'solid' },
    { id: 'agents', name: 'Agent Architectures', status: 'partial' },
  ],
  neighbors: ['Tool Use', 'Memory Systems'],
}

// ============================================================================
// Create Store
// ============================================================================

export const useForgeStore = create<ForgeState>((set, get) => ({
  // Initial state - journey intake
  journeyState: 'intake', // Start as 'intake' for E2E test
  journeyBrief: null,

  // Initial state - core
  mode: 'build',
  activeTab: 0,
  selectedQuestionId: null,
  path: initialPath,

  // Initial state - build phase
  buildJourney: null,

  // Initial state - mode data
  buildData: null,
  understandData: null,
  researchData: null,
  currentCode: null,
  currentCanvas: null,

  // Initial state - API
  sessionId: null,
  streamState: 'disconnected',
  isLoading: false,
  error: null,
  agentThinking: null,
  streamingText: '',
  conversationMessages: [],
  awaitingInput: false,
  inputPrompt: null,

  // Journey intake actions
  setJourneyBrief: (brief) => {
    set({
      journeyBrief: brief,
      journeyState: 'confirming',
    })
  },

  confirmJourney: () => {
    const { journeyBrief } = get()
    if (!journeyBrief) return

    // Set the mode from the brief and transition to active
    const mode = journeyBrief.primaryMode
    set({
      journeyState: 'active',
      mode,
      activeTab: 0,
      // Clear streaming text for new journey
      streamingText: '',
    })
    get().updateCSSVariables(mode)

    // Initialize mode-specific data based on selected mode
    // This is required for SSE handlers to work (they check for null)
    if (mode === 'build') {
      set({
        buildJourney: {
          phase: 'grounding',
          grounding: { concepts: [], ready: false },
        },
        buildData: {
          narrative: { prior: '', delta: '', full: '' },
          constructs: [],
          decisions: [],
          capabilities: [],
        },
      })
    } else if (mode === 'understand') {
      set({
        understandData: {
          essay: { prior: '', delta: '', full: '' },
          assumptions: [],
          concepts: [],
          models: [],
        },
      })
    } else if (mode === 'research') {
      set({
        researchData: {
          topic: journeyBrief.originalQuestion,
          meta: '',
          essay: { prior: '', delta: '', full: '' },
          categories: [],
          questions: [],
          keyInsights: [],
          adjacentQuestions: [],
        },
      })
    }
  },

  resetJourney: () => {
    set({
      journeyState: 'intake',
      journeyBrief: null,
      buildJourney: null,
      // Clear all mode data
      buildData: null,
      understandData: null,
      researchData: null,
      streamingText: '',
    })
  },

  // Build phase actions
  setBuildPhase: (phase) => {
    const { buildJourney } = get()
    if (!buildJourney) return

    set({
      buildJourney: { ...buildJourney, phase },
    })
  },

  addGroundingConcept: (name, distinction) => {
    const { buildJourney } = get()
    if (!buildJourney) return

    const newConcept: GroundingConcept = {
      id: generateId(),
      name,
      distinction,
      sufficient: false,
    }

    set({
      buildJourney: {
        ...buildJourney,
        grounding: {
          ...buildJourney.grounding,
          concepts: [...buildJourney.grounding.concepts, newConcept],
        },
      },
    })
  },

  markGroundingReady: () => {
    const { buildJourney } = get()
    if (!buildJourney) return

    set({
      buildJourney: {
        ...buildJourney,
        phase: 'making',
        grounding: { ...buildJourney.grounding, ready: true },
      },
    })
  },

  // Core actions
  setMode: (mode) => {
    set({ mode, activeTab: 0, selectedQuestionId: null })
    get().updateCSSVariables(mode)
  },

  setActiveTab: (tab) => set({ activeTab: tab }),

  selectQuestion: (questionId) => {
    set({ selectedQuestionId: questionId })

    // Update code and canvas panels if in research mode
    if (questionId && get().researchData) {
      const question = get().getSelectedQuestion()
      if (question) {
        set({
          currentCode: question.code || null,
          currentCanvas: question.canvas || null,
        })
      }
    }
  },

  setPath: (path) => set({ path }),

  setBuildData: (data) => set({ buildData: data }),
  setUnderstandData: (data) => set({ understandData: data }),
  setResearchData: (data) => set({ researchData: data }),

  setCurrentCode: (code) => set({ currentCode: code }),
  setCurrentCanvas: (canvas) => set({ currentCanvas: canvas }),

  // Helpers
  getSelectedQuestion: () => {
    const { selectedQuestionId, researchData } = get()
    if (!selectedQuestionId || !researchData) return null

    return researchData.questions.find((q) => q.id === selectedQuestionId) || null
  },

  updateCSSVariables: (mode) => {
    const colors = modeColors[mode]
    document.documentElement.style.setProperty('--accent', colors.accent)
    document.documentElement.style.setProperty('--accent-bg', colors.accentBg)
  },

  // Research Mode CRUD
  addQuestion: (categoryId, questionText) => {
    const { researchData } = get()
    if (!researchData) return

    const newQuestion: Question = {
      id: generateId(),
      question: questionText,
      status: 'open',
      sources: [],
      categoryId,
    }

    // Add question to questions array
    const updatedQuestions = [...researchData.questions, newQuestion]

    // Update category's questionIds
    const updatedCategories = researchData.categories.map((cat) =>
      cat.id === categoryId
        ? { ...cat, questionIds: [...cat.questionIds, newQuestion.id] }
        : cat
    )

    set({
      researchData: {
        ...researchData,
        questions: updatedQuestions,
        categories: updatedCategories,
      },
    })
  },

  addCategory: (categoryName) => {
    const { researchData } = get()
    if (!researchData) return

    const newCategory: CategoryQuestion = {
      id: generateId(),
      category: categoryName,
      questionIds: [],
    }

    set({
      researchData: {
        ...researchData,
        categories: [...researchData.categories, newCategory],
      },
    })
  },

  addKeyInsight: (title, description) => {
    const { researchData } = get()
    if (!researchData) return

    const newKeyInsight: KeyInsight = {
      id: generateId(),
      title,
      description,
      relevance: '',
    }

    set({
      researchData: {
        ...researchData,
        keyInsights: [...researchData.keyInsights, newKeyInsight],
      },
    })
  },

  addAdjacentQuestion: (question, discoveredFrom) => {
    const { researchData } = get()
    if (!researchData) return

    const newAdjacent: AdjacentQuestion = {
      id: generateId(),
      question,
      discoveredFrom,
    }

    set({
      researchData: {
        ...researchData,
        adjacentQuestions: [...researchData.adjacentQuestions, newAdjacent],
      },
    })
  },

  promoteAdjacentQuestion: (adjacentQuestionId, targetCategoryId) => {
    const { researchData } = get()
    if (!researchData) return

    const adjacent = researchData.adjacentQuestions.find((aq) => aq.id === adjacentQuestionId)
    if (!adjacent) return

    const newQuestion: Question = {
      id: generateId(),
      question: adjacent.question,
      status: 'open',
      sources: [],
      categoryId: targetCategoryId,
    }

    // Update categories to include new question ID
    const updatedCategories = researchData.categories.map((cat) =>
      cat.id === targetCategoryId
        ? { ...cat, questionIds: [...cat.questionIds, newQuestion.id] }
        : cat
    )

    set({
      researchData: {
        ...researchData,
        questions: [...researchData.questions, newQuestion],
        categories: updatedCategories,
        adjacentQuestions: researchData.adjacentQuestions.filter(
          (aq) => aq.id !== adjacentQuestionId
        ),
      },
    })
  },

  addCategoryInsight: (categoryId, insight) => {
    const { researchData } = get()
    if (!researchData) return

    set({
      researchData: {
        ...researchData,
        categories: researchData.categories.map((cat) =>
          cat.id === categoryId ? { ...cat, insight } : cat
        ),
      },
    })
  },

  // Build Mode CRUD
  addConstruct: (name, description) => {
    const { buildData } = get()
    if (!buildData) return

    const newConstruct: Construct = {
      id: generateId(),
      name,
      description,
      usage: '',
    }

    set({
      buildData: {
        ...buildData,
        constructs: [...buildData.constructs, newConstruct],
      },
    })
  },

  addDecision: (choice, alternative) => {
    const { buildData } = get()
    if (!buildData) return

    const newDecision: Decision = {
      id: generateId(),
      choice,
      alternative,
      rationale: '',
      constructIds: [],
    }

    set({
      buildData: {
        ...buildData,
        decisions: [...buildData.decisions, newDecision],
      },
    })
  },

  addCapability: (capability, enabledBy) => {
    const { buildData } = get()
    if (!buildData) return

    const newCapability: Capability = {
      id: generateId(),
      capability,
      enabledBy: enabledBy ? [enabledBy] : [],
    }

    set({
      buildData: {
        ...buildData,
        capabilities: [...buildData.capabilities, newCapability],
      },
    })
  },

  // Understand Mode CRUD
  addAssumption: (assumption, surfaced) => {
    const { understandData } = get()
    if (!understandData) return

    const newAssumption: Assumption = {
      id: generateId(),
      assumption,
      surfaced,
      status: 'active',
    }

    set({
      understandData: {
        ...understandData,
        assumptions: [...understandData.assumptions, newAssumption],
      },
    })
  },

  discardAssumption: (assumptionId) => {
    const { understandData } = get()
    if (!understandData) return

    set({
      understandData: {
        ...understandData,
        assumptions: understandData.assumptions.map((a) =>
          a.id === assumptionId ? { ...a, status: 'discarded' as const } : a
        ),
      },
    })
  },

  addConcept: (name, definition) => {
    const { understandData } = get()
    if (!understandData) return

    const newConcept: Concept = {
      id: generateId(),
      name,
      definition,
      isThreshold: false,
    }

    set({
      understandData: {
        ...understandData,
        concepts: [...understandData.concepts, newConcept],
      },
    })
  },

  addModel: (name, description) => {
    const { understandData } = get()
    if (!understandData) return

    const newModel: Model = {
      id: generateId(),
      name,
      description,
      conceptIds: [],
    }

    set({
      understandData: {
        ...understandData,
        models: [...understandData.models, newModel],
      },
    })
  },

  // ============================================================================
  // API State Actions
  // ============================================================================

  setSessionId: (sessionId) => set({ sessionId }),
  setStreamState: (streamState) => set({ streamState }),
  setIsLoading: (isLoading) => set({ isLoading }),
  setError: (error) => set({ error }),
  setAgentThinking: (agentThinking) => set({ agentThinking }),
  appendStreamingText: (delta) => set((state) => ({ streamingText: state.streamingText + delta })),
  clearStreamingText: () => set({ streamingText: '' }),

  // Conversation management
  addConversationMessage: (role, content) => set((state) => ({
    conversationMessages: [
      ...state.conversationMessages,
      {
        id: generateId(),
        role,
        content,
        timestamp: Date.now(),
      },
    ],
  })),
  clearConversation: () => set({ conversationMessages: [], streamingText: '' }),
  finalizeAgentMessage: () => {
    // Move current streamingText into conversation history as a tutor message
    const { streamingText } = get()
    if (streamingText.trim()) {
      set((state) => ({
        conversationMessages: [
          ...state.conversationMessages,
          {
            id: generateId(),
            role: 'tutor' as ConversationRole,
            content: streamingText,
            timestamp: Date.now(),
          },
        ],
        streamingText: '', // Clear after saving
      }))
    }
  },
  setAwaitingInput: (awaiting, prompt = null) => set({ awaitingInput: awaiting, inputPrompt: prompt }),

  // ============================================================================
  // SSE Event Handlers
  // ============================================================================

  handleQuestionAdded: (question, categoryId) => {
    const { researchData } = get()
    if (!researchData) return

    // Add question with categoryId
    const newQuestion = { ...question, categoryId }
    const updatedQuestions = [...researchData.questions, newQuestion]

    // Update category's questionIds
    const updatedCategories = researchData.categories.map((cat) =>
      cat.id === categoryId
        ? { ...cat, questionIds: [...cat.questionIds, question.id] }
        : cat
    )

    set({
      researchData: {
        ...researchData,
        questions: updatedQuestions,
        categories: updatedCategories,
      },
    })
  },

  handleQuestionAnswered: (questionId, answer, sources) => {
    const { researchData } = get()
    if (!researchData) return

    set({
      researchData: {
        ...researchData,
        questions: researchData.questions.map((q) =>
          q.id === questionId
            ? { ...q, answer, sources, status: 'answered' as const }
            : q
        ),
      },
    })
  },

  handleCategoryAdded: (id, category) => {
    const { researchData } = get()
    if (!researchData) return

    const newCategory: CategoryQuestion = {
      id,
      category,
      questionIds: [],
    }

    set({
      researchData: {
        ...researchData,
        categories: [...researchData.categories, newCategory],
      },
    })
  },

  handleCategoryInsight: (categoryId, insight) => {
    const { researchData } = get()
    if (!researchData) return

    set({
      researchData: {
        ...researchData,
        categories: researchData.categories.map((cat) =>
          cat.id === categoryId ? { ...cat, insight } : cat
        ),
      },
    })
  },

  handleKeyInsightAdded: (id, title, description, relevance) => {
    const { researchData } = get()
    if (!researchData) return

    const newInsight: KeyInsight = { id, title, description, relevance }

    set({
      researchData: {
        ...researchData,
        keyInsights: [...researchData.keyInsights, newInsight],
      },
    })
  },

  handleAdjacentQuestionAdded: (id, question, discoveredFrom) => {
    const { researchData } = get()
    if (!researchData) return

    const newAdjacent: AdjacentQuestion = { id, question, discoveredFrom }

    set({
      researchData: {
        ...researchData,
        adjacentQuestions: [...researchData.adjacentQuestions, newAdjacent],
      },
    })
  },

  handleConstructAdded: (id, name, description, usage) => {
    const { buildData } = get()
    if (!buildData) return

    const newConstruct: Construct = { id, name, description, usage }

    set({
      buildData: {
        ...buildData,
        constructs: [...buildData.constructs, newConstruct],
      },
    })
  },

  handleDecisionAdded: (id, choice, alternative, rationale) => {
    const { buildData } = get()
    if (!buildData) return

    const newDecision: Decision = { id, choice, alternative, rationale, constructIds: [] }

    set({
      buildData: {
        ...buildData,
        decisions: [...buildData.decisions, newDecision],
      },
    })
  },

  handleCapabilityAdded: (id, capability, enabledBy) => {
    const { buildData } = get()
    if (!buildData) return

    const newCapability: Capability = { id, capability, enabledBy }

    set({
      buildData: {
        ...buildData,
        capabilities: [...buildData.capabilities, newCapability],
      },
    })
  },

  handleGroundingConceptAdded: (id, name, distinction) => {
    const { buildJourney } = get()
    if (!buildJourney) return

    const newConcept: GroundingConcept = { id, name, distinction, sufficient: false }

    set({
      buildJourney: {
        ...buildJourney,
        grounding: {
          ...buildJourney.grounding,
          concepts: [...buildJourney.grounding.concepts, newConcept],
        },
      },
    })
  },

  handleAssumptionSurfaced: (id, assumption, surfaced) => {
    const { understandData } = get()
    if (!understandData) return

    const newAssumption: Assumption = { id, assumption, surfaced, status: 'active' }

    set({
      understandData: {
        ...understandData,
        assumptions: [...understandData.assumptions, newAssumption],
      },
    })
  },

  handleConceptDistinguished: (id, name, definition, distinguishedFrom, isThreshold = false) => {
    const { understandData } = get()
    if (!understandData) return

    const newConcept: Concept = { id, name, definition, distinguishedFrom, isThreshold }

    set({
      understandData: {
        ...understandData,
        concepts: [...understandData.concepts, newConcept],
      },
    })
  },

  handleModelIntegrated: (id, name, description, conceptIds) => {
    const { understandData } = get()
    if (!understandData) return

    const newModel: Model = { id, name, description, conceptIds }

    set({
      understandData: {
        ...understandData,
        models: [...understandData.models, newModel],
      },
    })
  },

  handleNarrativeUpdated: (mode, narrative, delta) => {
    const { buildData, understandData, researchData } = get()

    if (mode === 'build' && buildData) {
      set({
        buildData: { ...buildData, narrative },
        streamingText: delta ? get().streamingText + delta : get().streamingText,
      })
    } else if (mode === 'understand' && understandData) {
      set({
        understandData: { ...understandData, essay: narrative },
        streamingText: delta ? get().streamingText + delta : get().streamingText,
      })
    } else if (mode === 'research' && researchData) {
      set({
        researchData: { ...researchData, essay: narrative },
        streamingText: delta ? get().streamingText + delta : get().streamingText,
      })
    }
  },

  handlePhaseChanged: (_from, to) => {
    const { buildJourney } = get()
    if (!buildJourney) return

    set({
      buildJourney: { ...buildJourney, phase: to },
    })
  },
}))

// ============================================================================
// Selector Hooks (for optimized re-renders)
// ============================================================================

// Journey intake selectors
export const useJourneyState = () => useForgeStore((state) => state.journeyState)
export const useJourneyBrief = () => useForgeStore((state) => state.journeyBrief)

// Build phase selectors
export const useBuildJourney = () => useForgeStore((state) => state.buildJourney)

// Core selectors
export const useMode = () => useForgeStore((state) => state.mode)
export const useActiveTab = () => useForgeStore((state) => state.activeTab)
export const useSelectedQuestionId = () => useForgeStore((state) => state.selectedQuestionId)
export const usePath = () => useForgeStore((state) => state.path)
export const useBuildData = () => useForgeStore((state) => state.buildData)
export const useUnderstandData = () => useForgeStore((state) => state.understandData)
export const useResearchData = () => useForgeStore((state) => state.researchData)
export const useCurrentCode = () => useForgeStore((state) => state.currentCode)
export const useCurrentCanvas = () => useForgeStore((state) => state.currentCanvas)

// API state selectors
export const useSessionId = () => useForgeStore((state) => state.sessionId)
export const useStreamState = () => useForgeStore((state) => state.streamState)
export const useIsLoading = () => useForgeStore((state) => state.isLoading)
export const useApiError = () => useForgeStore((state) => state.error)
export const useAgentThinking = () => useForgeStore((state) => state.agentThinking)
export const useStreamingText = () => useForgeStore((state) => state.streamingText)
export const useConversationMessages = () => useForgeStore((state) => state.conversationMessages)
export const useAwaitingInput = () => useForgeStore((state) => state.awaitingInput)
export const useInputPrompt = () => useForgeStore((state) => state.inputPrompt)

// Action hooks - use useShallow to prevent infinite re-renders
export const useForgeActions = () =>
  useForgeStore(
    useShallow((state) => ({
      // Journey intake
      setJourneyBrief: state.setJourneyBrief,
      confirmJourney: state.confirmJourney,
      resetJourney: state.resetJourney,
      // Build phase
      setBuildPhase: state.setBuildPhase,
      addGroundingConcept: state.addGroundingConcept,
      markGroundingReady: state.markGroundingReady,
      // Core
      setMode: state.setMode,
      setActiveTab: state.setActiveTab,
      selectQuestion: state.selectQuestion,
      setPath: state.setPath,
      setBuildData: state.setBuildData,
      setUnderstandData: state.setUnderstandData,
      setResearchData: state.setResearchData,
      setCurrentCode: state.setCurrentCode,
      setCurrentCanvas: state.setCurrentCanvas,
      // Research CRUD
      addQuestion: state.addQuestion,
      addCategory: state.addCategory,
      addKeyInsight: state.addKeyInsight,
      addAdjacentQuestion: state.addAdjacentQuestion,
      promoteAdjacentQuestion: state.promoteAdjacentQuestion,
      addCategoryInsight: state.addCategoryInsight,
      // Build CRUD
      addConstruct: state.addConstruct,
      addDecision: state.addDecision,
      addCapability: state.addCapability,
      // Understand CRUD
      addAssumption: state.addAssumption,
      discardAssumption: state.discardAssumption,
      addConcept: state.addConcept,
      addModel: state.addModel,
      // API state actions
      setSessionId: state.setSessionId,
      setStreamState: state.setStreamState,
      setIsLoading: state.setIsLoading,
      setError: state.setError,
      setAgentThinking: state.setAgentThinking,
      appendStreamingText: state.appendStreamingText,
      clearStreamingText: state.clearStreamingText,
      // Conversation actions
      addConversationMessage: state.addConversationMessage,
      clearConversation: state.clearConversation,
      finalizeAgentMessage: state.finalizeAgentMessage,
      setAwaitingInput: state.setAwaitingInput,
    }))
  )

// SSE event handler hooks - use useShallow to prevent infinite re-renders
export const useStreamHandlers = () =>
  useForgeStore(
    useShallow((state) => ({
      handleQuestionAdded: state.handleQuestionAdded,
      handleQuestionAnswered: state.handleQuestionAnswered,
      handleCategoryAdded: state.handleCategoryAdded,
      handleCategoryInsight: state.handleCategoryInsight,
      handleKeyInsightAdded: state.handleKeyInsightAdded,
      handleAdjacentQuestionAdded: state.handleAdjacentQuestionAdded,
      handleConstructAdded: state.handleConstructAdded,
      handleDecisionAdded: state.handleDecisionAdded,
      handleCapabilityAdded: state.handleCapabilityAdded,
      handleGroundingConceptAdded: state.handleGroundingConceptAdded,
      handleAssumptionSurfaced: state.handleAssumptionSurfaced,
      handleConceptDistinguished: state.handleConceptDistinguished,
      handleModelIntegrated: state.handleModelIntegrated,
      handleNarrativeUpdated: state.handleNarrativeUpdated,
      handlePhaseChanged: state.handlePhaseChanged,
    }))
  )
