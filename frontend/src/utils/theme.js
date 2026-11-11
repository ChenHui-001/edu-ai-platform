/**
 * 主题取色（6.5 视觉一致性）。
 *
 * ## 为什么不能直接用 CSS 变量
 * ECharts 把图画在 `<canvas>` 上，canvas 的绘制 API 只认**具体色值**：
 * `ctx.strokeStyle = 'var(--chart-primary)'` 不会解析，直接退回黑色。
 * 所以图表颜色必须由 JS 把 CSS 变量读成真实色值再传进去。
 *
 * ## 为什么颜色只定义在 index.css
 * 此前 `#2f6fd0` 以字面量形式散在 10 个视图（ECharts 配置 + 统计数字色），
 * 同一次换色要改 10 个文件，还敢漏一个 —— `MasteryMap` 就漏着 Element 默认的
 * `#409eff`，同一个学生端里同时出现两种蓝。
 * 现在颜色只有一个出处（`styles/index.css` 的 `:root`），业务代码只写语义名。
 *
 * ## 读不到怎么办
 * 单测环境（jsdom）、样式还没加载、用户自定义主题——都可能读不到。
 * 此时**必须**回落到与 index.css 一致的默认值，而不是给 canvas 塞空串
 * （空串 = 透明 = 图看起来"没画出来"，比报错更难查）。
 */

/** 与 `styles/index.css` 的 `--chart-*` 保持一致；改色两处都要改，单测会盯 */
export const CHART_FALLBACK = {
  primary: '#2f6fd0',
  weak: '#e6a23c',
  strong: '#67c23a',
}

/** 侧边栏底色默认值（el-menu 需要真实色值，不能传 var()） */
export const MENU_BG_FALLBACK = '#1f2d3d'

function readVar(name) {
  if (typeof window === 'undefined' || !window.getComputedStyle) return ''
  const root = document.documentElement
  if (!root) return ''
  try {
    return (window.getComputedStyle(root).getPropertyValue(name) || '').trim()
  } catch {
    return ''
  }
}

/**
 * 取一个图表色，例如 `chartColor('primary')` → `#2f6fd0`。
 *
 * 刻意**不做缓存**：读一次 getComputedStyle 是微秒级，而缓存会让
 * 「换了主题色但页面没刷新」这种问题变成"有的模块是新色、有的还是旧色"。
 *
 * @param {'primary'|'weak'|'strong'} key
 * @returns {string} 形如 `#2f6fd0`
 */
export function chartColor(key) {
  const name = `--chart-${key}`
  const fromCss = readVar(name)
  if (fromCss) return fromCss
  return CHART_FALLBACK[key] || CHART_FALLBACK.primary
}

/**
 * 取同一颜色的半透明版本（ECharts 的 `areaStyle.color` 常用）。
 *
 * @param {string} hex 形如 `#2f6fd0`
 * @param {number} alpha 0~1
 * @returns {string} 形如 `rgba(47,111,208,0.2)`
 */
export function withAlpha(hex, alpha = 0.2) {
  const m = /^#([0-9a-f]{6})$/i.exec(String(hex || '').trim())
  if (!m) return String(hex || 'transparent')
  const int = parseInt(m[1], 16)
  const r = (int >> 16) & 255
  const g = (int >> 8) & 255
  const b = int & 255
  return `rgba(${r},${g},${b},${alpha})`
}

/** 侧边栏底色（真实色值，供 el-menu 的 background-color 属性使用） */
export function menuBg() {
  return readVar('--menu-bg') || MENU_BG_FALLBACK
}
