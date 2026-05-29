export function useAuth() {
  const authStore = useAuthStore()

  const init = () => authStore.init()

  const register = async (username: string, email: string, password: string, displayName?: string) => {
    return await authStore.register(username, email, password, displayName)
  }

  const login = async (username: string, password: string) => {
    return await authStore.login(username, password)
  }

  const logout = () => {
    authStore.logout()
    navigateTo('/login')
  }

  const requireAuth = () => {
    if (!authStore.isAuthenticated) {
      navigateTo('/login')
      return false
    }
    return true
  }

  return {
    user: computed(() => authStore.user),
    isAuthenticated: computed(() => authStore.isAuthenticated),
    isLoading: computed(() => authStore.isLoading),
    error: computed(() => authStore.error),
    displayName: computed(() => authStore.displayName),
    init,
    register,
    login,
    logout,
    requireAuth,
  }
}
