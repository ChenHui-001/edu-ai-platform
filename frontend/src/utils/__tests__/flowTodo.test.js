import { describe, expect, it } from 'vitest'

import {
  HISTORY_ACTIONS,
  INSTANCE_STATUS,
  OVERDUE_LABELS,
  RETURN_TARGETS,
  ROLE_LABELS,
  TASK_STATUS,
  countText,
  historyActionText,
  historyType,
  instanceStatusText,
  instanceStatusType,
  overdueText,
  overdueType,
  remainingText,
  returnTargets,
  roleLabel,
  taskStatusText,
  taskStatusType,
  urgeCooldownRemaining
} from '../flowTodo'

describe('状态枚举完整性', () => {
  it('任务状态覆盖引擎的 4 种取值', () => {
    // 与 backend/app/services/flow_engine.py 的 TASK_* 常量一一对应。
    // 少一种就会在前端显示成原始英文 —— 用例锁住这份对应关系。
    expect(Object.keys(TASK_STATUS).sort()).toEqual(['CANCEL', 'CLAIMED', 'DONE', 'TODO'])
  })

  it('实例状态覆盖引擎的 5 种取值', () => {
    expect(Object.keys(INSTANCE_STATUS).sort()).toEqual([
      'APPROVED', 'CANCELLED', 'REJECTED', 'RETURNED', 'RUNNING'
    ])
  })

  it('留痕动作覆盖引擎的 6 种取值', () => {
    expect(Object.keys(HISTORY_ACTIONS).sort()).toEqual([
      'APPROVE', 'CANCEL', 'EXECUTE', 'REJECT', 'RETURN', 'START'
    ])
  })

  it('角色标签覆盖 5 个内置角色', () => {
    expect(Object.keys(ROLE_LABELS).sort()).toEqual([
      'grade_admin', 'guest', 'student', 'sys_admin', 'teacher'
    ])
  })
})

describe('文案与颜色', () => {
  it('未知状态回落为原始值而不是空白', () => {
    // 引擎新增状态而前端没跟上时，至少要显示原始标识，
    // 否则用户看到空白格子，无法判断是什么状态。
    expect(taskStatusText('WHATEVER')).toBe('WHATEVER')
    expect(instanceStatusText('WHATEVER')).toBe('WHATEVER')
    expect(historyActionText('WHATEVER')).toBe('WHATEVER')
  })

  it('空值统一显示为短横线', () => {
    expect(taskStatusText(null)).toBe('-')
    expect(taskStatusText('')).toBe('-')
    expect(instanceStatusText(undefined)).toBe('-')
    expect(roleLabel(null)).toBe('-')
  })

  it('未知状态的颜色回落为 info，不抛异常', () => {
    expect(taskStatusType('WHATEVER')).toBe('info')
    expect(instanceStatusType('WHATEVER')).toBe('info')
  })

  it('通过是绿色、驳回是红色、退回是橙色', () => {
    // 颜色承载语义：审核人扫一眼颜色就知道该批还是该退。
    expect(historyType('APPROVE')).toBe('success')
    expect(historyType('REJECT')).toBe('danger')
    expect(historyType('RETURN')).toBe('warning')
  })

  it('角色编码回落为原始编码', () => {
    expect(roleLabel('grade_admin')).toBe('年级管理员')
    expect(roleLabel('custom_role')).toBe('custom_role')
  })
})

describe('退回目标', () => {
  it('按流程编码返回白名单目标', () => {
    const targets = returnTargets('PAPER_REVIEW_001')
    expect(targets).toEqual(RETURN_TARGETS.PAPER_REVIEW_001)
    expect(targets[0].activity_id).toBe('PR02')
  })

  it('白名单未覆盖时从留痕的 from_activity 取候选', () => {
    const history = [
      { from_activity: 'PR01', activity_name: '开始' },
      { from_activity: 'PR02', activity_name: '提交审核申请' },
      { from_activity: 'PR02', activity_name: '提交审核申请' }
    ]
    const targets = returnTargets('UNKNOWN_FLOW', history)
    expect(targets.map(t => t.activity_id)).toEqual(['PR01', 'PR02'])
  })

  it('白名单命中时忽略留痕候选', () => {
    // 命中白名单就以白名单为准：留痕里的节点未必是合法退回目标。
    const history = [{ from_activity: 'PR99', activity_name: '某个不合法节点' }]
    const targets = returnTargets('REGISTRATION_001_T', history)
    expect(targets.map(t => t.activity_id)).toEqual(['RG02'])
  })

  it('既无白名单也无留痕时返回空数组', () => {
    expect(returnTargets(null, [])).toEqual([])
    expect(returnTargets(undefined, undefined)).toEqual([])
  })
})


