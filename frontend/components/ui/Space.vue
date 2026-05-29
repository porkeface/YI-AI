<template>
  <div
    :class="[
      'flex',
      vertical ? 'flex-col' : 'flex-row',
      alignClasses,
      justifyClasses,
    ]"
    :style="{ gap: `${size}px` }"
  >
    <slot />
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'

interface Props {
  vertical?: boolean
  size?: number
  align?: 'start' | 'center' | 'end' | 'stretch'
  justify?: 'start' | 'center' | 'end' | 'between' | 'around'
}

const props = withDefaults(defineProps<Props>(), {
  vertical: false,
  size: 8,
  align: 'center',
  justify: 'start',
})

const alignClasses = computed(() => {
  switch (props.align) {
    case 'start':
      return 'items-start'
    case 'center':
      return 'items-center'
    case 'end':
      return 'items-end'
    case 'stretch':
      return 'items-stretch'
    default:
      return 'items-center'
  }
})

const justifyClasses = computed(() => {
  switch (props.justify) {
    case 'start':
      return 'justify-start'
    case 'center':
      return 'justify-center'
    case 'end':
      return 'justify-end'
    case 'between':
      return 'justify-between'
    case 'around':
      return 'justify-around'
    default:
      return 'justify-start'
  }
})
</script>
