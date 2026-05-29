<template>
  <div class="min-h-screen bg-ink-800">
    <!-- 顶部导航栏 -->
    <header class="fixed top-0 left-0 right-0 z-50 bg-ink-900/90 backdrop-blur-sm border-b border-gold-500/30">
      <nav class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div class="flex items-center justify-between h-16">
          <!-- Logo -->
          <NuxtLink to="/" class="flex items-center space-x-2">
            <span class="text-2xl font-bold text-gold-500 text-glow-gold font-chinese">
              YI-AI
            </span>
            <span class="text-xs text-gold-500/60 hidden sm:block">
              易学AI系统
            </span>
          </NuxtLink>

          <!-- 导航链接 -->
          <ResponsiveNav>
            <NuxtLink
              to="/divination"
              class="text-gold-500/80 hover:text-gold-400 transition-colors duration-200 text-sm font-medium"
              active-class="text-gold-400"
            >
              起卦
            </NuxtLink>
            <NuxtLink
              to="/history"
              class="text-gold-500/80 hover:text-gold-400 transition-colors duration-200 text-sm font-medium"
              active-class="text-gold-400"
            >
              历史
            </NuxtLink>
            <NuxtLink
              to="/graph"
              class="text-gold-500/80 hover:text-gold-400 transition-colors duration-200 text-sm font-medium"
              active-class="text-gold-400"
            >
              图谱
            </NuxtLink>
            <NuxtLink
              to="/agent"
              class="text-gold-500/80 hover:text-gold-400 transition-colors duration-200 text-sm font-medium"
              active-class="text-gold-400"
            >
              Agent
            </NuxtLink>
            <NuxtLink
              to="/reasoning"
              class="text-gold-500/80 hover:text-gold-400 transition-colors duration-200 text-sm font-medium"
              active-class="text-gold-400"
            >
              推理
            </NuxtLink>
            <NuxtLink
              to="/qimen"
              class="text-gold-500/80 hover:text-gold-400 transition-colors duration-200 text-sm font-medium"
              active-class="text-gold-400"
            >
              奇门
            </NuxtLink>
            <NuxtLink
              to="/ziwei"
              class="text-gold-500/80 hover:text-gold-400 transition-colors duration-200 text-sm font-medium"
              active-class="text-gold-400"
            >
              紫微
            </NuxtLink>
            <NuxtLink
              to="/observation"
              class="text-gold-500/80 hover:text-gold-400 transition-colors duration-200 text-sm font-medium"
              active-class="text-gold-400"
            >
              观察
            </NuxtLink>
            <NuxtLink
              to="/analytics"
              class="text-gold-500/80 hover:text-gold-400 transition-colors duration-200 text-sm font-medium"
              active-class="text-gold-400"
            >
              分析
            </NuxtLink>
            <ClientOnly>
              <ThemeToggle />
              <LanguageSwitcher />
            </ClientOnly>
          </ResponsiveNav>
        </div>
      </nav>
    </header>

    <!-- 主要内容 -->
    <main class="pt-16">
      <slot />
    </main>

    <!-- 底部 -->
    <footer class="py-6 border-t border-gold-500/20 mt-16">
      <div class="max-w-7xl mx-auto px-4 text-center text-gold-500/40 text-sm">
        <p>YI-AI 易学AI系统 - 东方变化学AI操作系统</p>
      </div>
    </footer>
  </div>
</template>

<script setup lang="ts">
// 默认布局
</script>
