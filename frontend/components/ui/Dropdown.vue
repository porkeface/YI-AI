<template>
  <div class="relative" ref="dropdownRef">
    <!-- 触发器 -->
    <div @click="toggle">
      <slot name="trigger" />
    </div>

    <!-- 菜单内容 -->
    <Transition name="fade">
      <div
        v-if="isOpen"
        class="absolute z-50 mt-2 w-48 rounded-lg border border-gold-500/30 bg-ink-900/95 backdrop-blur-sm shadow-lg"
        :class="positionClasses"
      >
        <slot />
      </div>
    </Transition>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, onUnmounted } from 'vue'

interface Props {
  position?: 'left' | 'right'
}

const props = withDefaults(defineProps<Props>(), {
  position: 'left',
})

const isOpen = ref(false)
const dropdownRef = ref<HTMLElement | null>(null)

const positionClasses = computed(() => {
  return props.position === 'right' ? 'right-0' : 'left-0'
})

function toggle() {
  isOpen.value = !isOpen.value
}

function close() {
  isOpen.value = false
}

function handleClickOutside(event: MouseEvent) {
  if (dropdownRef.value && !dropdownRef.value.contains(event.target as Node)) {
    close()
  }
}

onMounted(() => {
  document.addEventListener('click', handleClickOutside)
})

onUnmounted(() => {
  document.removeEventListener('click', handleClickOutside)
})
</script>
