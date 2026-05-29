import type { YinYang, LineData, HexagramData, GanZhi } from '~/types/hexagram'
import { hexagrams, getHexagramByTrigrams } from '~/data/hexagrams'

// 六神序列
const LIU_SHEN = ['青龙', '朱雀', '勾陈', '螣蛇', '白虎', '玄武'] as const

// 天干
const TIAN_GAN = ['甲', '乙', '丙', '丁', '戊', '己', '庚', '辛', '壬', '癸'] as const

// 地支
const DI_ZHI = ['子', '丑', '寅', '卯', '辰', '巳', '午', '未', '申', '酉', '戌', '亥'] as const

// 五行对应
const WU_XING_MAP: Record<string, string> = {
  '子': 'water', '亥': 'water',
  '寅': 'wood', '卯': 'wood',
  '巳': 'fire', '午': 'fire',
  '申': 'metal', '酉': 'metal',
  '辰': 'earth', '戌': 'earth', '丑': 'earth', '未': 'earth',
}

export function useHexagram() {
  /**
   * 根据时间生成六爻
   */
  function generateLinesByTime(): YinYang[] {
    const now = new Date()
    const lines: YinYang[] = []

    // 使用时间的各个部分生成随机数
    const seed = now.getHours() * 3600 + now.getMinutes() * 60 + now.getSeconds()

    for (let i = 0; i < 6; i++) {
      // 使用简单的伪随机算法
      const random = Math.sin(seed + i * 1234) * 10000
      const value = Math.floor(random) % 2
      lines.push(value === 0 ? 'yin' : 'yang')
    }

    return lines
  }

  /**
   * 根据数字生成六爻
   */
  function generateLinesByNumbers(n1: number, n2: number): YinYang[] {
    const lines: YinYang[] = []
    const sum = n1 + n2

    for (let i = 0; i < 6; i++) {
      const value = (sum + i) % 2
      lines.push(value === 0 ? 'yin' : 'yang')
    }

    return lines
  }

  /**
   * 确定动爻
   */
  function determineMovingLines(lines: YinYang[]): boolean[] {
    const now = new Date()
    const seed = now.getSeconds()
    return lines.map((_, index) => {
      return (seed + index) % 3 === 0 // 约1/3的概率为动爻
    })
  }

  /**
   * 获取干支
   */
  function getGanZhi(position: number): GanZhi {
    const now = new Date()
    const dayOfYear = Math.floor((now.getTime() - new Date(now.getFullYear(), 0, 0).getTime()) / 86400000)
    const ganIndex = (dayOfYear + position) % 10
    const zhiIndex = (dayOfYear + position) % 12

    return {
      gan: TIAN_GAN[ganIndex],
      zhi: DI_ZHI[zhiIndex],
    }
  }

  /**
   * 获取六亲
   */
  function getLiuQin(position: number, hexagramElement: string): string {
    const liuQin = ['父母', '兄弟', '子孙', '妻财', '官鬼']
    return liuQin[position % 5]
  }

  /**
   * 获取六神
   */
  function getLiuShen(position: number): string {
    const now = new Date()
    const dayOfWeek = now.getDay()
    const startIndex = dayOfWeek % 6
    return LIU_SHEN[(startIndex + position - 1) % 6]
  }

  /**
   * 构建完整的六爻数据
   */
  function buildLinesData(
    lines: YinYang[],
    movingLines: boolean[],
    hexagramElement: string
  ): LineData[] {
    return lines.map((yinYang, index) => {
      const position = index + 1
      const ganZhi = getGanZhi(position)

      return {
        position,
        yinYang,
        isMoving: movingLines[index],
        element: WU_XING_MAP[ganZhi.zhi] as any || 'earth',
        sixRelation: getLiuQin(position, hexagramElement) as any,
        sixSpirit: getLiuShen(position) as any,
        ganZhi,
        isShi: position === 4,  // 简化：世爻默认在第4爻
        isYing: position === 1, // 简化：应爻默认在第1爻
        changedYinYang: movingLines[index]
          ? (yinYang === 'yang' ? 'yin' : 'yang')
          : undefined,
      }
    })
  }

  /**
   * 模拟排盘（前端演示用）
   */
  function mockDivination(
    question: string,
    method: 'manual' | 'time' | 'number',
    manualLines?: YinYang[],
    numbers?: number[]
  ) {
    let lines: YinYang[]
    let movingLines: boolean[]

    switch (method) {
      case 'manual':
        lines = manualLines || generateLinesByTime()
        movingLines = determineMovingLines(lines)
        break
      case 'number':
        lines = numbers ? generateLinesByNumbers(numbers[0], numbers[1]) : generateLinesByTime()
        movingLines = determineMovingLines(lines)
        break
      case 'time':
      default:
        lines = generateLinesByTime()
        movingLines = determineMovingLines(lines)
        break
    }

    // 根据爻象确定上下卦
    const upperLines = lines.slice(3, 6)
    const lowerLines = lines.slice(0, 3)

    // 简单的卦象映射
    const trigramMap: Record<string, string> = {
      'yang,yang,yang': '乾',
      'yin,yin,yin': '坤',
      'yang,yin,yin': '震',
      'yin,yang,yang': '巽',
      'yin,yang,yin': '坎',
      'yang,yin,yang': '离',
      'yin,yin,yang': '艮',
      'yang,yang,yin': '兑',
    }

    const upperKey = upperLines.join(',')
    const lowerKey = lowerLines.join(',')
    const upperName = trigramMap[upperKey] || '乾'
    const lowerName = trigramMap[lowerKey] || '坤'

    // 查找对应的卦象
    const hexagramData = getHexagramByTrigrams(upperName, lowerName)
    const hexagramId = hexagramData?.id || 1

    const hexagramElement = 'fire' // 默认火属性
    const linesData = buildLinesData(lines, movingLines, hexagramElement)

    return {
      hexagram: {
        id: hexagramId,
        name: hexagramData?.name || '天火同人',
        fullName: hexagramData?.fullName || '天火同人卦',
        upperTrigram: {
          name: upperName,
          element: 'metal',
          lines: upperLines,
        },
        lowerTrigram: {
          name: lowerName,
          element: 'fire',
          lines: lowerLines,
        },
        lines: linesData,
        element: hexagramElement as any,
        palace: hexagramData?.palace || '乾',
        judgment: hexagramData?.judgment || '同人于野，亨。利涉大川，利君子贞。',
        image: hexagramData?.image || '天与火，同人。君子以类族辨物。',
        isChanged: false,
      },
      changedHexagram: movingLines.some(m => m)
        ? {
            id: hexagramId,
            name: hexagramData?.name || '天火同人',
            fullName: (hexagramData?.fullName || '天火同人卦') + '（变）',
            upperTrigram: {
              name: upperName,
              element: 'metal',
              lines: upperLines,
            },
            lowerTrigram: {
              name: lowerName,
              element: 'fire',
              lines: lowerLines,
            },
            lines: linesData.map(line => ({
              ...line,
              yinYang: line.isMoving ? (line.changedYinYang || line.yinYang) : line.yinYang,
            })),
            element: hexagramElement as any,
            palace: hexagramData?.palace || '乾',
            judgment: hexagramData?.judgment || '同人于野，亨。利涉大川，利君子贞。',
            image: hexagramData?.image || '天与火，同人。君子以类族辨物。',
            isChanged: true,
          }
        : undefined,
    }
  }

  return {
    generateLinesByTime,
    generateLinesByNumbers,
    determineMovingLines,
    getGanZhi,
    getLiuQin,
    getLiuShen,
    buildLinesData,
    mockDivination,
  }
}
