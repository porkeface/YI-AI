import type { ApiResponse, HistoryListResponse, HistoryRecord, HistorySaveRequest } from '~/types/hexagram'

export function useHistory() {
  const { request } = useApi()

  async function saveHistory(data: HistorySaveRequest): Promise<number | null> {
    const { data: resp, error } = await request<ApiResponse<{ id: number }>>('/api/history/', {
      method: 'POST',
      body: data,
    })
    if (error || !resp?.success) return null
    return resp.data?.id ?? null
  }

  async function getHistory(page = 1, limit = 10): Promise<HistoryListResponse | null> {
    const { data: resp, error } = await request<ApiResponse<HistoryListResponse>>('/api/history/', {
      params: { page: String(page), limit: String(limit) },
    })
    if (error || !resp?.success || !resp.data) return null
    return resp.data
  }

  async function getHistoryRecord(id: number): Promise<HistoryRecord | null> {
    const { data: resp, error } = await request<ApiResponse<HistoryRecord>>(`/api/history/${id}`)
    if (error || !resp?.success || !resp.data) return null
    return resp.data
  }

  async function deleteHistoryRecord(id: number): Promise<boolean> {
    const { data: resp, error } = await request<ApiResponse<null>>(`/api/history/${id}`, {
      method: 'DELETE',
    })
    return !error && resp?.success === true
  }

  return { saveHistory, getHistory, getHistoryRecord, deleteHistoryRecord }
}