describe('逾期标识', () => {
  it('逾期与正常两态齐全', () => {
    expect(Object.keys(OVERDUE_LABELS).sort()).toEqual(['normal', 'overdue'])
  })

  it('逾期是红色、正常是灰色', () => {
    // 颜色承载语义：扫一眼列表就知道哪些压着没处理。
    expect(overdueType(true)).toBe('danger')
    expect(overdueType(false)).toBe('info')
  })

  it('未逾期时文案为正常', () => {
    expect(overdueText(false)).toBe('正常')
    expect(overdueText(true)).toBe('已逾期')
  })
})

describe('剩余时间文案', () => {
  const now = new Date('2026/11/19 12:00:00')

  it('无截止时间时给出明确说明而不是空白', () => {
    expect(remainingText(null, false, now)).toBe('无截止时间')
    expect(remainingText('', false, now)).toBe('无截止时间')
  })

  it('时间格式非法时同样回落到无截止时间', () => {
    // 后端返回的字符串万一格式变了，前端不能显示 NaN。
    expect(remainingText('not-a-date', false, now)).toBe('无截止时间')
  })

  it('按分钟、小时、天三档显示剩余', () => {
    expect(remainingText('2026-11-19 12:30:00', false, now)).toBe('剩 30 分钟')
    expect(remainingText('2026-11-19 15:00:00', false, now)).toBe('剩 3 小时')
    expect(remainingText('2026-11-22 12:00:00', false, now)).toBe('剩 3 天')
  })

  it('逾期时显示已逾期时长', () => {
    expect(remainingText('2026-11-19 09:00:00', true, now)).toBe('已逾期 3 小时')
    expect(remainingText('2026-11-16 12:00:00', true, now)).toBe('已逾期 3 天')
  })

  it('不足一分钟显示即将到期或刚刚逾期', () => {
    expect(remainingText('2026-11-19 12:00:30', false, now)).toBe('即将到期')
    expect(remainingText('2026-11-19 11:59:30', true, now)).toBe('刚刚逾期')
  })
})

describe('催办频次限制', () => {
  const now = new Date('2026/11/19 12:00:00')

  it('没催办过时不限流', () => {
    expect(urgeCooldownRemaining({}, now)).toBe(0)
    expect(urgeCooldownRemaining({ last_urged_at: null }, now)).toBe(0)
  })

  it('刚催过则返回剩余分钟数', () => {
    // 后端限 30 分钟，前端同步禁用按钮 —— 否则用户点了才收报错。
    const remain = urgeCooldownRemaining(
      { last_urged_at: '2026-11-19 11:50:00' }, now)
    expect(remain).toBe(20)
  })

  it('超过冷却期则可再次催办', () => {
    const remain = urgeCooldownRemaining(
      { last_urged_at: '2026-11-19 11:00:00' }, now)
    expect(remain).toBe(0)
  })

  it('时间格式非法时不限流（交给后端判定）', () => {
    expect(urgeCooldownRemaining({ last_urged_at: 'bad' }, now)).toBe(0)
  })
})

describe('计数展示', () => {
  it('零次显示短横线而不是 0', () => {
    // 列表里满屏的 0 是噪音，用短横线表示「没有发生过」。
    expect(countText(0)).toBe('-')
    expect(countText(null)).toBe('-')
    expect(countText(undefined)).toBe('-')
  })

  it('有次数时显示数字', () => {
    expect(countText(3)).toBe('3')
    expect(countText('5')).toBe('5')
  })
})
