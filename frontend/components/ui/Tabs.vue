<template>
  <div>
    <!-- 标签头 -->
    <div class="flex border-b border-gold-500/30 mb-4">
      <button
        v-for="tab in tabs"
        :key="tab.value"
        @click="activeTab = tab.value"
        :class="[
          'px-4 py-2 text-sm font-medium transition-colors duration-200 border-b-2 -mb-px',
          activeTab === tab.value
            ? 'border-gold-500 text-gold-500'
            : 'border-transparent text-gold-500/60 hover:text-gold-500/80',
        ]"
      >
        {{ tab.label }}
      </button>
    </div>

    <!-- 标签内容 -->
    <div>
      <slot :active-tab="activeTab" />
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue'

interface Tab {
  value: string
  label: string
}

interface Props {
  tabs: Tab[]
  defaultValue?: string
}

const props = withDefaults(defineProps<Props>(), {
  defaultValue: '',
})

const activeTab = ref(props.defaultValue || props.tabs[0]?.value || '')
</script>
