<template>
  <div class="relative">
    <button
      @click="isOpen = !isOpen"
      class="p-2 rounded-lg border border-gold-500/30 bg-ink-800 hover:bg-ink-700 transition-colors duration-200 text-gold-500 text-sm"
    >
      {{ currentLocale }}
    </button>

    <Transition name="fade">
      <div
        v-if="isOpen"
        class="absolute right-0 top-10 w-24 py-1 rounded-lg border border-gold-500/30 bg-ink-900/95 backdrop-blur-sm shadow-lg"
      >
        <button
          v-for="locale in locales"
          :key="locale.code"
          @click="switchLocale(locale.code)"
          class="w-full px-3 py-2 text-left text-sm text-gold-500/80 hover:bg-gold-500/10 hover:text-gold-500 transition-colors duration-200"
        >
          {{ locale.name }}
        </button>
      </div>
    </Transition>
  </div>
</template>

<script setup lang="ts">
import { ref, computed } from 'vue'

const isOpen = ref(false)

const locales = [
  { code: 'zh', name: '中文' },
  { code: 'en', name: 'English' },
]

const currentLocaleCode = ref('zh')

const currentLocale = computed(() => {
  const locale = locales.find(l => l.code === currentLocaleCode.value)
  return locale?.name || '中文'
})

function switchLocale(code: string) {
  currentLocaleCode.value = code
  isOpen.value = false
  // 这里可以集成i18n
}
</script>
