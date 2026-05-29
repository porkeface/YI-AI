import { ref } from 'vue'
import { useApi } from '~/composables/useApi'

interface PalaceInfo {
  palace: number
  door: string
  star: string
  spirit: string
  tianPan: string
  diPan: string
  isShi: boolean
  isFuxing: boolean
  isFanin: boolean
}

interface QiMenChartResponse {
  ju: number
  yinYang: string
  dun: string
  palaceInfo: PalaceInfo[]
  yearGanZhi: string
  monthGanZhi: string
  dayGanZhi: string
  hourGanZhi: string
  xunKong: string[]
  maXing: string[]
}

interface Verdict {
  overall: string
  strength: string
  trend: string
  confidence: number
}

interface QiMenAnalysisResponse {
  yongShenPalace: number
  yongShenDoor: string
  yongShenStar: string
  description: string
  verdict: Verdict
}

export function useQiMen() {
  const api = useApi()
  const loading = ref(false)
  const chart = ref<QiMenChartResponse | null>(null)
  const analysis = ref<QiMenAnalysisResponse | null>(null)

  /**
   * 起局 - 创建奇门遁甲盘
   */
  async function createChart(params: {
    year: number
    month: number
    day: number
    hour: number
  }) {
    loading.value = true
    chart.value = null

    const { data, error } = await api.request<{ success: boolean; data: QiMenChartResponse }>(
      '/api/qimen/chart',
      {
        method: 'POST',
        body: params,
      }
    )

    loading.value = false

    if (error || !data?.success) {
      throw new Error(error || '奇门起局失败')
    }

    chart.value = data.data
    return data.data
  }

  /**
   * 分析奇门遁甲盘
   */
  async function analyze(params: {
    year: number
    month: number
    day: number
    hour: number
    question_type: string
  }) {
    loading.value = true
    analysis.value = null

    const { data, error } = await api.request<{ success: boolean; data: QiMenAnalysisResponse }>(
      '/api/qimen/analyze',
      {
        method: 'POST',
        body: params,
      }
    )

    loading.value = false

    if (error || !data?.success) {
      throw new Error(error || '奇门分析失败')
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
