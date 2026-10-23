import { describe, it, expect } from 'vitest'
import { parseServerDate, formatLocalDate } from '../date'

// 后端返回 naive 本地时间字符串（"YYYY-MM-DD HH:mm:ss"）：
// - 直接用 new Date("... ...") 在 Safari/iOS 上是 Invalid Date；
// - 用 toISOString() 取日期在东八区 0:00-8:00 会错一天。
// 这里锁住 parseServerDate 的 Safari 兼容格式与 formatLocalDate 的本地时区口径。
describe('parseServerDate（服务端时间解析）', () => {
  it('解析空格分隔的时间字符串（Safari 兼容）', () => {
    const d = parseServerDate('2026-10-22 19:47:58')
    expect(d).toBeInstanceOf(Date)
    // 未带时区 → 按本地时间解析，各字段应与原字符串一致
    expect(d.getFullYear()).toBe(2026)
    expect(d.getMonth()).toBe(9)
    expect(d.getDate()).toBe(22)
    expect(d.getHours()).toBe(19)
    expect(d.getMinutes()).toBe(47)
    expect(d.getSeconds()).toBe(58)
  })

  it('非法/空输入返回 null', () => {
    expect(parseServerDate(null)).toBeNull()
    expect(parseServerDate('')).toBeNull()
    expect(parseServerDate('not-a-date')).toBeNull()
  })

  it('Date 实例直接返回，非法 Date 返回 null', () => {
    const d = new Date(2026, 0, 5)
    expect(parseServerDate(d)).toBe(d)
    expect(parseServerDate(new Date('invalid'))).toBeNull()
  })
})

describe('formatLocalDate（本地日期格式化）', () => {
  it('凌晨时间仍取本地日期，不回退到 UTC 前一天', () => {
    // 东八区 2026-01-01 00:30 用 toISOString 会变成 2025-12-31 → 这里必须是 2026-01-01
    expect(formatLocalDate('2026-01-01 00:30:00')).toBe('2026-01-01')
  })

  it('按本地时区补零格式化', () => {
    expect(formatLocalDate(new Date(2026, 0, 5))).toBe('2026-01-05')
    expect(formatLocalDate('2026-12-09 23:59:59')).toBe('2026-12-09')
  })

  it('空值/非法值返回空串', () => {
    expect(formatLocalDate('')).toBe('')
    expect(formatLocalDate('not-a-date')).toBe('')
  })
})
