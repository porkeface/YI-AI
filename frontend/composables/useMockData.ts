import type { DivinationResponse } from '~/types/hexagram'
import { useHexagram } from '~/composables/useHexagram'

export function useMockData() {
  const hexagram = useHexagram()

  /**
   * 模拟起卦响应
   */
  function getMockDivinationResponse(
    question: string,
    method: 'manual' | 'time' | 'number' | 'plum_blossom',
    manualLines?: any[],
    numbers?: number[]
  ): DivinationResponse {
    const result = hexagram.mockDivination(question, method, manualLines, numbers)

    return {
      success: true,
      data: {
        hexagram: result.hexagram as any,
        changedHexagram: result.changedHexagram as any,
        analysis: {
          summary: `您所问之事，得${result.hexagram.name}。此卦象征着和谐与团结，预示着良好的发展前景。卦象显示，当前处于一个有利的时机，适合主动出击，寻求合作。`,
          advice: '建议您把握当前的有利时机，积极与他人合作，共同推进事业的发展。注意保持谦虚谨慎的态度，避免因过于自信而忽视潜在的风险。',
          fortune: '吉',
          keyPoints: [
            '时机成熟，适合行动',
            '贵人相助，事半功倍',
            '合作共赢，前途光明',
            '保持谦虚，方能长久',
          ],
        },
      },
    }
  }

  return {
    getMockDivinationResponse,
  }
}
