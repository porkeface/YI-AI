<template>
  <span
    class="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium"
    :class="variantClasses"
  >
    <slot />
  </span>
</template>

<script setup lang="ts">
import { computed } from 'vue'

interface Props {
  variant?: 'default' | 'success' | 'warning' | 'error' | 'info'
}

const props = withDefaults(defineProps<Props>(), {
  variant: 'default',
})

const variantClasses = computed(() => {
  switch (props.variant) {
    case 'success':
      return 'bg-green-500/20 text-green-400 border border-green-500/50'
    case 'warning':
      return 'bg-yellow-500/20 text-yellow-400 border border-yellow-500/50'
    case 'error':
      return 'bg-red-500/20 text-red-400 border border-red-500/50'
    case 'info':
      return 'bg-blue-500/20 text-blue-400 border border-blue-500/50'
    case 'default':
    default:
      return 'bg-gold-500/20 text-gold-500 border border-gold-500/50'
  }
})
</script>
