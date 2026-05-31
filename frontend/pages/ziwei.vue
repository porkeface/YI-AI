<template>
  <div class="min-h-screen py-8 relative">
    <!-- 背景装饰 -->
    <div class="fixed inset-0 pointer-events-none overflow-hidden">
      <div class="absolute top-1/4 -left-32 w-96 h-96 bg-gold-500/5 rounded-full blur-3xl"></div>
      <div class="absolute bottom-1/4 -right-32 w-96 h-96 bg-gold-500/3 rounded-full blur-3xl"></div>
    </div>

    <SeoHead title="紫微斗数" description="紫微斗数命盘排盘与分析" />

    <ResponsiveContainer max-width="lg" class="relative z-10">
      <!-- 页面标题 -->
      <div class="text-center mb-10">
        <h1 class="text-4xl font-bold text-gold-500 text-glow-gold font-chinese mb-3">
          紫微斗数
        </h1>
        <p class="text-gold-500/50 text-sm">星曜命盘分析系统</p>
        <div class="w-16 h-px bg-gradient-to-r from-transparent via-gold-500/50 to-transparent mx-auto mt-4"></div>
      </div>

      <!-- 输入区域 -->
      <div class="mb-8 p-6 rounded-xl border border-gold-500/20 bg-ink-900/50 backdrop-blur-sm">
        <h2 class="text-gold-500/80 text-sm mb-4 font-medium">排盘参数</h2>
        <div class="grid grid-cols-2 md:grid-cols-5 gap-4">
          <InputField
            v-model="year"
            type="number"
            placeholder="年"
            label="年份"
          />
          <InputField
            v-model="month"
            type="number"
            placeholder="月"
            label="月份"
          />
          <InputField
            v-model="day"
            type="number"
            placeholder="日"
            label="日期"
          />
          <InputField
            v-model="hour"
            type="number"
            placeholder="时"
            label="时辰"
          />
          <Select
            v-model="gender"
            label="性别"
            :options="genderOptions"
          />
        </div>
        <div class="mt-4">
          <Select
            v-model="questionType"
            label="问题类型"
            :options="questionTypeOptions"
          />
        </div>
      </div>

      <!-- 操作按钮 -->
      <div class="flex justify-center gap-4 mb-12">
        <button
          :disabled="!canSubmit || loading"
          @click="handleCreateChart"
          :class="[
            'px-8 py-3 rounded-xl font-medium transition-all duration-300',
            'border-2 border-gold-500 text-gold-500',
            canSubmit && !loading
              ? 'bg-gold-500/10 hover:bg-gold-500/20 hover:shadow-lg hover:shadow-gold-500/20 active:scale-95'
              : 'bg-ink-800/50 text-gold-500/40 cursor-not-allowed'
          ]"
        >
          <span v-if="loading" class="flex items-center gap-2">
            <svg class="animate-spin h-5 w-5" viewBox="0 0 24 24">
              <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4" fill="none"></circle>
              <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
            </svg>
            排盘中...
          </span>
          <span v-else>排盘</span>
        </button>
        <button
          :disabled="!canSubmit || loading"
          @click="handleAnalyze"
          :class="[
            'px-8 py-3 rounded-xl font-medium transition-all duration-300',
            'border-2 border-gold-500/50 text-gold-500/80',
            canSubmit && !loading
              ? 'bg-ink-800/50 hover:bg-gold-500/10 hover:border-gold-500 active:scale-95'
              : 'bg-ink-800/50 text-gold-500/40 cursor-not-allowed'
          ]"
        >
          分析
        </button>
      </div>

      <!-- 错误提示 -->
      <div v-if="error" class="mb-8 p-4 rounded-lg border border-red-500/50 bg-red-500/10">
        <p class="text-red-400 text-sm">{{ error }}</p>
      </div>

      <!-- 加载状态 -->
      <div v-if="loading" class="mt-8 text-center">
        <p class="text-gold-500/60 text-sm">正在排盘，请稍候...</p>
      </div>

      <!-- 命盘结果 -->
      <div v-if="chartData && !loading" class="mt-8 space-y-6">
          <!-- 基本信息 -->
          <div class="p-6 rounded-xl border border-gold-500/20 bg-ink-900/50 backdrop-blur-sm">
            <h3 class="text-gold-500 font-medium mb-4">基本信息</h3>
            <div class="grid grid-cols-2 md:grid-cols-4 gap-4">
              <div class="text-center">
                <p class="text-gold-500/50 text-xs">年柱</p>
                <p class="text-gold-400 text-lg font-chinese">{{ chartData?.yearGanZhi }}</p>
              </div>
              <div class="text-center">
                <p class="text-gold-500/50 text-xs">月柱</p>
                <p class="text-gold-400 text-lg font-chinese">{{ chartData?.monthGanZhi }}</p>
              </div>
              <div class="text-center">
                <p class="text-gold-500/50 text-xs">日柱</p>
                <p class="text-gold-400 text-lg font-chinese">{{ chartData?.dayGanZhi }}</p>
              </div>
              <div class="text-center">
                <p class="text-gold-500/50 text-xs">时柱</p>
                <p class="text-gold-400 text-lg font-chinese">{{ chartData?.hourGanZhi }}</p>
              </div>
            </div>
            <div class="mt-4 flex flex-wrap gap-2">
              <span class="px-3 py-1 rounded-md bg-gold-500/10 text-gold-500/80 text-xs">
                {{ chartData?.gender === 'male' ? '男' : '女' }}命
              </span>
              <span class="px-3 py-1 rounded-md bg-gold-500/10 text-gold-500/80 text-xs">
                {{ chartData?.wuXingJu }}
              </span>
              <span class="px-3 py-1 rounded-md bg-blue-500/10 text-blue-400 text-xs">
                命宫: {{ chartData?.mingPalace }}
              </span>
              <span class="px-3 py-1 rounded-md bg-purple-500/10 text-purple-400 text-xs">
                身宫: {{ chartData?.shenPalace }}
              </span>
            </div>
          </div>

          <!-- 十二宫格 -->
          <div class="p-6 rounded-xl border border-gold-500/20 bg-ink-900/50 backdrop-blur-sm">
            <h3 class="text-gold-500 font-medium mb-4">十二宫命盘</h3>
            <div class="grid grid-cols-4 gap-2 max-w-2xl mx-auto">
              <div v-for="dizhi in diZhiOrder" :key="dizhi" class="p-3 rounded-lg border border-gold-500/20 bg-ink-800/50 min-h-[100px]">
                <div class="flex justify-between items-start mb-2">
                  <span class="text-gold-500/50 text-xs">{{ dizhi }}</span>
                  <span class="text-gold-400 text-xs font-chinese">{{ getPalaceByPosition(dizhi)?.palace || '' }}</span>
                </div>
                <div class="space-y-1">
                  <p class="text-gold-500/80 text-xs font-chinese truncate">
                    {{ getPalaceByPosition(dizhi)?.mainStars?.join(' ') || '' }}
                  </p>
                  <p class="text-gold-500/60 text-xs truncate">
                    {{ getPalaceByPosition(dizhi)?.brightness || '' }}
                  </p>
                </div>
              </div>
            </div>
          </div>

          <!-- 宫位详情 -->
          <div class="p-6 rounded-xl border border-gold-500/20 bg-ink-900/50 backdrop-blur-sm">
            <h3 class="text-gold-500 font-medium mb-4">宫位详情</h3>
            <div class="overflow-x-auto">
              <table class="w-full">
                <thead>
                  <tr class="border-b border-gold-500/20">
                    <th class="text-left text-gold-500/60 text-xs py-2 px-3">宫位</th>
                    <th class="text-left text-gold-500/60 text-xs py-2 px-3">干支</th>
                    <th class="text-left text-gold-500/60 text-xs py-2 px-3">主星</th>
                    <th class="text-left text-gold-500/60 text-xs py-2 px-3">辅星</th>
                    <th class="text-left text-gold-500/60 text-xs py-2 px-3">亮度</th>
                    <th class="text-left text-gold-500/60 text-xs py-2 px-3">化星</th>
                    <th class="text-left text-gold-500/60 text-xs py-2 px-3">状态</th>
                  </tr>
                </thead>
                <tbody>
                  <tr
                    v-for="palace in chartData?.palaces ?? []"
                    :key="palace.palace"
                    class="border-b border-gold-500/10 hover:bg-gold-500/5"
                  >
                    <td class="py-3 px-3 text-gold-400 text-sm font-chinese">{{ palace.palace }}</td>
                    <td class="py-3 px-3 text-gold-500/80 text-sm font-chinese">{{ palace.ganZhi }}</td>
                    <td class="py-3 px-3 text-gold-500/80 text-sm font-chinese">
                      {{ palace.mainStars?.join(', ') || '-' }}
                    </td>
                    <td class="py-3 px-3 text-gold-500/80 text-sm font-chinese">
                      {{ palace.auxStars?.join(', ') || '-' }}
                    </td>
                    <td class="py-3 px-3 text-gold-500/80 text-sm">{{ palace.brightness }}</td>
                    <td class="py-3 px-3 text-gold-500/80 text-sm font-chinese">
                      {{ palace.huaStars?.join(', ') || '-' }}
                    </td>
                    <td class="py-3 px-3">
                      <span
                        v-if="palace.isBodyPalace"
                        class="px-2 py-1 rounded-md bg-purple-500/20 text-purple-400 text-xs"
                      >
                        身宫
                      </span>
                    </td>
                  </tr>
                </tbody>
              </table>
            </div>
          </div>
        </div>

      <!-- 分析结果 -->
      <div v-if="analysisData" class="mt-8 space-y-6">
          <!-- 分析目标 -->
          <div class="p-6 rounded-xl border border-gold-500/20 bg-ink-900/50 backdrop-blur-sm">
            <h3 class="text-gold-500 font-medium mb-4">分析目标</h3>
            <div class="grid grid-cols-1 md:grid-cols-3 gap-4">
              <div class="p-4 rounded-lg border border-gold-500/10 bg-ink-800/30">
                <p class="text-gold-500/50 text-xs mb-1">目标宫位</p>
                <p class="text-gold-400 text-lg font-chinese">{{ analysisData?.targetPalace }}</p>
              </div>
              <div class="p-4 rounded-lg border border-gold-500/10 bg-ink-800/30">
                <p class="text-gold-500/50 text-xs mb-1">主星</p>
                <p class="text-gold-400 text-lg font-chinese">{{ analysisData?.mainStars?.join(', ') }}</p>
              </div>
              <div class="p-4 rounded-lg border border-gold-500/10 bg-ink-800/30">
                <p class="text-gold-500/50 text-xs mb-1">化曜影响</p>
                <p class="text-gold-400 text-lg font-chinese">{{ analysisData?.huaInfluence?.join(', ') || '无' }}</p>
              </div>
            </div>
          </div>

          <!-- 分析描述 -->
          <div class="p-6 rounded-xl border border-gold-500/20 bg-ink-900/50 backdrop-blur-sm">
            <h3 class="text-gold-500 font-medium mb-4">分析结果</h3>
            <p class="text-gold-500/80 text-sm leading-relaxed mb-6">{{ analysisData?.description }}</p>

            <!-- 判定 -->
            <div class="grid grid-cols-2 md:grid-cols-4 gap-4">
              <div class="p-4 rounded-lg border border-gold-500/10 bg-ink-800/30 text-center">
                <p class="text-gold-500/50 text-xs mb-1">总体</p>
                <p class="text-gold-400 text-lg font-chinese">{{ analysisData?.verdict?.overall }}</p>
              </div>
              <div class="p-4 rounded-lg border border-gold-500/10 bg-ink-800/30 text-center">
                <p class="text-gold-500/50 text-xs mb-1">力量</p>
                <p class="text-gold-400 text-lg font-chinese">{{ analysisData?.verdict?.strength }}</p>
              </div>
              <div class="p-4 rounded-lg border border-gold-500/10 bg-ink-800/30 text-center">
                <p class="text-gold-500/50 text-xs mb-1">趋势</p>
                <p class="text-gold-400 text-lg font-chinese">{{ analysisData?.verdict?.trend }}</p>
              </div>
              <div class="p-4 rounded-lg border border-gold-500/10 bg-ink-800/30 text-center">
                <p class="text-gold-500/50 text-xs mb-1">置信度</p>
                <p class="text-gold-400 text-lg">{{ (analysisData?.verdict?.confidence * 100).toFixed(1) }}%</p>
              </div>
            </div>
          </div>
        </div>
    </ResponsiveContainer>
  </div>
