import { describe, expect, it } from 'vitest'

import {
  CHART_FALLBACK,
  chartColor,
  menuBg,
  MENU_BG_FALLBACK,
  withAlpha,
} from '../theme'

/**
 * 守 6.5 视觉一致性：图表色只能有一个出处。
 * 这里盯三件事——回落值不许变成空串（空串 = canvas 画透明 = 图"没画出来"）、
 * 回落值必须与 index.css 的定义一致、半透明转换不能算错通道。
 */
describe('chartColor', () => {
  it('jsdom 读不到 CSS 变量时回落到默认色，而不是空串', () => {
    const c = chartColor('primary')
    expect(c).toBe(CHART_FALLBACK.primary)
    expect(c).not.toBe('')
  })

  it('未知 key 回落到 primary（宁可颜色不对，也不能给空值）', () => {
    expect(chartColor('nope')).toBe(CHART_FALLBACK.primary)
  })

  it('弱/强两档各有独立默认值', () => {
    expect(chartColor('weak')).toBe(CHART_FALLBACK.weak)
    expect(chartColor('strong')).toBe(CHART_FALLBACK.strong)
    expect(new Set([chartColor('primary'), chartColor('weak'), chartColor('strong')]).size).toBe(3)
  })

  it('能读到 CSS 变量时以变量为准（换主题不用改代码）', () => {
    const root = document.documentElement
    root.style.setProperty('--chart-primary', ' #123456 ')
    try {
      expect(chartColor('primary')).toBe('#123456')
    } finally {
      root.style.removeProperty('--chart-primary')
    }
  })
})

describe('withAlpha', () => {
  it('把品牌蓝转成 rgba', () => {
    expect(withAlpha('#2f6fd0', 0.2)).toBe('rgba(47,111,208,0.2)')
  })

  it('非 6 位十六进制原样返回（不瞎猜，也不抛）', () => {
    expect(withAlpha('rgb(1,2,3)', 0.5)).toBe('rgb(1,2,3)')
    expect(withAlpha('', 0.5)).toBe('transparent')
  })

  it('alpha 默认 0.2', () => {
    expect(withAlpha('#000000')).toBe('rgba(0,0,0,0.2)')
  })
})

describe('menuBg', () => {
  it('读不到变量时回落成真实色值（el-menu 不能收 var()）', () => {
    const bg = menuBg()
    expect(bg).toBe(MENU_BG_FALLBACK)
    expect(bg.startsWith('#')).toBe(true)
  })
})
