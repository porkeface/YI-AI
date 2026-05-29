<template>
  <button
    @click="toggle"
    :class="[
      'relative inline-flex h-6 w-11 items-center rounded-full transition-colors duration-200 focus:outline-none focus:ring-2 focus:ring-gold-500 focus:ring-offset-2 focus:ring-offset-ink-900',
      modelValue ? 'bg-gold-500' : 'bg-ink-600',
    ]"
    role="switch"
    :aria-checked="modelValue"
  >
    <span
      :class="[
        'inline-block h-4 w-4 transform rounded-full bg-white transition-transform duration-200',
        modelValue ? 'translate-x-6' : 'translate-x-1',
      ]"
    />
  </button>
</template>

<script setup lang="ts">
interface Props {
  modelValue: boolean
}

const props = defineProps<Props>()

const emit = defineEmits<{
  'update:modelValue': [value: boolean]
}>()

function toggle() {
  emit('update:modelValue', !props.modelValue)
}
</script>
