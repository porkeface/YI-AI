<template>
  <div class="min-h-screen py-8 px-4">
    <div class="max-w-6xl mx-auto">
      <SeoHead title="观察报告" description="用户行为模式观察与异常检测" />

      <!-- 页面标题 -->
      <div class="text-center mb-10">
        <h1 class="text-3xl font-bold text-gold-500 text-glow-gold font-chinese mb-3">
          观察报告
        </h1>
        <p class="text-gold-500/50 text-sm">用户行为模式分析与异常检测</p>
        <div class="w-16 h-px bg-gradient-to-r from-transparent via-gold-500/50 to-transparent mx-auto mt-4"></div>
      </div>

      <!-- 用户ID输入 -->
      <div class="mb-8 p-6 rounded-xl border border-gold-500/20 bg-ink-900/50 backdrop-blur-sm">
        <div class="flex gap-4 items-end">
          <div class="flex-1">
            <label class="block text-gold-500/80 text-sm mb-2 font-medium">用户ID</label>
            <InputField
              v-model="userId"
              placeholder="请输入用户ID..."
              label="用户ID"
            />
          </div>
          <Button
            variant="primary"
            :disabled="!userId || loading"
            @click="fetchPatterns"
          >
            查询模式
          </Button>
        </div>
      </div>

      <!-- Tab 切换 -->
      <div class="flex border-b border-gold-500/30 mb-6">
        <button
          v-for="tab in tabs"
          :key="tab.value"
          @click="activeTab = tab.value"
          :class="[
            'px-4 py-2 text-sm font-medium transition-colors duration-200 border-b-2 -mb-px',
            activeTab === tab.value
              ? 'border-gold-500 text-gold-500'
              : 'border-transparent text-gold-500/60 hover:text-gold-500/80',
          ]"
        >
          {{ tab.label }}
        </button>
      </div>

      <!-- 加载状态 -->
      <div v-if="loading" class="mt-8">
        <LoadingSpinner text="加载观察数据中..." />
      </div>

      <!-- 行为模式 Tab -->
      <div v-else-if="activeTab === 'patterns'">
        <div v-if="patterns.length === 0" class="text-center py-12">
          <EmptyState
            icon="📊"
            title="暂无模式数据"
            description="请输入用户ID查询行为模式"
          />
        </div>
        <div v-else class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          <div
            v-for="(pattern, index) in patterns"
            :key="index"
            class="p-5 rounded-xl border border-gold-500/20 bg-ink-900/50 backdrop-blur-sm hover:border-gold-500/40 transition-colors duration-200"
          >
            <div class="flex items-center gap-3 mb-3">
              <div class="w-10 h-10 rounded-lg bg-gold-500/10 flex items-center justify-center">
                <span class="text-gold-400 text-lg">{{ getPatternIcon(pattern.type) }}</span>
              </div>
              <div>
                <h3 class="text-gold-500 font-medium text-sm">{{ pattern.name }}</h3>
                <p class="text-gold-500/50 text-xs">{{ pattern.type }}</p>
              </div>
            </div>
            <p class="text-gold-500/70 text-sm mb-3">{{ pattern.description }}</p>
            <div class="flex items-center justify-between">
              <Badge :variant="getConfidenceVariant(pattern.confidence)">
                置信度 {{ (pattern.confidence * 100).toFixed(0) }}%
              </Badge>
              <span class="text-gold-500/40 text-xs">{{ formatDate(pattern.lastSeen) }}</span>
            </div>
          </div>
        </div>
      </div>

      <!-- 异常检测 Tab -->
      <div v-else-if="activeTab === 'anomalies'">
        <div class="mb-6 p-6 rounded-xl border border-gold-500/20 bg-ink-900/50 backdrop-blur-sm">
          <h3 class="text-gold-500 font-medium mb-4">异常检测配置</h3>
          <div class="grid grid-cols-1 md:grid-cols-3 gap-4">
            <div>
              <label class="block text-gold-500/80 text-sm mb-2">检测类型</label>
              <Select
                v-model="anomalyType"
                :options="anomalyTypeOptions"
              />
            </div>
            <div>
              <label class="block text-gold-500/80 text-sm mb-2">时间范围</label>
              <Select
                v-model="timeRange"
                :options="timeRangeOptions"
              />
            </div>
            <div class="flex items-end">
              <Button
                variant="primary"
                :disabled="loading"
                @click="checkAnomalies"
                class="w-full"
              >
                执行检测
              </Button>
            </div>
          </div>
        </div>

        <div v-if="anomalies.length === 0" class="text-center py-12">
          <EmptyState
            icon="🔍"
            title="暂无异常数据"
            description="点击执行检测按钮开始异常检测"
          />
        </div>
        <div v-else class="space-y-3">
          <div
            v-for="(anomaly, index) in anomalies"
            :key="index"
            class="p-4 rounded-xl border bg-ink-900/50 backdrop-blur-sm"
            :class="anomaly.severity === 'high' ? 'border-red-500/40' : anomaly.severity === 'medium' ? 'border-yellow-500/40' : 'border-gold-500/20'"
          >
            <div class="flex items-start justify-between">
              <div class="flex items-start gap-3">
                <div
                  class="w-8 h-8 rounded-full flex items-center justify-center mt-0.5"
                  :class="anomaly.severity === 'high' ? 'bg-red-500/20' : anomaly.severity === 'medium' ? 'bg-yellow-500/20' : 'bg-gold-500/20'"
                >
                  <span class="text-sm">{{ anomaly.severity === 'high' ? '⚠' : anomaly.severity === 'medium' ? '⚡' : 'ℹ' }}</span>
                </div>
                <div>
                  <h4 class="text-gold-500 font-medium text-sm">{{ anomaly.title }}</h4>
                  <p class="text-gold-500/60 text-xs mt-1">{{ anomaly.description }}</p>
                  <div class="flex items-center gap-3 mt-2">
                    <Badge :variant="anomaly.severity === 'high' ? 'error' : anomaly.severity === 'medium' ? 'warning' : 'info'">
                      {{ anomaly.severity === 'high' ? '高危' : anomaly.severity === 'medium' ? '中危' : '低危' }}
                    </Badge>
                    <span class="text-gold-500/40 text-xs">{{ anomaly.metric }}: {{ anomaly.value }}</span>
                  </div>
                </div>
              </div>
              <span class="text-gold-500/40 text-xs shrink-0">{{ formatDate(anomaly.timestamp) }}</span>
            </div>
          </div>
        </div>
      </div>

      <!-- 趋势报告 Tab -->
      <div v-else-if="activeTab === 'trends'">
        <div class="mb-6 p-6 rounded-xl border border-gold-500/20 bg-ink-900/50 backdrop-blur-sm">
          <h3 class="text-gold-500 font-medium mb-4">生成趋势报告</h3>
          <div class="grid grid-cols-1 md:grid-cols-2 gap-4 mb-4">
            <div>
              <label class="block text-gold-500/80 text-sm mb-2">分析周期</label>
              <Select
                v-model="trendPeriod"
                :options="trendPeriodOptions"
              />
            </div>
            <div>
              <label class="block text-gold-500/80 text-sm mb-2">指标类型</label>
              <Select
                v-model="trendMetric"
                :options="trendMetricOptions"
              />
            </div>
          </div>
          <Button
            variant="primary"
            :disabled="loading"
            @click="generateTrend"
          >
            生成报告
          </Button>
        </div>

        <div v-if="trendReport" class="space-y-6">
          <!-- 趋势概览 -->
          <div class="grid grid-cols-1 md:grid-cols-4 gap-4">
            <div
              v-for="(stat, index) in trendReport.summary"
              :key="index"
              class="p-4 rounded-xl border border-gold-500/20 bg-ink-900/50 backdrop-blur-sm text-center"
            >
              <p class="text-gold-500/60 text-xs mb-1">{{ stat.label }}</p>
              <p class="text-2xl font-bold text-gold-500">{{ stat.value }}</p>
              <div class="flex items-center justify-center gap-1 mt-1">
                <span
                  :class="stat.change >= 0 ? 'text-green-400' : 'text-red-400'"
                  class="text-xs"
                >
                  {{ stat.change >= 0 ? '↑' : '↓' }} {{ Math.abs(stat.change) }}%
                </span>
              </div>
            </div>
          </div>

          <!-- 趋势数据表格 -->
          <div class="p-6 rounded-xl border border-gold-500/20 bg-ink-900/50 backdrop-blur-sm">
            <h3 class="text-gold-500 font-medium mb-4">趋势详情</h3>
            <DataTable
              :columns="trendColumns"
              :data="trendReport.details"
            />
          </div>

          <!-- 洞察 -->
          <div class="p-6 rounded-xl border border-gold-500/20 bg-ink-900/50 backdrop-blur-sm">
            <h3 class="text-gold-500 font-medium mb-4">分析洞察</h3>
            <div class="space-y-3">
              <div
                v-for="(insight, index) in trendReport.insights"
                :key="index"
                class="flex items-start gap-3 p-3 rounded-lg bg-ink-800/50"
              >
                <span class="text-gold-400 mt-0.5">💡</span>
                <p class="text-gold-500/80 text-sm">{{ insight }}</p>
              </div>
            </div>
          </div>
        </div>

        <div v-else class="text-center py-12">
          <EmptyState
            icon="📈"
            title="暂无趋势报告"
            description="配置参数后点击生成报告"
          />
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'

