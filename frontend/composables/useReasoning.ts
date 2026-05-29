import { ref } from 'vue'
import { useApi } from '~/composables/useApi'

interface ReasoningStep {
  stepNumber: number
  stepType: string
  inputState: string
  logic: string
  outputState: string
  confidence: number
  elementChanges: string[]
  relatedHexagrams: string[]
}

interface BranchPoint {
  stepNumber: number
  alternatives: string[]
  chosen: string
  reason: string
}

interface ProbabilityDistribution {
  [key: string]: number
}

interface DeepReasonResponse {
  steps: ReasoningStep[]
  initialHexagram: string
  finalHexagram: string
  branchPoints: BranchPoint[]
  overallConfidence: number
  conclusion: string
  probabilityDistribution: ProbabilityDistribution
}

interface TreePath {
  hexagrams: string[]
  probability: number
  verdict: string
  score: number
}

interface ReasoningTreeResponse {
  maxDepth: number
  branchFactor: number
  totalPaths: number
  expectedValue: number
  riskAssessment: string
  topPaths: TreePath[]
}

export function useReasoning() {
  const api = useApi()
  const loading = ref(false)
  const result = ref<DeepReasonResponse | null>(null)
  const tree = ref<ReasoningTreeResponse | null>(null)

  /**
   * 深度推理
   */
  async function deepReason(params: {
    hexagram_name: string
    question_type: string
    month_branch?: string
    max_steps?: number
  }) {
    loading.value = true
    result.value = null

    const { data, error } = await api.request<{ success: boolean; data: DeepReasonResponse }>(
      '/api/reasoning/deep',
      {
        method: 'POST',
        body: params,
      }
    )

    loading.value = false

    if (error || !data?.success) {
      throw new Error(error || '深度推理失败')
    }

    result.value = data.data
    return data.data
  }

  /**
   * 构建概率树
   */
  async function buildTree(params: {
    hexagram_name: string
    question_type: string
    month_branch?: string
    max_depth?: number
  }) {
    loading.value = true
    tree.value = null

    const { data, error } = await api.request<{ success: boolean; data: ReasoningTreeResponse }>(
      '/api/reasoning/tree',
      {
        method: 'POST',
        body: params,
      }
    )

    loading.value = false

    if (error || !data?.success) {
      throw new Error(error || '构建概率树失败')
    }

    tree.value = data.data
    return data.data
  }

  return {
    loading,
    result,
    tree,
    deepReason,
    buildTree,
  }
}
