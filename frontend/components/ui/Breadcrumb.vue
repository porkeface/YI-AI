<template>
  <nav class="flex items-center gap-2 text-sm">
    <template v-for="(item, index) in items" :key="index">
      <NuxtLink
        v-if="item.to"
        :to="item.to"
        class="text-gold-500/60 hover:text-gold-500 transition-colors duration-200"
      >
        {{ item.label }}
      </NuxtLink>
      <span
        v-else
        class="text-gold-500"
      >
        {{ item.label }}
      </span>

      <span
        v-if="index < items.length - 1"
        class="text-gold-500/40"
      >
        /
      </span>
    </template>
  </nav>
</template>

<script setup lang="ts">
interface BreadcrumbItem {
  label: string
  to?: string
}

interface Props {
  items: BreadcrumbItem[]
}

defineProps<Props>()
</script>