definePageMeta({ middleware: 'auth' })

const { request } = useApi()
const notification = useNotification()

const userId = ref('')
const loading = ref(false)
const activeTab = ref('patterns')

// 模式数据
const patterns = ref<any[]>([])

// 异常数据
const anomalies = ref<any[]>([])
const anomalyType = ref('behavior')
const timeRange = ref('7d')

// 趋势数据
const trendReport = ref<any>(null)
const trendPeriod = ref('weekly')
const trendMetric = ref('engagement')

const tabs = [
  { value: 'patterns', label: '行为模式' },
  { value: 'anomalies', label: '异常检测' },
  { value: 'trends', label: '趋势报告' },
]

const anomalyTypeOptions = [
  { value: 'behavior', label: '行为异常' },
  { value: 'performance', label: '性能异常' },
  { value: 'security', label: '安全异常' },
]

const timeRangeOptions = [
  { value: '1d', label: '最近1天' },
  { value: '7d', label: '最近7天' },
  { value: '30d', label: '最近30天' },
  { value: '90d', label: '最近90天' },
]

const trendPeriodOptions = [
  { value: 'daily', label: '每日' },
  { value: 'weekly', label: '每周' },
  { value: 'monthly', label: '每月' },
  { value: 'quarterly', label: '每季度' },
]

