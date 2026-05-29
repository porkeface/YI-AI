<template>
  <Transition name="fade">
    <div
      v-if="visible"
      class="fixed inset-0 z-50 flex items-center justify-center p-4"
    >
      <!-- 背景遮罩 -->
      <div
        class="absolute inset-0 bg-ink-900/80 backdrop-blur-sm"
        @click="close"
      ></div>

      <!-- 模态框内容 -->
      <div
        class="relative w-full p-6 rounded-lg border border-gold-500/30 bg-ink-800 shadow-xl"
        :class="sizeClass"
      >
        <!-- 标题 -->
        <div class="flex items-center justify-between mb-4">
          <h2 class="text-lg font-bold text-gold-500">{{ title }}</h2>
          <button
            @click="close"
            class="text-gold-500/60 hover:text-gold-500 transition-colors duration-200"
          >
            ✕
          </button>
        </div>

        <!-- 内容 -->
        <div class="mb-6">
          <slot />
        </div>

        <!-- 底部按钮 -->
        <div v-if="$slots.footer" class="flex justify-end gap-3">
          <slot name="footer" />
        </div>
      </div>
    </div>
  </Transition>
</template>

<script setup lang="ts">
import { computed } from 'vue'
interface Props {
  visible: boolean
  title: string
  size?: 'sm' | 'md' | 'lg'
}

const props = withDefaults(defineProps<Props>(), {
  size: 'md',
})

const sizeClass = computed(() => {
  switch (props.size) {
    case 'sm': return 'max-w-md'
    case 'lg': return 'max-w-3xl'
    default: return 'max-w-lg'
  }
})

const emit = defineEmits<{
  'update:visible': [value: boolean]
  close: []
}>()

function close() {
  emit('update:visible', false)
  emit('close')
}
</script>
