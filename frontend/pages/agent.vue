<script setup lang="ts">
/**
 * Agent对话页面
 *
 * 提供AI Agent交互界面，支持：
 * - 自然语言对话
 * - 推演结果展示
 * - 意图识别显示
 */

definePageMeta({
  middleware: 'auth',
})

const {
  messages,
  isLoading,
  isStreaming,
  currentIntent,
  evolutionResult,
  sendMessageStream,
  evolve,
  clearMessages,
} = useAgent()

const inputText = ref('')
const inputRef = ref<HTMLTextAreaElement | null>(null)
const chatContainerRef = ref<HTMLDivElement | null>(null)

// 自动滚动到底部
function scrollToBottom() {
  nextTick(() => {
    if (chatContainerRef.value) {
      chatContainerRef.value.scrollTop = chatContainerRef.value.scrollHeight
    }
  })
}

watch(messages, scrollToBottom, { deep: true })

// 发送消息
async function handleSend() {
  const text = inputText.value.trim()
  if (!text || isLoading.value) return

  inputText.value = ''
  await sendMessageStream(text)
}

// 键盘事件
function handleKeydown(e: KeyboardEvent) {
  if (e.key === 'Enter' && !e.shiftKey) {
    e.preventDefault()
    handleSend()
  }
}

// 意图标签颜色
function intentColor(intent: string): string {
  const map: Record<string, string> = {
    divination: 'text-yellow-400',
    evolution: 'text-purple-400',
    trend: 'text-blue-400',
    learn: 'text-green-400',
  }
  return map[intent] || 'text-gray-400'
}

// 意图中文名
function intentLabel(intent: string): string {
  const map: Record<string, string> = {
    divination: '解卦',
    evolution: '推演',
    trend: '趋势',
    learn: '学习',
  }
  return map[intent] || intent
}
</script>

<template>
  <div class="agent-page">
    <!-- 顶部标题栏 -->
    <header class="agent-header">
      <div class="header-left">
        <h1 class="header-title">🤖 AI Agent</h1>
        <span v-if="currentIntent" class="intent-badge" :class="intentColor(currentIntent)">
          {{ intentLabel(currentIntent) }}
        </span>
      </div>
      <div class="header-right">
        <button
          class="clear-btn"
          :disabled="messages.length === 0"
          @click="clearMessages"
        >
          清空对话
        </button>
      </div>
    </header>

    <!-- 对话区域 -->
    <div ref="chatContainerRef" class="chat-container">
      <!-- 欢迎消息 -->
      <div v-if="messages.length === 0" class="welcome-section">
        <div class="welcome-icon">☯</div>
        <h2 class="welcome-title">易学AI Agent</h2>
        <p class="welcome-desc">
          我是您的易学分析助手，可以帮您解卦、推演变化、分析趋势。
        </p>
        <div class="welcome-examples">
          <button
            v-for="example in [
              '乾卦初爻动，事业方面如何？',
              '帮我推演一下坤卦的变化趋势',
              '什么是五行相生相克？',
              '最近总是遇到坎卦，有什么规律吗？',
            ]"
            :key="example"
            class="example-btn"
            @click="inputText = example"
          >
            {{ example }}
          </button>
        </div>
      </div>

      <!-- 消息列表 -->
      <div
        v-for="msg in messages"
        :key="msg.id"
        class="message-row"
        :class="`message-${msg.role}`"
      >
        <!-- 用户消息 -->
        <div v-if="msg.role === 'user'" class="message-bubble user-bubble">
          <div class="message-content">{{ msg.content }}</div>
        </div>

        <!-- AI消息 -->
        <div v-else-if="msg.role === 'assistant'" class="message-bubble ai-bubble">
          <div class="message-content" v-html="formatMessage(msg.content)" />

          <!-- 元数据 -->
          <div v-if="msg.metadata" class="message-meta">
            <span v-if="msg.metadata.intent" class="meta-tag" :class="intentColor(msg.metadata.intent)">
              {{ intentLabel(msg.metadata.intent) }}
            </span>
            <span v-if="msg.metadata.confidence" class="meta-confidence">
              {{ Math.round(msg.metadata.confidence * 100) }}%
            </span>
            <span v-if="msg.metadata.durationMs" class="meta-time">
              {{ Math.round(msg.metadata.durationMs) }}ms
            </span>
          </div>

          <!-- 风险标记 -->
          <div v-if="msg.metadata?.riskFlags?.length" class="risk-flags">
            ⚠️ {{ msg.metadata.riskFlags.join(', ') }}
          </div>
        </div>

        <!-- 系统消息 -->
        <div v-else class="message-bubble system-bubble">
          <div class="message-content">{{ msg.content }}</div>
        </div>
      </div>

      <!-- 加载指示器 -->
      <div v-if="isLoading && !isStreaming" class="loading-indicator">
        <div class="loading-dots">
          <span /><span /><span />
        </div>
        <span>思考中...</span>
      </div>
    </div>

    <!-- 推演结果面板 -->
    <Transition name="slide-up">
      <div v-if="evolutionResult" class="evolution-panel">
        <div class="evolution-header">
          <h3>🌳 推演结果</h3>
          <button class="close-btn" @click="evolutionResult = null">×</button>
        </div>
        <div class="evolution-content">
          <div class="evolution-summary">
            <strong>{{ evolutionResult.source }}</strong> →
            {{ evolutionResult.recommended_path.join(' → ') }}
          </div>
          <div class="evolution-stats">
            <span>路径数: {{ evolutionResult.path_count }}</span>
            <span>节点数: {{ evolutionResult.total_nodes }}</span>
          </div>
          <pre class="evolution-detail">{{ evolutionResult.summary }}</pre>
        </div>
      </div>
    </Transition>

    <!-- 输入区域 -->
    <div class="input-area">
      <textarea
        ref="inputRef"
        v-model="inputText"
        class="input-field"
        placeholder="输入问题... (Enter发送, Shift+Enter换行)"
        rows="1"
        :disabled="isLoading"
        @keydown="handleKeydown"
      />
      <button
        class="send-btn"
        :disabled="!inputText.trim() || isLoading"
        @click="handleSend"
      >
        <span v-if="isLoading" class="spinner" />
        <span v-else>发送</span>
      </button>
    </div>
  </div>
