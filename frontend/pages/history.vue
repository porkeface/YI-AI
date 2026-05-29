<template>
  <div class="min-h-screen py-8 px-4">
    <div class="max-w-4xl mx-auto">
      <SeoHead title="占卜历史" description="查看您的占卜历史记录" />

      <h1 class="text-3xl font-bold text-gold-500 text-glow-gold font-chinese mb-8 text-center">
        占卜历史
      </h1>

      <!-- 加载状态 -->
      <div v-if="loading" class="mt-8">
        <LoadingSpinner text="加载历史记录中..." />
      </div>

      <!-- 空状态 -->
      <EmptyState
        v-else-if="records.length === 0"
        icon="📜"
        title="暂无历史记录"
        description="您还没有进行过占卜，快去试试吧！"
      >
        <NuxtLink
          to="/divination"
          class="px-6 py-2 bg-gradient-to-r from-gold-600 to-gold-500 text-ink-900 font-bold rounded-lg
                 hover:from-gold-500 hover:to-gold-400 transition-all duration-300 glow-gold"
        >
          开始占卜
        </NuxtLink>
      </EmptyState>

      <!-- 记录列表 -->
      <div v-else class="space-y-4">
        <div
          v-for="record in records"
          :key="record.id"
          class="border border-gold-500/20 rounded-lg p-4 bg-ink-900/50 hover:border-gold-500/40 transition-colors duration-200"
        >
          <div class="flex items-start justify-between gap-4">
            <div class="flex-1 min-w-0">
              <p class="text-gold-500 font-medium truncate">{{ record.question }}</p>
              <div class="flex items-center gap-3 mt-2">
                <span class="text-gold-500/60 text-sm">{{ record.hexagramName }}</span>
                <Badge :variant="fortuneVariant(record.fortune)">{{ record.fortune }}</Badge>
                <span class="text-gold-500/40 text-xs">{{ formatDate(record.createdAt) }}</span>
              </div>
            </div>
            <div class="flex gap-2 shrink-0">
              <Button variant="secondary" size="sm" @click="viewDetail(record)">查看</Button>
              <Button variant="danger" size="sm" @click="deleteRecord(record.id)">删除</Button>
            </div>
          </div>
        </div>

        <!-- 分页 -->
        <Pagination
          v-if="totalPages > 1"
          :current-page="currentPage"
          :total-pages="totalPages"
          class="mt-6"
          @change="fetchHistory"
        />
      </div>

      <!-- 详情弹窗 -->
      <Modal
        :visible="showDetail"
        title="占卜详情"
        size="lg"
        @update:visible="showDetail = $event"
      >
        <div v-if="selectedRecord" class="space-y-6">
          <div class="text-center">
            <p class="text-gold-500/80 text-sm mb-1">{{ selectedRecord.question }}</p>
            <div class="flex items-center justify-center gap-2">
              <span class="text-gold-500/60 text-xs">{{ formatDate(selectedRecord.createdAt) }}</span>
              <Badge :variant="fortuneVariant(selectedRecord.fortune)">{{ selectedRecord.fortune }}</Badge>
            </div>
          </div>
          <HexagramChart
            :hexagram="selectedRecord.hexagramData"
            :changed-hexagram="selectedRecord.changedHexagramData || undefined"
          />
          <AnalysisPanel :analysis="selectedRecord.analysisData" />
        </div>
      </Modal>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import type { HistoryRecord } from '~/types/hexagram'
import { useHistory } from '~/composables/useHistory'

const historyApi = useHistory()

const records = ref<HistoryRecord[]>([])
const totalPages = ref(1)
const currentPage = ref(1)
const loading = ref(true)
const selectedRecord = ref<HistoryRecord | null>(null)
const showDetail = ref(false)

async function fetchHistory(page: number) {
  loading.value = true
  const result = await historyApi.getHistory(page, 10)
  if (result) {
    records.value = result.records
    totalPages.value = result.totalPages
    currentPage.value = result.page
  }
  loading.value = false
}

function viewDetail(record: HistoryRecord) {
  selectedRecord.value = record
  showDetail.value = true
}

async function deleteRecord(id: number) {
  if (!confirm('确定要删除这条记录吗？')) return
  const success = await historyApi.deleteHistoryRecord(id)
  if (success) {
    await fetchHistory(currentPage.value)
  }
}

function fortuneVariant(fortune: string) {
  if (fortune.includes('吉')) return 'success'
  if (fortune.includes('凶')) return 'error'
  return 'warning'
}

function formatDate(iso: string) {
  return new Date(iso).toLocaleString('zh-CN', {
    year: 'numeric',
    month: '2-digit',
    day: '2-digit',
    hour: '2-digit',
    minute: '2-digit',
  })
}

onMounted(() => fetchHistory(1))
</script>
