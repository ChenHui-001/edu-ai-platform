/**
 * 全站响应式断点唯一口径（6.5 响应式适配）。
 *
 * CSS 变量不能用于 @media 条件，所以断点数字必须「两处手写、一处对齐」：
 * JS 从这里的 BREAKPOINTS 取值，CSS 的 @media 手写相同数字。数值对齐
 * Element Plus 栅格断点（xs<768、sm≥768、md≥992、lg≥1200），否则
 * `el-col :md` 的横排点和手写 @media 的堆叠点会错开 —— SystemSetting
 * 曾出现 991 与 992 两种写法，就是这个坑的实证。
 *
 * 页级例外（有意为之，见 styles/index.css --bp-* 注释）：
 * Login/AgentChat 900、GradingCenter 1100。
 */
export const BREAKPOINTS = { mobile: 768, tablet: 992, wide: 1200 }

/**
 * 「< 断点」的 matchMedia 条件串。减 0.02px 让它与栅格的「≥断点横排」
 * 严格互补：整数断点上两套布局恰好二选一，而不是 1px 重叠窗口。
 */
export function breakpointQuery(name) {
  const bp = BREAKPOINTS[name]
  if (!bp) throw new Error(`未知断点: ${name}`)
  return `(max-width: ${bp - 0.02}px)`
}

/**
 * TableCards 单元格取值：formatter 优先；null/undefined/'' 显示占位符。
 * 注意 0 和 false 是合法值，不能被占位符吞掉。
 */
export function formatCellValue(row, col) {
  if (col && typeof col.formatter === 'function') return col.formatter(row, col)
  const raw = row ? row[col.prop] : undefined
  if (raw === null || raw === undefined || raw === '') return '-'
  return raw
}

// ---- 以下为 Vue 组合式函数，只在组件 setup 中使用 ----
import { ref, onMounted, onBeforeUnmount } from 'vue'

/**
 * 响应式媒体查询。值在 setup 阶段同步初始化（避免移动端首帧闪桌面布局），
 * 监听器在 mounted 后注册、卸载时清理。
 */
export function useMediaQuery(query) {
  const matches = ref(false)
  if (typeof window !== 'undefined' && window.matchMedia) {
    matches.value = window.matchMedia(query).matches
  }
  let mql = null
  const update = () => { if (mql) matches.value = mql.matches }
  onMounted(() => {
    if (typeof window === 'undefined' || !window.matchMedia) return
    mql = window.matchMedia(query)
    update()
    // 旧 Safari 只有 addListener；现代浏览器两者都有
    if (mql.addEventListener) mql.addEventListener('change', update)
    else if (mql.addListener) mql.addListener(update)
  })
  onBeforeUnmount(() => {
    if (!mql) return
    if (mql.removeEventListener) mql.removeEventListener('change', update)
    else if (mql.removeListener) mql.removeListener(update)
    mql = null
  })
  return matches
}

/** 手机断点（<768）：TableCards 等移动端降级用它 */
export function useIsMobile() {
  return useMediaQuery(breakpointQuery('mobile'))
}
