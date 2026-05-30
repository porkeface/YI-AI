<template>
  <div class="min-h-screen py-8 relative">
    <!-- 背景装饰 -->
    <div class="fixed inset-0 pointer-events-none overflow-hidden">
      <div class="absolute top-1/4 -left-32 w-96 h-96 bg-gold-500/5 rounded-full blur-3xl"></div>
      <div class="absolute bottom-1/4 -right-32 w-96 h-96 bg-gold-500/3 rounded-full blur-3xl"></div>
    </div>

    <SeoHead title="六爻起卦" description="使用传统六爻排盘方法，为您解答疑惑" />

    <ResponsiveContainer max-width="lg" class="relative z-10">
      <!-- 页面标题 -->
      <div class="text-center mb-10">
        <h1 class="text-4xl font-bold text-gold-500 text-glow-gold font-chinese mb-3">
          六爻起卦
        </h1>
        <p class="text-gold-500/50 text-sm">心诚则灵，请专注于您的问题</p>
        <div class="w-16 h-px bg-gradient-to-r from-transparent via-gold-500/50 to-transparent mx-auto mt-4"></div>
      </div>

      <!-- 问题输入区 -->
      <div class="mb-8 p-6 rounded-xl border border-gold-500/20 bg-ink-900/50 backdrop-blur-sm">
        <label class="block text-gold-500/80 text-sm mb-3 font-medium">请输入您的问题</label>
        <InputField
          v-model="store.question"
          placeholder="请输入您想问的事情..."
          label="请输入您的问题"
        />
      </div>

      <!-- 起卦方式选择 -->
      <div class="mb-8 p-6 rounded-xl border border-gold-500/20 bg-ink-900/50 backdrop-blur-sm">
        <label class="block text-gold-500/80 text-sm mb-4 font-medium">选择起卦方式</label>
        <div class="grid grid-cols-2 sm:grid-cols-4 gap-3">
          <button
            v-for="method in methods"
            :key="method.value"
            @click="store.setMethod(method.value)"
            :class="[
              'px-4 py-3 rounded-lg border-2 transition-all duration-300 text-center',
              store.method === method.value
                ? 'border-gold-500 bg-gold-500/15 text-gold-400 shadow-lg shadow-gold-500/10'
                : 'border-gold-500/20 text-gold-500/60 hover:border-gold-500/40 hover:text-gold-500/80'
            ]"
          >
            <div class="text-sm font-medium">{{ method.label }}</div>
            <div class="text-xs mt-1 opacity-60">{{ method.desc }}</div>
          </button>
        </div>
      </div>

      <!-- 手动输入爻 -->
      <transition
        enter-active-class="transition-all duration-300 ease-out"
        enter-from-class="opacity-0 -translate-y-2 max-h-0"
        enter-to-class="opacity-100 translate-y-0 max-h-96"
        leave-active-class="transition-all duration-200 ease-in"
        leave-from-class="opacity-100 translate-y-0 max-h-96"
        leave-to-class="opacity-0 -translate-y-2 max-h-0"
      >
        <div v-if="store.isManualMode" class="mb-8 p-6 rounded-xl border border-gold-500/20 bg-ink-900/50 backdrop-blur-sm">
          <label class="block text-gold-500/80 text-sm mb-4 font-medium">
            请从下到上依次选择六爻（第1爻到第6爻）
          </label>
          <div class="grid grid-cols-6 gap-3">
            <div
              v-for="position in 6"
              :key="position"
              class="flex flex-col items-center"
            >
              <span class="text-gold-500/50 text-xs mb-2">第{{ position }}爻</span>
              <div class="flex gap-1.5">
                <button
                  @click="store.setManualLine(position, 'yang')"
                  :class="[
                    'w-14 h-8 rounded-md border transition-all duration-200',
                    store.manualLines[position - 1] === 'yang'
                      ? 'border-gold-400 bg-gold-500/20 shadow-sm shadow-gold-500/20'
                      : 'border-gold-500/20 hover:border-gold-500/50'
                  ]"
                >
                  <div class="w-10 h-1 bg-gold-500 mx-auto rounded-full"></div>
                </button>
                <button
                  @click="store.setManualLine(position, 'yin')"
                  :class="[
                    'w-14 h-8 rounded-md border transition-all duration-200',
                    store.manualLines[position - 1] === 'yin'
                      ? 'border-gold-400 bg-gold-500/20 shadow-sm shadow-gold-500/20'
                      : 'border-gold-500/20 hover:border-gold-500/50'
                  ]"
                >
                  <div class="flex justify-center gap-1">
                    <div class="w-4 h-1 bg-gold-500 rounded-full"></div>
                    <div class="w-4 h-1 bg-gold-500 rounded-full"></div>
                  </div>
                </button>
              </div>
            </div>
          </div>
        </div>
      </transition>

      <!-- 数字输入 -->
      <transition
        enter-active-class="transition-all duration-300 ease-out"
        enter-from-class="opacity-0 -translate-y-2"
        enter-to-class="opacity-100 translate-y-0"
        leave-active-class="transition-all duration-200 ease-in"
        leave-from-class="opacity-100 translate-y-0"
        leave-to-class="opacity-0 -translate-y-2"
      >
        <div v-if="store.method === 'number'" class="mb-8 p-6 rounded-xl border border-gold-500/20 bg-ink-900/50 backdrop-blur-sm">
          <label class="block text-gold-500/80 text-sm mb-3 font-medium">
            请输入两个数字（用于起卦）
          </label>
          <div class="flex gap-4">
            <InputField
              v-model="number1"
              type="number"
              placeholder="第一个数字"
              label="第一个数字"
              class="flex-1"
            />
            <InputField
              v-model="number2"
              type="number"
              placeholder="第二个数字"
              label="第二个数字"
              class="flex-1"
            />
          </div>
        </div>
      </transition>

      <!-- 时间起卦提示 -->
      <div v-if="store.method === 'time'" class="mb-8 p-6 rounded-xl border border-gold-500/20 bg-ink-900/50 backdrop-blur-sm">
        <div class="flex items-center gap-3">
          <div class="w-10 h-10 rounded-full bg-gold-500/10 flex items-center justify-center">
            <span class="text-gold-400 text-lg">☯</span>
          </div>
          <div>
            <p class="text-gold-500/80 text-sm font-medium">时间起卦</p>
            <p class="text-gold-500/50 text-xs mt-1">将使用当前时间自动起卦，请专注于您的问题后点击"开始起卦"。</p>
          </div>
        </div>
      </div>

      <!-- 提交按钮 -->
      <div class="flex justify-center mb-12">
        <button
          :disabled="!store.canSubmit || store.loading"
          @click="handleSubmit"
          :class="[
            'px-10 py-4 rounded-xl font-medium text-lg transition-all duration-300',
            'border-2 border-gold-500 text-gold-500',
            store.canSubmit && !store.loading
              ? 'bg-gold-500/10 hover:bg-gold-500/20 hover:shadow-lg hover:shadow-gold-500/20 active:scale-95'
              : 'bg-ink-800/50 text-gold-500/40 cursor-not-allowed'
          ]"
        >
          <span v-if="store.loading" class="flex items-center gap-2">
            <svg class="animate-spin h-5 w-5" viewBox="0 0 24 24">
              <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4" fill="none"></circle>
              <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
            </svg>
            排盘中...
          </span>
          <span v-else>开始起卦</span>
        </button>
      </div>

      <!-- 错误提示 -->
      <transition
        enter-active-class="transition-all duration-300"
        enter-from-class="opacity-0 scale-95"
        enter-to-class="opacity-100 scale-100"
      >
        <ErrorBoundary
          v-if="store.error"
          :error="store.error"
          :retryable="true"
          class="mb-8"
          @retry="handleSubmit"
        />
      </transition>

      <!-- 加载状态 -->
      <transition
        enter-active-class="transition-all duration-500"
        enter-from-class="opacity-0"
        enter-to-class="opacity-100"
      >
        <div v-if="store.loading" class="mt-8">
          <LoadingSpinner text="正在排盘中，请稍候..." />
        </div>
      </transition>

      <!-- 排盘结果 -->
      <transition
        enter-active-class="transition-all duration-700 ease-out"
        enter-from-class="opacity-0 translate-y-8"
        enter-to-class="opacity-100 translate-y-0"
      >
        <div v-if="store.hasResult" class="mt-8">
          <HexagramChart
            :hexagram="store.hexagram!"
            :changed-hexagram="store.changedHexagram ?? undefined"
          />
        </div>
      </transition>

      <!-- 分析结果 -->
      <transition
        enter-active-class="transition-all duration-700 ease-out delay-200"
        enter-from-class="opacity-0 translate-y-8"
        enter-to-class="opacity-100 translate-y-0"
      >
        <div v-if="store.analysis" class="mt-8">
          <AnalysisPanel :analysis="store.analysis" />
        </div>
      </transition>

      <!-- AI 解读（流式或静态） -->
      <transition
        enter-active-class="transition-all duration-700 ease-out delay-300"
        enter-from-class="opacity-0 translate-y-8"
        enter-to-class="opacity-100 translate-y-0"
      >
        <div v-if="store.aiInterpretation || wsStreaming" class="mt-8">
          <AIStreamPanel
            :text="streamText || store.aiInterpretation"
            :is-streaming="wsStreaming"
          />
        </div>
      </transition>
    </ResponsiveContainer>
  </div>
