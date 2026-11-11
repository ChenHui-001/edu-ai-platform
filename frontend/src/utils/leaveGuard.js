/**
 * 长任务离开保护（U-02）。
 *
 * ## 问题
 * 组卷 / AI 出题 / 教案生成都是「后台任务 + 前端轮询」。用户切走页面时
 * 现有实现只是把轮询停掉（`pollAborted = true`）—— 没有确认、没有提示，
 * 回来以后进度和结果全没了，用户以为白等了。更糟的是刷新浏览器：
 * 任务其实还在后端跑（状态在 `sys_agent_job`），但前端已经不知道该查哪个 job。
 *
 * ## 三件事
 * 1. **`beforeunload`**：刷新 / 关标签页时让浏览器弹原生确认（拦不住也
 *    不能自定义文案，这是浏览器规范）；不 busy 时**不注册处理器**，
 *    否则每次离开页面浏览器都问「确定要离开？」，很快就变成用户习惯性点确定。
 * 2. **路由离开确认**：站内切走用统一 `confirmAction`（不抛异常、取消返回 false）。
 * 3. **job 恢复**：`rememberJob` / `takeRememberedJob` 把 job_id 存本机，
 *    页面重新挂载时能接着轮询 —— 数据不出本机，与现有草稿方案一致。
 *
 * ## 为什么判定函数单独导出
 * composable 依赖 vue-router 上下文，只能在组件 setup 里跑；而「什么时候该拦」
 * 这条逻辑恰恰是最容易写错的（busy 判定、确认结果取反、异常兜底）。
 * 所以把它拆成纯函数，让它可被单测覆盖（`__tests__/leaveGuard.test.js`）。
 */
import { onBeforeUnmount, onMounted } from 'vue'
import { onBeforeRouteLeave } from 'vue-router'

import { confirmAction } from './confirm'

export const DEFAULT_LEAVE_MESSAGE =
  '任务仍在后台进行，离开后需要重新进入本页才能查看结果。确定离开吗？'

export const JOB_STORAGE_PREFIX = 'edu:runningJob:'

/**
 * 决定是否放行路由离开。
 *
 * @param {() => boolean} isBusy 当前是否有进行中的任务
 * @param {(message: string) => Promise<boolean>} confirm 确认框（默认 confirmAction）
 * @param {string} [message]
 * @returns {Promise<boolean>} true = 放行
 */
export async function resolveLeave(isBusy, confirm, message = DEFAULT_LEAVE_MESSAGE) {
  if (!isBusy()) return true
  const ok = await confirm(message)
  return ok === true
}

/** 存一个进行中的 job，供页面重新进入时恢复轮询 */
export function rememberJob(key, jobId) {
  try {
    if (jobId) localStorage.setItem(JOB_STORAGE_PREFIX + key, String(jobId))
    else localStorage.removeItem(JOB_STORAGE_PREFIX + key)
  } catch {
    // 隐私模式 / 存储满：恢复不了不影响主流程，静默忽略
  }
}

/** 取出并**清除**记住的 job_id（取过一次不再重复提示） */
export function takeRememberedJob(key) {
  try {
    const raw = localStorage.getItem(JOB_STORAGE_PREFIX + key)
    if (!raw) return 0
    localStorage.removeItem(JOB_STORAGE_PREFIX + key)
    const id = Number(raw)
    return Number.isFinite(id) && id > 0 ? id : 0
  } catch {
    return 0
  }
}

/**
 * 在组件里装上离开保护。
 *
 * @param {() => boolean} isBusy
 * @param {object} [opts]
 * @param {string} [opts.message] 站内离开发给确认框的文案
 * @param {string} [opts.unloadMessage] 原生弹窗文案（多数浏览器只显示自己的）
 */
export function useLeaveGuard(isBusy, opts = {}) {
  const message = opts.message || DEFAULT_LEAVE_MESSAGE
  const unloadMessage = opts.unloadMessage || message

  function onBeforeUnload(event) {
    if (!isBusy()) return
    event.preventDefault()
    // 老浏览器要求 returnValue 有值才弹；现代浏览器忽略具体文案
    event.returnValue = unloadMessage
    return unloadMessage
  }

  onMounted(() => window.addEventListener('beforeunload', onBeforeUnload))
  onBeforeUnmount(() => window.removeEventListener('beforeunload', onBeforeUnload))

  onBeforeRouteLeave(async () => resolveLeave(isBusy, confirmAction, message))
}
