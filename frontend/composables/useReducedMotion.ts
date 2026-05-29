/**
 * 减少动画偏好检测 Composable
 * 遵循 WCAG 2.1 AA 无障碍标准
 */
import { ref, onMounted, onUnmounted } from 'vue'

export function useReducedMotion() {
  const prefersReducedMotion = ref(false)
  let mediaQuery: MediaQueryList | null = null

  function check() {
    mediaQuery = window.matchMedia('(prefers-reduced-motion: reduce)')
    prefersReducedMotion.value = mediaQuery.matches
    mediaQuery.addEventListener('change', onChange)
  }

  function onChange(e: MediaQueryListEvent) {
    prefersReducedMotion.value = e.matches
  }

  onMounted(check)
  onUnmounted(() => {
    mediaQuery?.removeEventListener('change', onChange)
  })

  return { prefersReducedMotion }
}
