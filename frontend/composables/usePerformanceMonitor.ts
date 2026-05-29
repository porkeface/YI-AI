/**
 * 性能监控 Composable - Phase 2.5
 * 监控 Core Web Vitals (LCP, FID, CLS)
 * 可视化帧率监控
 * 自动降级策略
 */
import { ref, onMounted, onUnmounted } from 'vue'

interface PerformanceMetrics {
  lcp: number | null       // Largest Contentful Paint (ms)
  fid: number | null       // First Input Delay (ms)
  cls: number | null       // Cumulative Layout Shift
  ttfb: number | null      // Time to First Byte (ms)
  fps: number              // 当前帧率
  memoryUsed: number | null // 内存使用 (MB)
}

interface PerformanceThresholds {
  lcp: number    // < 2500ms 为良好
  fid: number    // < 100ms 为良好
  cls: number    // < 0.1 为良好
  ttfb: number   // < 800ms 为良好
  fps: number    // > 30 为良好
}

const DEFAULT_THRESHOLDS: PerformanceThresholds = {
  lcp: 2500,
  fid: 100,
  cls: 0.1,
  ttfb: 800,
  fps: 30,
}

export function usePerformanceMonitor(thresholds: Partial<PerformanceThresholds> = {}) {
  const config = { ...DEFAULT_THRESHOLDS, ...thresholds }
  const metrics = ref<PerformanceMetrics>({
    lcp: null,
    fid: null,
    cls: null,
    ttfb: null,
    fps: 60,
    memoryUsed: null,
  })

  const isLowPerformance = ref(false)
  let fpsFrames = 0
  let fpsLastTime = performance.now()
  let animationId: number | null = null
  let observers: PerformanceObserver[] = []

  // LCP 监控
  function measureLCP() {
    if (!('PerformanceObserver' in window)) return

    try {
      const observer = new PerformanceObserver((list) => {
        const entries = list.getEntries()
        const lastEntry = entries[entries.length - 1]
        metrics.value.lcp = lastEntry.startTime
        checkPerformance()
      })
      observer.observe({ type: 'largest-contentful-paint', buffered: true })
      observers.push(observer)
    } catch {
      // 浏览器不支持
    }
  }

  // FID 监控
  function measureFID() {
    if (!('PerformanceObserver' in window)) return

    try {
      const observer = new PerformanceObserver((list) => {
        const entries = list.getEntries()
        for (const entry of entries) {
          metrics.value.fid = (entry as any).processingStart - entry.startTime
          checkPerformance()
        }
      })
      observer.observe({ type: 'first-input', buffered: true })
      observers.push(observer)
    } catch {
      // 浏览器不支持
    }
  }

  // CLS 监控
  function measureCLS() {
    if (!('PerformanceObserver' in window)) return

    try {
      let clsValue = 0
      const observer = new PerformanceObserver((list) => {
        const entries = list.getEntries()
        for (const entry of entries) {
          if (!(entry as any).hadRecentInput) {
            clsValue += (entry as any).value
            metrics.value.cls = clsValue
            checkPerformance()
          }
        }
      })
      observer.observe({ type: 'layout-shift', buffered: true })
      observers.push(observer)
    } catch {
      // 浏览器不支持
    }
  }

  // TTFB 监控
  function measureTTFB() {
    if (!('performance' in window)) return

    const navEntry = performance.getEntriesByType('navigation')[0] as PerformanceNavigationTiming | undefined
    if (navEntry) {
      metrics.value.ttfb = navEntry.responseStart - navEntry.requestStart
    }
  }

  // FPS 监控
  function measureFPS() {
    fpsFrames++
    const now = performance.now()
    const delta = now - fpsLastTime

    if (delta >= 1000) {
      metrics.value.fps = Math.round((fpsFrames * 1000) / delta)
      fpsFrames = 0
      fpsLastTime = now
      checkPerformance()
    }

    animationId = requestAnimationFrame(measureFPS)
  }

  // 内存监控
  function measureMemory() {
    if ('memory' in performance) {
      const mem = (performance as any).memory
      metrics.value.memoryUsed = Math.round(mem.usedJSHeapSize / 1024 / 1024)
    }
  }

  // 检查是否低性能
  function checkPerformance() {
    const issues: string[] = []

    if (metrics.value.lcp !== null && metrics.value.lcp > config.lcp) {
      issues.push('LCP过高')
    }
    if (metrics.value.fid !== null && metrics.value.fid > config.fid) {
      issues.push('FID过高')
    }
    if (metrics.value.cls !== null && metrics.value.cls > config.cls) {
      issues.push('CLS过高')
    }
    if (metrics.value.fps < config.fps) {
      issues.push('FPS过低')
    }

    isLowPerformance.value = issues.length > 0
  }

  // 获取降级建议
  function getDegradationSuggestions(): string[] {
    const suggestions: string[] = []

    if (metrics.value.fps < 30) {
      suggestions.push('关闭粒子动画')
      suggestions.push('减少太极动画复杂度')
      suggestions.push('降低图谱节点数量')
    }
    if (metrics.value.lcp !== null && metrics.value.lcp > 4000) {
      suggestions.push('延迟加载非关键资源')
      suggestions.push('优化首屏图片')
    }
    if (metrics.value.memoryUsed !== null && metrics.value.memoryUsed > 100) {
      suggestions.push('清理未使用的图谱实例')
      suggestions.push('减少同时渲染的动画')
    }

    return suggestions
  }

  // 导出报告
  function exportReport(): string {
    return JSON.stringify({
      ...metrics.value,
      isLowPerformance: isLowPerformance.value,
      suggestions: getDegradationSuggestions(),
      timestamp: new Date().toISOString(),
      userAgent: navigator.userAgent,
    }, null, 2)
  }

  onMounted(() => {
    measureLCP()
    measureFID()
    measureCLS()
    measureTTFB()
    measureFPS()

    // 定期检测内存
    const memInterval = setInterval(measureMemory, 5000)

    onUnmounted(() => {
      if (animationId !== null) {
        cancelAnimationFrame(animationId)
      }
      observers.forEach(o => o.disconnect())
      clearInterval(memInterval)
    })
  })

  return {
    metrics,
    isLowPerformance,
    getDegradationSuggestions,
    exportReport,
  }
}
