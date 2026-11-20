/**
 * 流程待办页的展示映射（纯函数，便于单测）。
 *
 * 为什么单独抽出来：页面组件里塞状态映射会让「状态枚举 → 文案/颜色」
 * 这类最容易出错的逻辑只能靠肉眼看组件。抽成纯函数后，
 * 枚举漏一种、颜色写错一类，都能被用例直接抓出来。
 *
 * 与后端保持一致：
 *   - 任务状态：TODO / CLAIMED / DONE / CANCEL（flow_engine.TASK_*）
 *   - 实例状态：RUNNING / APPROVED / REJECTED / RETURNED / CANCELLED
 *   - 留痕动作：START / APPROVE / REJECT / RETURN / EXECUTE / CANCEL
 */

export const ROLE_LABELS = {
  sys_admin: '系统管理员',
  grade_admin: '年级管理员',
  teacher: '教师',
  student: '学生',
  guest: '访客'
}

export const TASK_STATUS = {
  TODO: { text: '待处理', type: 'warning' },
  CLAIMED: { text: '已认领', type: 'primary' },
  DONE: { text: '已完成', type: 'success' },
  CANCEL: { text: '已取消', type: 'info' }
}

export const INSTANCE_STATUS = {
  RUNNING: { text: '进行中', type: 'warning' },
  APPROVED: { text: '已通过', type: 'success' },
  REJECTED: { text: '已驳回', type: 'danger' },
  RETURNED: { text: '已退回', type: 'info' },
  CANCELLED: { text: '已取消', type: 'info' }
}

export const HISTORY_ACTIONS = {
  START: '发起',
  APPROVE: '通过',
  REJECT: '驳回',
  RETURN: '退回',
  EXECUTE: '执行',
  CANCEL: '取消'
}

export function roleLabel(code) {
  return ROLE_LABELS[code] || code || '-'
}

export function taskStatusText(status) {
  return TASK_STATUS[status]?.text || status || '-'
}

export function taskStatusType(status) {
  return TASK_STATUS[status]?.type || 'info'
}

export function instanceStatusText(status) {
  return INSTANCE_STATUS[status]?.text || status || '-'
}

export function instanceStatusType(status) {
  return INSTANCE_STATUS[status]?.type || 'info'
}

export function historyActionText(action) {
  return HISTORY_ACTIONS[action] || action || '-'
}

export function historyType(action) {
  if (action === 'APPROVE') return 'success'
  if (action === 'REJECT') return 'danger'
  if (action === 'RETURN') return 'warning'
  return 'primary'
}

/**
 * 退回的可选目标节点。
 *
 * 优先用流程编码查白名单——不同流程的合法退回目标不同，
 * 让用户从任意历史节点里瞎选，引擎会以「后继不存在」拒绝。
 * 白名单没覆盖时，退回用实例留痕里出现过的 from_activity 作为候选。
 */
export const RETURN_TARGETS = {
  PAPER_REVIEW_001: [{ activity_id: 'PR02', activity_name: '提交审核申请' }],
  REGISTRATION_001_T: [{ activity_id: 'RG02', activity_name: '提交注册申请' }]
}

export function returnTargets(flowCode, history = []) {
  if (flowCode && RETURN_TARGETS[flowCode]) return RETURN_TARGETS[flowCode]
  const seen = new Map()
  for (const h of history || []) {
    if (h.from_activity && !seen.has(h.from_activity)) {
      seen.set(h.from_activity, {
        activity_id: h.from_activity,
        activity_name: h.activity_name
      })
    }
  }
  return Array.from(seen.values())
}


/**
 * 逾期与超时相关的展示映射。
 *
 * **逾期是计算属性**：后端按 deadline 与当前时刻比较得出 is_overdue，
 * 前端不再自己算一次 —— 两处各算一次必然漂移（时区、格式、
 * 边界秒数都会让结果不一致），用户看到「列表说没逾期、
 * 详情说逾期」时完全无法理解。
 */

/** 逾期标识文案。 */
export const OVERDUE_LABELS = {
  overdue: { text: '已逾期', type: 'danger' },
  normal: { text: '正常', type: 'info' }
}

export function overdueText(isOverdue) {
  return isOverdue ? OVERDUE_LABELS.overdue.text : OVERDUE_LABELS.normal.text
}

export function overdueType(isOverdue) {
  return isOverdue ? OVERDUE_LABELS.overdue.type : OVERDUE_LABELS.normal.type
}

/**
 * 剩余时间文案。
 *
 * @param {string|null} deadline 形如 '2026-11-20 09:00:00' 的截止时间
 * @param {boolean} isOverdue 后端算出的逾期结论
 * @param {Date} now 可注入的当前时刻（测试用）
 * @returns {string} 如「剩 3 小时」「已逾期 2 天」
 */
export function remainingText(deadline, isOverdue, now = new Date()) {
  if (!deadline) return '无截止时间'
  const target = new Date(String(deadline).replace(/-/g, '/'))
  if (Number.isNaN(target.getTime())) return '无截止时间'

  const diffMs = target.getTime() - now.getTime()
  const diffMin = Math.floor(Math.abs(diffMs) / 60000)

  if (diffMin < 1) return isOverdue ? '刚刚逾期' : '即将到期'
  if (diffMin < 60) {
    return isOverdue ? `已逾期 ${diffMin} 分钟` : `剩 ${diffMin} 分钟`
  }
  const diffHour = Math.floor(diffMin / 60)
  if (diffHour < 24) {
    return isOverdue ? `已逾期 ${diffHour} 小时` : `剩 ${diffHour} 小时`
  }
  const diffDay = Math.floor(diffHour / 24)
  return isOverdue ? `已逾期 ${diffDay} 天` : `剩 ${diffDay} 天`
}

/**
 * 催办按钮是否可点。
 *
 * 后端有 30 分钟频次限制，前端同步禁用 —— 否则用户点了才收报错，
 * 体验上像是「按钮坏了」。这里用后端回的 last_urged_at 判断。
 *
 * @param {object} task 待办行
 * @param {Date} now 可注入的当前时刻
 */
export function urgeCooldownRemaining(task, now = new Date()) {
  if (!task || !task.last_urged_at) return 0
  const last = new Date(String(task.last_urged_at).replace(/-/g, '/'))
  if (Number.isNaN(last.getTime())) return 0
  const elapsedMin = (now.getTime() - last.getTime()) / 60000
  const remain = 30 - elapsedMin
  return remain > 0 ? Math.ceil(remain) : 0
}

/** 催办次数 / 转办次数的展示文案。 */
export function countText(n) {
  const num = Number(n || 0)
  return num > 0 ? String(num) : '-'
}
