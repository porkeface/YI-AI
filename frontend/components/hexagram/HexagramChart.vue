<template>
  <div class="hexagram-chart border border-gold-500/20 rounded-xl overflow-hidden bg-gradient-to-br from-ink-900/90 to-ink-800/50 backdrop-blur-sm">
    <!-- 卦名标题 -->
    <div class="p-6 border-b border-gold-500/20 text-center relative overflow-hidden">
      <!-- 背景装饰 -->
      <div class="absolute inset-0 bg-gradient-to-b from-gold-500/5 to-transparent"></div>
      <div class="relative">
        <h2 class="text-3xl font-bold text-gold-500 text-glow-gold font-chinese">
          {{ hexagram.name }}
        </h2>
        <p class="text-gold-500/50 text-sm mt-2">
          {{ hexagram.fullName }}（{{ hexagram.palace }}宫）
        </p>
      </div>
    </div>

    <!-- 排盘表格 -->
    <div class="overflow-x-auto">
      <table class="w-full">
        <thead>
          <tr class="border-b border-gold-500/20">
            <th class="px-4 py-3 text-gold-500/70 text-xs font-medium uppercase tracking-wider">六神</th>
            <th class="px-4 py-3 text-gold-500/70 text-xs font-medium uppercase tracking-wider">六亲</th>
            <th class="px-4 py-3 text-gold-500/70 text-xs font-medium uppercase tracking-wider">爻</th>
            <th class="px-4 py-3 text-gold-500/70 text-xs font-medium uppercase tracking-wider">干支</th>
            <th class="px-4 py-3 text-gold-500/70 text-xs font-medium uppercase tracking-wider">动变</th>
          </tr>
        </thead>
        <tbody>
          <tr
            v-for="(line, index) in reversedLines"
            :key="line.position"
            class="border-b border-gold-500/10 hover:bg-gold-500/5 transition-all duration-300 line-row"
            :class="{ 'bg-gold-500/10': line.isShi || line.isYing }"
            :style="{ animationDelay: `${index * 80}ms` }"
          >
            <!-- 六神 -->
            <td class="px-4 py-3 text-center text-gold-500/80 text-sm">
              {{ line.sixSpirit }}
            </td>

            <!-- 六亲 -->
            <td class="px-4 py-3 text-center text-gold-500 text-sm font-medium">
              {{ line.sixRelation }}
            </td>

            <!-- 爻象 -->
            <td class="px-4 py-3">
              <YinYangLine
                :yin-yang="line.yinYang"
                :is-moving="line.isMoving"
                :is-shi="line.isShi"
                :is-ying="line.isYing"
              />
            </td>

            <!-- 干支 -->
            <td class="px-4 py-3 text-center text-gold-500/80 text-sm">
              {{ line.ganZhi.gan }}{{ line.ganZhi.zhi }}
            </td>

            <!-- 动变 -->
            <td class="px-4 py-3 text-center text-gold-500/80 text-sm">
              <div v-if="line.isMoving" class="flex items-center justify-center gap-1">
                <span class="text-gold-400">○</span>
                <span class="text-gold-500/60">→</span>
                <YinYangLine
                  :yin-yang="line.changedYinYang || line.yinYang"
                  :is-moving="false"
                  :is-shi="false"
                  :is-ying="false"
                />
              </div>
            </td>
          </tr>
        </tbody>
      </table>
    </div>

    <!-- 世爻应爻说明 -->
    <div class="p-4 border-t border-gold-500/20 flex justify-between text-sm">
      <div class="text-gold-500/70">
        <span class="text-gold-400 font-medium">世爻：</span>第{{ shiLine }}爻
      </div>
      <div class="text-gold-500/70">
        <span class="text-gold-400 font-medium">应爻：</span>第{{ yingLine }}爻
      </div>
    </div>

    <!-- 变卦信息（如有） -->
    <div v-if="changedHexagram" class="p-5 border-t border-gold-500/20">
      <div class="text-center mb-4">
        <div class="inline-block px-3 py-1 rounded-full bg-gold-500/10 border border-gold-500/20 mb-3">
          <p class="text-gold-500/60 text-xs">变卦</p>
        </div>
        <h3 class="text-xl font-bold text-gold-500 font-chinese">
          {{ changedHexagram.name }}
        </h3>
        <p class="text-gold-500/50 text-xs mt-1">
          {{ changedHexagram.fullName }}
        </p>
      </div>

      <!-- 变卦排盘 -->
      <div class="overflow-x-auto">
        <table class="w-full">
          <thead>
            <tr class="border-b border-gold-500/20">
              <th class="px-4 py-2 text-gold-500/80 text-sm">六神</th>
              <th class="px-4 py-2 text-gold-500/80 text-sm">六亲</th>
              <th class="px-4 py-2 text-gold-500/80 text-sm">爻</th>
              <th class="px-4 py-2 text-gold-500/80 text-sm">干支</th>
            </tr>
          </thead>
          <tbody>
            <tr
              v-for="(line, index) in reversedChangedLines"
              :key="line.position"
              class="border-b border-gold-500/10"
            >
              <td class="px-4 py-3 text-center text-gold-500/80 text-sm">
                {{ line.sixSpirit }}
              </td>
              <td class="px-4 py-3 text-center text-gold-500 text-sm font-medium">
                {{ line.sixRelation }}
              </td>
              <td class="px-4 py-3">
                <YinYangLine
                  :yin-yang="line.yinYang"
                  :is-moving="false"
                  :is-shi="line.isShi"
                  :is-ying="line.isYing"
                />
              </td>
              <td class="px-4 py-3 text-center text-gold-500/80 text-sm">
                {{ line.ganZhi.gan }}{{ line.ganZhi.zhi }}
              </td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import type { HexagramData } from '~/types/hexagram'

interface Props {
  hexagram: HexagramData
  changedHexagram?: HexagramData
}

const props = defineProps<Props>()

// 倒序显示（从第6爻到第1爻）
const reversedLines = computed(() => {
  return [...props.hexagram.lines].reverse()
})

// 变卦倒序显示
const reversedChangedLines = computed(() => {
  if (!props.changedHexagram) return []
  return [...props.changedHexagram.lines].reverse()
})

// 世爻位置
const shiLine = computed(() => {
  const shi = props.hexagram.lines.find(l => l.isShi)
  return shi ? shi.position : 4
})

// 应爻位置
const yingLine = computed(() => {
  const ying = props.hexagram.lines.find(l => l.isYing)
  return ying ? ying.position : 1
})

// GSAP动画
const isVisible = ref(false)

onMounted(() => {
  // 延迟触发动画
  setTimeout(() => {
    isVisible.value = true
  }, 100)
})
</script>

<style scoped>
.animate-pulse-gold {
  animation: pulse-gold 2s ease-in-out infinite;
}

@keyframes pulse-gold {
  0%, 100% { opacity: 1; }
  50% { opacity: 0.6; }
}

@keyframes line-slide-in {
  from {
    opacity: 0;
    transform: translateX(-12px);
  }
  to {
    opacity: 1;
    transform: translateX(0);
  }
}

.line-row {
  animation: line-slide-in 0.4s ease-out both;
}

@keyframes chart-fade-in {
  from {
    opacity: 0;
    transform: translateY(16px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

.hexagram-chart {
  animation: chart-fade-in 0.6s ease-out;
}
</style>
