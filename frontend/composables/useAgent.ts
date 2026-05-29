/**
 * Agent对话 composable
 *
 * 提供Agent工作流的前端接口，支持：
 * - 普通对话
 * - SSE流式对话
 * - 深度推演
 */
import { ref, computed } from 'vue'

export interface AgentMessage {
  id: string
  role: 'user' | 'assistant' | 'system'
  content: string
  timestamp: number
  metadata?: {
    intent?: string
    confidence?: number
    riskFlags?: string[]
    inferenceResult?: any
    durationMs?: number
  }
}

export interface EvolutionNode {
  name: string
  depth: number
  probability: number
  trigger: string
  relation: string
  trend: string
  element_strength: number
  children: EvolutionNode[]
}

export interface EvolutionResult {
  source: string
  tree: EvolutionNode
  total_nodes: number
  path_count: number
  recommended_path: string[]
  summary: string
}

export function useAgent() {
  const config = useRuntimeConfig()
  const baseUrl = config.public.apiBase

  const messages = ref<AgentMessage[]>([])
  const isLoading = ref(false)
  const isStreaming = ref(false)
  const currentIntent = ref<string>('')
  const evolutionResult = ref<EvolutionResult | null>(null)

  // 生成唯一ID
  let messageIdCounter = 0
  function nextId(): string {
    return `msg_${Date.now()}_${++messageIdCounter}`
  }

  /**
   * 发送消息（非流式）
   */
  async function sendMessage(
    content: string,
    hexagramData?: any,
    sessionId?: string,
  ): Promise<AgentMessage | null> {
    // 添加用户消息
    const userMsg: AgentMessage = {
      id: nextId(),
      role: 'user',
      content,
      timestamp: Date.now(),
    }
    messages.value = [...messages.value, userMsg]

    isLoading.value = true

    try {
      const token = localStorage.getItem('auth_token')
      const headers: Record<string, string> = {
        'Content-Type': 'application/json',
      }
      if (token) {
        headers['Authorization'] = `Bearer ${token}`
      }

      const response = await fetch(`${baseUrl}/api/agent/chat`, {
        method: 'POST',
        headers,
        body: JSON.stringify({
          message: content,
          hexagram_data: hexagramData || null,
          session_id: sessionId || '',
        }),
      })

      if (!response.ok) {
        throw new Error(`请求失败: ${response.status}`)
      }

      const data = await response.json()

      const assistantMsg: AgentMessage = {
        id: nextId(),
        role: 'assistant',
        content: data.response,
        timestamp: Date.now(),
        metadata: {
          intent: data.intent,
          confidence: data.confidence,
          riskFlags: data.risk_flags,
          inferenceResult: data.inference_result,
          durationMs: data.duration_ms,
        },
      }

      messages.value = [...messages.value, assistantMsg]
      currentIntent.value = data.intent

      // 如果有推演结果，保存
      if (data.inference_result) {
        evolutionResult.value = data.inference_result
      }

      return assistantMsg
    } catch (err: any) {
      const errorMsg: AgentMessage = {
        id: nextId(),
        role: 'system',
        content: `错误: ${err.message}`,
        timestamp: Date.now(),
      }
      messages.value = [...messages.value, errorMsg]
      return null
    } finally {
      isLoading.value = false
    }
  }

  /**
   * 发送消息（SSE流式）
   */
  async function sendMessageStream(
    content: string,
    hexagramData?: any,
    sessionId?: string,
  ): Promise<void> {
    const userMsg: AgentMessage = {
      id: nextId(),
      role: 'user',
      content,
      timestamp: Date.now(),
    }
    messages.value = [...messages.value, userMsg]

    isLoading.value = true
    isStreaming.value = true

    // 创建一个空的assistant消息，逐步填充
    const assistantMsg: AgentMessage = {
      id: nextId(),
      role: 'assistant',
      content: '',
      timestamp: Date.now(),
      metadata: {},
    }
    messages.value = [...messages.value, assistantMsg]

    try {
      const token = localStorage.getItem('auth_token')
      const headers: Record<string, string> = {
        'Content-Type': 'application/json',
      }
      if (token) {
        headers['Authorization'] = `Bearer ${token}`
      }

      const response = await fetch(`${baseUrl}/api/agent/chat/stream`, {
        method: 'POST',
        headers,
        body: JSON.stringify({
          message: content,
          hexagram_data: hexagramData || null,
          session_id: sessionId || '',
        }),
      })

      if (!response.ok) {
        throw new Error(`请求失败: ${response.status}`)
      }

      const reader = response.body?.getReader()
      if (!reader) throw new Error('无法读取响应流')

      const decoder = new TextDecoder()
      let buffer = ''

      while (true) {
        const { done, value } = await reader.read()
        if (done) break

        buffer += decoder.decode(value, { stream: true })
        const lines = buffer.split('\n')
        buffer = lines.pop() || ''

        for (const line of lines) {
          if (!line.startsWith('data: ')) continue
          const data = line.slice(6)

          if (data === '[DONE]') break

          try {
            const event = JSON.parse(data)

            if (event.type === 'content') {
              assistantMsg.content += event.data
              // 触发响应式更新
              messages.value = [...messages.value]
            } else if (event.type === 'status') {
              assistantMsg.content += `\n[${event.data}]\n`
              messages.value = [...messages.value]
            } else if (event.type === 'tool_call') {
              assistantMsg.content += `\n🔧 ${event.data}\n`
              messages.value = [...messages.value]
            } else if (event.type === 'done') {
              if (event.metadata) {
                assistantMsg.metadata = {
                  intent: event.metadata.intent,
                  confidence: event.metadata.confidence,
                  riskFlags: event.metadata.risk_flags,
                  inferenceResult: event.metadata.inference_result,
                }
                currentIntent.value = event.metadata.intent || ''
                if (event.metadata.inference_result) {
                  evolutionResult.value = event.metadata.inference_result
                }
              }
              messages.value = [...messages.value]
            }
          } catch {
            // 忽略解析错误
          }
        }
      }
    } catch (err: any) {
      assistantMsg.content += `\n\n❌ 错误: ${err.message}`
      messages.value = [...messages.value]
    } finally {
      isLoading.value = false
      isStreaming.value = false
    }
  }

  /**
   * 执行深度推演
   */
  async function evolve(
    hexagramName: string,
    maxDepth: number = 5,
    branchFactor: number = 3,
  ): Promise<EvolutionResult | null> {
    try {
      const token = localStorage.getItem('auth_token')
      const headers: Record<string, string> = {
        'Content-Type': 'application/json',
      }
      if (token) {
        headers['Authorization'] = `Bearer ${token}`
      }

      const response = await fetch(`${baseUrl}/api/agent/evolve`, {
        method: 'POST',
        headers,
        body: JSON.stringify({
          hexagram_name: hexagramName,
          max_depth: maxDepth,
          branch_factor: branchFactor,
        }),
      })

      if (!response.ok) {
        throw new Error(`推演失败: ${response.status}`)
      }

      const data = await response.json()
      evolutionResult.value = data
      return data
    } catch (err: any) {
      console.error('推演错误:', err)
      return null
    }
  }

  /**
   * 清空对话
   */
  function clearMessages() {
    messages.value = []
    evolutionResult.value = null
    currentIntent.value = ''
  }

  return {
    messages,
    isLoading,
    isStreaming,
    currentIntent,
    evolutionResult,
    sendMessage,
    sendMessageStream,
    evolve,
    clearMessages,
  }
}
