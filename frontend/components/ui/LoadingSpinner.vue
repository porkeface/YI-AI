<template>
  <div class="flex flex-col items-center justify-center p-8">
    <!-- 太极旋转 -->
    <div class="relative w-16 h-16 mb-4">
      <div class="absolute inset-0 rounded-full border-2 border-gold-500/30"></div>
      <div class="absolute inset-0 rounded-full border-2 border-transparent border-t-gold-500 animate-spin"></div>
    </div>

    <!-- 加载文字 -->
    <p class="text-gold-500/60 text-sm">{{ text }}</p>
  </div>
</template>

<script setup lang="ts">
interface Props {
  text?: string
}

const props = withDefaults(defineProps<Props>(), {
  text: '加载中...',
})
</script>
