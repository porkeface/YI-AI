<template>
  <Transition name="fade">
    <button
      v-if="visible"
      @click="scrollToTop"
      class="fixed bottom-8 right-8 z-40 p-3 rounded-full border border-gold-500/30 bg-ink-900/90 backdrop-blur-sm
             hover:bg-ink-800 hover:border-gold-500/50 transition-all duration-200 shadow-lg"
      title="返回顶部"
    >
      <span class="text-gold-500 text-lg">↑</span>
    </button>
  </Transition>
</template>

<script setup lang="ts">
import { ref, onMounted, onUnmounted } from 'vue'

const visible = ref(false)

function handleScroll() {
  visible.value = window.scrollY > 300
}

function scrollToTop() {
  window.scrollTo({
    top: 0,
    behavior: 'smooth',
  })
}

onMounted(() => {
  window.addEventListener('scroll', handleScroll)
})

onUnmounted(() => {
  window.removeEventListener('scroll', handleScroll)
})
</script>
