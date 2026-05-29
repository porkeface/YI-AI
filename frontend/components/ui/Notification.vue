<template>
  <Transition name="slide-right">
    <div
      v-if="visible"
      class="fixed top-20 right-4 z-50 p-4 rounded-lg border shadow-lg max-w-sm"
      :class="typeClasses"
    >
      <div class="flex items-start gap-3">
        <span class="text-lg">{{ icon }}</span>
        <div class="flex-1">
          <h4 class="font-bold text-sm">{{ title }}</h4>
          <p class="text-sm opacity-80 mt-1">{{ message }}</p>
        </div>
        <button
          @click="close"
          class="opacity-60 hover:opacity-100 transition-opacity duration-200"
        >
          ✕
        </button>
      </div>
    </div>
  </Transition>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'

interface Props {
  type?: 'success' | 'error' | 'warning' | 'info'
  title: string
  message: string
  duration?: number
}

const props = withDefaults(defineProps<Props>(), {
  type: 'info',
  duration: 3000,
})

const emit = defineEmits<{
  close: []
}>()

const visible = ref(false)

const typeClasses = computed(() => {
  switch (props.type) {
    case 'success':
      return 'border-green-500/50 bg-green-500/10 text-green-400'
    case 'error':
      return 'border-red-500/50 bg-red-500/10 text-red-400'
    case 'warning':
      return 'border-yellow-500/50 bg-yellow-500/10 text-yellow-400'
    case 'info':
    default:
      return 'border-gold-500/50 bg-gold-500/10 text-gold-400'
  }
})

const icon = computed(() => {
  switch (props.type) {
    case 'success':
      return '✓'
    case 'error':
      return '✕'
    case 'warning':
      return '⚠'
    case 'info':
    default:
      return 'ℹ'
  }
})

function close() {
  visible.value = false
  emit('close')
}

onMounted(() => {
  visible.value = true

  if (props.duration > 0) {
    setTimeout(() => {
      close()
    }, props.duration)
  }
})
</script>

<style scoped>
.slide-right-enter-active,
.slide-right-leave-active {
  transition: transform 0.3s ease, opacity 0.3s ease;
}

.slide-right-enter-from,
.slide-right-leave-to {
  transform: translateX(100%);
  opacity: 0;
}
</style>
