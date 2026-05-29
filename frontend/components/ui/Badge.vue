<template>
  <span
    class="inline-flex items-center justify-center px-2 py-0.5 text-xs font-medium rounded-full"
    :class="variantClasses"
  >
    <slot />
  </span>
</template>

<script setup lang="ts">
import { computed } from 'vue'

interface Props {
  variant?: 'default' | 'success' | 'warning' | 'error' | 'info'
  dot?: boolean
}

const props = withDefaults(defineProps<Props>(), {
  variant: 'default',
  dot: false,
})

const variantClasses = computed(() => {
  switch (props.variant) {
    case 'success':
      return 'bg-green-500/20 text-green-400'
    case 'warning':
      return 'bg-yellow-500/20 text-yellow-400'
    case 'error':
      return 'bg-red-500/20 text-red-400'
    case 'info':
      return 'bg-blue-500/20 text-blue-400'
    case 'default':
    default:
      return 'bg-gold-500/20 text-gold-500'
  }
})
</script>
