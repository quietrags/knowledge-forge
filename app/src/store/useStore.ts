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
} from '../types'

// Helper to generate unique IDs
const generateId = () => `id-${Date.now()}-${Math.random().toString(36).substr(2, 9)}`

// ============================================================================
// Store State Interface
// ============================================================================

interface ForgeState {
  // Core state
  mode: Mode
  activeTab: number
  selectedQuestionId: string | null

  // Path data
  path: PathData

  // Mode-specific data
  buildData: BuildModeData | null
  understandData: UnderstandModeData | null
  researchData: ResearchModeData | null

  // Contextual panels
  currentCode: CodeContent | null
  currentCanvas: CanvasContent | null

  // Actions
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
  // Initial state
  mode: 'build',
  activeTab: 0,
  selectedQuestionId: null,
  path: initialPath,
  buildData: null,
  understandData: null,
  researchData: null,
  currentCode: null,
  currentCanvas: null,

  // Actions
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
}))

// ============================================================================
// Selector Hooks (for optimized re-renders)
// ============================================================================

export const useMode = () => useForgeStore((state) => state.mode)
export const useActiveTab = () => useForgeStore((state) => state.activeTab)
export const useSelectedQuestionId = () => useForgeStore((state) => state.selectedQuestionId)
export const usePath = () => useForgeStore((state) => state.path)
export const useBuildData = () => useForgeStore((state) => state.buildData)
export const useUnderstandData = () => useForgeStore((state) => state.understandData)
export const useResearchData = () => useForgeStore((state) => state.researchData)
export const useCurrentCode = () => useForgeStore((state) => state.currentCode)
export const useCurrentCanvas = () => useForgeStore((state) => state.currentCanvas)

// Action hooks - use useShallow to prevent infinite re-renders
export const useForgeActions = () =>
  useForgeStore(
    useShallow((state) => ({
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
    }))
  )
