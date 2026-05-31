<template>
  <div class="min-h-screen py-8 relative">
    <!-- 背景装饰 -->
    <div class="fixed inset-0 pointer-events-none overflow-hidden">
      <div class="absolute top-1/4 -left-32 w-96 h-96 bg-gold-500/5 rounded-full blur-3xl"></div>
      <div class="absolute bottom-1/4 -right-32 w-96 h-96 bg-gold-500/3 rounded-full blur-3xl"></div>
    </div>

    <SeoHead title="深度推理" description="AI驱动的深度易学推理分析" />

    <ResponsiveContainer max-width="lg" class="relative z-10">
      <!-- 页面标题 -->
      <div class="text-center mb-10">
        <h1 class="text-4xl font-bold text-gold-500 text-glow-gold font-chinese mb-3">
          深度推理
        </h1>
        <p class="text-gold-500/50 text-sm">AI驱动的多步骤推理分析</p>
        <div class="w-16 h-px bg-gradient-to-r from-transparent via-gold-500/50 to-transparent mx-auto mt-4"></div>
      </div>

      <!-- 输入区域 -->
      <div class="mb-8 p-6 rounded-xl border border-gold-500/20 bg-ink-900/50 backdrop-blur-sm">
        <h2 class="text-gold-500/80 text-sm mb-4 font-medium">推理参数</h2>
        <div class="grid grid-cols-1 md:grid-cols-3 gap-4">
          <InputField
            v-model="hexagramName"
            placeholder="如：乾、坤、屯..."
            label="卦名"
          />
          <Select
            v-model="questionType"
            label="问题类型"
            :options="questionTypeOptions"
          />
          <Select
            v-model="monthBranch"
            label="月支（可选）"
            :options="monthBranchOptions"
          />
        </div>
      </div>

      <!-- 操作按钮 -->
      <div class="flex justify-center gap-4 mb-12">
        <button
          :disabled="!canSubmit || loading"
          @click="handleDeepReason"
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
            推理中...
          </span>
          <span v-else>深度推理</span>
        </button>
        <button
          :disabled="!canSubmit || loading"
          @click="handleBuildTree"
          :class="[
            'px-8 py-3 rounded-xl font-medium transition-all duration-300',
            'border-2 border-gold-500/50 text-gold-500/80',
            canSubmit && !loading
              ? 'bg-ink-800/50 hover:bg-gold-500/10 hover:border-gold-500 active:scale-95'
              : 'bg-ink-800/50 text-gold-500/40 cursor-not-allowed'
          ]"
        >
          概率树
        </button>
      </div>

      <!-- 错误提示 -->
      <div v-if="error" class="mb-8 p-4 rounded-lg border border-red-500/50 bg-red-500/10">
        <p class="text-red-400 text-sm">{{ error }}</p>
      </div>

      <!-- 加载状态 -->
      <div v-if="loading" class="mt-8 text-center">
        <p class="text-gold-500/60 text-sm">正在进行深度推理，请稍候...</p>
      </div>

      <!-- 推理链结果 -->
      <div v-if="result && !loading" class="mt-8 space-y-6">
          <!-- 总体信息 -->
          <div class="p-6 rounded-xl border border-gold-500/20 bg-ink-900/50 backdrop-blur-sm">
            <h3 class="text-gold-500 font-medium mb-4">推理概览</h3>
            <div class="grid grid-cols-2 md:grid-cols-4 gap-4">
              <div class="text-center">
                <p class="text-gold-500/50 text-xs">初始卦</p>
                <p class="text-gold-400 text-lg font-chinese">{{ result?.initialHexagram }}</p>
              </div>
              <div class="text-center">
                <p class="text-gold-500/50 text-xs">最终卦</p>
                <p class="text-gold-400 text-lg font-chinese">{{ result?.finalHexagram }}</p>
              </div>
              <div class="text-center">
                <p class="text-gold-500/50 text-xs">整体置信度</p>
                <p class="text-gold-400 text-lg">{{ result?.overallConfidence ?? '-' }}</p>
              </div>
              <div class="text-center">
                <p class="text-gold-500/50 text-xs">推理步骤</p>
                <p class="text-gold-400 text-lg">{{ result?.steps?.length ?? 0 }}</p>
              </div>
            </div>
          </div>

          <!-- 推理链 -->
          <div class="p-6 rounded-xl border border-gold-500/20 bg-ink-900/50 backdrop-blur-sm">
            <h3 class="text-gold-500 font-medium mb-4">推理链</h3>
            <div class="space-y-4">
              <div
                v-for="step in result?.steps ?? []"
                :key="step.stepNumber"
                class="p-4 rounded-lg border border-gold-500/10 bg-ink-800/30"
              >
                <div class="flex items-center justify-between mb-2">
                  <div class="flex items-center gap-3">
                    <span class="w-8 h-8 rounded-full bg-gold-500/20 flex items-center justify-center text-gold-400 text-sm font-bold">
                      {{ step.stepNumber }}
                    </span>
                    <span class="text-gold-500/80 text-sm font-medium">{{ step.stepType }}</span>
                  </div>
                  <span class="text-gold-500/60 text-xs">
                    置信度: {{ step.confidence }}
                  </span>
                </div>
                <p class="text-gold-500/70 text-sm mb-2">{{ step.logic }}</p>
                <div class="flex gap-2 flex-wrap">
                  <span
                    v-for="change in step.elementChanges"
                    :key="change"
                    class="px-2 py-1 rounded-md bg-gold-500/10 text-gold-500/60 text-xs"
                  >
                    {{ change }}
                  </span>
                </div>
              </div>
            </div>
          </div>

          <!-- 结论 -->
          <div class="p-6 rounded-xl border border-gold-500/20 bg-ink-900/50 backdrop-blur-sm">
            <h3 class="text-gold-500 font-medium mb-4">推理结论</h3>
            <p class="text-gold-500/80 text-sm leading-relaxed">{{ result?.conclusion }}</p>
          </div>

          <!-- 概率分布 -->
          <div v-if="result?.probabilityDistribution && Object.keys(result.probabilityDistribution).length > 0" class="p-6 rounded-xl border border-gold-500/20 bg-ink-900/50 backdrop-blur-sm">
            <h3 class="text-gold-500 font-medium mb-4">概率分布</h3>
            <div class="space-y-2">
              <div
                v-for="(prob, outcome) in result.probabilityDistribution"
                :key="String(outcome)"
                class="flex items-center gap-3"
              >
                <span class="text-gold-500/70 text-sm w-24">{{ outcome }}</span>
                <div class="flex-1 h-4 rounded-full bg-ink-800 overflow-hidden">
                  <div
                    class="h-full bg-gradient-to-r from-gold-500/50 to-gold-500 rounded-full transition-all duration-500"
                    :style="{ width: `${Number(prob) * 100}%` }"
                  ></div>
                </div>
                <span class="text-gold-500/60 text-xs w-16 text-right">{{ (Number(prob) * 100).toFixed(1) }}%</span>
              </div>
            </div>
          </div>
        </div>

      <!-- 概率树结果 -->
      <div v-if="tree?.topPaths" class="mt-8 space-y-6">
          <!-- 树概览 -->
          <div class="p-6 rounded-xl border border-gold-500/20 bg-ink-900/50 backdrop-blur-sm">
            <h3 class="text-gold-500 font-medium mb-4">概率树概览</h3>
            <div class="grid grid-cols-2 md:grid-cols-4 gap-4">
              <div class="text-center">
                <p class="text-gold-500/50 text-xs">最大深度</p>
                <p class="text-gold-400 text-lg">{{ tree?.maxDepth }}</p>
              </div>
              <div class="text-center">
                <p class="text-gold-500/50 text-xs">分支因子</p>
                <p class="text-gold-400 text-lg">{{ tree?.branchFactor }}</p>
              </div>
              <div class="text-center">
                <p class="text-gold-500/50 text-xs">总路径数</p>
                <p class="text-gold-400 text-lg">{{ tree?.totalPaths }}</p>
              </div>
              <div class="text-center">
                <p class="text-gold-500/50 text-xs">期望值</p>
                <p class="text-gold-400 text-lg">{{ tree?.expectedValue?.toFixed(2) }}</p>
              </div>
            </div>
          </div>

          <!-- 风险评估 -->
          <div class="p-6 rounded-xl border border-gold-500/20 bg-ink-900/50 backdrop-blur-sm">
            <h3 class="text-gold-500 font-medium mb-4">风险评估</h3>
            <p class="text-gold-500/80 text-sm leading-relaxed">{{ tree?.riskAssessment }}</p>
          </div>

          <!-- 最优路径 -->
          <div class="p-6 rounded-xl border border-gold-500/20 bg-ink-900/50 backdrop-blur-sm">
            <h3 class="text-gold-500 font-medium mb-4">最优路径 TOP {{ tree?.topPaths?.length }}</h3>
            <div class="overflow-x-auto">
              <table class="w-full">
                <thead>
                  <tr class="border-b border-gold-500/20">
                    <th class="text-left text-gold-500/60 text-xs py-2 px-3">排名</th>
                    <th class="text-left text-gold-500/60 text-xs py-2 px-3">卦象路径</th>
                    <th class="text-left text-gold-500/60 text-xs py-2 px-3">概率</th>
                    <th class="text-left text-gold-500/60 text-xs py-2 px-3">评分</th>
                    <th class="text-left text-gold-500/60 text-xs py-2 px-3">判定</th>
                  </tr>
                </thead>
                <tbody>
                  <tr
                    v-for="(path, index) in tree?.topPaths"
                    :key="index"
                    class="border-b border-gold-500/10 hover:bg-gold-500/5"
                  >
                    <td class="py-3 px-3 text-gold-400 text-sm">{{ index + 1 }}</td>
                    <td class="py-3 px-3 text-gold-500/80 text-sm font-chinese">
                      {{ path.hexagrams?.join(' → ') }}
                    </td>
                    <td class="py-3 px-3 text-gold-500/80 text-sm">{{ (path.probability * 100).toFixed(1) }}%</td>
                    <td class="py-3 px-3 text-gold-500/80 text-sm">{{ path.score?.toFixed(2) }}</td>
                    <td class="py-3 px-3">
                      <span
                        :class="[
                          'px-2 py-1 rounded-md text-xs',
                          path.verdict === '吉' ? 'bg-green-500/20 text-green-400' :
                          path.verdict === '凶' ? 'bg-red-500/20 text-red-400' :
                          'bg-yellow-500/20 text-yellow-400'
                        ]"
                      >
                        {{ path.verdict }}
                      </span>
                    </td>
                  </tr>
                </tbody>
              </table>
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

