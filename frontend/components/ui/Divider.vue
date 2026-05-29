<template>
  <div :class="['flex items-center gap-4', vertical ? 'flex-col' : '']">
    <div
      :class="[
        'bg-gold-500/30',
        vertical ? 'w-0.5 h-full' : 'h-px flex-1',
      ]"
    ></div>
    <span v-if="$slots.default" class="text-gold-500/60 text-sm whitespace-nowrap">
      <slot />
    </span>
    <div
      v-if="$slots.default"
      :class="[
        'bg-gold-500/30',
        vertical ? 'w-0.5 h-full' : 'h-px flex-1',
      ]"
    ></div>
  </div>
</template>

<script setup lang="ts">
interface Props {
  vertical?: boolean
}

const props = withDefaults(defineProps<Props>(), {
  vertical: false,
})
</script>
