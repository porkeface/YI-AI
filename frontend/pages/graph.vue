<template>
  <div class="min-h-screen py-8 px-4">
    <div class="max-w-4xl mx-auto">
      <h1 class="text-3xl font-bold text-gold-500 text-glow-gold font-chinese mb-8 text-center">
        卦象图谱
      </h1>

      <EmptyState
        icon="📊"
        title="图谱开发中"
        description="六十四卦关系图谱功能正在开发中，敬请期待！"
      >
        <NuxtLink
          to="/divination"
          class="px-6 py-2 bg-gradient-to-r from-gold-600 to-gold-500 text-ink-900 font-bold rounded-lg
                 hover:from-gold-500 hover:to-gold-400 transition-all duration-300 glow-gold"
        >
          先去起卦
        </NuxtLink>
      </EmptyState>
    </div>
  </div>
</template>

<script setup lang="ts">
// 卦象图谱页面
</script>
