<template>
  <div class="min-h-screen py-8 px-4">
    <div class="max-w-7xl mx-auto">
      <SeoHead title="卦象图谱" description="浏览六十四卦，探索卦象关系" />

      <h1 class="text-3xl font-bold text-gold-500 text-glow-gold font-chinese mb-8 text-center">
        卦象图谱
      </h1>

      <!-- 搜索和筛选 -->
      <div class="mb-6 space-y-4">
        <InputField
          v-model="searchQuery"
          placeholder="搜索卦名..."
          label="搜索卦名"
        />

        <!-- 宫位筛选 -->
        <div class="flex flex-wrap gap-2">
          <button
            v-for="palace in palaces"
            :key="palace"
            @click="togglePalace(palace)"
            :class="[
              'px-3 py-1 rounded-full text-sm border transition-colors duration-200',
              selectedPalace === palace
                ? 'border-gold-500 bg-gold-500/20 text-gold-500'
                : 'border-gold-500/30 text-gold-500/60 hover:border-gold-500/60',
            ]"
          >
            {{ palace }}宫
          </button>
        </div>

        <!-- 五行筛选 -->
        <div class="flex flex-wrap gap-2">
          <button
            v-for="el in elements"
            :key="el.value"
            @click="toggleElement(el.value)"
            :class="[
              'px-3 py-1 rounded-full text-sm border transition-colors duration-200',
              selectedElement === el.value
                ? 'border-gold-500 bg-gold-500/20 text-gold-500'
                : 'border-gold-500/30 text-gold-500/60 hover:border-gold-500/60',
            ]"
          >
            {{ el.label }}
          </button>
        </div>
      </div>

      <!-- 加载状态 -->
      <div v-if="loading" class="mt-8">
        <LoadingSpinner text="加载卦象数据中..." />
      </div>

      <!-- 空状态 -->
      <EmptyState
        v-else-if="filteredHexagrams.length === 0"
        icon="🔍"
        title="未找到卦象"
        description="请尝试其他搜索条件"
      />

      <!-- 卦象网格 -->
      <div v-else class="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 lg:grid-cols-6 xl:grid-cols-8 gap-3">
        <button
          v-for="hex in filteredHexagrams"
          :key="hex.id"
          @click="openDetail(hex.id)"
          class="border border-gold-500/20 rounded-lg p-3 bg-ink-900/50
                 hover:border-gold-500/60 hover:bg-ink-900/80 transition-all duration-200
                 flex flex-col items-center gap-1 text-center group"
        >
          <!-- 简易卦象线条 -->
          <div class="flex flex-col-reverse gap-0.5 mb-1">
            <div
              v-for="i in 6"
              :key="i"
              class="h-1 bg-gold-500/70 group-hover:bg-gold-500 transition-colors"
              :class="getLineStyle(hex, i)"
            ></div>
          </div>
          <span class="text-gold-500 font-bold text-sm font-chinese">{{ hex.name }}</span>
          <span class="text-gold-500/40 text-xs truncate w-full">{{ hex.palace }}宫</span>
          <Badge :variant="elementVariant(hex.element)">{{ elementLabel(hex.element) }}</Badge>
        </button>
      </div>

      <!-- 详情弹窗 -->
      <Modal
        :visible="showDetail"
        :title="detailHexagram?.name || '卦象详情'"
        size="lg"
        @update:visible="showDetail = $event"
      >
        <div v-if="detailLoading" class="py-8">
          <LoadingSpinner text="加载详情中..." />
        </div>
        <div v-else-if="detailHexagram" class="space-y-6">
          <!-- 基本信息 -->
          <div class="text-center">
            <h2 class="text-2xl font-bold text-gold-500 font-chinese">{{ detailHexagram.name }}</h2>
            <p class="text-gold-500/60 text-sm mt-1">
              {{ detailHexagram.fullName }} · {{ detailHexagram.palace }}宫 · {{ elementLabel(detailHexagram.element) }}
            </p>
          </div>

          <!-- 六爻展示 -->
          <div class="border border-gold-500/20 rounded-lg overflow-hidden">
            <table class="w-full">
              <thead>
                <tr class="border-b border-gold-500/20">
                  <th class="px-3 py-2 text-gold-500/80 text-xs">爻位</th>
                  <th class="px-3 py-2 text-gold-500/80 text-xs">阴阳</th>
                  <th class="px-3 py-2 text-gold-500/80 text-xs">六亲</th>
                  <th class="px-3 py-2 text-gold-500/80 text-xs">六神</th>
                  <th class="px-3 py-2 text-gold-500/80 text-xs">干支</th>
                </tr>
              </thead>
              <tbody>
                <tr
                  v-for="line in detailHexagram.lines.slice().reverse()"
                  :key="line.position"
                  class="border-b border-gold-500/10"
                  :class="{ 'bg-gold-500/10': line.isShi || line.isYing }"
                >
                  <td class="px-3 py-2 text-gold-500/80 text-sm text-center">
                    {{ line.position }}
                    <span v-if="line.isShi" class="text-gold-500 text-xs ml-1">世</span>
                    <span v-if="line.isYing" class="text-gold-500 text-xs ml-1">应</span>
                  </td>
                  <td class="px-3 py-2 text-center">
                    <div class="flex justify-center">
                      <div v-if="line.yinYang === 'yang'" class="w-10 h-1 bg-gold-500 rounded"></div>
                      <div v-else class="flex gap-1">
                        <div class="w-4 h-1 bg-gold-500 rounded"></div>
                        <div class="w-4 h-1 bg-gold-500 rounded"></div>
                      </div>
                    </div>
                  </td>
                  <td class="px-3 py-2 text-gold-500/80 text-sm text-center">{{ line.sixRelation }}</td>
                  <td class="px-3 py-2 text-gold-500/80 text-sm text-center">{{ line.sixSpirit }}</td>
                  <td class="px-3 py-2 text-gold-500/80 text-sm text-center">
                    {{ line.ganZhi.gan }}{{ line.ganZhi.zhi }}
                  </td>
                </tr>
              </tbody>
            </table>
          </div>

          <!-- 卦辞 -->
          <div class="space-y-3">
            <div>
              <h4 class="text-gold-500/80 text-xs mb-1">卦辞</h4>
              <p class="text-gold-500/90 text-sm leading-relaxed">{{ detailHexagram.judgment }}</p>
            </div>
            <div>
              <h4 class="text-gold-500/80 text-xs mb-1">象辞</h4>
              <p class="text-gold-500/90 text-sm leading-relaxed">{{ detailHexagram.image }}</p>
            </div>
          </div>

          <!-- 关系卦 -->
          <div v-if="relationships">
            <h3 class="text-gold-500 font-bold font-chinese mb-3">关系卦</h3>
            <div class="grid grid-cols-3 gap-3">
              <button
                v-for="(rel, key) in relationshipItems"
                :key="key"
                @click="openDetail(rel.hexagram.id)"
                class="border border-gold-500/20 rounded-lg p-3 bg-ink-900/30
                       hover:border-gold-500/50 transition-colors duration-200 text-center"
              >
                <span class="text-gold-500/60 text-xs block mb-1">{{ rel.label }}</span>
                <span class="text-gold-500 font-bold font-chinese">{{ rel.hexagram.name }}</span>
                <span class="text-gold-500/40 text-xs block mt-1">{{ rel.hexagram.palace }}宫</span>
              </button>
            </div>
          </div>
        </div>
      </Modal>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, watch } from 'vue'
