<template>
  <div>
    <Head>
      <Title>{{ title }} - YI-AI 易学AI系统</Title>
      <Meta name="description" :content="description" />
      <Meta property="og:title" :content="title + ' - YI-AI 易学AI系统'" />
      <Meta property="og:description" :content="description" />
      <Meta property="og:type" content="website" />
    </Head>
  </div>
</template>

<script setup lang="ts">
interface Props {
  title: string
  description?: string
}

const props = withDefaults(defineProps<Props>(), {
  description: '东方变化学AI操作系统 - 六爻排盘、易学分析',
})
</script>
