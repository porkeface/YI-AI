<template>
  <button
    @click="toggleTheme"
    class="p-2 rounded-lg border border-gold-500/30 bg-ink-800 hover:bg-ink-700 transition-colors duration-200"
    :title="isDark ? '切换到亮色模式' : '切换到暗色模式'"
  >
    <span class="text-gold-500">
      {{ isDark ? '☀' : '🌙' }}
    </span>
  </button>
</template>

<script setup lang="ts">
import { computed } from 'vue'

const colorMode = useColorMode()

const isDark = computed(() => colorMode.value === 'dark')

function toggleTheme() {
  colorMode.preference = isDark.value ? 'light' : 'dark'
}
</script>