</template>

<script setup lang="ts">
import { ref, watch, onUnmounted } from 'vue'
import { useDivinationStore } from '~/stores/divination'
import { useApi } from '~/composables/useApi'
import { useMockData } from '~/composables/useMockData'
import { useNotification } from '~/composables/useNotification'
import { useHistory } from '~/composables/useHistory'
import { useWebSocket } from '~/composables/useWebSocket'

const store = useDivinationStore()
const api = useApi()
const mockData = useMockData()
const notification = useNotification()
const history = useHistory()
const ws = useWebSocket()

const number1 = ref('')
const number2 = ref('')
const streamText = ref('')
const wsStreaming = ref(false)

const methods = [
  { value: 'time' as const, label: '时间起卦', desc: '当前时间' },
  { value: 'number' as const, label: '数字起卦', desc: '输入数字' },
  { value: 'manual' as const, label: '手动排盘', desc: '自选阴阳' },
  { value: 'plum_blossom' as const, label: '梅花易数', desc: '数字起卦' },
]

// 监听数字输入
watch([number1, number2], ([n1, n2]) => {
  if (n1 && n2) {
    store.setNumbers([parseInt(n1), parseInt(n2)])
  }
})

async function saveToHistory() {
  if (!store.hexagram || !store.analysis) return
  try {
    await history.saveHistory({
      question: store.question,
      method: store.method,
      hexagramData: store.hexagram,
      changedHexagramData: store.changedHexagram,
      analysisData: store.analysis,
    })
  } catch (err) {
    console.warn('保存历史记录失败:', err)
  }
}

