<template>
  <div class="relative w-full h-full">
    <canvas
      ref="canvasRef"
      class="w-full h-full"
      :width="canvasSize"
      :height="canvasSize"
    ></canvas>

    <!-- 外圈装饰 -->
    <div class="absolute inset-0 rounded-full border-2 border-gold-500/30 animate-spin-slow"></div>
    <div class="absolute inset-2 rounded-full border border-gold-500/20"></div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, onUnmounted } from 'vue'

const canvasRef = ref<HTMLCanvasElement | null>(null)
const canvasSize = 256
let animationId: number | null = null
let rotation = 0

function drawTaiji() {
  const canvas = canvasRef.value
  if (!canvas) return

  const ctx = canvas.getContext('2d')
  if (!ctx) return

  const centerX = canvasSize / 2
  const centerY = canvasSize / 2
  const radius = canvasSize / 2 - 20

  // 清空画布
  ctx.clearRect(0, 0, canvasSize, canvasSize)

  // 保存状态并旋转
  ctx.save()
  ctx.translate(centerX, centerY)
  ctx.rotate(rotation)
  ctx.translate(-centerX, -centerY)

  // 绘制外圆（深色）
  ctx.beginPath()
  ctx.arc(centerX, centerY, radius, 0, Math.PI * 2)
  ctx.fillStyle = '#121212'
  ctx.fill()
  ctx.strokeStyle = '#d4a017'
  ctx.lineWidth = 2
  ctx.stroke()

  // 绘制阳鱼（右侧，金色）
  ctx.beginPath()
  ctx.arc(centerX, centerY, radius, -Math.PI / 2, Math.PI / 2)
  ctx.arc(centerX, centerY - radius / 2, radius / 2, Math.PI / 2, -Math.PI / 2, true)
  ctx.arc(centerX, centerY + radius / 2, radius / 2, -Math.PI / 2, Math.PI / 2)
  ctx.fillStyle = '#d4a017'
  ctx.fill()

  // 绘制阴鱼（左侧，深色）
  ctx.beginPath()
  ctx.arc(centerX, centerY, radius, Math.PI / 2, -Math.PI / 2)
  ctx.arc(centerX, centerY - radius / 2, radius / 2, -Math.PI / 2, Math.PI / 2, true)
  ctx.arc(centerX, centerY + radius / 2, radius / 2, Math.PI / 2, -Math.PI / 2)
  ctx.fillStyle = '#1a1a1a'
  ctx.fill()

  // 绘制阳眼（深色）
  ctx.beginPath()
  ctx.arc(centerX, centerY - radius / 2, radius / 6, 0, Math.PI * 2)
  ctx.fillStyle = '#121212'
  ctx.fill()

  // 绘制阴眼（金色）
  ctx.beginPath()
  ctx.arc(centerX, centerY + radius / 2, radius / 6, 0, Math.PI * 2)
  ctx.fillStyle = '#d4a017'
  ctx.fill()

  ctx.restore()

  // 更新旋转角度
  rotation += 0.005

  // 继续动画
  animationId = requestAnimationFrame(drawTaiji)
}

onMounted(() => {
  drawTaiji()
})

onUnmounted(() => {
  if (animationId) {
    cancelAnimationFrame(animationId)
  }
})
</script>

<style scoped>
@keyframes spin-slow {
  from { transform: rotate(0deg); }
  to { transform: rotate(360deg); }
}

.animate-spin-slow {
  animation: spin-slow 20s linear infinite;
}
</style>