</template>

<script lang="ts">
import DOMPurify from 'dompurify'

// 格式化消息（简单Markdown + XSS消毒）
function formatMessage(content: string): string {
  const raw = content
    .replace(/\n/g, '<br>')
    .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
    .replace(/\*(.*?)\*/g, '<em>$1</em>')
    .replace(/`(.*?)`/g, '<code>$1</code>')
  return DOMPurify.sanitize(raw)
}
</script>

<style scoped>
.agent-page {
  @apply flex flex-col h-screen;
  background: linear-gradient(135deg, #0a0a0a 0%, #1a1a2e 100%);
}

/* 头部 */
.agent-header {
  @apply flex items-center justify-between px-6 py-3;
  border-bottom: 1px solid rgba(212, 168, 67, 0.2);
  background: rgba(10, 10, 10, 0.8);
  backdrop-filter: blur(12px);
}

.header-left {
  @apply flex items-center gap-3;
}

.header-title {
  @apply text-lg font-semibold;
  color: #d4a843;
  font-family: 'Noto Serif SC', serif;
}

.intent-badge {
  @apply text-xs px-2 py-0.5 rounded-full;
  background: rgba(255, 255, 255, 0.05);
  border: 1px solid rgba(255, 255, 255, 0.1);
}

.clear-btn {
  @apply text-xs px-3 py-1 rounded;
  color: #888;
  border: 1px solid rgba(255, 255, 255, 0.1);
  transition: all 0.2s;
}
.clear-btn:hover:not(:disabled) {
  color: #d4a843;
  border-color: rgba(212, 168, 67, 0.3);
}
.clear-btn:disabled {
  @apply opacity-30 cursor-not-allowed;
}

/* 对话区域 */
.chat-container {
  @apply flex-1 overflow-y-auto px-6 py-4;
  scroll-behavior: smooth;
}

/* 欢迎区域 */
.welcome-section {
  @apply flex flex-col items-center justify-center py-16;
}

.welcome-icon {
  @apply text-6xl mb-4;
  animation: float 3s ease-in-out infinite;
}

@keyframes float {
  0%, 100% { transform: translateY(0); }
  50% { transform: translateY(-10px); }
}

.welcome-title {
  @apply text-2xl font-bold mb-2;
  color: #d4a843;
  font-family: 'Noto Serif SC', serif;
}

.welcome-desc {
  @apply text-sm mb-8;
  color: #888;
}

.welcome-examples {
  @apply flex flex-wrap justify-center gap-2 max-w-2xl;
}

.example-btn {
  @apply text-xs px-3 py-2 rounded-lg;
  color: #aaa;
  background: rgba(255, 255, 255, 0.03);
  border: 1px solid rgba(255, 255, 255, 0.08);
  transition: all 0.2s;
}
.example-btn:hover {
  color: #d4a843;
  border-color: rgba(212, 168, 67, 0.3);
  background: rgba(212, 168, 67, 0.05);
}

/* 消息行 */
.message-row {
  @apply mb-4;
}

.message-bubble {
  @apply max-w-3xl rounded-2xl px-4 py-3;
}

.message-user {
  @apply flex justify-end;
}

.message-ai {
  @apply flex justify-start;
}

.message-system {
  @apply flex justify-center;
}

.user-bubble {
  background: linear-gradient(135deg, rgba(212, 168, 67, 0.15), rgba(212, 168, 67, 0.05));
  border: 1px solid rgba(212, 168, 67, 0.2);
  color: #e8e8e8;
}

.ai-bubble {
  background: rgba(255, 255, 255, 0.03);
  border: 1px solid rgba(255, 255, 255, 0.06);
  color: #d4d4d4;
}

.system-bubble {
  @apply text-xs;
  background: rgba(255, 200, 50, 0.05);
  border: 1px solid rgba(255, 200, 50, 0.1);
  color: #aaa;
}

.message-content {
  @apply text-sm leading-relaxed;
}

.message-content :deep(code) {
  @apply px-1 py-0.5 rounded text-xs;
  background: rgba(255, 255, 255, 0.05);
  color: #d4a843;
}

.message-meta {
  @apply flex items-center gap-2 mt-2 pt-2;
  border-top: 1px solid rgba(255, 255, 255, 0.05);
}

.meta-tag {
  @apply text-xs px-2 py-0.5 rounded;
  background: rgba(255, 255, 255, 0.05);
}

.meta-confidence {
  @apply text-xs;
  color: #666;
}

.meta-time {
  @apply text-xs;
  color: #555;
}

.risk-flags {
  @apply text-xs mt-2 px-2 py-1 rounded;
  background: rgba(255, 100, 50, 0.1);
  color: #ff8c5a;
}

/* 加载指示器 */
.loading-indicator {
  @apply flex items-center gap-2 px-4 py-2;
  color: #888;
}

.loading-dots {
  @apply flex gap-1;
}
.loading-dots span {
  @apply w-1.5 h-1.5 rounded-full;
  background: #d4a843;
  animation: dot-bounce 1.4s infinite ease-in-out both;
}
.loading-dots span:nth-child(1) { animation-delay: -0.32s; }
.loading-dots span:nth-child(2) { animation-delay: -0.16s; }

@keyframes dot-bounce {
  0%, 80%, 100% { transform: scale(0); }
  40% { transform: scale(1); }
}

/* 推演面板 */
.evolution-panel {
  @apply mx-6 mb-4 rounded-xl overflow-hidden;
  background: rgba(20, 20, 40, 0.9);
  border: 1px solid rgba(168, 85, 247, 0.2);
  backdrop-filter: blur(12px);
}

.evolution-header {
  @apply flex items-center justify-between px-4 py-2;
  background: rgba(168, 85, 247, 0.1);
  border-bottom: 1px solid rgba(168, 85, 247, 0.15);
}

.evolution-header h3 {
  @apply text-sm font-semibold;
  color: #a855f7;
}

.close-btn {
  @apply text-lg;
  color: #888;
}
.close-btn:hover {
  color: #fff;
}

.evolution-content {
  @apply p-4;
}

.evolution-summary {
  @apply text-sm mb-2;
  color: #d4d4d4;
}

.evolution-stats {
  @apply flex gap-4 text-xs mb-3;
  color: #888;
}

.evolution-detail {
  @apply text-xs p-3 rounded-lg overflow-auto max-h-40;
  background: rgba(0, 0, 0, 0.3);
  color: #aaa;
  font-family: 'JetBrains Mono', monospace;
}

/* 输入区域 */
.input-area {
  @apply flex items-end gap-3 px-6 py-4;
  border-top: 1px solid rgba(212, 168, 67, 0.1);
  background: rgba(10, 10, 10, 0.6);
  backdrop-filter: blur(12px);
}

.input-field {
  @apply flex-1 resize-none rounded-xl px-4 py-3 text-sm;
  background: rgba(255, 255, 255, 0.03);
  border: 1px solid rgba(255, 255, 255, 0.08);
  color: #e8e8e8;
  outline: none;
  transition: border-color 0.2s;
  min-height: 44px;
  max-height: 120px;
}
.input-field:focus {
  border-color: rgba(212, 168, 67, 0.4);
}
.input-field::placeholder {
  color: #555;
}
.input-field:disabled {
  @apply opacity-50;
}

.send-btn {
  @apply px-5 py-3 rounded-xl text-sm font-medium;
  background: linear-gradient(135deg, #d4a843, #b8922e);
  color: #0a0a0a;
  transition: all 0.2s;
  min-height: 44px;
}
.send-btn:hover:not(:disabled) {
  transform: translateY(-1px);
  box-shadow: 0 4px 12px rgba(212, 168, 67, 0.3);
}
.send-btn:disabled {
  @apply opacity-40 cursor-not-allowed;
}

.spinner {
  @apply inline-block w-4 h-4 border-2 border-current border-t-transparent rounded-full;
  animation: spin 0.6s linear infinite;
}

@keyframes spin {
  to { transform: rotate(360deg); }
}

/* 过渡动画 */
.slide-up-enter-active,
.slide-up-leave-active {
  transition: all 0.3s ease;
}
.slide-up-enter-from,
.slide-up-leave-to {
  opacity: 0;
  transform: translateY(20px);
}

/* 响应式 */
@media (max-width: 768px) {
  .agent-header {
    @apply px-4 py-2;
  }
  .chat-container {
    @apply px-4;
  }
  .input-area {
    @apply px-4 py-3;
  }
  .welcome-examples {
    @apply flex-col items-center;
  }
}
</style>
