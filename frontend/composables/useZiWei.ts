import { ref } from 'vue'
import { useApi } from '~/composables/useApi'

interface PalaceData {
  palace: string
  ganZhi: string
  mainStars: string[]
  auxStars: string[]
  brightness: string
  huaStars: string[]
  isBodyPalace: boolean
}

interface ZiWeiChartResponse {
  palaces: PalaceData[]
  yearGanZhi: string
  monthGanZhi: string
  dayGanZhi: string
  hourGanZhi: string
  gender: string
  wuXingJu: string
  mingPalace: string
  shenPalace: string
}

interface Verdict {
  overall: string
  strength: string
  trend: string
  confidence: number
}

interface ZiWeiAnalysisResponse {
  targetPalace: string
  mainStars: string[]
  huaInfluence: string[]
  description: string
  verdict: Verdict
}

export function useZiWei() {
  const api = useApi()
  const loading = ref(false)
  const chart = ref<ZiWeiChartResponse | null>(null)
  const analysis = ref<ZiWeiAnalysisResponse | null>(null)

  /**
   * 起盘 - 创建紫微斗数命盘
   */
  async function createChart(params: {
    year: number
    month: number
    day: number
    hour: number
    gender: string
  }) {
    loading.value = true
    chart.value = null

    const { data, error } = await api.request<{ success: boolean; data: ZiWeiChartResponse }>(
      '/api/ziwei/chart',
      {
        method: 'POST',
        body: params,
      }
    )

    loading.value = false

    if (error || !data?.success) {
      throw new Error(error || '紫微起盘失败')
    }

    chart.value = data.data
    return data.data
  }

  /**
   * 分析紫微斗数命盘
   */
  async function analyze(params: {
    year: number
    month: number
    day: number
    hour: number
    gender: string
    question_type: string
  }) {
    loading.value = true
    analysis.value = null

    const { data, error } = await api.request<{ success: boolean; data: ZiWeiAnalysisResponse }>(
      '/api/ziwei/analyze',
      {
        method: 'POST',
        body: params,
      }
    )

    loading.value = false

    if (error || !data?.success) {
      throw new Error(error || '紫微分析失败')
    }

    analysis.value = data.data
    return data.data
  }

  return {
    loading,
    chart,
    analysis,
    createChart,
    analyze,
  }
}