import type { HexagramSummary, HexagramRelationships } from '~/types/hexagram'
import { useGraph } from '~/composables/useGraph'
import { useApi } from '~/composables/useApi'

const graphApi = useGraph()
const { getHexagramDetail } = useApi()

const allHexagrams = ref<HexagramSummary[]>([])
const searchQuery = ref('')
const selectedPalace = ref('')
const selectedElement = ref('')
const loading = ref(true)
const showDetail = ref(false)
const detailLoading = ref(false)
const detailHexagram = ref<any>(null)
const relationships = ref<HexagramRelationships | null>(null)

const palaces = ['乾', '坤', '震', '巽', '坎', '离', '艮', '兑']
const elements = [
  { value: '金', label: '金' },
  { value: '木', label: '木' },
  { value: '水', label: '水' },
  { value: '火', label: '火' },
  { value: '土', label: '土' },
]

const filteredHexagrams = computed(() => {
  let result = allHexagrams.value
  if (searchQuery.value) {
    const q = searchQuery.value.toLowerCase()
    result = result.filter(h => h.name.includes(q) || h.fullName.includes(q))
  }
  if (selectedPalace.value) {
    result = result.filter(h => h.palace === selectedPalace.value)
  }
  if (selectedElement.value) {
    result = result.filter(h => h.element === selectedElement.value)
  }
  return result
})

const relationshipItems = computed(() => {
  if (!relationships.value) return []
  return [
    { label: '错卦', hexagram: relationships.value.opposite },
    { label: '综卦', hexagram: relationships.value.reversed },
    { label: '互卦', hexagram: relationships.value.interlock },
  ]
})

function togglePalace(palace: string) {
  selectedPalace.value = selectedPalace.value === palace ? '' : palace
}

function toggleElement(element: string) {
  selectedElement.value = selectedElement.value === element ? '' : element
}

function getLineStyle(hex: HexagramSummary, position: number) {
  // 简化：根据上下卦名推断线条样式
  // 实际需要根据卦的二进制数据来判断，这里用ID做简单映射
  const bits = hex.id.toString(2).padStart(6, '0')
  const bit = bits[position - 1]
  return bit === '1' ? 'w-10' : 'w-4'
}

function elementVariant(element: string) {
  switch (element) {
    case '金': return 'info'
    case '木': return 'success'
    case '水': return 'info'
    case '火': return 'error'
    case '土': return 'warning'
    default: return 'default'
  }
}

function elementLabel(element: string) {
  const map: Record<string, string> = { metal: '金', wood: '木', water: '水', fire: '火', earth: '土' }
  return map[element] || element
}

async function openDetail(id: number) {
  showDetail.value = true
  detailLoading.value = true
  detailHexagram.value = null
  relationships.value = null

  const [detailResp, rels] = await Promise.all([
    getHexagramDetail(id),
    graphApi.getHexagramRelationships(id),
  ])

  const detail = detailResp?.data as any
  if (detail?.success && detail.data) {
    detailHexagram.value = detail.data
  }
  relationships.value = rels
  detailLoading.value = false
}

onMounted(async () => {
  allHexagrams.value = await graphApi.getAllHexagrams()
  loading.value = false
})
</script>
