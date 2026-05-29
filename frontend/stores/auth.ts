import { defineStore } from 'pinia'

interface User {
  id: string
  username: string
  email: string
  displayName: string | null
  avatarUrl: string | null
  isActive: boolean
  createdAt: string
}

interface AuthState {
  user: User | null
  token: string | null
  isAuthenticated: boolean
  isLoading: boolean
  error: string | null
}

export const useAuthStore = defineStore('auth', {
  state: (): AuthState => ({
    user: null,
    token: null,
    isAuthenticated: false,
    isLoading: false,
    error: null,
  }),

  getters: {
    displayName: (state) => state.user?.displayName || state.user?.username || '用户',
    avatarUrl: (state) => state.user?.avatarUrl || null,
  },

  actions: {
    async register(username: string, email: string, password: string, displayName?: string) {
      this.isLoading = true
      this.error = null
      try {
        const config = useRuntimeConfig()
        const response = await fetch(`${config.public.apiBase}/api/auth/register`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ username, email, password, display_name: displayName }),
        })
        if (!response.ok) {
          const data = await response.json().catch(() => ({}))
          throw new Error(data.detail || '注册失败')
        }
        const data = await response.json()
        this._setAuth(data.access_token, data.user)
        return true
      } catch (err: any) {
        this.error = err.message || '注册失败'
        return false
      } finally {
        this.isLoading = false
      }
    },

    async login(username: string, password: string) {
      this.isLoading = true
      this.error = null
      try {
        const config = useRuntimeConfig()
        const response = await fetch(`${config.public.apiBase}/api/auth/login`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ username, password }),
        })
        if (!response.ok) {
          const data = await response.json().catch(() => ({}))
          throw new Error(data.detail || '登录失败')
        }
        const data = await response.json()
        this._setAuth(data.access_token, data.user)
        return true
      } catch (err: any) {
        this.error = err.message || '登录失败'
        return false
      } finally {
        this.isLoading = false
      }
    },

    async fetchUser() {
      if (!this.token) return
      try {
        const config = useRuntimeConfig()
        const response = await fetch(`${config.public.apiBase}/api/auth/me`, {
          headers: { Authorization: `Bearer ${this.token}` },
        })
        if (!response.ok) {
          this.logout()
          return
        }
        const data = await response.json()
        this.user = data
        this.isAuthenticated = true
      } catch {
        this.logout()
      }
    },

    logout() {
      this.user = null
      this.token = null
      this.isAuthenticated = false
      if (import.meta.client) {
        localStorage.removeItem('auth_token')
      }
    },

    init() {
      if (import.meta.client) {
        const token = localStorage.getItem('auth_token')
        if (token) {
          this.token = token
          this.fetchUser()
        }
      }
    },

    _setAuth(token: string, user: User) {
      this.token = token
      this.user = user
      this.isAuthenticated = true
      if (import.meta.client) {
        localStorage.setItem('auth_token', token)
      }
    },
  },
})
