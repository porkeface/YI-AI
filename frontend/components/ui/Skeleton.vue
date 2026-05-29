<template>
  <div
    class="animate-pulse bg-ink-700 rounded"
    :class="classes"
    :style="style"
  ></div>
</template>

<script setup lang="ts">
import { computed } from 'vue'

interface Props {
  width?: string
  height?: string
  rounded?: boolean
}

const props = withDefaults(defineProps<Props>(), {
  width: '100%',
  height: '1rem',
  rounded: false,
})

const classes = computed(() => {
  return props.rounded ? 'rounded-full' : 'rounded'
})

const style = computed(() => {
  return {
    width: props.width,
    height: props.height,
  }
})
</script>
