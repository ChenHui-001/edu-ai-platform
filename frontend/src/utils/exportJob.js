/**
 * 试卷导出异步化（F-05）的轮询编排。
 *
 * ## 为什么抽成独立模块
 * 后端把「渲染 + 生成文件」挪到后台任务之后，前端必须做三件容易做错的事：
 * ① 提交后**立刻**返回 job_id，不能同步等文件；② 按终态判断结束，
 * 而不是按"拿到响应"判断（`failed`/`cancelled` 也是响应）；
 * ③ 有上限的轮询 —— 后台线程会随进程重启消失，无上限轮询就是永久转圈。
 *
 * 这三件事写在页面里就只能靠点页面回归，所以抽出来配单测（见
 * `__tests__/exportJob.test.js`），页面只负责"进度文案 + 下载"。
 */

/** 轮询间隔：导出通常 1~5s 完成，1.2s 足够细，又不会把接口打满 */
export const EXPORT_POLL_INTERVAL_MS = 1200

/** 等多久算超时。后端 job 超时阈值 300s，这里留一半，避免用户干等 5 分钟 */
export const EXPORT_MAX_WAIT_MS = 120000

/** 这些状态表示「已经结束，且文件可用」 */
const OK_STATUSES = ['success', 'succeeded']
/** 这些状态表示「已经结束，但没文件」 */
const BAD_STATUSES = ['failed', 'cancelled']

function sleep(ms) {
  return new Promise((resolve) => setTimeout(resolve, ms))
}

/** 给用户看的进度文案：后端没给 stage 时兜底成百分比 */
export function exportProgressText(job) {
  const stage = String(job?.stage || '').trim()
  if (stage) return stage
  const pct = Number(job?.progress)
  return Number.isFinite(pct) && pct > 0 ? `正在导出 ${pct}%` : '正在导出'
}

/**
 * 提交导出任务并轮询到终态，成功时返回下载响应（blob）。
 *
 * @param {object} api         必须提供 createExportJob / exportJob / downloadExportJob
 * @param {number} paperId     试卷 id
 * @param {object} payload     { kind, mode, layout, with_seal_line, with_page_number }
 * @param {object} [opts]
 * @param {(job: object) => void} [opts.onProgress] 每次轮询回调（用于展示 stage）
 * @param {number} [opts.timeoutMs]
 * @param {number} [opts.intervalMs]
 * @returns {Promise<any>} downloadExportJob 的返回值（拦截器下是 axios response）
 */
export async function runExportJob(api, paperId, payload, opts = {}) {
  const intervalMs = opts.intervalMs ?? EXPORT_POLL_INTERVAL_MS
  const timeoutMs = opts.timeoutMs ?? EXPORT_MAX_WAIT_MS

  const created = await api.createExportJob(paperId, payload)
  const jobId = created?.data?.job_id ?? created?.job_id
  if (!jobId) throw new Error('提交导出任务失败：没有拿到任务号')

  // 先等一个间隔再查：任务是刚提交的，立刻查必然是 pending，
  // 白打一次接口还可能让用户看到「排队中」闪一下。
  let waited = 0
  while (waited < timeoutMs) {
    await sleep(intervalMs)
    waited += intervalMs

    const res = await api.exportJob(jobId)
    const job = res?.data ?? res ?? {}
    opts.onProgress?.(job)

    if (OK_STATUSES.includes(job.status)) {
      return await api.downloadExportJob(jobId)
    }
    if (BAD_STATUSES.includes(job.status)) {
      throw new Error(job.error || (job.status === 'cancelled' ? '导出已取消' : '导出失败'))
    }
  }
  throw new Error('导出超时，请稍后重试')
}
