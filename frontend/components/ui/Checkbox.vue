<template>
  <label class="flex items-center gap-2 cursor-pointer">
    <input
      type="checkbox"
      :checked="modelValue"
      @change="updateValue"
      class="w-4 h-4 text-gold-500 bg-ink-700 border-gold-500/30 rounded focus:ring-gold-500 focus:ring-2"
    />
    <span class="text-gold-500/80 text-sm">{{ label }}</span>
  </label>
</template>

<script setup lang="ts">
interface Props {
  modelValue: boolean
  label: string
}

const props = defineProps<Props>()

const emit = defineEmits<{
  'update:modelValue': [value: boolean]
}>()

function updateValue(event: Event) {
  const target = event.target as HTMLInputElement
  emit('update:modelValue', target.checked)
}
</script>
