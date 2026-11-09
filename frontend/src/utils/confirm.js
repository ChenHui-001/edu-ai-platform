import { ElMessageBox } from 'element-plus'

/**
 * 统一确认框：用户点「取消 / 关闭」一律返回 false，**不抛异常**。
 *
 * 为什么需要它：`ElMessageBox.confirm()` 被取消时 reject 的是字符串
 * `'cancel'`，不是 Error。直接 `await` 且未 catch 时，Vue 会把这个
 * rejection 交给 `app.config.errorHandler`，于是用户只是点了「取消」，
 * 页面却弹「页面运行时错误」并挂一条红色横幅（详见 audit-reports/
 * reaudit-2026-11-06.md P1-9）。
 *
 * `main.js` 的 `isBusinessError` 已经把这类字符串 rejection 归为业务错误
 * 兜底，本模块是**主动**做法：让调用方拿到一个布尔值，而不是依赖全局兜底。
 * 新代码请优先用 `if (!(await confirmAction('确认删除？'))) return`。
 *
 * @param {string} message 确认文案
 * @param {object} [options] 透传给 ElMessageBox.confirm 的选项
 * @returns {Promise<boolean>} 确认 true；取消 / 关闭 / 出错 false
 */
export async function confirmAction(message, options = {}) {
  try {
    await ElMessageBox.confirm(message, options.title || '提示', {
      type: 'warning',
      ...options
    })
    return true
  } catch {
    // 用户取消、点右上角关闭、或确认框本身异常：都按「不继续」处理
    return false
  }
}