const trendMetricOptions = [
  { value: 'engagement', label: '用户参与度' },
  { value: 'retention', label: '用户留存' },
  { value: 'conversion', label: '转化率' },
  { value: 'performance', label: '性能指标' },
]

const trendColumns = [
  { key: 'date', title: '日期' },
  { key: 'value', title: '数值' },
  { key: 'change', title: '变化' },
]

// 获取行为模式
async function fetchPatterns() {
  if (!userId.value) return
  loading.value = true
  try {
    const { data, error } = await request(`/api/observation/patterns/${userId.value}`)
    if (error) {
      notification.error('查询失败', error)
      return
    }
    patterns.value = data?.patterns || []
    notification.success('查询成功', `找到 ${patterns.value.length} 个行为模式`)
  } catch (err) {
    notification.error('查询失败', '网络请求失败')
  } finally {
    loading.value = false
  }
}

// 异常检测
async function checkAnomalies() {
  loading.value = true
  try {
    const { data, error } = await request('/api/observation/anomaly', {
      method: 'POST',
      body: {
        user_id: userId.value || undefined,
        recent_records: [],
      },
    })
    if (error) {
      notification.error('检测失败', error)
      return
    }
    anomalies.value = data?.anomalies || []
    notification.success('检测完成', `发现 ${anomalies.value.length} 个异常`)
  } catch (err) {
    notification.error('检测失败', '网络请求失败')
  } finally {
    loading.value = false
  }
}

// 生成趋势报告
async function generateTrend() {
  loading.value = true
  try {
    const { data, error } = await request('/api/observation/trend', {
      method: 'POST',
      body: {
        user_id: userId.value || undefined,
        period: trendPeriod.value,
      },
    })
    if (error) {
      notification.error('生成失败', error)
      return
    }
    trendReport.value = data
    notification.success('生成成功', '趋势报告已生成')
  } catch (err) {
    notification.error('生成失败', '网络请求失败')
  } finally {
    loading.value = false
  }
}

// 辅助函数
function getPatternIcon(type: string) {
  const icons: Record<string, string> = {
    usage: '📱',
    navigation: '🧭',
    interaction: '👆',
    timing: '⏱',
    default: '📊',
  }
  return icons[type] || icons.default
}

function getConfidenceVariant(confidence: number) {
  if (confidence >= 0.8) return 'success'
  if (confidence >= 0.5) return 'warning'
  return 'error'
}

function formatDate(iso: string) {
  if (!iso) return '-'
  return new Date(iso).toLocaleString('zh-CN', {
    month: '2-digit',
    day: '2-digit',
    hour: '2-digit',
    minute: '2-digit',
  })
}
</script>
