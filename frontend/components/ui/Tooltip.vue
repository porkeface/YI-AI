<template>
  <div
    class="relative inline-block"
    @mouseenter="show = true"
    @mouseleave="show = false"
  >
    <slot />

    <Transition name="fade">
      <div
        v-if="show"
        class="absolute z-50 px-3 py-2 text-sm rounded-lg border shadow-lg whitespace-nowrap"
        :class="positionClasses"
      >
        {{ text }}
      </div>
    </Transition>
  </div>
</template>

<script setup lang="ts">
import { ref, computed } from 'vue'

interface Props {
  text: string
  position?: 'top' | 'bottom' | 'left' | 'right'
}

const props = withDefaults(defineProps<Props>(), {
  position: 'top',
})

const show = ref(false)

const positionClasses = computed(() => {
  const base = 'border-gold-500/50 bg-ink-900/95 text-gold-500 backdrop-blur-sm'

  switch (props.position) {
    case 'top':
      return `${base} bottom-full left-1/2 -translate-x-1/2 mb-2`
    case 'bottom':
      return `${base} top-full left-1/2 -translate-x-1/2 mt-2`
    case 'left':
      return `${base} right-full top-1/2 -translate-y-1/2 mr-2`
    case 'right':
      return `${base} left-full top-1/2 -translate-y-1/2 ml-2`
    default:
      return base
  }
})
</script>
