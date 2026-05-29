export default defineNuxtRouteMiddleware((to) => {
  const authStore = useAuthStore()

  // Public routes that don't require auth
  const publicRoutes = ['/', '/login', '/register', '/test']
  if (publicRoutes.includes(to.path)) return

  // Check auth
  if (!authStore.isAuthenticated) {
    return navigateTo('/login')
  }
})
