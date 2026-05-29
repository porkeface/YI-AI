<template>
  <div class="min-h-screen py-8 px-4">
    <div class="max-w-6xl mx-auto">
      <SeoHead title="数据分析" description="数据追踪、漏斗分析与可视化仪表盘" />

      <!-- 页面标题 -->
      <div class="text-center mb-10">
        <h1 class="text-3xl font-bold text-gold-500 text-glow-gold font-chinese mb-3">
          数据分析
        </h1>
        <p class="text-gold-500/50 text-sm">事件追踪、漏斗分析与数据可视化</p>
        <div class="w-16 h-px bg-gradient-to-r from-transparent via-gold-500/50 to-transparent mx-auto mt-4"></div>
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
        <LoadingSpinner text="加载数据中..." />
      </div>

      <!-- 仪表盘 Tab -->
      <div v-else-if="activeTab === 'dashboard'">
        <!-- 核心指标卡片 -->
        <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4 mb-8">
          <div
            v-for="(metric, index) in dashboardData.metrics"
            :key="index"
            class="p-5 rounded-xl border border-gold-500/20 bg-ink-900/50 backdrop-blur-sm"
          >
            <div class="flex items-center justify-between mb-2">
              <p class="text-gold-500/60 text-sm">{{ metric.label }}</p>
              <span class="text-lg">{{ metric.icon }}</span>
            </div>
            <p class="text-2xl font-bold text-gold-500 mb-1">{{ formatNumber(metric.value) }}</p>
            <div class="flex items-center gap-1">
              <span
                :class="metric.change >= 0 ? 'text-green-400' : 'text-red-400'"
                class="text-xs"
              >
                {{ metric.change >= 0 ? '↑' : '↓' }} {{ Math.abs(metric.change) }}%
              </span>
              <span class="text-gold-500/40 text-xs">较上期</span>
            </div>
          </div>
        </div>

        <!-- 趋势图表区域 -->
        <div class="grid grid-cols-1 lg:grid-cols-2 gap-6 mb-8">
          <!-- 用户趋势 -->
          <div class="p-6 rounded-xl border border-gold-500/20 bg-ink-900/50 backdrop-blur-sm">
            <h3 class="text-gold-500 font-medium mb-4">用户趋势</h3>
            <div class="space-y-3">
              <div
                v-for="(item, index) in dashboardData.userTrend"
                :key="index"
                class="flex items-center gap-3"
              >
                <span class="text-gold-500/60 text-xs w-12 shrink-0">{{ item.date }}</span>
                <div class="flex-1 h-6 bg-ink-800 rounded-full overflow-hidden">
                  <div
                    class="h-full bg-gold-500/60 rounded-full transition-all duration-500"
                    :style="{ width: `${(item.value / maxUserTrend) * 100}%` }"
                  ></div>
                </div>
                <span class="text-gold-500/80 text-xs w-10 text-right">{{ item.value }}</span>
              </div>
            </div>
          </div>

          <!-- 事件分布 -->
          <div class="p-6 rounded-xl border border-gold-500/20 bg-ink-900/50 backdrop-blur-sm">
            <h3 class="text-gold-500 font-medium mb-4">事件分布</h3>
            <div class="space-y-3">
              <div
                v-for="(item, index) in dashboardData.eventDistribution"
                :key="index"
                class="flex items-center gap-3"
              >
                <div class="flex items-center gap-2 w-32 shrink-0">
                  <div
                    class="w-3 h-3 rounded-full"
                    :style="{ backgroundColor: item.color }"
                  ></div>
                  <span class="text-gold-500/80 text-xs truncate">{{ item.name }}</span>
                </div>
                <div class="flex-1 h-6 bg-ink-800 rounded-full overflow-hidden">
                  <div
                    class="h-full rounded-full transition-all duration-500"
                    :style="{ width: `${item.percent}%`, backgroundColor: item.color }"
                  ></div>
                </div>
                <span class="text-gold-500/80 text-xs w-16 text-right">{{ item.percent }}%</span>
              </div>
            </div>
          </div>
        </div>

        <!-- 热门事件表格 -->
        <div class="p-6 rounded-xl border border-gold-500/20 bg-ink-900/50 backdrop-blur-sm">
          <h3 class="text-gold-500 font-medium mb-4">热门事件</h3>
          <DataTable
            :columns="eventColumns"
            :data="dashboardData.topEvents"
          >
            <template #count="{ row }">
              <span class="text-gold-500 font-mono">{{ row.count.toLocaleString() }}</span>
            </template>
            <template #trend="{ row }">
              <span
                :class="row.trend >= 0 ? 'text-green-400' : 'text-red-400'"
                class="text-xs"
              >
                {{ row.trend >= 0 ? '↑' : '↓' }} {{ Math.abs(row.trend) }}%
              </span>
            </template>
          </DataTable>
        </div>
      </div>

      <!-- 事件追踪 Tab -->
      <div v-else-if="activeTab === 'events'">
        <!-- 事件追踪表单 -->
        <div class="mb-8 p-6 rounded-xl border border-gold-500/20 bg-ink-900/50 backdrop-blur-sm">
          <h3 class="text-gold-500 font-medium mb-4">追踪新事件</h3>
          <div class="grid grid-cols-1 md:grid-cols-2 gap-4 mb-4">
            <div>
              <label class="block text-gold-500/80 text-sm mb-2">事件类型 *</label>
              <InputField
                v-model="eventForm.event_type"
                placeholder="例如: page_view"
                label="事件类型"
              />
            </div>
            <div>
              <label class="block text-gold-500/80 text-sm mb-2">用户ID</label>
              <InputField
                v-model="eventForm.user_id"
                placeholder="输入用户ID"
                label="用户ID"
              />
            </div>
          </div>
          <div class="mb-4">
            <label class="block text-gold-500/80 text-sm mb-2">事件属性 (JSON)</label>
            <Textarea
              v-model="eventForm.properties"
              placeholder='{"page": "/home", "referrer": "google.com"}'
              :rows="3"
            />
          </div>
          <Button
            variant="primary"
            :disabled="!eventForm.event_type || tracking"
            @click="trackEvent"
          >
            {{ tracking ? '追踪中...' : '追踪事件' }}
          </Button>
        </div>

        <!-- 事件类型列表 -->
        <div class="p-6 rounded-xl border border-gold-500/20 bg-ink-900/50 backdrop-blur-sm">
          <div class="flex items-center justify-between mb-4">
            <h3 class="text-gold-500 font-medium">事件类型列表</h3>
            <Button
              variant="secondary"
              size="sm"
              @click="fetchEventTypes"
            >
              刷新
            </Button>
          </div>
          <div v-if="eventTypes.length === 0" class="text-center py-8 text-gold-500/60">
            暂无事件类型
          </div>
          <div v-else class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-3">
            <div
              v-for="(eventType, index) in eventTypes"
              :key="index"
              class="p-4 bg-ink-800/50 rounded-lg border border-gold-500/10"
            >
              <div class="flex items-center justify-between mb-2">
                <span class="text-gold-500 font-medium text-sm">{{ eventType.name }}</span>
                <Badge variant="default">{{ eventType.category || '未分类' }}</Badge>
              </div>
              <div class="flex items-center justify-between text-xs">
                <span class="text-gold-500/60">触发次数: {{ eventType.count?.toLocaleString() || 0 }}</span>
                <span class="text-gold-500/40">{{ formatDate(eventType.lastTriggered) }}</span>
              </div>
            </div>
          </div>
        </div>
      </div>

      <!-- 漏斗分析 Tab -->
      <div v-else-if="activeTab === 'funnels'">
        <!-- 漏斗配置 -->
        <div class="mb-8 p-6 rounded-xl border border-gold-500/20 bg-ink-900/50 backdrop-blur-sm">
          <h3 class="text-gold-500 font-medium mb-4">创建漏斗分析</h3>
          <div class="grid grid-cols-1 md:grid-cols-2 gap-4 mb-4">
            <div>
              <label class="block text-gold-500/80 text-sm mb-2">漏斗名称 *</label>
              <InputField
                v-model="funnelForm.funnel_name"
                placeholder="例如: 注册转化漏斗"
                label="漏斗名称"
              />
            </div>
            <div>
              <label class="block text-gold-500/80 text-sm mb-2">分析天数</label>
              <InputField
                v-model="funnelForm.days"
                type="number"
                placeholder="例如: 7"
                label="分析天数"
              />
            </div>
          </div>
          <div class="mb-4">
            <label class="block text-gold-500/80 text-sm mb-2">漏斗步骤 (每行一个事件名称)</label>
            <Textarea
              v-model="funnelForm.steps"
              placeholder="page_view&#10;sign_up_start&#10;sign_up_complete&#10;first_purchase"
              :rows="4"
            />
          </div>
          <Button
            variant="primary"
            :disabled="!funnelForm.funnel_name || !funnelForm.steps || analyzing"
            @click="analyzeFunnel"
          >
            {{ analyzing ? '分析中...' : '开始分析' }}
          </Button>
        </div>

        <!-- 漏斗结果 -->
        <div v-if="funnelResult" class="space-y-6">
          <!-- 漏斗概览 -->
          <div class="grid grid-cols-1 md:grid-cols-3 gap-4">
            <div class="p-5 rounded-xl border border-gold-500/20 bg-ink-900/50 backdrop-blur-sm text-center">
              <p class="text-gold-500/60 text-sm mb-1">总进入人数</p>
              <p class="text-2xl font-bold text-gold-500">{{ funnelResult.totalEntered?.toLocaleString() }}</p>
            </div>
            <div class="p-5 rounded-xl border border-gold-500/20 bg-ink-900/50 backdrop-blur-sm text-center">
              <p class="text-gold-500/60 text-sm mb-1">完成人数</p>
              <p class="text-2xl font-bold text-green-400">{{ funnelResult.totalCompleted?.toLocaleString() }}</p>
            </div>
            <div class="p-5 rounded-xl border border-gold-500/20 bg-ink-900/50 backdrop-blur-sm text-center">
              <p class="text-gold-500/60 text-sm mb-1">总体转化率</p>
              <p class="text-2xl font-bold text-gold-500">{{ funnelResult.conversionRate }}%</p>
            </div>
          </div>

          <!-- 漏斗可视化 -->
          <div class="p-6 rounded-xl border border-gold-500/20 bg-ink-900/50 backdrop-blur-sm">
            <h3 class="text-gold-500 font-medium mb-6">漏斗步骤</h3>
            <div class="space-y-4">
              <div
                v-for="(step, index) in funnelResult.steps"
                :key="index"
                class="relative"
              >
                <!-- 步骤条 -->
                <div class="flex items-center gap-4">
                  <div class="w-8 h-8 rounded-full bg-gold-500/20 flex items-center justify-center shrink-0">
                    <span class="text-gold-400 text-sm font-medium">{{ index + 1 }}</span>
                  </div>
                  <div class="flex-1">
                    <div class="flex items-center justify-between mb-1">
                      <span class="text-gold-500 font-medium text-sm">{{ step.name }}</span>
                      <span class="text-gold-500/80 text-sm">{{ step.count?.toLocaleString() }} 人</span>
                    </div>
                    <div class="h-8 bg-ink-800 rounded-lg overflow-hidden relative">
                      <div
                        class="h-full bg-gradient-to-r from-gold-600/60 to-gold-500/60 rounded-lg transition-all duration-700"
                        :style="{ width: `${step.percent}%` }"
                      ></div>
                      <span class="absolute inset-0 flex items-center justify-center text-gold-500 text-xs font-medium">
                        {{ step.percent }}%
                      </span>
                    </div>
                  </div>
                </div>

                <!-- 转化率箭头 -->
                <div
                  v-if="index < funnelResult.steps.length - 1"
                  class="flex items-center gap-4 mt-2 mb-2"
                >
                  <div class="w-8 flex justify-center">
                    <span class="text-gold-500/40 text-xs">↓</span>
                  </div>
                  <div class="flex-1 text-center">
                    <span
                      class="text-xs px-2 py-0.5 rounded-full"
                      :class="step.dropRate > 50 ? 'bg-red-500/20 text-red-400' : step.dropRate > 30 ? 'bg-yellow-500/20 text-yellow-400' : 'bg-green-500/20 text-green-400'"
                    >
                      流失 {{ step.dropRate }}%
                    </span>
                  </div>
                </div>
              </div>
            </div>
          </div>

          <!-- 漏斗洞察 -->
          <div v-if="funnelResult.insights?.length" class="p-6 rounded-xl border border-gold-500/20 bg-ink-900/50 backdrop-blur-sm">
            <h3 class="text-gold-500 font-medium mb-4">分析洞察</h3>
            <div class="space-y-3">
              <div
                v-for="(insight, index) in funnelResult.insights"
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
            icon="🔬"
            title="暂无漏斗分析"
            description="配置漏斗步骤后点击开始分析"
          />
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'

