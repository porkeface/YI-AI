<template>
  <div class="border border-gold-500/30 rounded-lg overflow-hidden">
    <button
      @click="toggle"
      class="w-full px-4 py-3 flex items-center justify-between bg-ink-800 hover:bg-ink-700 transition-colors duration-200"
    >
      <span class="text-gold-500 font-medium">{{ title }}</span>
      <span
        :class="[
          'text-gold-500/60 transition-transform duration-200',
          isOpen ? 'rotate-180' : '',
        ]"
      >
        ▼
      </span>
    </button>

    <Transition name="collapse">
      <div v-if="isOpen" class="px-4 py-3 bg-ink-900/50">
        <slot />
      </div>
    </Transition>
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue'

interface Props {
  title: string
  defaultOpen?: boolean
}

const props = withDefaults(defineProps<Props>(), {
  defaultOpen: false,
})

const isOpen = ref(props.defaultOpen)

function toggle() {
  isOpen.value = !isOpen.value
}
</script>

<style scoped>
.collapse-enter-active,
.collapse-leave-active {
  transition: max-height 0.3s ease, opacity 0.3s ease;
  overflow: hidden;
}

.collapse-enter-from,
.collapse-leave-to {
  max-height: 0;
  opacity: 0;
}

.collapse-enter-to,
.collapse-leave-from {
  max-height: 500px;
  opacity: 1;
}
</style>
