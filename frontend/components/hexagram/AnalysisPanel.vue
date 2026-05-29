<template>
  <div class="border border-gold-500/30 rounded-lg overflow-hidden bg-ink-900/80">
    <!-- 标题 -->
    <div class="p-4 border-b border-gold-500/30">
      <h3 class="text-lg font-bold text-gold-500 font-chinese">卦象分析</h3>
    </div>

    <!-- 吉凶 -->
    <div class="p-4 border-b border-gold-500/20 text-center">
      <span
        class="inline-block px-6 py-2 rounded-full text-lg font-bold"
        :class="fortuneClass"
      >
        {{ analysis.fortune }}
      </span>
    </div>

    <!-- 总体分析 -->
    <div class="p-4 border-b border-gold-500/20">
      <h4 class="text-gold-500/80 text-sm mb-2 font-medium">总体分析</h4>
      <p class="text-gold-500/90 leading-relaxed">
        {{ analysis.summary }}
      </p>
    </div>

    <!-- 建议 -->
    <div class="p-4 border-b border-gold-500/20">
      <h4 class="text-gold-500/80 text-sm mb-2 font-medium">建议</h4>
      <p class="text-gold-500/90 leading-relaxed">
        {{ analysis.advice }}
      </p>
    </div>

    <!-- 关键点 -->
    <div v-if="analysis.keyPoints.length > 0" class="p-4">
      <h4 class="text-gold-500/80 text-sm mb-3 font-medium">关键点</h4>
      <ul class="space-y-2">
        <li
          v-for="(point, index) in analysis.keyPoints"
          :key="index"
          class="flex items-start gap-2 text-gold-500/90"
        >
          <span class="text-gold-500 mt-1">•</span>
          <span>{{ point }}</span>
        </li>
      </ul>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import type { AnalysisResult } from '~/types/hexagram'

interface Props {
  analysis: AnalysisResult
}

const props = defineProps<Props>()

const fortuneClass = computed(() => {
  const fortune = props.analysis.fortune
  switch (fortune) {
    case '大吉':
    case '吉':
      return 'bg-green-500/20 text-green-400 border border-green-500/50'
    case '中吉':
    case '小吉':
      return 'bg-emerald-500/20 text-emerald-400 border border-emerald-500/50'
    case '平':
      return 'bg-yellow-500/20 text-yellow-400 border border-yellow-500/50'
    case '小凶':
    case '凶':
      return 'bg-orange-500/20 text-orange-400 border border-orange-500/50'
    case '大凶':
      return 'bg-red-500/20 text-red-400 border border-red-500/50'
    default:
      return 'bg-gold-500/20 text-gold-500 border border-gold-500/50'
  }
})
</script>