async function handleSubmit() {
  if (!store.canSubmit) return

  store.setLoading(true)
  store.setError(null)
  streamText.value = ''
  wsStreaming.value = false

  const request = {
    question: store.question,
    method: store.method,
    manualLines: store.isManualMode ? store.manualLines : undefined,
    numbers: store.method === 'number' ? store.numbers : undefined,
    pbNumbers: store.method === 'plum_blossom' ? store.numbers : undefined,
  }

  try {
    // 尝试调用真实API
    const response = await api.submitDivination(request)

    if (response.success && response.data) {
      store.setResult(
        response.data.hexagram,
        response.data.changedHexagram,
        response.data.analysis,
        response.data.aiInterpretation
      )
      notification.success('排盘完成', '卦象已生成，请查看结果')
      saveToHistory()

      // 尝试 WebSocket 流式 AI 解读（如果后端支持）
      tryStreamAI(request)
    } else {
      // 如果API失败，使用mock数据
      const mockResponse = mockData.getMockDivinationResponse(
        request.question,
        request.method,
        request.manualLines,
        request.numbers
      )

      if (mockResponse.success && mockResponse.data) {
        const data = mockResponse.data
        store.setResult(data.hexagram, data.changedHexagram, data.analysis)
        notification.info('演示模式', '后端API未连接，使用演示数据')
        saveToHistory()
      } else {
        store.setError(response.error || '起卦失败，请重试')
        notification.error('起卦失败', response.error || '请重试')
      }
    }
  } catch (err) {
    // 网络错误时使用mock数据
    const mockResponse = mockData.getMockDivinationResponse(
      request.question,
      request.method,
      request.manualLines,
      request.numbers
    )

    if (mockResponse.success && mockResponse.data) {
      const data = mockResponse.data
      store.setResult(data.hexagram, data.changedHexagram, data.analysis)
      notification.info('演示模式', '后端API未连接，使用演示数据')
      saveToHistory()
    } else {
      store.setError('网络连接失败，请检查后端服务')
      notification.error('网络错误', '无法连接到后端服务')
    }
  }
}

/**
 * 尝试通过 WebSocket 获取流式 AI 解读
 */
async function tryStreamAI(request: Record<string, unknown>) {
  try {
    const config = useRuntimeConfig()
    const wsBase = (config.public.apiBase as string).replace(/^http/, 'ws')
    await ws.connect(`${wsBase}/ws/divination`)

    wsStreaming.value = true
    streamText.value = ''

    // 监听流式文本
    watch(ws.streamedText, (newText) => {
      streamText.value = newText
    })

    // 监听流式结束
    watch(ws.isStreaming, (streaming) => {
      if (!streaming) {
        wsStreaming.value = false
        if (streamText.value) {
          store.aiInterpretation = streamText.value
        }
      }
    })

    await ws.streamDivination(request)
  } catch {
    // WebSocket 不可用时静默降级，使用 HTTP 返回的 AI 解读
    wsStreaming.value = false
  }
}

// 页面离开时重置
onUnmounted(() => {
  store.reset()
  ws.disconnect()
})
</script>
