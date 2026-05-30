/**
 * 格式化日期字符串为中文可读格式
 */
export function formatDate(dateStr: string): string {
  if (!dateStr) return ''
  const date = new Date(dateStr)
  if (isNaN(date.getTime())) return dateStr

  const year = date.getFullYear()
  const month = String(date.getMonth() + 1).padStart(2, '0')
  const day = String(date.getDate()).padStart(2, '0')
  const hours = String(date.getHours()).padStart(2, '0')
  const minutes = String(date.getMinutes()).padStart(2, '0')

  return `${year}-${month}-${day} ${hours}:${minutes}`
}

/**
 * 获取指定年月的实际天数
 */
export function getDaysInMonth(year: number, month: number): number {
  return new Date(year, month, 0).getDate()
}

/**
 * 校验日期是否合法
 */
export function isValidDate(year: number, month: number, day: number): boolean {
  if (month < 1 || month > 12) return false
  if (day < 1) return false
  return day <= getDaysInMonth(year, month)
}
