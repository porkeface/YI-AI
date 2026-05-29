<template>
  <div class="flex items-center gap-4">
    <input
      type="range"
      :min="min"
      :max="max"
      :step="step"
      :value="modelValue"
      @input="updateValue"
      class="flex-1 h-2 bg-ink-600 rounded-lg appearance-none cursor-pointer
             [&::-webkit-slider-thumb]:appearance-none
             [&::-webkit-slider-thumb]:w-4
             [&::-webkit-slider-thumb]:h-4
             [&::-webkit-slider-thumb]:bg-gold-500
             [&::-webkit-slider-thumb]:rounded-full
             [&::-webkit-slider-thumb]:cursor-pointer
             [&::-webkit-slider-thumb]:transition-all
             [&::-webkit-slider-thumb]:duration-200
             [&::-webkit-slider-thumb]:hover:scale-125"
    />
    <span class="text-gold-500 text-sm min-w-[3rem] text-right">{{ modelValue }}</span>
  </div>
</template>

<script setup lang="ts">
interface Props {
  modelValue: number
  min?: number
  max?: number
  step?: number
}

const props = withDefaults(defineProps<Props>(), {
  min: 0,
  max: 100,
  step: 1,
})

const emit = defineEmits<{
  'update:modelValue': [value: number]
}>()

function updateValue(event: Event) {
  const target = event.target as HTMLInputElement
  emit('update:modelValue', Number(target.value))
}
</script>
