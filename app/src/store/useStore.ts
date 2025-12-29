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
  Category,
  KeyIdea,
  EmergentQuestion,
  Boundary,
  Concept,
  AnswerableQuestion,
  Misconception,
  Insight,
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
  addSubQuestion: (questionId: string, subQuestionText: string) => void
  addCategory: (categoryName: string) => void
  addKeyIdea: (title: string, description: string) => void
  addEmergentQuestion: (question: string, sourceCategory: string) => void
  promoteEmergentQuestion: (emergentQuestionId: string, targetCategoryId: string) => void

  // Build Mode CRUD
  addBoundary: (question: string, answer: string) => void
  addConcept: (term: string, definition: string) => void
  addAnswerableQuestion: (question: string) => void

  // Understand Mode CRUD
  addMisconception: (question: string, answer: string) => void
  addInsight: (insight: string, context: string) => void
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

    for (const category of researchData.categories) {
      const question = category.questions.find((q) => q.id === selectedQuestionId)
      if (question) return question
    }
    return null
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
      status: 'pending',
      sources: [],
      subQuestions: [],
    }

    set({
      researchData: {
        ...researchData,
        categories: researchData.categories.map((cat) =>
          cat.id === categoryId
            ? { ...cat, questions: [...cat.questions, newQuestion] }
            : cat
        ),
      },
    })
  },

  addSubQuestion: (questionId, subQuestionText) => {
    const { researchData } = get()
    if (!researchData) return

    set({
      researchData: {
        ...researchData,
        categories: researchData.categories.map((cat) => ({
          ...cat,
          questions: cat.questions.map((q) =>
            q.id === questionId
              ? {
                  ...q,
                  subQuestions: [
                    ...q.subQuestions,
                    { id: generateId(), question: subQuestionText, status: 'pending' as const },
                  ],
                }
              : q
          ),
        })),
      },
    })
  },

  addCategory: (categoryName) => {
    const { researchData } = get()
    if (!researchData) return

    const newCategory: Category = {
      id: generateId(),
      name: categoryName,
      questions: [],
    }

    set({
      researchData: {
        ...researchData,
        categories: [...researchData.categories, newCategory],
      },
    })
  },

  addKeyIdea: (title, description) => {
    const { researchData } = get()
    if (!researchData) return

    const newKeyIdea: KeyIdea = {
      id: generateId(),
      title,
      description,
      relevance: '',
    }

    set({
      researchData: {
        ...researchData,
        keyIdeas: [...researchData.keyIdeas, newKeyIdea],
      },
    })
  },

  addEmergentQuestion: (question, sourceCategory) => {
    const { researchData } = get()
    if (!researchData) return

    const newEmergent: EmergentQuestion = {
      id: generateId(),
      question,
      sourceCategory,
    }

    set({
      researchData: {
        ...researchData,
        emergentQuestions: [...researchData.emergentQuestions, newEmergent],
      },
    })
  },

  promoteEmergentQuestion: (emergentQuestionId, targetCategoryId) => {
    const { researchData } = get()
    if (!researchData) return

    const emergent = researchData.emergentQuestions.find((eq) => eq.id === emergentQuestionId)
    if (!emergent) return

    const newQuestion: Question = {
      id: generateId(),
      question: emergent.question,
      status: 'pending',
      sources: [],
      subQuestions: [],
    }

    set({
      researchData: {
        ...researchData,
        categories: researchData.categories.map((cat) =>
          cat.id === targetCategoryId
            ? { ...cat, questions: [...cat.questions, newQuestion] }
            : cat
        ),
        emergentQuestions: researchData.emergentQuestions.filter(
          (eq) => eq.id !== emergentQuestionId
        ),
      },
    })
  },

  // Build Mode CRUD
  addBoundary: (question, answer) => {
    const { buildData } = get()
    if (!buildData) return

    const newBoundary: Boundary = {
      id: generateId(),
      question,
      answer,
    }

    set({
      buildData: {
        ...buildData,
        boundaries: [...buildData.boundaries, newBoundary],
      },
    })
  },

  addConcept: (term, definition) => {
    const { buildData } = get()
    if (!buildData) return

    const newConcept: Concept = {
      id: generateId(),
      term,
      definition,
    }

    set({
      buildData: {
        ...buildData,
        concepts: [...buildData.concepts, newConcept],
      },
    })
  },

  addAnswerableQuestion: (question) => {
    const { buildData } = get()
    if (!buildData) return

    const newQuestion: AnswerableQuestion = {
      id: generateId(),
      question,
    }

    set({
      buildData: {
        ...buildData,
        questions: [...buildData.questions, newQuestion],
      },
    })
  },

  // Understand Mode CRUD
  addMisconception: (question, answer) => {
    const { understandData } = get()
    if (!understandData) return

    const newMisconception: Misconception = {
      id: generateId(),
      question,
      answer,
    }

    set({
      understandData: {
        ...understandData,
        misconceptions: [...understandData.misconceptions, newMisconception],
      },
    })
  },

  addInsight: (insight, context) => {
    const { understandData } = get()
    if (!understandData) return

    const newInsight: Insight = {
      id: generateId(),
      insight,
      context,
    }

    set({
      understandData: {
        ...understandData,
        insights: [...understandData.insights, newInsight],
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
      addSubQuestion: state.addSubQuestion,
      addCategory: state.addCategory,
      addKeyIdea: state.addKeyIdea,
      addEmergentQuestion: state.addEmergentQuestion,
      promoteEmergentQuestion: state.promoteEmergentQuestion,
      // Build CRUD
      addBoundary: state.addBoundary,
      addConcept: state.addConcept,
      addAnswerableQuestion: state.addAnswerableQuestion,
      // Understand CRUD
      addMisconception: state.addMisconception,
      addInsight: state.addInsight,
    }))
  )
