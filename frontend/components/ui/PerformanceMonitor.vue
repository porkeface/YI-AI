<template>
  <div v-if="showMetrics" class="fixed bottom-4 right-4 p-4 rounded-lg border border-gold-500/30 bg-ink-900/90 backdrop-blur-sm z-50">
    <div class="flex items-center justify-between mb-2">
      <h3 class="text-gold-500 font-bold text-sm">性能指标</h3>
      <button
        @click="showMetrics = false"
        class="text-gold-500/60 hover:text-gold-500 transition-colors duration-200"
      >
        ✕
      </button>
    </div>
    <div class="space-y-1 text-xs text-gold-500/80">
      <div>FCP: {{ metrics.fcp }}ms</div>
      <div>LCP: {{ metrics.lcp }}ms</div>
      <div>CLS: {{ metrics.cls }}</div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'

const showMetrics = ref(false)

const metrics = ref({
  fcp: 0,
  lcp: 0,
  cls: 0,
})

onMounted(() => {
  // 监听FCP
  const observer = new PerformanceObserver((list) => {
    const entries = list.getEntries()
    entries.forEach((entry) => {
      if (entry.name === 'first-contentful-paint') {
        metrics.value.fcp = Math.round(entry.startTime)
      }
    })
  })

  observer.observe({ entryTypes: ['paint'] })

  // 监听LCP
  const lcpObserver = new PerformanceObserver((list) => {
    const entries = list.getEntries()
    const lastEntry = entries[entries.length - 1]
    if (lastEntry) {
      metrics.value.lcp = Math.round(lastEntry.startTime)
    }
  })

  lcpObserver.observe({ entryTypes: ['largest-contentful-paint'] })

  // 监听CLS
  const clsObserver = new PerformanceObserver((list) => {
    let clsValue = 0
    list.getEntries().forEach((entry: any) => {
      if (!entry.hadRecentInput) {
        clsValue += entry.value
      }
    })
    metrics.value.cls = Math.round(clsValue * 1000) / 1000
  })

  clsObserver.observe({ entryTypes: ['layout-shift'] })
})
</script>
