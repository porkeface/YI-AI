<template>
  <div class="min-h-screen py-8 relative">
    <!-- 背景装饰 -->
    <div class="fixed inset-0 pointer-events-none overflow-hidden">
      <div class="absolute top-1/4 -left-32 w-96 h-96 bg-gold-500/5 rounded-full blur-3xl"></div>
      <div class="absolute bottom-1/4 -right-32 w-96 h-96 bg-gold-500/3 rounded-full blur-3xl"></div>
    </div>

    <SeoHead title="奇门遁甲" description="奇门遁甲排盘与分析" />

    <ResponsiveContainer max-width="lg" class="relative z-10">
      <!-- 页面标题 -->
      <div class="text-center mb-10">
        <h1 class="text-4xl font-bold text-gold-500 text-glow-gold font-chinese mb-3">
          奇门遁甲
        </h1>
        <p class="text-gold-500/50 text-sm">时空能量场分析系统</p>
        <div class="w-16 h-px bg-gradient-to-r from-transparent via-gold-500/50 to-transparent mx-auto mt-4"></div>
      </div>

      <!-- 输入区域 -->
      <div class="mb-8 p-6 rounded-xl border border-gold-500/20 bg-ink-900/50 backdrop-blur-sm">
        <h2 class="text-gold-500/80 text-sm mb-4 font-medium">起局参数</h2>
        <div class="grid grid-cols-2 md:grid-cols-4 gap-4">
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
          :disabled="!canSubmit || qimen.loading"
          @click="handleCreateChart"
          :class="[
            'px-8 py-3 rounded-xl font-medium transition-all duration-300',
            'border-2 border-gold-500 text-gold-500',
            canSubmit && !qimen.loading
              ? 'bg-gold-500/10 hover:bg-gold-500/20 hover:shadow-lg hover:shadow-gold-500/20 active:scale-95'
              : 'bg-ink-800/50 text-gold-500/40 cursor-not-allowed'
          ]"
        >
          <span v-if="qimen.loading" class="flex items-center gap-2">
            <svg class="animate-spin h-5 w-5" viewBox="0 0 24 24">
              <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4" fill="none"></circle>
              <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
            </svg>
            起局中...
          </span>
          <span v-else>起局</span>
        </button>
        <button
          :disabled="!canSubmit || qimen.loading"
          @click="handleAnalyze"
          :class="[
            'px-8 py-3 rounded-xl font-medium transition-all duration-300',
            'border-2 border-gold-500/50 text-gold-500/80',
            canSubmit && !qimen.loading
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
        <div v-if="qimen.loading" class="mt-8">
          <LoadingSpinner text="正在起局，请稍候..." />
        </div>
      </transition>

      <!-- 奇门盘结果 -->
      <transition
        enter-active-class="transition-all duration-700 ease-out"
        enter-from-class="opacity-0 translate-y-8"
        enter-to-class="opacity-100 translate-y-0"
      >
        <div v-if="qimen.chart" class="mt-8 space-y-6">
          <!-- 干支信息 -->
          <div class="p-6 rounded-xl border border-gold-500/20 bg-ink-900/50 backdrop-blur-sm">
            <h3 class="text-gold-500 font-medium mb-4">干支信息</h3>
            <div class="grid grid-cols-2 md:grid-cols-5 gap-4">
              <div class="text-center">
                <p class="text-gold-500/50 text-xs">年柱</p>
                <p class="text-gold-400 text-lg font-chinese">{{ qimen.chart.yearGanZhi }}</p>
              </div>
              <div class="text-center">
                <p class="text-gold-500/50 text-xs">月柱</p>
                <p class="text-gold-400 text-lg font-chinese">{{ qimen.chart.monthGanZhi }}</p>
              </div>
              <div class="text-center">
                <p class="text-gold-500/50 text-xs">日柱</p>
                <p class="text-gold-400 text-lg font-chinese">{{ qimen.chart.dayGanZhi }}</p>
              </div>
              <div class="text-center">
                <p class="text-gold-500/50 text-xs">时柱</p>
                <p class="text-gold-400 text-lg font-chinese">{{ qimen.chart.hourGanZhi }}</p>
              </div>
              <div class="text-center">
                <p class="text-gold-500/50 text-xs">局数</p>
                <p class="text-gold-400 text-lg">{{ qimen.chart.ju }}局</p>
              </div>
            </div>
            <div class="mt-4 flex flex-wrap gap-2">
              <span class="px-3 py-1 rounded-md bg-gold-500/10 text-gold-500/80 text-xs">
                {{ qimen.chart.yinYang }}
              </span>
              <span class="px-3 py-1 rounded-md bg-gold-500/10 text-gold-500/80 text-xs">
                {{ qimen.chart.dun }}
              </span>
              <span
                v-for="kong in qimen.chart.xunKong"
                :key="kong"
                class="px-3 py-1 rounded-md bg-red-500/10 text-red-400 text-xs"
              >
                空亡: {{ kong }}
              </span>
              <span
                v-for="ma in qimen.chart.maXing"
                :key="ma"
                class="px-3 py-1 rounded-md bg-blue-500/10 text-blue-400 text-xs"
              >
                马星: {{ ma }}
              </span>
            </div>
          </div>

          <!-- 九宫格 -->
          <div class="p-6 rounded-xl border border-gold-500/20 bg-ink-900/50 backdrop-blur-sm">
            <h3 class="text-gold-500 font-medium mb-4">九宫奇门盘</h3>
            <div class="grid grid-cols-3 gap-2 max-w-md mx-auto">
              <!-- 巽四宫 -->
              <div class="p-3 rounded-lg border border-gold-500/20 bg-ink-800/50 aspect-square flex flex-col justify-center items-center">
                <p class="text-gold-500/50 text-xs mb-1">巽四</p>
                <p class="text-gold-400 text-sm font-chinese">{{ getPalace(4)?.door || '-' }}</p>
                <p class="text-gold-500/80 text-xs">{{ getPalace(4)?.star || '-' }}</p>
                <p class="text-gold-500/60 text-xs">{{ getPalace(4)?.spirit || '-' }}</p>
              </div>
              <!-- 离九宫 -->
              <div class="p-3 rounded-lg border border-gold-500/20 bg-ink-800/50 aspect-square flex flex-col justify-center items-center">
                <p class="text-gold-500/50 text-xs mb-1">离九</p>
                <p class="text-gold-400 text-sm font-chinese">{{ getPalace(9)?.door || '-' }}</p>
                <p class="text-gold-500/80 text-xs">{{ getPalace(9)?.star || '-' }}</p>
                <p class="text-gold-500/60 text-xs">{{ getPalace(9)?.spirit || '-' }}</p>
              </div>
              <!-- 坤二宫 -->
              <div class="p-3 rounded-lg border border-gold-500/20 bg-ink-800/50 aspect-square flex flex-col justify-center items-center">
                <p class="text-gold-500/50 text-xs mb-1">坤二</p>
                <p class="text-gold-400 text-sm font-chinese">{{ getPalace(2)?.door || '-' }}</p>
                <p class="text-gold-500/80 text-xs">{{ getPalace(2)?.star || '-' }}</p>
                <p class="text-gold-500/60 text-xs">{{ getPalace(2)?.spirit || '-' }}</p>
              </div>
              <!-- 震三宫 -->
              <div class="p-3 rounded-lg border border-gold-500/20 bg-ink-800/50 aspect-square flex flex-col justify-center items-center">
                <p class="text-gold-500/50 text-xs mb-1">震三</p>
                <p class="text-gold-400 text-sm font-chinese">{{ getPalace(3)?.door || '-' }}</p>
                <p class="text-gold-500/80 text-xs">{{ getPalace(3)?.star || '-' }}</p>
                <p class="text-gold-500/60 text-xs">{{ getPalace(3)?.spirit || '-' }}</p>
              </div>
              <!-- 中五宫 -->
              <div class="p-3 rounded-lg border border-gold-500/30 bg-gold-500/10 aspect-square flex flex-col justify-center items-center">
                <p class="text-gold-500/50 text-xs mb-1">中五</p>
                <p class="text-gold-400 text-sm font-chinese">{{ getPalace(5)?.door || '-' }}</p>
                <p class="text-gold-500/80 text-xs">{{ getPalace(5)?.star || '-' }}</p>
                <p class="text-gold-500/60 text-xs">{{ getPalace(5)?.spirit || '-' }}</p>
              </div>
              <!-- 兑七宫 -->
              <div class="p-3 rounded-lg border border-gold-500/20 bg-ink-800/50 aspect-square flex flex-col justify-center items-center">
                <p class="text-gold-500/50 text-xs mb-1">兑七</p>
                <p class="text-gold-400 text-sm font-chinese">{{ getPalace(7)?.door || '-' }}</p>
                <p class="text-gold-500/80 text-xs">{{ getPalace(7)?.star || '-' }}</p>
                <p class="text-gold-500/60 text-xs">{{ getPalace(7)?.spirit || '-' }}</p>
              </div>
              <!-- 艮八宫 -->
              <div class="p-3 rounded-lg border border-gold-500/20 bg-ink-800/50 aspect-square flex flex-col justify-center items-center">
                <p class="text-gold-500/50 text-xs mb-1">艮八</p>
                <p class="text-gold-400 text-sm font-chinese">{{ getPalace(8)?.door || '-' }}</p>
                <p class="text-gold-500/80 text-xs">{{ getPalace(8)?.star || '-' }}</p>
                <p class="text-gold-500/60 text-xs">{{ getPalace(8)?.spirit || '-' }}</p>
              </div>
              <!-- 坎一宫 -->
              <div class="p-3 rounded-lg border border-gold-500/20 bg-ink-800/50 aspect-square flex flex-col justify-center items-center">
                <p class="text-gold-500/50 text-xs mb-1">坎一</p>
                <p class="text-gold-400 text-sm font-chinese">{{ getPalace(1)?.door || '-' }}</p>
                <p class="text-gold-500/80 text-xs">{{ getPalace(1)?.star || '-' }}</p>
                <p class="text-gold-500/60 text-xs">{{ getPalace(1)?.spirit || '-' }}</p>
              </div>
              <!-- 乾六宫 -->
              <div class="p-3 rounded-lg border border-gold-500/20 bg-ink-800/50 aspect-square flex flex-col justify-center items-center">
                <p class="text-gold-500/50 text-xs mb-1">乾六</p>
                <p class="text-gold-400 text-sm font-chinese">{{ getPalace(6)?.door || '-' }}</p>
                <p class="text-gold-500/80 text-xs">{{ getPalace(6)?.star || '-' }}</p>
                <p class="text-gold-500/60 text-xs">{{ getPalace(6)?.spirit || '-' }}</p>
              </div>
            </div>
          </div>

          <!-- 详细宫位信息 -->
          <div class="p-6 rounded-xl border border-gold-500/20 bg-ink-900/50 backdrop-blur-sm">
            <h3 class="text-gold-500 font-medium mb-4">宫位详情</h3>
            <div class="overflow-x-auto">
              <table class="w-full">
                <thead>
                  <tr class="border-b border-gold-500/20">
                    <th class="text-left text-gold-500/60 text-xs py-2 px-3">宫位</th>
                    <th class="text-left text-gold-500/60 text-xs py-2 px-3">门</th>
                    <th class="text-left text-gold-500/60 text-xs py-2 px-3">星</th>
                    <th class="text-left text-gold-500/60 text-xs py-2 px-3">神</th>
                    <th class="text-left text-gold-500/60 text-xs py-2 px-3">天盘</th>
                    <th class="text-left text-gold-500/60 text-xs py-2 px-3">地盘</th>
                    <th class="text-left text-gold-500/60 text-xs py-2 px-3">状态</th>
                  </tr>
                </thead>
                <tbody>
                  <tr
                    v-for="palace in qimen.chart.palaceInfo"
                    :key="palace.palace"
                    class="border-b border-gold-500/10 hover:bg-gold-500/5"
                  >
                    <td class="py-3 px-3 text-gold-400 text-sm">{{ palace.palace }}宫</td>
                    <td class="py-3 px-3 text-gold-500/80 text-sm font-chinese">{{ palace.door }}</td>
                    <td class="py-3 px-3 text-gold-500/80 text-sm font-chinese">{{ palace.star }}</td>
                    <td class="py-3 px-3 text-gold-500/80 text-sm font-chinese">{{ palace.spirit }}</td>
                    <td class="py-3 px-3 text-gold-500/80 text-sm font-chinese">{{ palace.tianPan }}</td>
                    <td class="py-3 px-3 text-gold-500/80 text-sm font-chinese">{{ palace.diPan }}</td>
                    <td class="py-3 px-3">
                      <div class="flex gap-1">
                        <span v-if="palace.isShi" class="px-1 py-0.5 rounded bg-gold-500/20 text-gold-400 text-xs">值</span>
                        <span v-if="palace.isFuxing" class="px-1 py-0.5 rounded bg-blue-500/20 text-blue-400 text-xs">符</span>
                        <span v-if="palace.isFanin" class="px-1 py-0.5 rounded bg-red-500/20 text-red-400 text-xs">反</span>
                      </div>
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
        <div v-if="qimen.analysis" class="mt-8 space-y-6">
          <!-- 用神信息 -->
          <div class="p-6 rounded-xl border border-gold-500/20 bg-ink-900/50 backdrop-blur-sm">
            <h3 class="text-gold-500 font-medium mb-4">用神分析</h3>
            <div class="grid grid-cols-1 md:grid-cols-3 gap-4">
              <div class="p-4 rounded-lg border border-gold-500/10 bg-ink-800/30">
                <p class="text-gold-500/50 text-xs mb-1">用神宫位</p>
                <p class="text-gold-400 text-lg">{{ qimen.analysis.yongShenPalace }}宫</p>
              </div>
              <div class="p-4 rounded-lg border border-gold-500/10 bg-ink-800/30">
                <p class="text-gold-500/50 text-xs mb-1">用神门</p>
                <p class="text-gold-400 text-lg font-chinese">{{ qimen.analysis.yongShenDoor }}</p>
              </div>
              <div class="p-4 rounded-lg border border-gold-500/10 bg-ink-800/30">
                <p class="text-gold-500/50 text-xs mb-1">用神星</p>
                <p class="text-gold-400 text-lg font-chinese">{{ qimen.analysis.yongShenStar }}</p>
              </div>
            </div>
          </div>

          <!-- 分析描述 -->
          <div class="p-6 rounded-xl border border-gold-500/20 bg-ink-900/50 backdrop-blur-sm">
            <h3 class="text-gold-500 font-medium mb-4">分析结果</h3>
            <p class="text-gold-500/80 text-sm leading-relaxed mb-6">{{ qimen.analysis.description }}</p>

            <!-- 判定 -->
            <div class="grid grid-cols-2 md:grid-cols-4 gap-4">
              <div class="p-4 rounded-lg border border-gold-500/10 bg-ink-800/30 text-center">
                <p class="text-gold-500/50 text-xs mb-1">总体</p>
                <p class="text-gold-400 text-lg font-chinese">{{ qimen.analysis.verdict.overall }}</p>
              </div>
              <div class="p-4 rounded-lg border border-gold-500/10 bg-ink-800/30 text-center">
                <p class="text-gold-500/50 text-xs mb-1">力量</p>
                <p class="text-gold-400 text-lg font-chinese">{{ qimen.analysis.verdict.strength }}</p>
              </div>
              <div class="p-4 rounded-lg border border-gold-500/10 bg-ink-800/30 text-center">
                <p class="text-gold-500/50 text-xs mb-1">趋势</p>
                <p class="text-gold-400 text-lg font-chinese">{{ qimen.analysis.verdict.trend }}</p>
              </div>
              <div class="p-4 rounded-lg border border-gold-500/10 bg-ink-800/30 text-center">
                <p class="text-gold-500/50 text-xs mb-1">置信度</p>
                <p class="text-gold-400 text-lg">{{ (qimen.analysis.verdict.confidence * 100).toFixed(1) }}%</p>
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
import { useQiMen } from '~/composables/useQiMen'
import { useNotification } from '~/composables/useNotification'

