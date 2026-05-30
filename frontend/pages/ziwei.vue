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
          >
            <option value="male">男</option>
            <option value="female">女</option>
          </Select>
        </div>
        <div class="mt-4">
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
        </div>
      </div>

      <!-- 操作按钮 -->
      <div class="flex justify-center gap-4 mb-12">
        <button
          :disabled="!canSubmit || ziwei.loading"
          @click="handleCreateChart"
          :class="[
            'px-8 py-3 rounded-xl font-medium transition-all duration-300',
            'border-2 border-gold-500 text-gold-500',
            canSubmit && !ziwei.loading
              ? 'bg-gold-500/10 hover:bg-gold-500/20 hover:shadow-lg hover:shadow-gold-500/20 active:scale-95'
              : 'bg-ink-800/50 text-gold-500/40 cursor-not-allowed'
          ]"
        >
          <span v-if="ziwei.loading" class="flex items-center gap-2">
            <svg class="animate-spin h-5 w-5" viewBox="0 0 24 24">
              <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4" fill="none"></circle>
              <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
            </svg>
            排盘中...
          </span>
          <span v-else>排盘</span>
        </button>
        <button
          :disabled="!canSubmit || ziwei.loading"
          @click="handleAnalyze"
          :class="[
            'px-8 py-3 rounded-xl font-medium transition-all duration-300',
            'border-2 border-gold-500/50 text-gold-500/80',
            canSubmit && !ziwei.loading
              ? 'bg-ink-800/50 hover:bg-gold-500/10 hover:border-gold-500 active:scale-95'
              : 'bg-ink-800/50 text-gold-500/40 cursor-not-allowed'
          ]"
        >
          分析
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
          @retry="handleCreateChart"
        />
      </transition>

      <!-- 加载状态 -->
      <transition
        enter-active-class="transition-all duration-500"
        enter-from-class="opacity-0"
        enter-to-class="opacity-100"
      >
        <div v-if="ziwei.loading" class="mt-8">
          <LoadingSpinner text="正在排盘，请稍候..." />
        </div>
      </transition>

      <!-- 命盘结果 -->
      <transition
        enter-active-class="transition-all duration-700 ease-out"
        enter-from-class="opacity-0 translate-y-8"
        enter-to-class="opacity-100 translate-y-0"
      >
        <div v-if="ziwei.chart" class="mt-8 space-y-6">
          <!-- 基本信息 -->
          <div class="p-6 rounded-xl border border-gold-500/20 bg-ink-900/50 backdrop-blur-sm">
            <h3 class="text-gold-500 font-medium mb-4">基本信息</h3>
            <div class="grid grid-cols-2 md:grid-cols-4 gap-4">
              <div class="text-center">
                <p class="text-gold-500/50 text-xs">年柱</p>
                <p class="text-gold-400 text-lg font-chinese">{{ ziwei.chart?.yearGanZhi }}</p>
              </div>
              <div class="text-center">
                <p class="text-gold-500/50 text-xs">月柱</p>
                <p class="text-gold-400 text-lg font-chinese">{{ ziwei.chart?.monthGanZhi }}</p>
              </div>
              <div class="text-center">
                <p class="text-gold-500/50 text-xs">日柱</p>
                <p class="text-gold-400 text-lg font-chinese">{{ ziwei.chart?.dayGanZhi }}</p>
              </div>
              <div class="text-center">
                <p class="text-gold-500/50 text-xs">时柱</p>
                <p class="text-gold-400 text-lg font-chinese">{{ ziwei.chart?.hourGanZhi }}</p>
              </div>
            </div>
            <div class="mt-4 flex flex-wrap gap-2">
              <span class="px-3 py-1 rounded-md bg-gold-500/10 text-gold-500/80 text-xs">
                {{ ziwei.chart?.gender === 'male' ? '男' : '女' }}命
              </span>
              <span class="px-3 py-1 rounded-md bg-gold-500/10 text-gold-500/80 text-xs">
                {{ ziwei.chart?.wuXingJu }}
              </span>
              <span class="px-3 py-1 rounded-md bg-blue-500/10 text-blue-400 text-xs">
                命宫: {{ ziwei.chart?.mingPalace }}
              </span>
              <span class="px-3 py-1 rounded-md bg-purple-500/10 text-purple-400 text-xs">
                身宫: {{ ziwei.chart?.shenPalace }}
              </span>
            </div>
          </div>

          <!-- 十二宫格 -->
          <div class="p-6 rounded-xl border border-gold-500/20 bg-ink-900/50 backdrop-blur-sm">
            <h3 class="text-gold-500 font-medium mb-4">十二宫命盘</h3>
            <div class="grid grid-cols-4 gap-2 max-w-2xl mx-auto">
              <!-- 巳宫 -->
              <div class="p-3 rounded-lg border border-gold-500/20 bg-ink-800/50 min-h-[100px]">
                <div class="flex justify-between items-start mb-2">
                  <span class="text-gold-500/50 text-xs">巳</span>
                  <span class="text-gold-400 text-xs font-chinese">{{ getPalaceByPosition('巳')?.palace || '' }}</span>
                </div>
                <div class="space-y-1">
                  <p class="text-gold-500/80 text-xs font-chinese truncate">
                    {{ getPalaceByPosition('巳')?.mainStars?.join(' ') || '' }}
                  </p>
                  <p class="text-gold-500/60 text-xs truncate">
                    {{ getPalaceByPosition('巳')?.brightness || '' }}
                  </p>
                </div>
              </div>
              <!-- 午宫 -->
              <div class="p-3 rounded-lg border border-gold-500/20 bg-ink-800/50 min-h-[100px]">
                <div class="flex justify-between items-start mb-2">
                  <span class="text-gold-500/50 text-xs">午</span>
                  <span class="text-gold-400 text-xs font-chinese">{{ getPalaceByPosition('午')?.palace || '' }}</span>
                </div>
                <div class="space-y-1">
                  <p class="text-gold-500/80 text-xs font-chinese truncate">
                    {{ getPalaceByPosition('午')?.mainStars?.join(' ') || '' }}
                  </p>
                  <p class="text-gold-500/60 text-xs truncate">
                    {{ getPalaceByPosition('午')?.brightness || '' }}
                  </p>
                </div>
              </div>
              <!-- 未宫 -->
              <div class="p-3 rounded-lg border border-gold-500/20 bg-ink-800/50 min-h-[100px]">
                <div class="flex justify-between items-start mb-2">
                  <span class="text-gold-500/50 text-xs">未</span>
                  <span class="text-gold-400 text-xs font-chinese">{{ getPalaceByPosition('未')?.palace || '' }}</span>
                </div>
                <div class="space-y-1">
                  <p class="text-gold-500/80 text-xs font-chinese truncate">
                    {{ getPalaceByPosition('未')?.mainStars?.join(' ') || '' }}
                  </p>
                  <p class="text-gold-500/60 text-xs truncate">
                    {{ getPalaceByPosition('未')?.brightness || '' }}
                  </p>
                </div>
              </div>
              <!-- 申宫 -->
              <div class="p-3 rounded-lg border border-gold-500/20 bg-ink-800/50 min-h-[100px]">
                <div class="flex justify-between items-start mb-2">
                  <span class="text-gold-500/50 text-xs">申</span>
                  <span class="text-gold-400 text-xs font-chinese">{{ getPalaceByPosition('申')?.palace || '' }}</span>
                </div>
                <div class="space-y-1">
                  <p class="text-gold-500/80 text-xs font-chinese truncate">
                    {{ getPalaceByPosition('申')?.mainStars?.join(' ') || '' }}
                  </p>
                  <p class="text-gold-500/60 text-xs truncate">
                    {{ getPalaceByPosition('申')?.brightness || '' }}
                  </p>
                </div>
              </div>
              <!-- 辰宫 -->
              <div class="p-3 rounded-lg border border-gold-500/20 bg-ink-800/50 min-h-[100px]">
                <div class="flex justify-between items-start mb-2">
                  <span class="text-gold-500/50 text-xs">辰</span>
                  <span class="text-gold-400 text-xs font-chinese">{{ getPalaceByPosition('辰')?.palace || '' }}</span>
                </div>
                <div class="space-y-1">
                  <p class="text-gold-500/80 text-xs font-chinese truncate">
                    {{ getPalaceByPosition('辰')?.mainStars?.join(' ') || '' }}
                  </p>
                  <p class="text-gold-500/60 text-xs truncate">
                    {{ getPalaceByPosition('辰')?.brightness || '' }}
                  </p>
                </div>
              </div>
              <!-- 中宫 -->
              <div class="col-span-2 p-3 rounded-lg border border-gold-500/30 bg-gold-500/10 min-h-[100px] flex flex-col justify-center items-center">
                <p class="text-gold-500/80 text-sm font-chinese mb-2">{{ ziwei.chart?.wuXingJu }}</p>
                <p class="text-gold-500/50 text-xs">{{ ziwei.chart?.gender === 'male' ? '男' : '女' }}命</p>
                <p class="text-gold-500/50 text-xs mt-1">命宫: {{ ziwei.chart?.mingPalace }}</p>
              </div>
              <!-- 酉宫 -->
              <div class="p-3 rounded-lg border border-gold-500/20 bg-ink-800/50 min-h-[100px]">
                <div class="flex justify-between items-start mb-2">
                  <span class="text-gold-500/50 text-xs">酉</span>
                  <span class="text-gold-400 text-xs font-chinese">{{ getPalaceByPosition('酉')?.palace || '' }}</span>
                </div>
                <div class="space-y-1">
                  <p class="text-gold-500/80 text-xs font-chinese truncate">
                    {{ getPalaceByPosition('酉')?.mainStars?.join(' ') || '' }}
                  </p>
                  <p class="text-gold-500/60 text-xs truncate">
                    {{ getPalaceByPosition('酉')?.brightness || '' }}
                  </p>
                </div>
              </div>
              <!-- 卯宫 -->
              <div class="p-3 rounded-lg border border-gold-500/20 bg-ink-800/50 min-h-[100px]">
                <div class="flex justify-between items-start mb-2">
                  <span class="text-gold-500/50 text-xs">卯</span>
                  <span class="text-gold-400 text-xs font-chinese">{{ getPalaceByPosition('卯')?.palace || '' }}</span>
                </div>
                <div class="space-y-1">
                  <p class="text-gold-500/80 text-xs font-chinese truncate">
                    {{ getPalaceByPosition('卯')?.mainStars?.join(' ') || '' }}
                  </p>
                  <p class="text-gold-500/60 text-xs truncate">
                    {{ getPalaceByPosition('卯')?.brightness || '' }}
                  </p>
                </div>
              </div>
              <!-- 戌宫 -->
              <div class="p-3 rounded-lg border border-gold-500/20 bg-ink-800/50 min-h-[100px]">
                <div class="flex justify-between items-start mb-2">
                  <span class="text-gold-500/50 text-xs">戌</span>
                  <span class="text-gold-400 text-xs font-chinese">{{ getPalaceByPosition('戌')?.palace || '' }}</span>
                </div>
                <div class="space-y-1">
                  <p class="text-gold-500/80 text-xs font-chinese truncate">
                    {{ getPalaceByPosition('戌')?.mainStars?.join(' ') || '' }}
                  </p>
                  <p class="text-gold-500/60 text-xs truncate">
                    {{ getPalaceByPosition('戌')?.brightness || '' }}
                  </p>
                </div>
              </div>
              <!-- 亥宫 -->
              <div class="p-3 rounded-lg border border-gold-500/20 bg-ink-800/50 min-h-[100px]">
                <div class="flex justify-between items-start mb-2">
                  <span class="text-gold-500/50 text-xs">亥</span>
                  <span class="text-gold-400 text-xs font-chinese">{{ getPalaceByPosition('亥')?.palace || '' }}</span>
                </div>
                <div class="space-y-1">
                  <p class="text-gold-500/80 text-xs font-chinese truncate">
                    {{ getPalaceByPosition('亥')?.mainStars?.join(' ') || '' }}
                  </p>
                  <p class="text-gold-500/60 text-xs truncate">
                    {{ getPalaceByPosition('亥')?.brightness || '' }}
                  </p>
                </div>
              </div>
              <!-- 寅宫 -->
              <div class="p-3 rounded-lg border border-gold-500/20 bg-ink-800/50 min-h-[100px]">
                <div class="flex justify-between items-start mb-2">
                  <span class="text-gold-500/50 text-xs">寅</span>
                  <span class="text-gold-400 text-xs font-chinese">{{ getPalaceByPosition('寅')?.palace || '' }}</span>
                </div>
                <div class="space-y-1">
                  <p class="text-gold-500/80 text-xs font-chinese truncate">
                    {{ getPalaceByPosition('寅')?.mainStars?.join(' ') || '' }}
                  </p>
                  <p class="text-gold-500/60 text-xs truncate">
                    {{ getPalaceByPosition('寅')?.brightness || '' }}
                  </p>
                </div>
              </div>
              <!-- 丑宫 -->
              <div class="p-3 rounded-lg border border-gold-500/20 bg-ink-800/50 min-h-[100px]">
                <div class="flex justify-between items-start mb-2">
                  <span class="text-gold-500/50 text-xs">丑</span>
                  <span class="text-gold-400 text-xs font-chinese">{{ getPalaceByPosition('丑')?.palace || '' }}</span>
                </div>
                <div class="space-y-1">
                  <p class="text-gold-500/80 text-xs font-chinese truncate">
                    {{ getPalaceByPosition('丑')?.mainStars?.join(' ') || '' }}
                  </p>
                  <p class="text-gold-500/60 text-xs truncate">
                    {{ getPalaceByPosition('丑')?.brightness || '' }}
                  </p>
                </div>
              </div>
              <!-- 子宫 -->
              <div class="p-3 rounded-lg border border-gold-500/20 bg-ink-800/50 min-h-[100px]">
                <div class="flex justify-between items-start mb-2">
                  <span class="text-gold-500/50 text-xs">子</span>
                  <span class="text-gold-400 text-xs font-chinese">{{ getPalaceByPosition('子')?.palace || '' }}</span>
                </div>
                <div class="space-y-1">
                  <p class="text-gold-500/80 text-xs font-chinese truncate">
                    {{ getPalaceByPosition('子')?.mainStars?.join(' ') || '' }}
                  </p>
                  <p class="text-gold-500/60 text-xs truncate">
                    {{ getPalaceByPosition('子')?.brightness || '' }}
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
                    v-for="palace in ziwei.chart?.palaces ?? []"
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
      </transition>

      <!-- 分析结果 -->
      <transition
        enter-active-class="transition-all duration-700 ease-out delay-200"
        enter-from-class="opacity-0 translate-y-8"
        enter-to-class="opacity-100 translate-y-0"
      >
        <div v-if="ziwei.analysis" class="mt-8 space-y-6">
          <!-- 分析目标 -->
          <div class="p-6 rounded-xl border border-gold-500/20 bg-ink-900/50 backdrop-blur-sm">
            <h3 class="text-gold-500 font-medium mb-4">分析目标</h3>
            <div class="grid grid-cols-1 md:grid-cols-3 gap-4">
              <div class="p-4 rounded-lg border border-gold-500/10 bg-ink-800/30">
                <p class="text-gold-500/50 text-xs mb-1">目标宫位</p>
                <p class="text-gold-400 text-lg font-chinese">{{ ziwei.analysis.targetPalace }}</p>
              </div>
              <div class="p-4 rounded-lg border border-gold-500/10 bg-ink-800/30">
                <p class="text-gold-500/50 text-xs mb-1">主星</p>
                <p class="text-gold-400 text-lg font-chinese">{{ ziwei.analysis?.mainStars?.join(', ') }}</p>
              </div>
              <div class="p-4 rounded-lg border border-gold-500/10 bg-ink-800/30">
                <p class="text-gold-500/50 text-xs mb-1">化曜影响</p>
                <p class="text-gold-400 text-lg font-chinese">{{ ziwei.analysis?.huaInfluence?.join(', ') || '无' }}</p>
              </div>
            </div>
          </div>

          <!-- 分析描述 -->
          <div class="p-6 rounded-xl border border-gold-500/20 bg-ink-900/50 backdrop-blur-sm">
            <h3 class="text-gold-500 font-medium mb-4">分析结果</h3>
            <p class="text-gold-500/80 text-sm leading-relaxed mb-6">{{ ziwei.analysis.description }}</p>

            <!-- 判定 -->
            <div class="grid grid-cols-2 md:grid-cols-4 gap-4">
              <div class="p-4 rounded-lg border border-gold-500/10 bg-ink-800/30 text-center">
                <p class="text-gold-500/50 text-xs mb-1">总体</p>
                <p class="text-gold-400 text-lg font-chinese">{{ ziwei.analysis?.verdict?.overall }}</p>
              </div>
              <div class="p-4 rounded-lg border border-gold-500/10 bg-ink-800/30 text-center">
                <p class="text-gold-500/50 text-xs mb-1">力量</p>
                <p class="text-gold-400 text-lg font-chinese">{{ ziwei.analysis?.verdict?.strength }}</p>
              </div>
              <div class="p-4 rounded-lg border border-gold-500/10 bg-ink-800/30 text-center">
                <p class="text-gold-500/50 text-xs mb-1">趋势</p>
                <p class="text-gold-400 text-lg font-chinese">{{ ziwei.analysis?.verdict?.trend }}</p>
              </div>
              <div class="p-4 rounded-lg border border-gold-500/10 bg-ink-800/30 text-center">
                <p class="text-gold-500/50 text-xs mb-1">置信度</p>
                <p class="text-gold-400 text-lg">{{ (ziwei.analysis?.verdict?.confidence * 100).toFixed(1) }}%</p>
              </div>
            </div>
          </div>
        </div>
      </transition>
    </ResponsiveContainer>
  </div>
