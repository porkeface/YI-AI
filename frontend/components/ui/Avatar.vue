<template>
  <div
    :class="[
      'flex items-center justify-center rounded-full bg-gold-500/20 text-gold-500 font-medium',
      sizeClasses,
    ]"
  >
    <img
      v-if="src"
      :src="src"
      :alt="alt"
      class="w-full h-full rounded-full object-cover"
    />
    <span v-else>{{ initials }}</span>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'

interface Props {
  src?: string
  alt?: string
  name?: string
  size?: 'sm' | 'md' | 'lg'
}

const props = withDefaults(defineProps<Props>(), {
  size: 'md',
})

const sizeClasses = computed(() => {
  switch (props.size) {
    case 'sm':
      return 'w-8 h-8 text-xs'
    case 'md':
      return 'w-10 h-10 text-sm'
    case 'lg':
      return 'w-12 h-12 text-base'
    default:
      return 'w-10 h-10 text-sm'
  }
})

const initials = computed(() => {
  if (!props.name) return '?'
  return props.name
    .split(' ')
    .map(word => word[0])
    .join('')
    .toUpperCase()
    .slice(0, 2)
})
</script>