definePageMeta({
  middleware: 'auth',
})

const qimen = useQiMen()
const notification = useNotification()

const year = ref(new Date().getFullYear())
const month = ref(new Date().getMonth() + 1)
const day = ref(new Date().getDate())
const hour = ref(new Date().getHours())
const questionType = ref('general')
const error = ref<string | null>(null)

const canSubmit = computed(() => {
  return year.value > 0 && month.value > 0 && month.value <= 12 &&
         day.value > 0 && day.value <= 31 && hour.value >= 0 && hour.value <= 23
})

function getPalace(num: number) {
  return qimen.chart?.palaceInfo.find(p => p.palace === num)
}

async function handleCreateChart() {
  if (!canSubmit.value) return

  error.value = null

  try {
    await qimen.createChart({
      year: year.value,
      month: month.value,
      day: day.value,
      hour: hour.value,
    })
    notification.success('起局完成', '奇门盘已生成')
  } catch (err) {
    error.value = err instanceof Error ? err.message : '起局失败'
    notification.error('起局失败', error.value)
  }
}

async function handleAnalyze() {
  if (!canSubmit.value) return

  error.value = null

  try {
    await qimen.analyze({
      year: year.value,
      month: month.value,
      day: day.value,
      hour: hour.value,
      question_type: questionType.value,
    })
    notification.success('分析完成', '奇门分析已完成')
  } catch (err) {
    error.value = err instanceof Error ? err.message : '分析失败'
    notification.error('分析失败', error.value)
  }
}
</script>