</template>

<script setup lang="ts">
import { ref, computed } from 'vue'
import { useZiWei } from '~/composables/useZiWei'
import { useNotification } from '~/composables/useNotification'
import { isValidDate } from '~/utils/format'

definePageMeta({})

const ziwei = useZiWei()
const notification = useNotification()

const year = ref(new Date().getFullYear())
const month = ref(new Date().getMonth() + 1)
const day = ref(new Date().getDate())
const hour = ref(new Date().getHours())
const gender = ref('male')
const questionType = ref('general')
const error = ref<string | null>(null)

const canSubmit = computed(() => {
  return year.value > 0 && isValidDate(year.value, month.value, day.value) && hour.value >= 0 && hour.value <= 23
})

// 地支顺序
const diZhiOrder = ['子', '丑', '寅', '卯', '辰', '巳', '午', '未', '申', '酉', '戌', '亥']

function getPalaceByPosition(dizhi: string) {
  if (!ziwei.chart?.palaces) return null
  const index = diZhiOrder.indexOf(dizhi)
  if (index === -1) return null
  return ziwei.chart?.palaces?.[index]
}

async function handleCreateChart() {
  if (!canSubmit.value) return

  error.value = null

  try {
    await ziwei.createChart({
      year: year.value,
      month: month.value,
      day: day.value,
      hour: hour.value,
      gender: gender.value,
    })
    notification.success('排盘完成', '紫微命盘已生成')
  } catch (err) {
    error.value = err instanceof Error ? err.message : '排盘失败'
    notification.error('排盘失败', error.value)
  }
}

async function handleAnalyze() {
  if (!canSubmit.value) return

  error.value = null

  try {
    await ziwei.analyze({
      year: year.value,
      month: month.value,
      day: day.value,
      hour: hour.value,
      gender: gender.value,
      question_type: questionType.value,
    })
    notification.success('分析完成', '紫微分析已完成')
  } catch (err) {
    error.value = err instanceof Error ? err.message : '分析失败'
    notification.error('分析失败', error.value)
  }
}
</script>
