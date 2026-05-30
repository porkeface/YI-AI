<template>
  <div v-if="showWarnings" class="fixed bottom-4 left-4 p-4 rounded-lg border border-yellow-500/50 bg-ink-900/90 backdrop-blur-sm z-50 max-w-sm">
    <div class="flex items-center justify-between mb-2">
      <h3 class="text-yellow-400 font-bold text-sm">可访问性检查</h3>
      <button
        @click="showWarnings = false"
        class="text-yellow-400/60 hover:text-yellow-400 transition-colors duration-200"
      >
        ✕
      </button>
    </div>
    <ul class="space-y-1 text-xs text-yellow-400/80">
      <li v-for="(warning, index) in warnings" :key="index">
        {{ warning }}
      </li>
    </ul>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'

const showWarnings = ref(false)
const warnings = ref<string[]>([])

onMounted(() => {
  // 检查图片alt属性（仅查询img标签，不遍历全部DOM）
  const images = document.querySelectorAll('img:not([alt])')
  if (images.length > 0) {
    warnings.value.push(`${images.length} 个图片缺少 alt 属性`)
  }

  // 检查表单标签（仅查询input标签）
  const inputs = document.querySelectorAll('input:not([aria-label]):not([id])')
  if (inputs.length > 0) {
    warnings.value.push(`${inputs.length} 个输入框缺少标签`)
  }

  // 如果有警告，显示面板
  if (warnings.value.length > 0) {
    showWarnings.value = true
  }
})
</script>
