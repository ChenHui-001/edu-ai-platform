import { beforeEach, describe, expect, it, vi } from 'vitest'

import {
  DEFAULT_LEAVE_MESSAGE,
  JOB_STORAGE_PREFIX,
  rememberJob,
  resolveLeave,
  takeRememberedJob,
} from '../leaveGuard'

/**
 * 守 U-02：长任务页面的离开保护。最容易错的两点——
 * ① 不 busy 时仍然拦人（用久了用户就习惯性点「确定」，等于没有保护）；
 * ② 确认框「取消」被当成放行（那正好反了：取消 = 留下继续等）。
 */
describe('resolveLeave', () => {
  const confirmYes = vi.fn(async () => true)
  const confirmNo = vi.fn(async () => false)

  beforeEach(() => {
    confirmYes.mockClear()
    confirmNo.mockClear()
  })

  it('没有进行中的任务直接放行，且不问用户', async () => {
    const confirm = vi.fn(async () => true)
    expect(await resolveLeave(() => false, confirm)).toBe(true)
    expect(confirm).not.toHaveBeenCalled()
  })

  it('有任务时确认 = 放行', async () => {
    expect(await resolveLeave(() => true, confirmYes, '自定义文案')).toBe(true)
    expect(confirmYes).toHaveBeenCalledWith('自定义文案')
  })

  it('有任务时取消 = 留在本页', async () => {
    expect(await resolveLeave(() => true, confirmNo)).toBe(false)
    expect(confirmNo).toHaveBeenCalledWith(DEFAULT_LEAVE_MESSAGE)
  })

  it('确认框返回非 true（undefined / 字符串）也按留下处理', async () => {
    expect(await resolveLeave(() => true, async () => undefined)).toBe(false)
    expect(await resolveLeave(() => true, async () => 'cancel')).toBe(false)
  })
})

describe('rememberJob / takeRememberedJob', () => {
  it('存进去能取出来，且只取一次', () => {
    rememberJob('paper_wizard', 42)
    expect(localStorage.getItem(JOB_STORAGE_PREFIX + 'paper_wizard')).toBe('42')
    expect(takeRememberedJob('paper_wizard')).toBe(42)
    // 取过一次就清掉：否则用户每次进页面都被问「要恢复上次任务吗」
    expect(takeRememberedJob('paper_wizard')).toBe(0)
  })

  it('传 0 / 空清除记录', () => {
    rememberJob('agent_generate', 7)
    rememberJob('agent_generate', 0)
    expect(takeRememberedJob('agent_generate')).toBe(0)
  })

  it('脏数据不抛异常，按「没有任务」处理', () => {
    localStorage.setItem(JOB_STORAGE_PREFIX + 'x', 'not-a-number')
    expect(takeRememberedJob('x')).toBe(0)
    localStorage.setItem(JOB_STORAGE_PREFIX + 'y', '-3')
    expect(takeRememberedJob('y')).toBe(0)
  })

  it('不同页面互不串（key 前缀隔离）', () => {
    rememberJob('a', 1)
    rememberJob('b', 2)
    expect(takeRememberedJob('a')).toBe(1)
    expect(takeRememberedJob('b')).toBe(2)
  })
})