</template>

<script setup lang="ts">
import { ref, computed } from 'vue'
import { useApi } from '~/composables/useApi'
import { useNotification } from '~/composables/useNotification'
import { isValidDate } from '~/utils/format'

definePageMeta({ ssr: false })

const api = useApi()
const notification = useNotification()

const loading = ref(false)
const chartData = ref<any>(null)
const analysisData = ref<any>(null)

const year = ref(String(new Date().getFullYear()))
const month = ref(String(new Date().getMonth() + 1))
const day = ref(String(new Date().getDate()))
const hour = ref(String(new Date().getHours()))
const gender = ref('male')
const questionType = ref('general')
const error = ref<string | null>(null)

const diZhiOrder = ['子', '丑', '寅', '卯', '辰', '巳', '午', '未', '申', '酉', '戌', '亥']

const genderOptions = [
  { value: 'male', label: '男' },
  { value: 'female', label: '女' },
]

const questionTypeOptions = [
  { value: 'career', label: '事业' },
  { value: 'wealth', label: '财运' },
  { value: 'love', label: '感情' },
  { value: 'health', label: '健康' },
  { value: 'general', label: '综合' },
]

const canSubmit = computed(() => {
  const y = Number(year.value)
  const m = Number(month.value)
  const d = Number(day.value)
  const h = Number(hour.value)
  return y > 0 && isValidDate(y, m, d) && h >= 0 && h <= 23
})

