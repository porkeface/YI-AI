<template>
  <div class="ai-stream-panel rounded-xl border border-gold-500/20 bg-gradient-to-br from-ink-900/90 to-ink-800/50 overflow-hidden">
    <!-- 标题栏 -->
    <div class="px-6 py-4 border-b border-gold-500/20 flex items-center gap-3">
      <div class="w-8 h-8 rounded-full bg-gold-500/20 flex items-center justify-center">
        <span class="text-gold-400 text-sm">✦</span>
      </div>
      <div>
        <h3 class="text-gold-500 font-semibold font-chinese">AI 深度解读</h3>
        <p class="text-gold-500/50 text-xs mt-0.5">
          {{ isStreaming ? '正在生成...' : '解读完成' }}
        </p>
      </div>
      <!-- 流式状态指示器 -->
      <div v-if="isStreaming" class="ml-auto flex items-center gap-2">
        <div class="flex gap-1">
          <span class="w-1.5 h-1.5 bg-gold-400 rounded-full animate-bounce" style="animation-delay: 0ms"></span>
          <span class="w-1.5 h-1.5 bg-gold-400 rounded-full animate-bounce" style="animation-delay: 150ms"></span>
          <span class="w-1.5 h-1.5 bg-gold-400 rounded-full animate-bounce" style="animation-delay: 300ms"></span>
        </div>
      </div>
    </div>

    <!-- 内容区 -->
    <div class="px-6 py-5 relative">
      <!-- 背景装饰 -->
      <div class="absolute top-0 right-0 w-32 h-32 bg-gold-500/5 rounded-full blur-3xl -translate-y-1/2 translate-x-1/2"></div>

      <!-- 文本内容 -->
      <div class="relative">
        <div
          ref="contentRef"
          class="text-gold-500/85 leading-relaxed whitespace-pre-wrap text-sm"
          :class="{ 'streaming-cursor': isStreaming }"
        >
          {{ displayText }}
        </div>

        <!-- 空状态 -->
        <div v-if="!displayText && !isStreaming" class="text-gold-500/40 text-sm italic">
          暂无 AI 解读
        </div>
      </div>
    </div>

    <!-- 底部装饰线 -->
    <div class="h-px bg-gradient-to-r from-transparent via-gold-500/30 to-transparent"></div>
  </div>
</template>

<script setup lang="ts">
import { ref, watch, nextTick, computed } from 'vue'

interface Props {
  text?: string | null
  isStreaming?: boolean
}

const props = withDefaults(defineProps<Props>(), {
  text: null,
  isStreaming: false,
})

const contentRef = ref<HTMLElement | null>(null)

// 用于流式逐字显示的内部文本
const internalText = ref('')
let streamTimer: ReturnType<typeof setInterval> | null = null
let pendingChars = ''

const displayText = computed(() => {
  if (props.isStreaming) {
    return internalText.value
  }
  return props.text || ''
})

// 监听 text 变化，实现逐字显示效果
watch(() => props.text, (newText) => {
  if (!newText) {
    internalText.value = ''
    return
  }

  if (!props.isStreaming) {
    // 非流式模式，直接显示
    internalText.value = newText
    return
  }
}, { immediate: true })

// 监听流式文本变化
watch(() => props.text, (newText) => {
  if (newText && props.isStreaming) {
    // 追加新字符到内部文本
    const newChars = newText.slice(internalText.value.length)
    if (newChars) {
      pendingChars += newChars
      startStreamDisplay()
    }
  }
})

function startStreamDisplay() {
  if (streamTimer) return

  streamTimer = setInterval(() => {
    if (pendingChars.length > 0) {
      // 每次显示1-3个字符，模拟自然打字
      const charsToAdd = Math.min(
        Math.floor(Math.random() * 3) + 1,
        pendingChars.length
      )
      internalText.value += pendingChars.slice(0, charsToAdd)
      pendingChars = pendingChars.slice(charsToAdd)

      // 自动滚动到底部
      nextTick(() => {
        if (contentRef.value) {
          contentRef.value.scrollTop = contentRef.value.scrollHeight
        }
      })
    } else {
      if (streamTimer) {
        clearInterval(streamTimer)
        streamTimer = null
      }
    }
  }, 30)
}

// 流式结束时同步文本
watch(() => props.isStreaming, (streaming) => {
  if (!streaming && props.text) {
    // 流式结束，确保显示完整文本
    if (streamTimer) {
      clearInterval(streamTimer)
      streamTimer = null
    }
    // 快速补齐剩余字符
    pendingChars = ''
    internalText.value = props.text
  }
})
</script>

<style scoped>
.streaming-cursor::after {
  content: '▊';
  @apply text-gold-400 animate-pulse ml-0.5;
}

@keyframes fade-in {
  from {
    opacity: 0;
    transform: translateY(8px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

.ai-stream-panel {
  animation: fade-in 0.5s ease-out;
}
</style>
