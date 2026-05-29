<template>
  <div class="flex flex-col items-center justify-center p-8 text-center">
    <div class="text-4xl mb-4">{{ icon }}</div>
    <h3 class="text-lg font-bold text-gold-500 mb-2">{{ title }}</h3>
    <p class="text-gold-500/60 text-sm mb-4">{{ description }}</p>
    <slot />
  </div>
</template>

<script setup lang="ts">
interface Props {
  icon?: string
  title: string
  description: string
}

const props = withDefaults(defineProps<Props>(), {
  icon: '📭',
})
</script>
