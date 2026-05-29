<template>
  <NuxtLayout>
    <PageTransition>
      <NuxtPage />
    </PageTransition>
  </NuxtLayout>

  <!-- 开发模式工具 -->
  <ClientOnly>
    <PerformanceMonitor />
    <AccessibilityChecker />
  </ClientOnly>

  <!-- 通知容器 -->
  <NotificationContainer />

  <!-- 返回顶部按钮 -->
  <BackToTop />
</template>

<script setup lang="ts">
// 应用入口
</script>

<style>
/* 全局样式 */
@import url('https://fonts.googleapis.com/css2?family=Noto+Serif+SC:wght@400;600;700&display=swap');

body {
  font-family: 'Noto Serif SC', 'Source Han Serif SC', serif;
  background-color: #121212;
  color: #d4a017;
  min-height: 100vh;
}

/* 金色发光效果 */
.glow-gold {
  box-shadow: 0 0 10px rgba(212, 160, 23, 0.5),
              0 0 20px rgba(212, 160, 23, 0.3);
}

.glow-gold-strong {
  box-shadow: 0 0 15px rgba(212, 160, 23, 0.7),
              0 0 30px rgba(212, 160, 23, 0.5),
              0 0 45px rgba(212, 160, 23, 0.3);
}

.text-glow-gold {
  text-shadow: 0 0 10px rgba(212, 160, 23, 0.5),
               0 0 20px rgba(212, 160, 23, 0.3);
}

/* 滚动条样式 */
::-webkit-scrollbar {
  width: 8px;
}

::-webkit-scrollbar-track {
  background: #1a1a1a;
}

::-webkit-scrollbar-thumb {
  background: #d4a017;
  border-radius: 4px;
}

::-webkit-scrollbar-thumb:hover {
  background: #b8860b;
}
</style>
