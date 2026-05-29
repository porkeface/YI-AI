<template>
  <div class="relative">
    <!-- 桌面导航 -->
    <div class="hidden md:flex items-center space-x-6">
      <slot />
    </div>

    <!-- 移动端汉堡菜单 -->
    <div class="md:hidden">
      <button
        @click="isOpen = !isOpen"
        class="p-2 rounded-lg border border-gold-500/30 bg-ink-800 hover:bg-ink-700 transition-colors duration-200"
      >
        <div class="w-5 h-0.5 bg-gold-500 mb-1"></div>
        <div class="w-5 h-0.5 bg-gold-500 mb-1"></div>
        <div class="w-5 h-0.5 bg-gold-500"></div>
      </button>

      <!-- 移动端菜单 -->
      <Transition name="slide-down">
        <div
          v-if="isOpen"
          class="absolute right-0 top-12 w-48 py-2 rounded-lg border border-gold-500/30 bg-ink-900/95 backdrop-blur-sm shadow-lg"
        >
          <slot />
        </div>
      </Transition>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue'

const isOpen = ref(false)
</script>

<style scoped>
.slide-down-enter-active,
.slide-down-leave-active {
  transition: transform 0.2s ease, opacity 0.2s ease;
}

.slide-down-enter-from,
.slide-down-leave-to {
  transform: translateY(-10px);
  opacity: 0;
}
</style>
