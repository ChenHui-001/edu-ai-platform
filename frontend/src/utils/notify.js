import { ElMessage } from 'element-plus'

/**
 * 只在「还没有人提示过用户」时才弹错误提示。
 *
 * 为什么需要它：`api/request.js` 的响应拦截器对每个失败请求都已经弹过一次
 * 中文提示，并给 error 打了 `__handled` 标记。组件里再写一句
 * `ElMessage.error(e.message)` 就成了**同一个错误弹两次**（reaudit3 P2-13）：
 * 两条 toast 上下叠着，用户不知道该处理哪条；文案还可能一条中文一条英文。
 *
 * 用法：
 *   catch (e) { toastIfUnhandled(e, '保存失败') }
 *
 * - 请求失败（拦截器已提示）→ 静默，不重复打扰
 * - 组件内部自己抛的错（`__handled` 缺失）→ 照常提示，不会被吞掉
 *
 * 注意 fallback 只在**确实没有可读文案**时使用，不要用它覆盖后端给的
 * 具体原因 —— 「试卷名称已存在」比「保存失败」有用得多。
 *
 * @param {any} err 捕获到的异常
 * @param {string} [fallback] 无文案时的兜底提示
 */
export function toastIfUnhandled(err, fallback = '操作失败') {
  if (err && typeof err === 'object' && err.__handled === true) return
  ElMessage.error(pickMessage(err, fallback))
}

/** 从异常里取一句人能读的话：后端 message > 已回写的 error.message > 兜底 */
export function pickMessage(err, fallback = '操作失败') {
  const backendMsg = err?.response?.data?.message
  if (backendMsg && typeof backendMsg === 'string') return backendMsg
  const msg = err?.message
  if (msg && typeof msg === 'string') return msg
  if (typeof err === 'string' && err) return err
  return fallback
}