definePageMeta({ middleware: 'auth' })

const { request } = useApi()
const notification = useNotification()

const loading = ref(false)
const activeTab = ref('dashboard')
const tracking = ref(false)
const analyzing = ref(false)

// 仪表盘数据
const dashboardData = ref({
  metrics: [
    { label: '总用户数', value: 0, change: 0, icon: '👥' },
    { label: '活跃用户', value: 0, change: 0, icon: '🔥' },
    { label: '事件总数', value: 0, change: 0, icon: '📊' },
    { label: '转化率', value: 0, change: 0, icon: '🎯' },
  ],
  userTrend: [] as any[],
  eventDistribution: [] as any[],
  topEvents: [] as any[],
})

// 事件追踪
const eventForm = ref({
  event_type: '',
  user_id: '',
  properties: '',
})
const eventTypes = ref<any[]>([])

// 漏斗分析
const funnelForm = ref({
  funnel_name: '',
  days: 7,
  steps: '',
})
const funnelResult = ref<any>(null)

const tabs = [
  { value: 'dashboard', label: '仪表盘' },
  { value: 'events', label: '事件追踪' },
  { value: 'funnels', label: '漏斗分析' },
]

const eventCategoryOptions = [
  { value: 'interaction', label: '交互' },
  { value: 'navigation', label: '导航' },
  { value: 'conversion', label: '转化' },
  { value: 'error', label: '错误' },
  { value: 'custom', label: '自定义' },
]

