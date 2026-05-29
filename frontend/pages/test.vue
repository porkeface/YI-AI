<template>
  <div class="min-h-screen py-8 px-4">
    <div class="max-w-4xl mx-auto">
      <h1 class="text-3xl font-bold text-gold-500 text-glow-gold font-chinese mb-8 text-center">
        排盘测试
      </h1>

      <!-- 测试控制 -->
      <div class="mb-8 p-4 rounded-lg border border-gold-500/30 bg-ink-900/50">
        <h2 class="text-lg font-bold text-gold-500 mb-4">测试控制</h2>
        <div class="flex gap-4">
          <Button variant="primary" @click="testTimeDivination">
            时间起卦测试
          </Button>
          <Button variant="secondary" @click="testNumberDivination">
            数字起卦测试
          </Button>
          <Button variant="secondary" @click="testManualDivination">
            手动排盘测试
          </Button>
        </div>
      </div>

      <!-- 测试结果 -->
      <div v-if="testResult" class="mt-8">
        <h2 class="text-lg font-bold text-gold-500 mb-4">测试结果</h2>

        <!-- 排盘展示 -->
        <div class="mb-8">
          <HexagramChart :hexagram="testResult.hexagram" />
        </div>

        <!-- 分析结果 -->
        <div v-if="testResult.analysis" class="mb-8">
          <AnalysisPanel :analysis="testResult.analysis" />
        </div>

        <!-- 原始数据 -->
        <div class="p-4 rounded-lg border border-gold-500/30 bg-ink-900/50">
          <h3 class="text-gold-500 font-bold mb-2">原始数据</h3>
          <pre class="text-gold-500/60 text-sm overflow-auto">{{ JSON.stringify(testResult, null, 2) }}</pre>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue'
import { useMockData } from '~/composables/useMockData'

const mockData = useMockData()

const testResult = ref<any>(null)

function testTimeDivination() {
  const response = mockData.getMockDivinationResponse(
    '测试时间起卦',
    'time'
  )

  if (response.success && response.data) {
    testResult.value = response.data
  }
}

function testNumberDivination() {
  const response = mockData.getMockDivinationResponse(
    '测试数字起卦',
    'number',
    undefined,
    [123, 456]
  )

  if (response.success && response.data) {
    testResult.value = response.data
  }
}

function testManualDivination() {
  const response = mockData.getMockDivinationResponse(
    '测试手动排盘',
    'manual',
    ['yang', 'yin', 'yang', 'yin', 'yang', 'yin']
  )

  if (response.success && response.data) {
    testResult.value = response.data
  }
}
</script>
