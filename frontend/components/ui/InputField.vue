<template>
  <div class="relative">
    <label v-if="label" :for="inputId" class="sr-only">{{ label }}</label>
    <input
      :id="inputId"
      :type="type"
      :value="modelValue"
      :placeholder="placeholder"
      :disabled="disabled"
      :aria-label="label || placeholder"
      @input="$emit('update:modelValue', ($event.target as HTMLInputElement).value)"
      class="w-full px-4 py-3 bg-ink-800 border border-gold-500/30 rounded-lg
             text-gold-500 placeholder-gold-500/40
             focus:outline-none focus:border-gold-500 focus:ring-1 focus:ring-gold-500/50
             disabled:opacity-50 disabled:cursor-not-allowed
             transition-all duration-200"
    />
  </div>
</template>

<script setup lang="ts">
interface Props {
  modelValue: string
  type?: string
  placeholder?: string
  disabled?: boolean
  label?: string
  id?: string
}

const props = withDefaults(defineProps<Props>(), {
  type: 'text',
  placeholder: '',
  disabled: false,
  label: '',
  id: '',
})

const inputId = computed(() => props.id || `input-${props.placeholder.replace(/\s+/g, '-').slice(0, 10) || 'field'}`)

defineEmits<{
  'update:modelValue': [value: string]
}>()
</script>
