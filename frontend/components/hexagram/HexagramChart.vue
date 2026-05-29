<template>
  <div class="border border-gold-500/30 rounded-lg overflow-hidden bg-ink-900/80">
    <!-- 卦名标题 -->
    <div class="p-4 border-b border-gold-500/30 text-center">
      <h2 class="text-2xl font-bold text-gold-500 text-glow-gold font-chinese">
        {{ hexagram.name }}
      </h2>
      <p class="text-gold-500/60 text-sm mt-1">
        {{ hexagram.fullName }}（{{ hexagram.palace }}宫）
      </p>
    </div>

    <!-- 排盘表格 -->
    <div class="overflow-x-auto">
      <table class="w-full">
        <thead>
          <tr class="border-b border-gold-500/20">
            <th class="px-4 py-2 text-gold-500/80 text-sm">六神</th>
            <th class="px-4 py-2 text-gold-500/80 text-sm">六亲</th>
            <th class="px-4 py-2 text-gold-500/80 text-sm">爻</th>
            <th class="px-4 py-2 text-gold-500/80 text-sm">干支</th>
            <th class="px-4 py-2 text-gold-500/80 text-sm">动变</th>
          </tr>
        </thead>
        <tbody>
          <tr
            v-for="(line, index) in reversedLines"
            :key="line.position"
            class="border-b border-gold-500/10 hover:bg-gold-500/5 transition-colors duration-200"
            :class="{ 'bg-gold-500/10': line.isShi || line.isYing }"
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
    <div class="p-4 border-t border-gold-500/30 flex justify-between text-sm">
      <div class="text-gold-500/80">
        <span class="font-bold">世爻：</span>第{{ shiLine }}爻
      </div>
      <div class="text-gold-500/80">
        <span class="font-bold">应爻：</span>第{{ yingLine }}爻
      </div>
    </div>

    <!-- 变卦信息（如有） -->
    <div v-if="changedHexagram" class="p-4 border-t border-gold-500/30">
      <div class="text-center mb-4">
        <p class="text-gold-500/60 text-sm mb-2">变卦</p>
        <h3 class="text-lg font-bold text-gold-500 font-chinese">
          {{ changedHexagram.name }}
        </h3>
        <p class="text-gold-500/60 text-xs mt-1">
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
</style>
