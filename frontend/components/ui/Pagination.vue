<template>
  <div class="flex items-center justify-center gap-2">
    <!-- 上一页 -->
    <button
      @click="prev"
      :disabled="currentPage <= 1"
      class="px-3 py-1 rounded border border-gold-500/30 text-gold-500/80 hover:bg-gold-500/10 disabled:opacity-50 disabled:cursor-not-allowed transition-colors duration-200"
    >
      上一页
    </button>

    <!-- 页码 -->
    <template v-for="page in displayedPages" :key="page">
      <button
        v-if="page !== '...'"
        @click="goTo(page as number)"
        :class="[
          'px-3 py-1 rounded border transition-colors duration-200',
          currentPage === page
            ? 'border-gold-500 bg-gold-500/20 text-gold-500'
            : 'border-gold-500/30 text-gold-500/80 hover:bg-gold-500/10',
        ]"
      >
        {{ page }}
      </button>
      <span v-else class="px-2 text-gold-500/60">...</span>
    </template>

    <!-- 下一页 -->
    <button
      @click="next"
      :disabled="currentPage >= totalPages"
      class="px-3 py-1 rounded border border-gold-500/30 text-gold-500/80 hover:bg-gold-500/10 disabled:opacity-50 disabled:cursor-not-allowed transition-colors duration-200"
    >
      下一页
    </button>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'

interface Props {
  currentPage: number
  totalPages: number
  maxVisible?: number
}

const props = withDefaults(defineProps<Props>(), {
  maxVisible: 5,
})

const emit = defineEmits<{
  'update:currentPage': [page: number]
  change: [page: number]
}>()

const displayedPages = computed(() => {
  const pages: (number | string)[] = []
  const half = Math.floor(props.maxVisible / 2)

  let start = Math.max(1, props.currentPage - half)
  let end = Math.min(props.totalPages, start + props.maxVisible - 1)

  if (end - start + 1 < props.maxVisible) {
    start = Math.max(1, end - props.maxVisible + 1)
  }

  if (start > 1) {
    pages.push(1)
    if (start > 2) {
      pages.push('...')
    }
  }

  for (let i = start; i <= end; i++) {
    pages.push(i)
  }

  if (end < props.totalPages) {
    if (end < props.totalPages - 1) {
      pages.push('...')
    }
    pages.push(props.totalPages)
  }

  return pages
})

function goTo(page: number) {
  if (page >= 1 && page <= props.totalPages) {
    emit('update:currentPage', page)
    emit('change', page)
  }
}

function prev() {
  goTo(props.currentPage - 1)
}

function next() {
  goTo(props.currentPage + 1)
}
</script>
