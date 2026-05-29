<template>
  <div
    class="relative flex items-center justify-center h-8"
    :class="{ 'animate-pulse-gold': isMoving }"
  >
    <!-- 阳爻：实线 -->
    <div
      v-if="yinYang === 'yang'"
      class="w-20 h-2 bg-gold-500 rounded-full shadow-lg"
      :class="{ 'glow-gold': isShi || isYing }"
    ></div>

    <!-- 阴爻：断线 -->
    <div v-else class="flex items-center justify-center gap-2">
      <div
        class="w-8 h-2 bg-gold-500 rounded-full shadow-lg"
        :class="{ 'glow-gold': isShi || isYing }"
      ></div>
      <div
        class="w-8 h-2 bg-gold-500 rounded-full shadow-lg"
        :class="{ 'glow-gold': isShi || isYing }"
      ></div>
    </div>

    <!-- 动爻标记 -->
    <div
      v-if="isMoving"
      class="absolute -right-8 w-5 h-5 border-2 border-gold-400 rounded-full flex items-center justify-center"
    >
      <div class="w-2 h-2 bg-gold-400 rounded-full"></div>
    </div>

    <!-- 世爻标记 -->
    <div
      v-if="isShi"
      class="absolute -left-8 text-xs text-gold-400 font-bold"
    >
      世
    </div>

    <!-- 应爻标记 -->
    <div
      v-if="isYing"
      class="absolute -left-8 text-xs text-gold-400 font-bold"
    >
      应
    </div>
  </div>
</template>

<script setup lang="ts">
import type { YinYang } from '~/types/hexagram'

interface Props {
  yinYang: YinYang
  isMoving?: boolean
  isShi?: boolean
  isYing?: boolean
}

const props = withDefaults(defineProps<Props>(), {
  isMoving: false,
  isShi: false,
  isYing: false,
})
</script>