const timeRangeOptions = [
  { value: '1d', label: '最近1天' },
  { value: '7d', label: '最近7天' },
  { value: '30d', label: '最近30天' },
  { value: '90d', label: '最近90天' },
]

const eventColumns = [
  { key: 'name', title: '事件名称' },
  { key: 'category', title: '类别' },
  { key: 'count', title: '触发次数' },
  { key: 'trend', title: '趋势' },
]

const maxUserTrend = computed(() => {
  if (dashboardData.value.userTrend.length === 0) return 1
  return Math.max(...dashboardData.value.userTrend.map(i => i.value), 1)
})

// 获取仪表盘数据
async function fetchDashboard() {
  loading.value = true
  try {
    const { data, error } = await request('/api/analytics/dashboard')
    if (error) {
      notification.error('加载失败', error)
      return
    }
    if (data?.dashboard) {
      const d = data.dashboard
      dashboardData.value = {
        metrics: [
          { label: '总用户数', value: d.total_users || 0, change: 0, icon: '👥' },
          { label: '活跃用户', value: d.active_users || 0, change: 0, icon: '🔥' },
          { label: '总会话数', value: d.total_sessions || 0, change: 0, icon: '📊' },
          { label: '平均会话时长', value: d.avg_session_duration || 0, change: 0, icon: '🎯' },
        ],
        userTrend: [],
        eventDistribution: [],
        topEvents: (d.top_hexagrams || []).map((h: any) => ({
          name: h.name,
          category: '卦象',
          count: h.count,
          trend: 0,
        })),
      }
    }
  } catch (err) {
    notification.error('加载失败', '网络请求失败')
  } finally {
    loading.value = false
  }
}

