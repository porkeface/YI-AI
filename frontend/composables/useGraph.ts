import type { ApiResponse, HexagramRelationships, HexagramSummary } from '~/types/hexagram'

export function useGraph() {
  const { request } = useApi()

  async function getAllHexagrams(): Promise<HexagramSummary[]> {
    const { data: resp, error } = await request<ApiResponse<HexagramSummary[]>>('/api/hexagram/')
    if (error || !resp?.success || !resp.data) return []
    return resp.data
  }

  async function searchHexagrams(name: string): Promise<HexagramSummary[]> {
    const { data: resp, error } = await request<ApiResponse<HexagramSummary[]>>(
      `/api/hexagram/search/${encodeURIComponent(name)}`
    )
    if (error || !resp?.success || !resp.data) return []
    return resp.data
  }

  async function getHexagramRelationships(id: number): Promise<HexagramRelationships | null> {
    const { data: resp, error } = await request<ApiResponse<HexagramRelationships>>(
      `/api/hexagram/${id}/relationships`
    )
    if (error || !resp?.success || !resp.data) return null
    return resp.data
  }

  return { getAllHexagrams, searchHexagrams, getHexagramRelationships }
}
