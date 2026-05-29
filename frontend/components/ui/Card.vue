<template>
  <div
    :class="[
      'rounded-lg border bg-ink-900/80 transition-all duration-200',
      hoverable ? 'hover:border-gold-500/50 hover:shadow-lg cursor-pointer' : '',
      bordered ? 'border-gold-500/30' : 'border-transparent',
    ]"
    @click="hoverable ? $emit('click') : null"
  >
    <!-- 头部 -->
    <div v-if="$slots.header" class="px-4 py-3 border-b border-gold-500/20">
      <slot name="header" />
    </div>

    <!-- 内容 -->
    <div class="p-4">
      <slot />
    </div>

    <!-- 底部 -->
    <div v-if="$slots.footer" class="px-4 py-3 border-t border-gold-500/20">
      <slot name="footer" />
    </div>
  </div>
</template>

<script setup lang="ts">
interface Props {
  bordered?: boolean
  hoverable?: boolean
}

const props = withDefaults(defineProps<Props>(), {
  bordered: true,
  hoverable: false,
})

defineEmits<{
  click: []
}>()
</script>
