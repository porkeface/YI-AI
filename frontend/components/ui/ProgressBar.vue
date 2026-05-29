<template>
  <div class="w-full bg-ink-700 rounded-full overflow-hidden">
    <div
      class="h-2 rounded-full transition-all duration-300 ease-out"
      :class="variantClasses"
      :style="{ width: `${value}%` }"
    ></div>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'

interface Props {
  value: number
  variant?: 'default' | 'success' | 'warning' | 'error'
}

const props = withDefaults(defineProps<Props>(), {
  variant: 'default',
})

const variantClasses = computed(() => {
  switch (props.variant) {
    case 'success':
      return 'bg-green-500'
    case 'warning':
      return 'bg-yellow-500'
    case 'error':
      return 'bg-red-500'
    case 'default':
    default:
      return 'bg-gold-500'
  }
})
</script>
