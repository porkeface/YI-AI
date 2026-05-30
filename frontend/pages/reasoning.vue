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
          >
            <option value="career">事业</option>
            <option value="wealth">财运</option>
            <option value="love">感情</option>
            <option value="health">健康</option>
            <option value="general">综合</option>
          </Select>
          <Select
            v-model="monthBranch"
            label="月支（可选）"
          >
            <option value="">自动</option>
            <option value="子">子</option>
            <option value="丑">丑</option>
            <option value="寅">寅</option>
            <option value="卯">卯</option>
            <option value="辰">辰</option>
            <option value="巳">巳</option>
            <option value="午">午</option>
            <option value="未">未</option>
            <option value="申">申</option>
            <option value="酉">酉</option>
            <option value="戌">戌</option>
            <option value="亥">亥</option>
          </Select>
        </div>
      </div>

      <!-- 操作按钮 -->
      <div class="flex justify-center gap-4 mb-12">
        <button
          :disabled="!canSubmit || reasoning.loading"
          @click="handleDeepReason"
          :class="[
            'px-8 py-3 rounded-xl font-medium transition-all duration-300',
            'border-2 border-gold-500 text-gold-500',
            canSubmit && !reasoning.loading
              ? 'bg-gold-500/10 hover:bg-gold-500/20 hover:shadow-lg hover:shadow-gold-500/20 active:scale-95'
              : 'bg-ink-800/50 text-gold-500/40 cursor-not-allowed'
          ]"
        >
          <span v-if="reasoning.loading" class="flex items-center gap-2">
            <svg class="animate-spin h-5 w-5" viewBox="0 0 24 24">
              <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4" fill="none"></circle>
              <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
            </svg>
            推理中...
          </span>
          <span v-else>深度推理</span>
        </button>
        <button
          :disabled="!canSubmit || reasoning.loading"
          @click="handleBuildTree"
          :class="[
            'px-8 py-3 rounded-xl font-medium transition-all duration-300',
            'border-2 border-gold-500/50 text-gold-500/80',
            canSubmit && !reasoning.loading
              ? 'bg-ink-800/50 hover:bg-gold-500/10 hover:border-gold-500 active:scale-95'
              : 'bg-ink-800/50 text-gold-500/40 cursor-not-allowed'
          ]"
        >
          概率树
        </button>
      </div>

      <!-- 错误提示 -->
      <transition
        enter-active-class="transition-all duration-300"
        enter-from-class="opacity-0 scale-95"
        enter-to-class="opacity-100 scale-100"
      >
        <ErrorBoundary
          v-if="error"
          :error="error"
          :retryable="true"
          class="mb-8"
          @retry="handleDeepReason"
        />
      </transition>

      <!-- 加载状态 -->
      <transition
        enter-active-class="transition-all duration-500"
        enter-from-class="opacity-0"
        enter-to-class="opacity-100"
      >
        <div v-if="reasoning.loading" class="mt-8">
          <LoadingSpinner text="正在进行深度推理，请稍候..." />
        </div>
      </transition>

      <!-- 推理链结果 -->
      <transition
        enter-active-class="transition-all duration-700 ease-out"
        enter-from-class="opacity-0 translate-y-8"
        enter-to-class="opacity-100 translate-y-0"
      >
        <div v-if="reasoning.result" class="mt-8 space-y-6">
          <!-- 总体信息 -->
          <div class="p-6 rounded-xl border border-gold-500/20 bg-ink-900/50 backdrop-blur-sm">
            <h3 class="text-gold-500 font-medium mb-4">推理概览</h3>
            <div class="grid grid-cols-2 md:grid-cols-4 gap-4">
              <div class="text-center">
                <p class="text-gold-500/50 text-xs">初始卦</p>
                <p class="text-gold-400 text-lg font-chinese">{{ reasoning.result?.initialHexagram }}</p>
              </div>
              <div class="text-center">
                <p class="text-gold-500/50 text-xs">最终卦</p>
                <p class="text-gold-400 text-lg font-chinese">{{ reasoning.result?.finalHexagram }}</p>
              </div>
              <div class="text-center">
                <p class="text-gold-500/50 text-xs">整体置信度</p>
                <p class="text-gold-400 text-lg">{{ ((reasoning.result?.overallConfidence ?? 0) * 100).toFixed(1) }}%</p>
              </div>
              <div class="text-center">
                <p class="text-gold-500/50 text-xs">推理步骤</p>
                <p class="text-gold-400 text-lg">{{ reasoning.result?.steps?.length ?? 0 }}</p>
              </div>
            </div>
          </div>

          <!-- 推理链 -->
          <div class="p-6 rounded-xl border border-gold-500/20 bg-ink-900/50 backdrop-blur-sm">
            <h3 class="text-gold-500 font-medium mb-4">推理链</h3>
            <div class="space-y-4">
              <div
                v-for="step in reasoning.result?.steps ?? []"
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
                    置信度: {{ (step.confidence * 100).toFixed(1) }}%
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

          <!-- 分支点 -->
          <div v-if="(reasoning.result?.branchPoints?.length ?? 0) > 0" class="p-6 rounded-xl border border-gold-500/20 bg-ink-900/50 backdrop-blur-sm">
            <h3 class="text-gold-500 font-medium mb-4">关键分支点</h3>
            <div class="space-y-3">
              <div
                v-for="bp in reasoning.result?.branchPoints ?? []"
                :key="bp.stepNumber"
                class="p-3 rounded-lg border border-gold-500/10 bg-ink-800/30"
              >
                <p class="text-gold-500/80 text-sm">
                  <span class="text-gold-400">步骤 {{ bp.stepNumber }}:</span>
                  {{ bp.reason }}
                </p>
                <p class="text-gold-500/50 text-xs mt-1">
                  选择: {{ bp.chosen }} | 备选: {{ bp.alternatives.join(', ') }}
                </p>
              </div>
            </div>
          </div>

          <!-- 结论 -->
          <div class="p-6 rounded-xl border border-gold-500/20 bg-ink-900/50 backdrop-blur-sm">
            <h3 class="text-gold-500 font-medium mb-4">推理结论</h3>
            <p class="text-gold-500/80 text-sm leading-relaxed">{{ reasoning.result?.conclusion }}</p>
          </div>

          <!-- 概率分布 -->
          <div v-if="Object.keys(reasoning.result?.probabilityDistribution ?? {}).length > 0" class="p-6 rounded-xl border border-gold-500/20 bg-ink-900/50 backdrop-blur-sm">
            <h3 class="text-gold-500 font-medium mb-4">概率分布</h3>
            <div class="space-y-2">
              <div
                v-for="(prob, outcome) in reasoning.result?.probabilityDistribution ?? {}"
                :key="outcome"
                class="flex items-center gap-3"
              >
                <span class="text-gold-500/70 text-sm w-24">{{ outcome }}</span>
                <div class="flex-1 h-4 rounded-full bg-ink-800 overflow-hidden">
                  <div
                    class="h-full bg-gradient-to-r from-gold-500/50 to-gold-500 rounded-full transition-all duration-500"
                    :style="{ width: `${prob * 100}%` }"
                  ></div>
                </div>
                <span class="text-gold-500/60 text-xs w-16 text-right">{{ (prob * 100).toFixed(1) }}%</span>
              </div>
            </div>
          </div>
        </div>
      </transition>

      <!-- 概率树结果 -->
      <transition
        enter-active-class="transition-all duration-700 ease-out"
        enter-from-class="opacity-0 translate-y-8"
        enter-to-class="opacity-100 translate-y-0"
      >
        <div v-if="reasoning.tree?.topPaths" class="mt-8 space-y-6">
          <!-- 树概览 -->
          <div class="p-6 rounded-xl border border-gold-500/20 bg-ink-900/50 backdrop-blur-sm">
            <h3 class="text-gold-500 font-medium mb-4">概率树概览</h3>
            <div class="grid grid-cols-2 md:grid-cols-4 gap-4">
              <div class="text-center">
                <p class="text-gold-500/50 text-xs">最大深度</p>
                <p class="text-gold-400 text-lg">{{ reasoning.tree?.maxDepth }}</p>
              </div>
              <div class="text-center">
                <p class="text-gold-500/50 text-xs">分支因子</p>
                <p class="text-gold-400 text-lg">{{ reasoning.tree?.branchFactor }}</p>
              </div>
              <div class="text-center">
                <p class="text-gold-500/50 text-xs">总路径数</p>
                <p class="text-gold-400 text-lg">{{ reasoning.tree?.totalPaths }}</p>
              </div>
              <div class="text-center">
                <p class="text-gold-500/50 text-xs">期望值</p>
                <p class="text-gold-400 text-lg">{{ reasoning.tree?.expectedValue?.toFixed(2) }}</p>
              </div>
            </div>
          </div>

          <!-- 风险评估 -->
          <div class="p-6 rounded-xl border border-gold-500/20 bg-ink-900/50 backdrop-blur-sm">
            <h3 class="text-gold-500 font-medium mb-4">风险评估</h3>
            <p class="text-gold-500/80 text-sm leading-relaxed">{{ reasoning.tree?.riskAssessment }}</p>
          </div>

          <!-- 最优路径 -->
          <div class="p-6 rounded-xl border border-gold-500/20 bg-ink-900/50 backdrop-blur-sm">
            <h3 class="text-gold-500 font-medium mb-4">最优路径 TOP {{ reasoning.tree?.topPaths?.length }}</h3>
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
                    v-for="(path, index) in reasoning.tree?.topPaths"
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
      </transition>
    </ResponsiveContainer>
  </div>
