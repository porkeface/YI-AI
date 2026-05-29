<template>
  <div v-if="error" class="p-4 rounded-lg border border-red-500/50 bg-red-500/10">
    <div class="flex items-center gap-2 mb-2">
      <span class="text-red-400">⚠</span>
      <h3 class="text-red-400 font-bold">出错了</h3>
    </div>
    <p class="text-red-400/80 text-sm">{{ error }}</p>
    <button
      v-if="retryable"
      @click="$emit('retry')"
      class="mt-3 px-4 py-2 bg-red-500/20 text-red-400 rounded hover:bg-red-500/30 transition-colors duration-200 text-sm"
    >
      重试
    </button>
  </div>
</template>

<script setup lang="ts">
interface Props {
  error: string | null
  retryable?: boolean
}

const props = withDefaults(defineProps<Props>(), {
  retryable: false,
})

defineEmits<{
  retry: []
}>()
</script>
