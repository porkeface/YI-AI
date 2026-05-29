<template>
  <div :class="containerClasses">
    <slot />
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'

interface Props {
  maxWidth?: 'sm' | 'md' | 'lg' | 'xl' | '2xl' | 'full'
  padding?: boolean
}

const props = withDefaults(defineProps<Props>(), {
  maxWidth: 'lg',
  padding: true,
})

const containerClasses = computed(() => {
  const classes = ['mx-auto']

  // 最大宽度
  switch (props.maxWidth) {
    case 'sm':
      classes.push('max-w-sm')
      break
    case 'md':
      classes.push('max-w-md')
      break
    case 'lg':
      classes.push('max-w-4xl')
      break
    case 'xl':
      classes.push('max-w-6xl')
      break
    case '2xl':
      classes.push('max-w-7xl')
      break
    case 'full':
      classes.push('max-w-full')
      break
  }

  // 内边距
  if (props.padding) {
    classes.push('px-4 sm:px-6 lg:px-8')
  }

  return classes.join(' ')
})
</script>