</template>

<script setup lang="ts">
import { ref, computed } from 'vue'
import { useReasoning } from '~/composables/useReasoning'
import { useNotification } from '~/composables/useNotification'

definePageMeta({})

const reasoning = useReasoning()
const notification = useNotification()

const hexagramName = ref('')
const questionType = ref('general')
const monthBranch = ref('')
const error = ref<string | null>(null)

const canSubmit = computed(() => hexagramName.value.trim().length > 0)

async function handleDeepReason() {
  if (!canSubmit.value) return

  error.value = null

  try {
    await reasoning.deepReason({
      hexagram_name: hexagramName.value,
      question_type: questionType.value,
      month_branch: monthBranch.value || undefined,
      max_steps: 10,
    })
    notification.success('推理完成', '深度推理已完成，请查看结果')
  } catch (err) {
    error.value = err instanceof Error ? err.message : '推理失败'
    notification.error('推理失败', error.value)
  }
}

async function handleBuildTree() {
  if (!canSubmit.value) return

  error.value = null

  try {
    await reasoning.buildTree({
      hexagram_name: hexagramName.value,
      question_type: questionType.value,
      month_branch: monthBranch.value || undefined,
      max_depth: 5,
    })
    notification.success('构建完成', '概率树已生成，请查看结果')
  } catch (err) {
    error.value = err instanceof Error ? err.message : '构建概率树失败'
    notification.error('构建失败', error.value)
  }
}
</script>
