/**
 * Auth 初始化插件
 *
 * 在客户端启动时从 localStorage 恢复认证状态。
 * 必须在 middleware 运行之前完成初始化。
 */
export default defineNuxtPlugin(() => {
  const authStore = useAuthStore()
  authStore.init()
})
