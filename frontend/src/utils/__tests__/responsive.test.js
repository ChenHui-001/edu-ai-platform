import { describe, expect, it } from 'vitest'
import { BREAKPOINTS, breakpointQuery, formatCellValue } from '../responsive'

describe('breakpointQuery', () => {
  it('mobile 返回 <768 的条件串，且与栅格 md 严格互补（减 0.02px）', () => {
    expect(breakpointQuery('mobile')).toBe('(max-width: 767.98px)')
  })
  it('tablet 对齐 Element Plus md 断点 992', () => {
    expect(breakpointQuery('tablet')).toBe('(max-width: 991.98px)')
  })
  it('wide 对齐 lg 断点 1200', () => {
    expect(breakpointQuery('wide')).toBe('(max-width: 1199.98px)')
  })
  it('未知断点名抛错而不是返回 undefined 串', () => {
    expect(() => breakpointQuery('foo')).toThrow('未知断点')
  })
  it('三个断点数值与 Element Plus 栅格一致', () => {
    expect(BREAKPOINTS).toEqual({ mobile: 768, tablet: 992, wide: 1200 })
  })
})

describe('formatCellValue', () => {
  it('formatter 优先于取值', () => {
    const row = { score: 88 }
    const col = { prop: 'score', formatter: () => '特优' }
    expect(formatCellValue(row, col)).toBe('特优')
  })
  it('null/undefined/空串显示占位符', () => {
    expect(formatCellValue({}, { prop: 'a' })).toBe('-')
    expect(formatCellValue({ a: null }, { prop: 'a' })).toBe('-')
    expect(formatCellValue({ a: '' }, { prop: 'a' })).toBe('-')
    expect(formatCellValue(null, { prop: 'a' })).toBe('-')
  })
  it('0 和 false 是合法值不能被占位符吞掉', () => {
    expect(formatCellValue({ a: 0 }, { prop: 'a' })).toBe(0)
    expect(formatCellValue({ a: false }, { prop: 'a' })).toBe(false)
  })
  it('普通值原样返回', () => {
    expect(formatCellValue({ a: 'x' }, { prop: 'a' })).toBe('x')
  })
})
