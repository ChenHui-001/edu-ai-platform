/**
 * 标准组卷向导的提交前置校验（纯函数，便于单测与复用）。
 *
 * 独立成模块的原因：这段判定直接决定「AI 一键组卷 / 生成试卷预览」按钮是否可点，
 * 曾经因为把「必须手选年级+学科」写死成硬门槛，导致 AI 模式下按钮恒灰 ——
 * 而后端 `/question/papers/compose/ai` 本来就能用大模型从自然语言里推断年级与学科。
 * 逻辑放在 SFC 里只能靠点页面才发现回归，抽出来就能用 vitest 锁死。
 */

/**
 * 返回按钮禁用原因；空字符串表示可以提交。
 *
 * @param {{ mode: 'custom'|'ai', request?: string,
 *           gradeId?: number|null, subjectId?: number|null,
 *           hasSections?: boolean }} input
 * @returns {string}
 */
export function composeBlockReason({ mode, request = '', gradeId = null,
                                    subjectId = null, hasSections = false } = {}) {
  if (mode === 'ai') {
    // AI 模式只要求「有描述」：年级/学科留空时由后端解析，
    // 解析不出来会返回「无法从描述中识别年级或学科」，比前端拦死更有指导性。
    return String(request || '').trim() ? '' : '请先填写组卷需求描述'
  }
  if (!gradeId) return '请选择年级'
  if (!subjectId) return '请选择学科'
  if (!hasSections) return '请至少配置一个大题'
  return ''
}

/**
 * 是否会命中「必须手选年级/学科」的硬门槛（仅自定义模式为真）。
 * 模板里用它决定表单标签是否显示必填星号。
 */
export function requiresGradeSubject(mode) {
  return mode !== 'ai'
}

/**
 * 组装组卷请求参数。
 *
 * AI 模式下**不发送** `difficulty_ratio`：界面上的难度滑块此时是禁用的，
 * 一旦发送固定 70/20/10，后端 `/compose/ai` 的「客户端给了就不覆盖」合并逻辑
 * 会把 AI 从描述里解析出的难度顶掉，而用户又改不动滑块 —— 难度既不随描述也不随用户。
 */
export function buildComposePayload(form, { sections, knowledgePointIds = [] } = {}) {
  const isAi = form.mode === 'ai'
  return {
    grade_id: form.grade_id,
    subject_id: form.subject_id,
    standard_id: form.standard_id,
    sections: isAi ? undefined : sections,
    total_score: form.total_score,
    duration: form.duration,
    source: form.source,
    difficulty_ratio: isAi ? undefined : form.difficulty_ratio,
    knowledge_point_ids: knowledgePointIds,
    avoid_recent: form.avoid_recent,
    avoid_duplicate_kp: form.avoid_duplicate_kp,
  }
}
