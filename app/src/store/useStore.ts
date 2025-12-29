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
  MODE_COLORS,
} from '../types'

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
    }))
  )
