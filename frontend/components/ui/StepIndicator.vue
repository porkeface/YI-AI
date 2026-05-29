<template>
  <div class="flex items-center justify-between">
    <template v-for="(step, index) in steps" :key="index">
      <!-- 步骤圆圈 -->
      <div class="flex flex-col items-center">
        <div
          :class="[
            'w-8 h-8 rounded-full flex items-center justify-center text-sm font-medium border-2 transition-all duration-300',
            getStepClasses(index),
          ]"
        >
          <span v-if="index < currentStep">✓</span>
          <span v-else>{{ index + 1 }}</span>
        </div>
        <span class="mt-2 text-xs text-gold-500/60">{{ step }}</span>
      </div>

      <!-- 连接线 -->
      <div
        v-if="index < steps.length - 1"
        :class="[
          'flex-1 h-0.5 mx-2 transition-all duration-300',
          index < currentStep ? 'bg-gold-500' : 'bg-ink-600',
        ]"
      ></div>
    </template>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'

interface Props {
  steps: string[]
  currentStep: number
}

const props = defineProps<Props>()

function getStepClasses(index: number) {
  if (index < props.currentStep) {
    return 'border-gold-500 bg-gold-500/20 text-gold-500'
  } else if (index === props.currentStep) {
    return 'border-gold-500 bg-gold-500 text-ink-900'
  } else {
    return 'border-ink-600 bg-ink-800 text-ink-400'
  }
}
</script>
