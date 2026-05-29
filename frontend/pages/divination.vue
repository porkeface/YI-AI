<template>
  <div class="min-h-screen py-8">
    <SeoHead title="六爻起卦" description="使用传统六爻排盘方法，为您解答疑惑" />

    <ResponsiveContainer max-width="lg">
      <!-- 页面标题 -->
      <h1 class="text-3xl font-bold text-gold-500 text-glow-gold font-chinese mb-8 text-center">
        六爻起卦
      </h1>

      <!-- 问题输入 -->
      <div class="mb-8">
        <label class="block text-gold-500/80 text-sm mb-2">请输入您的问题</label>
        <InputField
          v-model="store.question"
          placeholder="请输入您想问的事情..."
          label="请输入您的问题"
        />
      </div>

      <!-- 起卦方式选择 -->
      <div class="mb-8">
        <label class="block text-gold-500/80 text-sm mb-3">选择起卦方式</label>
        <div class="flex flex-wrap gap-3">
          <Button
            v-for="method in methods"
            :key="method.value"
            :variant="store.method === method.value ? 'primary' : 'secondary'"
            @click="store.setMethod(method.value)"
          >
            {{ method.label }}
          </Button>
        </div>
      </div>

      <!-- 手动输入爻 -->
      <div v-if="store.isManualMode" class="mb-8">
        <label class="block text-gold-500/80 text-sm mb-3">
          请从下到上依次选择六爻（第1爻到第6爻）
        </label>
        <div class="grid grid-cols-6 gap-4">
          <div
            v-for="position in 6"
            :key="position"
            class="flex flex-col items-center"
          >
            <span class="text-gold-500/60 text-xs mb-2">第{{ position }}爻</span>
            <div class="flex gap-2">
              <button
                @click="store.setManualLine(position, 'yang')"
                :class="[
                  'w-16 h-8 rounded border-2 transition-all duration-200',
                  store.manualLines[position - 1] === 'yang'
                    ? 'border-gold-500 bg-gold-500/20'
                    : 'border-gold-500/30 hover:border-gold-500/60'
                ]"
              >
                <div class="w-12 h-1.5 bg-gold-500 mx-auto rounded"></div>
              </button>
              <button
                @click="store.setManualLine(position, 'yin')"
                :class="[
                  'w-16 h-8 rounded border-2 transition-all duration-200',
                  store.manualLines[position - 1] === 'yin'
                    ? 'border-gold-500 bg-gold-500/20'
                    : 'border-gold-500/30 hover:border-gold-500/60'
                ]"
              >
                <div class="flex justify-center gap-1">
                  <div class="w-5 h-1.5 bg-gold-500 rounded"></div>
                  <div class="w-5 h-1.5 bg-gold-500 rounded"></div>
                </div>
              </button>
            </div>
          </div>
        </div>
      </div>

      <!-- 数字输入 -->
      <div v-if="store.method === 'number'" class="mb-8">
        <label class="block text-gold-500/80 text-sm mb-2">
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

      <!-- 时间起卦提示 -->
      <div v-if="store.method === 'time'" class="mb-8 p-4 rounded-lg border border-gold-500/30 bg-ink-900/50">
        <p class="text-gold-500/80 text-sm">
          将使用当前时间自动起卦，请专注于您的问题后点击"开始起卦"。
        </p>
      </div>

      <!-- 提交按钮 -->
      <div class="flex justify-center mb-12">
        <Button
          variant="primary"
          size="lg"
          :disabled="!store.canSubmit || store.loading"
          @click="handleSubmit"
        >
          <span v-if="store.loading">排盘中...</span>
          <span v-else>开始起卦</span>
        </Button>
      </div>

      <!-- 错误提示 -->
      <ErrorBoundary
        v-if="store.error"
        :error="store.error"
        :retryable="true"
        class="mb-8"
        @retry="handleSubmit"
      />

      <!-- 加载状态 -->
      <div v-if="store.loading" class="mt-8">
        <LoadingSpinner text="正在排盘中，请稍候..." />
      </div>

      <!-- 排盘结果 -->
      <div v-if="store.hasResult" class="mt-8">
        <HexagramChart
          :hexagram="store.hexagram!"
          :changed-hexagram="store.changedHexagram"
        />
      </div>

      <!-- 分析结果 -->
      <div v-if="store.analysis" class="mt-8">
        <AnalysisPanel :analysis="store.analysis" />
      </div>
    </ResponsiveContainer>
  </div>
</template>

<script setup lang="ts">
import { ref, watch, onUnmounted } from 'vue'
import { useDivinationStore } from '~/stores/divination'
import { useApi } from '~/composables/useApi'
import { useMockData } from '~/composables/useMockData'
import { useNotification } from '~/composables/useNotification'

const store = useDivinationStore()
const api = useApi()
const mockData = useMockData()
const notification = useNotification()

const number1 = ref('')
const number2 = ref('')

const methods = [
  { value: 'time' as const, label: '时间起卦' },
  { value: 'number' as const, label: '数字起卦' },
  { value: 'manual' as const, label: '手动排盘' },
]

// 监听数字输入
watch([number1, number2], ([n1, n2]) => {
  if (n1 && n2) {
    store.setNumbers([parseInt(n1), parseInt(n2)])
  }
})

async function handleSubmit() {
  if (!store.canSubmit) return

  store.setLoading(true)
  store.setError(null)

  const request = {
    question: store.question,
    method: store.method,
    manualLines: store.isManualMode ? store.manualLines : undefined,
    numbers: store.method === 'number' ? store.numbers : undefined,
  }

  try {
    // 尝试调用真实API
    const response = await api.submitDivination(request)

    if (response.success && response.data) {
      store.setResult(
        response.data.hexagram,
        response.data.changedHexagram,
        response.data.analysis
      )
      notification.success('排盘完成', '卦象已生成，请查看结果')
    } else {
      // 如果API失败，使用mock数据
      const mockResponse = mockData.getMockDivinationResponse(
        request.question,
        request.method,
        request.manualLines,
        request.numbers
      )

      if (mockResponse.success && mockResponse.data) {
        const { hexagram, changedHexagram, ...analysisData } = mockResponse.data
        store.setResult(hexagram, changedHexagram, analysisData as any)
        notification.info('演示模式', '后端API未连接，使用演示数据')
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
      const { hexagram, changedHexagram, ...analysisData } = mockResponse.data
      store.setResult(hexagram, changedHexagram, analysisData as any)
      notification.info('演示模式', '后端API未连接，使用演示数据')
    } else {
      store.setError('网络连接失败，请检查后端服务')
      notification.error('网络错误', '无法连接到后端服务')
    }
  }
}

// 页面离开时重置
onUnmounted(() => {
  store.reset()
})
</script>
