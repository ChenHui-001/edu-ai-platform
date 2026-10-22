// 服务端时间解析/本地日期格式化工具。
// 后端统一返回 naive 本地时间字符串（"YYYY-MM-DD HH:mm:ss" / "YYYY-MM-DD"）：
// - `new Date("2026-10-22 19:47:58")` 在 Safari/iOS 上是 Invalid Date；
// - `Date.toISOString()` 会把本地日期转成 UTC，东八区 0:00-8:00 取日期会错一天。
// 因此统一在这里解析/格式化，页面不要直接 new Date(serverString) 或 toISOString()。

/** 解析后端本地时间字符串；无效返回 null。 */
export function parseServerDate(value) {
  if (!value) return null
  if (value instanceof Date) return Number.isNaN(value.getTime()) ? null : value
  const text = String(value).trim()
  if (!text) return null
  // Safari 只稳定支持 ISO 格式：把日期与时间之间的空格换成 T
  const normalized = /^\d{4}-\d{2}-\d{2} \d{2}:\d{2}/.test(text)
    ? text.replace(' ', 'T')
    : text
  const date = new Date(normalized)
  return Number.isNaN(date.getTime()) ? null : date
}

/** 按本地时区格式化为 YYYY-MM-DD（不要用 toISOString）。 */
export function formatLocalDate(value) {
  const date = value instanceof Date ? value : parseServerDate(value)
  if (!date) return ''
  const year = date.getFullYear()
  const month = String(date.getMonth() + 1).padStart(2, '0')
  const day = String(date.getDate()).padStart(2, '0')
  return `${year}-${month}-${day}`
}
