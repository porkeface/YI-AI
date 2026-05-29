<template>
  <label class="flex items-center gap-2 cursor-pointer">
    <input
      type="radio"
      :name="name"
      :value="value"
      :checked="modelValue === value"
      @change="updateValue"
      class="w-4 h-4 text-gold-500 bg-ink-700 border-gold-500/30 focus:ring-gold-500 focus:ring-2"
    />
    <span class="text-gold-500/80 text-sm">{{ label }}</span>
  </label>
</template>

<script setup lang="ts">
interface Props {
  modelValue: string | number
  value: string | number
  name?: string
  label: string
}

const props = defineProps<Props>()

const emit = defineEmits<{
  'update:modelValue': [value: string | number]
}>()

function updateValue() {
  emit('update:modelValue', props.value)
}
</script>
