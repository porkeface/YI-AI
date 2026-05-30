<template>
  <div class="min-h-screen flex flex-col items-center justify-center px-4">
    <SeoHead title="首页" description="YI-AI 易学AI系统 - 东方变化学AI操作系统，智能六爻排盘" />

    <!-- 太极动画 -->
    <div class="relative w-64 h-64 mb-8">
      <TaijiAnimation />
    </div>

    <!-- 标题 -->
    <h1 class="text-4xl md:text-5xl font-bold text-gold-500 text-glow-gold font-chinese mb-4 text-center">
      YI-AI
    </h1>
    <p class="text-gold-500/60 text-lg mb-8 text-center">
      东方变化学AI操作系统
    </p>

    <!-- 开始按钮 -->
    <NuxtLink
      to="/divination"
      class="group relative px-8 py-4 bg-gradient-to-r from-gold-600 to-gold-500 text-ink-900 font-bold rounded-lg
             hover:from-gold-500 hover:to-gold-400 transition-all duration-300 glow-gold
             transform hover:scale-105 active:scale-95"
    >
      <span class="relative z-10">开始占卜</span>
      <div class="absolute inset-0 bg-gold-400 rounded-lg opacity-0 group-hover:opacity-20 transition-opacity duration-300"></div>
    </NuxtLink>

    <!-- 特性介绍 -->
    <div class="mt-16 grid grid-cols-1 md:grid-cols-3 gap-8 max-w-4xl">
      <div
        v-for="feature in features"
        :key="feature.title"
        class="text-center p-6 rounded-lg border border-gold-500/20 bg-ink-900/50 hover:border-gold-500/40 transition-colors duration-300"
      >
        <div class="text-3xl mb-3">{{ feature.icon }}</div>
        <h3 class="text-gold-500 font-bold mb-2">{{ feature.title }}</h3>
        <p class="text-gold-500/60 text-sm">{{ feature.description }}</p>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
const features = [
  {
    icon: '☯',
    title: '智能排盘',
    description: '基于传统六爻排盘规则，AI智能解析卦象',
  },
  {
    icon: '📊',
    title: '深度分析',
    description: '结合五行生克、六亲六神，提供全面解读',
  },
  {
    icon: '🤖',
    title: 'AI解卦',
    description: '大语言模型辅助，给出通俗易懂的建议',
  },
]
</script>
