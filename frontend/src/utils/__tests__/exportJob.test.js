import { describe, expect, it, vi } from 'vitest'

import {
  EXPORT_MAX_WAIT_MS,
  EXPORT_POLL_INTERVAL_MS,
  exportProgressText,
  runExportJob,
} from '../exportJob'

/**
 * 守 F-05：把导出从「同步等文件」改成「提交 + 轮询 + 下载」之后，
 * 前端最容易错的三件事——按非终态结束、无上限轮询、下载到未完成的文件。
 */
function makeApi(states) {
  const queue = [...states]
  return {
    createExportJob: vi.fn(async () => ({ data: { job_id: 42 } })),
    exportJob: vi.fn(async () => ({ data: queue.length > 1 ? queue.shift() : queue[0] })),
    downloadExportJob: vi.fn(async () => ({ data: 'BLOB' })),
  }
}

// 轮询间隔用 0 让测试不必真等（sleep 的 setTimeout(0) 仍会让出事件循环）
const FAST = { intervalMs: 0 }

describe('runExportJob', () => {
  it('轮询到 success 才下载（pending/running 不算结束）', async () => {
    const api = makeApi([
      { status: 'pending', progress: 0 },
      { status: 'running', progress: 45, stage: '渲染文件' },
      { status: 'success', progress: 100, stage: '完成' },
    ])
    const stages = []
    const res = await runExportJob(api, 7, { kind: 'pdf' }, {
      ...FAST, onProgress: (j) => stages.push(j.stage || j.status),
    })

    expect(res).toEqual({ data: 'BLOB' })
    expect(api.downloadExportJob).toHaveBeenCalledWith(42)
    expect(stages).toEqual(['pending', '渲染文件', '完成'])
    expect(api.createExportJob).toHaveBeenCalledWith(7, { kind: 'pdf' })
  })

  it('历史拼写 succeeded 也算成功（后端两套拼写都读过）', async () => {
    const api = makeApi([{ status: 'succeeded' }])
    await runExportJob(api, 1, { kind: 'docx' }, FAST)
    expect(api.downloadExportJob).toHaveBeenCalled()
  })

  it('failed 直接抛后端原因，且不下载', async () => {
    const api = makeApi([{ status: 'failed', error: '试卷不存在（可能已被删除）' }])
    await expect(runExportJob(api, 1, { kind: 'pdf' }, FAST))
      .rejects.toThrow('试卷不存在')
    expect(api.downloadExportJob).not.toHaveBeenCalled()
  })

  it('cancelled 不算失败也不下载，给出可读提示', async () => {
    const api = makeApi([{ status: 'cancelled' }])
    await expect(runExportJob(api, 1, { kind: 'pdf' }, FAST)).rejects.toThrow('导出已取消')
    expect(api.downloadExportJob).not.toHaveBeenCalled()
  })

  it('一直 running 会超时退出，而不是永久转圈', async () => {
    const api = makeApi([{ status: 'running' }])
    await expect(runExportJob(api, 1, { kind: 'pdf' }, { intervalMs: 5, timeoutMs: 20 }))
      .rejects.toThrow('导出超时')
    expect(api.downloadExportJob).not.toHaveBeenCalled()
  })

  it('提交后没拿到 job_id 立刻报错（不进入轮询）', async () => {
    const api = makeApi([{ status: 'success' }])
    api.createExportJob = vi.fn(async () => ({ data: {} }))
    await expect(runExportJob(api, 1, { kind: 'pdf' }, FAST)).rejects.toThrow('没有拿到任务号')
    expect(api.exportJob).not.toHaveBeenCalled()
  })

  it('两次查询之间真的按 intervalMs 等待（不做忙轮询）', async () => {
    // 若实现是「立即循环」，两次查询间隔会是 0 —— 服务端会被打满
    const api = makeApi([{ status: 'running' }, { status: 'success' }])
    const t0 = Date.now()
    await runExportJob(api, 1, { kind: 'pdf' }, { intervalMs: 20, timeoutMs: 2000 })
    expect(Date.now() - t0).toBeGreaterThanOrEqual(18)
    expect(api.exportJob).toHaveBeenCalledTimes(2)
  })

  it('常量：间隔小于超时，否则首查即超时', () => {
    expect(EXPORT_POLL_INTERVAL_MS).toBeLessThan(EXPORT_MAX_WAIT_MS)
  })
})

describe('exportProgressText', () => {
  it('优先用后端 stage', () => {
    expect(exportProgressText({ stage: '渲染文件', progress: 45 })).toBe('渲染文件')
  })

  it('没有 stage 时回落百分比', () => {
    expect(exportProgressText({ progress: 45 })).toBe('正在导出 45%')
  })

  it('什么都没有时不显示 0%', () => {
    expect(exportProgressText({})).toBe('正在导出')
    expect(exportProgressText(null)).toBe('正在导出')
  })
})
