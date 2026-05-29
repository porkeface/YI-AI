// 六爻排盘核心类型定义

// API统一响应格式
export interface ApiResponse<T = unknown> {
  success: boolean
  data?: T
  error?: string
}

export type YinYang = 'yin' | 'yang'

export type WuXing = 'metal' | 'wood' | 'water' | 'fire' | 'earth'

export type LiuQin = '父母' | '兄弟' | '子孙' | '妻财' | '官鬼'

export type LiuShen = '青龙' | '朱雀' | '勾陈' | '螣蛇' | '白虎' | '玄武'

export type TianGan = '甲' | '乙' | '丙' | '丁' | '戊' | '己' | '庚' | '辛' | '壬' | '癸'

export type DiZhi = '子' | '丑' | '寅' | '卯' | '辰' | '巳' | '午' | '未' | '申' | '酉' | '戌' | '亥'

export interface GanZhi {
  gan: TianGan
  zhi: DiZhi
}

export interface LineData {
  position: number        // 爻位 1-6
  yinYang: YinYang       // 阴阳
  isMoving: boolean       // 是否动爻
  element: WuXing        // 五行属性
  sixRelation: LiuQin    // 六亲
  sixSpirit: LiuShen     // 六神
  ganZhi: GanZhi         // 干支
  isShi: boolean         // 是否世爻
  isYing: boolean        // 是否应爻
  changedYinYang?: YinYang  // 变爻后的阴阳
}

export interface TrigramData {
  name: string           // 卦名：乾、坤、震、巽、坎、离、艮、兑
  element: WuXing       // 五行属性
  lines: [YinYang, YinYang, YinYang]  // 三爻
}

export interface HexagramData {
  id: number             // 卦序 1-64
  name: string           // 卦名
  fullName: string       // 全称
  upperTrigram: TrigramData   // 上卦
  lowerTrigram: TrigramData   // 下卦
  lines: LineData[]      // 六爻数据
  element: WuXing        // 卦的五行属性
  palace: string         // 所属宫
  judgment: string       // 卦辞
  image: string          // 象辞
  isChanged: boolean     // 是否为变卦
}

export interface AnalysisResult {
  summary: string        // 总体分析
  advice: string         // 建议
  fortune: '大吉' | '吉' | '中吉' | '小吉' | '平' | '小凶' | '凶' | '大凶'
  keyPoints: string[]    // 关键点
}

export interface DivinationRequest {
  question: string
  method: 'manual' | 'time' | 'number'
  manualLines?: YinYang[]  // 手动输入时的六爻
  numbers?: number[]       // 数字起卦时的数字
}

export interface DivinationResultData {
  hexagram: HexagramData
  changedHexagram?: HexagramData
  analysis: AnalysisResult
}

export interface DivinationResponse {
  success: boolean
  data?: DivinationResultData
  error?: string
}

// 卦象摘要（用于列表展示）
export interface HexagramSummary {
  id: number
  name: string
  fullName: string
  palace: string
  upperTrigram: string
  lowerTrigram: string
  element: string
}

// 卦象关系
export interface HexagramRelationships {
  opposite: HexagramSummary
  reversed: HexagramSummary
  interlock: HexagramSummary
}

// 历史记录
export interface HistoryRecord {
  id: number
  question: string
  method: string
  hexagramName: string
  fortune: string
  createdAt: string
  hexagramData: HexagramData
  changedHexagramData: HexagramData | null
  analysisData: AnalysisResult
}

export interface HistoryListResponse {
  records: HistoryRecord[]
  total: number
  page: number
  limit: number
  totalPages: number
}

export interface HistorySaveRequest {
  question: string
  method: string
  hexagramData: HexagramData
  changedHexagramData: HexagramData | null
  analysisData: AnalysisResult
}