definePageMeta({ ssr: false })

const api = useApi()
const notification = useNotification()

// 直接内联状态，不使用 composable
const loading = ref(false)
const result = ref<any>(null)
const tree = ref<any>(null)
const hexagramName = ref('')
const questionType = ref('general')
const monthBranch = ref('')
const error = ref<string | null>(null)

const questionTypeOptions = [
  { value: 'career', label: '事业' },
  { value: 'wealth', label: '财运' },
  { value: 'love', label: '感情' },
  { value: 'health', label: '健康' },
  { value: 'general', label: '综合' },
]

const monthBranchOptions = [
  { value: '', label: '自动' },
  { value: '子', label: '子' },
  { value: '丑', label: '丑' },
  { value: '寅', label: '寅' },
  { value: '卯', label: '卯' },
  { value: '辰', label: '辰' },
  { value: '巳', label: '巳' },
  { value: '午', label: '午' },
  { value: '未', label: '未' },
  { value: '申', label: '申' },
  { value: '酉', label: '酉' },
  { value: '戌', label: '戌' },
  { value: '亥', label: '亥' },
]

const canSubmit = computed(() => hexagramName.value.trim().length > 0)

async function handleDeepReason() {
  if (!canSubmit.value) return
  error.value = null
  loading.value = true
  result.value = null

  try {
    const { data, error: apiError } = await api.request<{ success: boolean; data: any }>(
      '/api/reasoning/deep',
      {
        method: 'POST',
        body: {
          hexagram_name: hexagramName.value,
          question_type: questionType.value,
          month_branch: monthBranch.value || undefined,
          max_steps: 10,
        },
      }
    )
    loading.value = false

    if (apiError || !data?.success) {
      throw new Error(apiError || '深度推理失败')
    }
    result.value = data.data
    notification.success('推理完成', '深度推理已完成，请查看结果')
  } catch (err) {
    loading.value = false
    error.value = err instanceof Error ? err.message : '推理失败'
    notification.error('推理失败', error.value)
  }
}

async function handleBuildTree() {
  if (!canSubmit.value) return
  error.value = null
  loading.value = true
  tree.value = null

  try {
    const { data, error: apiError } = await api.request<{ success: boolean; data: any }>(
      '/api/reasoning/tree',
      {
        method: 'POST',
        body: {
          hexagram_name: hexagramName.value,
          question_type: questionType.value,
          month_branch: monthBranch.value || undefined,
          max_depth: 5,
        },
      }
    )
    loading.value = false

    if (apiError || !data?.success) {
      throw new Error(apiError || '构建概率树失败')
    }
    tree.value = data.data
    notification.success('构建完成', '概率树已生成，请查看结果')
  } catch (err) {
    loading.value = false
    error.value = err instanceof Error ? err.message : '构建概率树失败'
    notification.error('构建失败', error.value)
  }
}
</script>
