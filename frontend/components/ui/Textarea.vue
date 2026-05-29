<template>
  <textarea
    :value="modelValue"
    :placeholder="placeholder"
    :rows="rows"
    :disabled="disabled"
    @input="updateValue"
    class="w-full px-4 py-3 bg-ink-800 border border-gold-500/30 rounded-lg
           text-gold-500 placeholder-gold-500/40
           focus:outline-none focus:border-gold-500 focus:ring-1 focus:ring-gold-500/50
           disabled:opacity-50 disabled:cursor-not-allowed
           transition-all duration-200 resize-none"
  ></textarea>
</template>

<script setup lang="ts">
interface Props {
  modelValue: string
  placeholder?: string
  rows?: number
  disabled?: boolean
}

const props = withDefaults(defineProps<Props>(), {
  placeholder: '',
  rows: 4,
  disabled: false,
})

const emit = defineEmits<{
  'update:modelValue': [value: string]
}>()

function updateValue(event: Event) {
  const target = event.target as HTMLTextAreaElement
  emit('update:modelValue', target.value)
}
</script>
