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
 * 一个大题的分值小计。
 *
 * 有 `score_pattern`（同一大题内每题分值不同）时以序列之和为准。
 * 真实卷面大量存在这种结构：数学解答题 6/6/6/8/8/8/10/11/12、
 * 化学选择题 8 题×1 分 + 5 题×2 分、语文各板块小题 2~8 分不等。
 * 只算 `count * score_per` 会用平均值×题量，把梯度抹平且合计对不上。
 */
export function sectionScoreTotal(sec) {
  const pattern = Array.isArray(sec?.score_pattern) ? sec.score_pattern : null
  if (pattern && pattern.length) {
    return round2(pattern.reduce((sum, v) => sum + (Number(v) || 0), 0))
  }
  return round2((Number(sec?.count) || 0) * (Number(sec?.score_per) || 0))
}

/**
 * 大题分值的展示文案：均分时「10题×3分」，阶梯时「9题 6/6/6/8/8/8/10/11/12」。
 */
export function sectionScoreLabel(sec) {
  const pattern = Array.isArray(sec?.score_pattern) ? sec.score_pattern : null
  if (pattern && pattern.length) {
    return `${sec.count}题 ${pattern.join('/')}`
  }
  return `${sec?.count ?? 0}题×${sec?.score_per ?? 0}分`
}

function round2(v) {
  return Math.round((Number(v) || 0) * 100) / 100
}

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

/* ---------------- 组卷草稿（6.5 操作流程） ----------------
 * 目的：向导填了一半关掉/误退时，配置不丢。localStorage 只存「参数」，
 * 不存预览题目 —— 预览是后端内存态（无 paper_id），存了也没法还原。
 * 因此恢复时最多回到「设定参数」这一步（见 DRAFT_RESTORE_MAX_STEP）。 */

export const DRAFT_STORAGE_KEY = 'edu:paperWizardDraft'

/** 预览(2)/保存(3)步依赖内存态题目，草稿无法还原，恢复时封顶到参数步 */
export const DRAFT_RESTORE_MAX_STEP = 1

/** 保存草稿；localStorage 满/被禁时静默失败（草稿是锦上添花，不因它报错） */
export function saveDraft(form, step, savedAt) {
  try {
    localStorage.setItem(DRAFT_STORAGE_KEY, JSON.stringify({ form, step, savedAt }))
    return true
  } catch {
    return false
  }
}

/** 读取草稿；不存在或脏数据返回 null（绝不抛错——恢复流程不能炸页面） */
export function loadDraft() {
  try {
    const raw = localStorage.getItem(DRAFT_STORAGE_KEY)
    if (!raw) return null
    const draft = JSON.parse(raw)
    if (!draft || typeof draft.form !== 'object' || draft.form === null) return null
    if (!Array.isArray(draft.form.sections)) draft.form.sections = []
    if (typeof draft.step !== 'number') draft.step = 0
    return draft
  } catch {
    return null
  }
}

export function clearDraft() {
  try {
    localStorage.removeItem(DRAFT_STORAGE_KEY)
  } catch { /* 同上，静默 */ }
}

/** 草稿保存时间的相对文案：「刚刚 / 5 分钟前 / 3 小时前 / 2 天前 / 未知时间」 */
export function draftAgeText(savedAt, now = Date.now()) {
  const t = Number(savedAt)
  if (!t || Number.isNaN(t)) return '未知时间'
  const diff = Math.max(0, now - t)
  if (diff < 60000) return '刚刚'
  if (diff < 3600000) return `${Math.floor(diff / 60000)} 分钟前`
  if (diff < 86400000) return `${Math.floor(diff / 3600000)} 小时前`
  return `${Math.floor(diff / 86400000)} 天前`
}

/** 恢复确认弹窗用的一句话摘要 */
export function draftSummaryText(draft, now = Date.now()) {
  const modeText = draft?.form?.mode === 'ai' ? 'AI 一键' : '自定义'
  return `${draftAgeText(draft?.savedAt, now)}保存 · ${modeText}模式`
}