// 追踪事件
async function trackEvent() {
  if (!eventForm.value.event_type) return
  if (!eventForm.value.user_id) {
    notification.error('参数错误', '请填写用户ID')
    return
  }

  tracking.value = true
  try {
    let properties = undefined
    if (eventForm.value.properties) {
      try {
        properties = JSON.parse(eventForm.value.properties)
      } catch {
        notification.error('格式错误', '属性必须是有效的 JSON 格式')
        tracking.value = false
        return
      }
    }

    const { error } = await request('/api/analytics/events', {
      method: 'POST',
      body: {
        event_type: eventForm.value.event_type,
        user_id: eventForm.value.user_id || undefined,
        properties,
      },
    })

    if (error) {
      notification.error('追踪失败', error)
      return
    }

    notification.success('追踪成功', `事件 "${eventForm.value.event_type}" 已记录`)
    eventForm.value = { event_type: '', user_id: '', properties: '' }
    await fetchEventTypes()
  } catch (err) {
    notification.error('追踪失败', '网络请求失败')
  } finally {
    tracking.value = false
  }
}

// 获取事件类型列表
async function fetchEventTypes() {
  try {
    const { data, error } = await request('/api/analytics/events')
    if (error) {
      notification.error('加载失败', error)
      return
    }
    eventTypes.value = data?.events || []
  } catch (err) {
    notification.error('加载失败', '网络请求失败')
  }
}

// 漏斗分析
async function analyzeFunnel() {
  if (!funnelForm.value.funnel_name || !funnelForm.value.steps) return

  analyzing.value = true
  try {
    const stepNames = funnelForm.value.steps
      .split('\n')
      .map(s => s.trim())
      .filter(s => s.length > 0)

    if (stepNames.length < 2) {
      notification.error('参数错误', '漏斗至少需要2个步骤')
      analyzing.value = false
      return
    }

    const steps = stepNames.map((step_name, index) => ({
      step_name,
      event_type: step_name,
    }))

    const { data, error } = await request('/api/analytics/funnel', {
      method: 'POST',
      body: {
        funnel_name: funnelForm.value.funnel_name,
        steps,
        days: parseInt(funnelForm.value.days) || 7,
      },
    })

    if (error) {
      notification.error('分析失败', error)
      return
    }

    funnelResult.value = data
    notification.success('分析完成', '漏斗分析报告已生成')
  } catch (err) {
    notification.error('分析失败', '网络请求失败')
  } finally {
    analyzing.value = false
  }
}

// 辅助函数
function formatNumber(num: number) {
  if (num >= 1000000) return (num / 1000000).toFixed(1) + 'M'
  if (num >= 1000) return (num / 1000).toFixed(1) + 'K'
  return num.toString()
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

onMounted(() => {
  fetchDashboard()
  fetchEventTypes()
})
</script>
