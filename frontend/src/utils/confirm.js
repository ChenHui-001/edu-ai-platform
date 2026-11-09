import { ElMessageBox } from 'element-plus'

/**
 * 统一确认框：用户点「取消 / 关闭」一律返回 false，**不抛异常**。
 *
 * 为什么需要它：`ElMessageBox.confirm()` 被取消时 reject 的是字符串
 * `'cancel'`，不是 Error。直接 `await` 且未 catch 时，Vue 会把这个
 * rejection 交给 `app.config.errorHandler`，于是用户只是点了「取消」，
 * 页面却弹「页面运行时错误」并挂一条红色横幅（audit-reports/
 * reaudit-2026-11-06.md P1-9）。
 *
 * 更根本的问题是**依赖了 Element Plus 的实现细节**：它现在 reject 字符串，
 * 将来完全可能改成 reject 一个带 action 的 Error。调用点自己用布尔值
 * 分支，才不随组件库版本漂移。
 *
 * 两种调用形式都支持（迁移期兼容）：
 *   confirmAction('确认删除？')
 *   confirmAction('确认删除？', '删除确认', { confirmButtonText: '确认删除' })
 *   confirmAction('确认删除？', { title: '删除确认' })
 *
 * @param {string} message 确认文案
 * @param {string|object} titleOrOptions 标题，或直接给 options（含 title）
 * @param {object} [options] 透传给 ElMessageBox.confirm 的选项
 * @returns {Promise<boolean>} 确认 true；取消 / 关闭 / 出错 false
 */
function splitArgs(titleOrOptions, options) {
  if (typeof titleOrOptions === 'string' || titleOrOptions == null) {
    const opts = options || {}
    return { title: titleOrOptions || opts.title || '提示', opts }
  }
  const opts = titleOrOptions || {}
  return { title: opts.title || '提示', opts }
}

export async function confirmAction(message, titleOrOptions = '提示', options = {}) {
  const { title, opts } = splitArgs(titleOrOptions, options)
  // title 走第二个参数，避免同一个键从 options 里再覆盖一次
  const { title: _ignored, ...rest } = opts
  try {
    await ElMessageBox.confirm(message, title, { type: 'warning', ...rest })
    return true
  } catch {
    // 用户取消、点右上角关闭、或确认框本身异常：都按「不继续」处理
    return false
  }
}

/**
 * 带输入框的确认：取消返回 `null`，确认返回字符串（可能为空串）。
 *
 * 与 `confirmAction` 同一个理由 —— `ElMessageBox.prompt` 取消时同样 reject
 * 字符串，`catch` 一旦漏写就会冒出「页面运行时错误： cancel」。
 *
 * @returns {Promise<string|null>}
 */
export async function promptAction(message, titleOrOptions = '提示', options = {}) {
  const { title, opts } = splitArgs(titleOrOptions, options)
  const { title: _ignored, ...rest } = opts
  try {
    const { value } = await ElMessageBox.prompt(message, title, { type: 'warning', ...rest })
    return value == null ? '' : String(value)
  } catch {
    return null
  }
}

/**
 * 只读提示框（没有取消语义）。内部吞掉「点右上角关闭」的 rejection，
 * 调用方不必写 `.catch(() => {})`，也不会污染全局错误处理。
 */
export function alertAction(message, titleOrOptions = '提示', options = {}) {
  const { title, opts } = splitArgs(titleOrOptions, options)
  const { title: _ignored, ...rest } = opts
  return ElMessageBox.alert(message, title, { ...rest }).catch(() => {})
}
