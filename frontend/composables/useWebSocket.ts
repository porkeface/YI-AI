/**
 * WebSocket 流式输出 Composable
 *
 * 用于实时接收 AI 解读的流式文本。
 * 连接 ws://localhost:8000/ws/divination，逐字显示 AI 解读。
 */

import { ref, onUnmounted } from 'vue'

export function useWebSocket() {
  const isConnected = ref(false)
  const isStreaming = ref(false)
  const streamedText = ref('')
  const error = ref<string | null>(null)

  let ws: WebSocket | null = null
  let resolveStream: ((text: string) => void) | null = null

  function connect(url: string): Promise<void> {
    return new Promise((resolve, reject) => {
      try {
        ws = new WebSocket(url)

        ws.onopen = () => {
          isConnected.value = true
          error.value = null
          resolve()
        }

        ws.onmessage = (event) => {
          try {
            const data = JSON.parse(event.data)

            if (data.type === 'chunk') {
              // 流式文本片段
              streamedText.value += data.content
              isStreaming.value = true
            } else if (data.type === 'done') {
              // 流式输出完成
              isStreaming.value = false
              if (resolveStream) {
                resolveStream(streamedText.value)
                resolveStream = null
              }
            } else if (data.type === 'error') {
              error.value = data.message || 'AI解读失败'
              isStreaming.value = false
              if (resolveStream) {
                resolveStream(streamedText.value)
                resolveStream = null
              }
            }
          } catch {
            // 非JSON消息忽略
          }
        }

        ws.onerror = () => {
          error.value = 'WebSocket连接失败'
          isConnected.value = false
          reject(new Error('WebSocket connection failed'))
        }

        ws.onclose = () => {
          isConnected.value = false
          isStreaming.value = false
          if (resolveStream) {
            resolveStream(streamedText.value)
            resolveStream = null
          }
        }
      } catch (err) {
        reject(err)
      }
    })
  }

  /**
   * 发送起卦请求并接收流式 AI 解读
   */
  function streamDivination(payload: Record<string, unknown>): Promise<string> {
    return new Promise((resolve, reject) => {
      if (!ws || ws.readyState !== WebSocket.OPEN) {
        reject(new Error('WebSocket未连接'))
        return
      }

      // 重置状态
      streamedText.value = ''
      isStreaming.value = true
      error.value = null
      resolveStream = resolve

      ws.send(JSON.stringify(payload))
    })
  }

  function disconnect() {
    if (ws) {
      ws.close()
      ws = null
    }
    isConnected.value = false
    isStreaming.value = false
  }

  onUnmounted(() => {
    disconnect()
  })

  return {
    isConnected,
    isStreaming,
    streamedText,
    error,
    connect,
    streamDivination,
    disconnect,
  }
}
