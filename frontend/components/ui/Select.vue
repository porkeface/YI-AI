<template>
  <select
    :value="modelValue"
    @change="updateValue"
    :disabled="disabled"
    class="w-full px-4 py-3 bg-ink-800 border border-gold-500/30 rounded-lg
           text-gold-500
           focus:outline-none focus:border-gold-500 focus:ring-1 focus:ring-gold-500/50
           disabled:opacity-50 disabled:cursor-not-allowed
           transition-all duration-200 appearance-none"
  >
    <option
      v-for="option in options"
      :key="option.value"
      :value="option.value"
      class="bg-ink-800 text-gold-500"
    >
      {{ option.label }}
    </option>
  </select>
</template>

<script setup lang="ts">
interface Option {
  value: string | number
  label: string
}

interface Props {
  modelValue: string | number
  options: Option[]
  disabled?: boolean
}

const props = withDefaults(defineProps<Props>(), {
  disabled: false,
})

const emit = defineEmits<{
  'update:modelValue': [value: string | number]
}>()

function updateValue(event: Event) {
  const target = event.target as HTMLSelectElement
  emit('update:modelValue', target.value)
}
</script>
