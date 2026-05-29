<template>
  <button
    :type="type"
    :disabled="disabled"
    :class="[
      'inline-flex items-center justify-center font-medium rounded-lg transition-all duration-200',
      'focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-offset-ink-900',
      sizeClasses,
      variantClasses,
      { 'opacity-50 cursor-not-allowed': disabled },
    ]"
    @click="$emit('click', $event)"
  >
    <slot />
  </button>
</template>

<script setup lang="ts">
import { computed } from 'vue'

interface Props {
  variant?: 'primary' | 'secondary' | 'danger'
  size?: 'sm' | 'md' | 'lg'
  type?: 'button' | 'submit' | 'reset'
  disabled?: boolean
}

const props = withDefaults(defineProps<Props>(), {
  variant: 'primary',
  size: 'md',
  type: 'button',
  disabled: false,
})

defineEmits<{
  click: [event: MouseEvent]
}>()

const sizeClasses = computed(() => {
  switch (props.size) {
    case 'sm':
      return 'px-3 py-1.5 text-sm'
    case 'md':
      return 'px-4 py-2 text-sm'
    case 'lg':
      return 'px-6 py-3 text-base'
    default:
      return 'px-4 py-2 text-sm'
  }
})

const variantClasses = computed(() => {
  switch (props.variant) {
    case 'primary':
      return 'bg-gradient-to-r from-gold-600 to-gold-500 text-ink-900 hover:from-gold-500 hover:to-gold-400 focus:ring-gold-500 glow-gold'
    case 'secondary':
      return 'bg-ink-700 text-gold-500 border border-gold-500/30 hover:border-gold-500/60 hover:bg-ink-600 focus:ring-gold-500'
    case 'danger':
      return 'bg-red-600 text-white hover:bg-red-500 focus:ring-red-500'
    default:
      return 'bg-gradient-to-r from-gold-600 to-gold-500 text-ink-900 hover:from-gold-500 hover:to-gold-400 focus:ring-gold-500'
  }
})
</script>
