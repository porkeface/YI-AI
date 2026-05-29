<template>
  <div class="overflow-x-auto">
    <table class="w-full">
      <!-- 表头 -->
      <thead>
        <tr class="border-b border-gold-500/30">
          <th
            v-for="column in columns"
            :key="column.key"
            class="px-4 py-3 text-left text-sm font-medium text-gold-500/80"
          >
            {{ column.title }}
          </th>
        </tr>
      </thead>

      <!-- 表体 -->
      <tbody>
        <tr
          v-for="(row, index) in data"
          :key="index"
          class="border-b border-gold-500/10 hover:bg-gold-500/5 transition-colors duration-200"
        >
          <td
            v-for="column in columns"
            :key="column.key"
            class="px-4 py-3 text-sm text-gold-500/90"
          >
            <slot :name="column.key" :row="row" :value="row[column.key]">
              {{ row[column.key] }}
            </slot>
          </td>
        </tr>
      </tbody>
    </table>

    <!-- 空状态 -->
    <div v-if="data.length === 0" class="p-8 text-center text-gold-500/60">
      暂无数据
    </div>
  </div>
</template>

<script setup lang="ts">
interface Column {
  key: string
  title: string
}

interface Props {
  columns: Column[]
  data: Record<string, any>[]
}

defineProps<Props>()
</script>
