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
    // AI 模式两条合法路径：
    //   1) 写了描述 → 后端用大模型把描述翻译成年级/学科/难度等参数
    //   2) 没写描述但选了年级+学科 → 直接按命题标准出结构（等价规则组卷）
    // 强制写一段自然语言属于无谓门槛：用户明确反馈"选好年级科目就该能出卷"。
    if (String(request || '').trim()) return ''
    if (gradeId && subjectId) return ''
    return '请填写组卷需求描述，或选择年级与学科'
  }
  if (!gradeId) return '请选择年级'
  if (!subjectId) return '请选择学科'
  if (!hasSections) return '请至少配置一个大题'
  return ''
}

/**
 * 按钮是否应置灰。
 *
 * **AI 模式不置灰**：用户已经两次把"灰色按钮"直接判定为"功能坏了"（且分不清是
 * 自己没填描述还是真故障）。AI 模式的缺项只有「描述」一个，且就在按钮上方一眼可见，
 * 让按钮保持可点、点击时给出明确提示（并聚焦输入框）比静默置灰可诊断得多。
 * 自定义模式有多个必填项分散在表单里，置灰 + 旁边写明缺什么更合适。
 */
export function isComposeButtonDisabled({ mode, reason } = {}) {
  if (mode === 'ai') return false
  return Boolean(reason)
}

/**
 * 是否会命中「必须手选年级/学科」的硬门槛（仅自定义模式为真）。
 * 模板里用它决定表单标签是否显示必填星号。
 */
export function requiresGradeSubject(mode) {
  return mode !== 'ai'
}

/**
 * AI 模式下「出题来源」的固定取值。
 *
 * AI 一键组卷的语义是**让模型把自然语言翻译成结构化参数，再交给确定性引擎
 * 从题库抽题**。若允许在这里选「仅使用 AI 生成」，同一请求里就出现了两轮
 * 模型调用（解析 + 逐大题造题），耗时随大题数线性增长，且题库里明明有同题型
 * 的题也不会用 —— 用户看到的现象是"选了 AI 组卷，等很久还缺题"。
 * 因此 AI 模式锁定为「题库优先 + AI 补充」，需要纯 AI 造题时走自定义模式。
 */
export const AI_MODE_SOURCE = 'bank_first'

/**
 * 组装组卷请求参数。
 *
 * AI 模式下**不发送** `difficulty_ratio`：界面上的难度滑块此时是禁用的，
 * 一旦发送固定 70/20/10，后端 `/compose/ai` 的「客户端给了就不覆盖」合并逻辑
 * 会把 AI 从描述里解析出的难度顶掉，而用户又改不动滑块 —— 难度既不随描述也不随用户。
 *
 * 同理，AI 模式固定发送 `AI_MODE_SOURCE`：界面上的来源下拉在 AI 模式已禁用，
 * 但用户可能先在自定义模式选了 `ai_only` 再切回来，若原样发送就会绕过禁用。
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
    source: isAi ? AI_MODE_SOURCE : form.source,
    difficulty_ratio: isAi ? undefined : form.difficulty_ratio,
    knowledge_point_ids: knowledgePointIds,
    avoid_recent: form.avoid_recent,
    avoid_duplicate_kp: form.avoid_duplicate_kp,
  }
}
