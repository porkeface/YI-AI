import type { DivinationRequest, DivinationResponse } from '~/types/hexagram'

export function useApi() {
  const config = useRuntimeConfig()
  const baseUrl = config.public.apiBase

  /**
   * 通用请求函数
   */
  async function request<T>(
    endpoint: string,
    options: {
      method?: 'GET' | 'POST' | 'PUT' | 'DELETE'
      body?: unknown
      params?: Record<string, string>
    } = {}
  ): Promise<{ data: T | null; error: string | null }> {
    try {
      const url = new URL(`${baseUrl}${endpoint}`)

      if (options.params) {
        Object.entries(options.params).forEach(([key, value]) => {
          url.searchParams.append(key, value)
        })
      }

      const response = await fetch(url.toString(), {
        method: options.method || 'GET',
        headers: {
          'Content-Type': 'application/json',
        },
        body: options.body ? JSON.stringify(options.body) : undefined,
      })

      if (!response.ok) {
        const errorData = await response.json().catch(() => ({}))
        return {
          data: null,
          error: errorData.message || `请求失败: ${response.status}`,
        }
      }

      const data = await response.json()
      return { data, error: null }
    } catch (err) {
      console.error('API请求错误:', err)
      return {
        data: null,
        error: err instanceof Error ? err.message : '网络请求失败',
      }
    }
  }

  /**
   * 起卦请求
   */
  async function submitDivination(divinationRequest: DivinationRequest): Promise<DivinationResponse> {
    const { data, error } = await request<DivinationResponse>('/api/divination/', {
      method: 'POST',
      body: divinationRequest,
    })

    if (error) {
      return { success: false, error }
    }

    return data || { success: false, error: '未收到响应数据' }
  }

  /**
   * 获取历史记录
   */
  async function getHistory(page = 1, limit = 20) {
    return request('/api/history', {
      params: { page: String(page), limit: String(limit) },
    })
  }

  /**
   * 获取卦象详情
   */
  async function getHexagramDetail(id: number) {
    return request(`/api/hexagram/${id}`)
  }

  return {
    request,
    submitDivination,
    getHistory,
    getHexagramDetail,
  }
}
