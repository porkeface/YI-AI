<template>
  <button
    @click="$emit('click')"
    class="w-full px-4 py-2 text-left text-sm text-gold-500/80 hover:bg-gold-500/10 hover:text-gold-500 transition-colors duration-200"
  >
    <slot />
  </button>
</template>

<script setup lang="ts">
defineEmits<{
  click: []
}>()
</script>