function getPalaceByPosition(dizhi: string) {
  if (!chartData.value?.palaces) return null
  const index = diZhiOrder.indexOf(dizhi)
  if (index === -1) return null
  return chartData.value?.palaces?.[index]
}

async function handleCreateChart() {
  if (!canSubmit.value) return
  error.value = null
  loading.value = true
  chartData.value = null

  try {
    const { data, error: apiError } = await api.request<{ success: boolean; data: any }>(
      '/api/ziwei/chart',
      {
        method: 'POST',
        body: {
          year: Number(year.value),
          month: Number(month.value),
          day: Number(day.value),
          hour: Number(hour.value),
          gender: gender.value,
        },
      }
    )
    loading.value = false

    if (apiError || !data?.success) {
      throw new Error(apiError || '紫微起盘失败')
    }
    chartData.value = data.data
    notification.success('排盘完成', '紫微命盘已生成')
  } catch (err) {
    loading.value = false
    error.value = err instanceof Error ? err.message : '排盘失败'
    notification.error('排盘失败', error.value)
  }
}

async function handleAnalyze() {
  if (!canSubmit.value) return
  error.value = null
  loading.value = true
  analysisData.value = null

  try {
    const { data, error: apiError } = await api.request<{ success: boolean; data: any }>(
      '/api/ziwei/analyze',
      {
        method: 'POST',
        body: {
          year: Number(year.value),
          month: Number(month.value),
          day: Number(day.value),
          hour: Number(hour.value),
          gender: gender.value,
          question_type: questionType.value,
        },
      }
    )
    loading.value = false

    if (apiError || !data?.success) {
      throw new Error(apiError || '紫微分析失败')
    }
    analysisData.value = data.data
    notification.success('分析完成', '紫微分析已完成')
  } catch (err) {
    loading.value = false
    error.value = err instanceof Error ? err.message : '分析失败'
    notification.error('分析失败', error.value)
  }
}
</script>
