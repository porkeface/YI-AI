import { defineStore } from 'pinia'
import type { HexagramData, AnalysisResult, DivinationRequest, YinYang } from '~/types/hexagram'

interface DivinationState {
  question: string
  questionType: string
  method: 'manual' | 'time' | 'number'
  manualLines: YinYang[]
  numbers: number[]
  hexagram: HexagramData | null
  changedHexagram: HexagramData | null
  analysis: AnalysisResult | null
  aiInterpretation: string | null
  loading: boolean
  error: string | null
}

export const useDivinationStore = defineStore('divination', {
  state: (): DivinationState => ({
    question: '',
    questionType: 'general',
    method: 'time',
    manualLines: [],
    numbers: [],
    hexagram: null,
    changedHexagram: null,
    analysis: null,
    aiInterpretation: null,
    loading: false,
    error: null,
  }),

  getters: {
    hasQuestion: (state) => state.question.trim().length > 0,
    hasResult: (state) => state.hexagram !== null,
    isManualMode: (state) => state.method === 'manual',
    canSubmit: (state) => {
      if (!state.question.trim()) return false
      if (state.method === 'manual' && state.manualLines.length !== 6) return false
      if (state.method === 'number' && state.numbers.length < 2) return false
      return true
    },
  },

  actions: {
    setQuestion(question: string) {
      this.question = question
    },

    setMethod(method: 'manual' | 'time' | 'number') {
      this.method = method
      this.resetLines()
    },

    setManualLine(position: number, yinYang: YinYang) {
      if (position < 1 || position > 6) return
      this.manualLines[position - 1] = yinYang
    },

    setNumbers(numbers: number[]) {
      this.numbers = numbers
    },

    resetLines() {
      this.manualLines = []
      this.numbers = []
    },

    setResult(hexagram: HexagramData, changedHexagram?: HexagramData, analysis?: AnalysisResult, aiInterpretation?: string | null) {
      this.hexagram = hexagram
      this.changedHexagram = changedHexagram || null
      this.analysis = analysis || null
      this.aiInterpretation = aiInterpretation ?? null
      this.loading = false
      this.error = null
    },

    setLoading(loading: boolean) {
      this.loading = loading
    },

    setError(error: string | null) {
      this.error = error
      this.loading = false
    },

    reset() {
      this.question = ''
      this.questionType = 'general'
      this.method = 'time'
      this.manualLines = []
      this.numbers = []
      this.hexagram = null
      this.changedHexagram = null
      this.analysis = null
      this.aiInterpretation = null
      this.loading = false
      this.error = null
    },
  },
})
