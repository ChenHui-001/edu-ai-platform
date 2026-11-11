import { describe, it, expect } from 'vitest'
import {
  composeBlockReason, requiresGradeSubject, buildComposePayload,
  isComposeButtonDisabled, sectionScoreTotal, sectionScoreLabel, AI_MODE_SOURCE,
  saveDraft, loadDraft, clearDraft, draftAgeText, draftSummaryText,
  DRAFT_STORAGE_KEY, DRAFT_RESTORE_MAX_STEP,
} from '../paperWizard'

/**
 * 回归锁：AI 一键组卷按钮曾恒为灰色。
 *
 * 根因是 canCompose 先判 `grade_id && subject_id`，而 AI 模式用户往往只写了一句
 * 需求描述 —— 按钮就永远点不动。后端 `/compose/ai` 明明支持从描述里解析年级学科
 * （解析失败才报「无法从描述中识别年级或学科」），被前端提前拦死了。
 */
describe('composeBlockReason（组卷按钮可用性）', () => {
  it('AI 模式：只填描述即可提交，不要求手选年级/学科', () => {
    expect(composeBlockReason({
      mode: 'ai', request: '出一份七年级数学期末卷', gradeId: null, subjectId: null,
    })).toBe('')
  })

  it('AI 模式：描述为空时给出可操作原因（两条合法路径都没满足）', () => {
    expect(composeBlockReason({ mode: 'ai', request: '   ' }))
      .toBe('请填写组卷需求描述，或选择年级与学科')
  })

  it('AI 模式：不写描述、只选年级+学科也能提交（按命题标准出结构）', () => {
    // 用户明确反馈：选好年级科目就该能出卷，不该被迫写一段自然语言
    expect(composeBlockReason({ mode: 'ai', request: '', gradeId: 7, subjectId: 34 }))
      .toBe('')
  })

  it('AI 模式：只选了年级但没学科、也没描述 → 仍提示补齐', () => {
    expect(composeBlockReason({ mode: 'ai', request: '', gradeId: 7 }))
      .toBe('请填写组卷需求描述，或选择年级与学科')
  })

  it('AI 模式：描述有内容但年级/学科都为空，仍然可以提交', () => {
    expect(composeBlockReason({ mode: 'ai', request: '八年级物理单元测' })).toBe('')
  })

  it('自定义模式：缺年级 → 提示选年级', () => {
    expect(composeBlockReason({ mode: 'custom', subjectId: 2, hasSections: true }))
      .toBe('请选择年级')
  })

  it('自定义模式：缺学科 → 提示选学科', () => {
    expect(composeBlockReason({ mode: 'custom', gradeId: 1, hasSections: true }))
      .toBe('请选择学科')
  })

  it('自定义模式：没有大题 → 提示配置大题', () => {
    expect(composeBlockReason({
      mode: 'custom', gradeId: 1, subjectId: 2, hasSections: false,
    })).toBe('请至少配置一个大题')
  })

  it('自定义模式：条件齐备 → 可提交', () => {
    expect(composeBlockReason({
      mode: 'custom', gradeId: 1, subjectId: 2, hasSections: true,
    })).toBe('')
  })
})

describe('isComposeButtonDisabled（按钮是否置灰）', () => {
  it('AI 模式永不置灰：缺描述也要可点，点了再提示', () => {
    // 用户两次把"灰色按钮"直接当成"功能坏了"，AI 模式只有描述一个缺项，
    // 点击后给 toast + 聚焦输入框，比静默置灰可诊断。
    expect(isComposeButtonDisabled({ mode: 'ai', reason: '请先填写组卷需求描述' }))
      .toBe(false)
  })

  it('AI 模式描述齐全时当然可点', () => {
    expect(isComposeButtonDisabled({ mode: 'ai', reason: '' })).toBe(false)
  })

  it('自定义模式缺项时置灰', () => {
    expect(isComposeButtonDisabled({ mode: 'custom', reason: '请选择年级' })).toBe(true)
  })

  it('自定义模式条件齐备时可点', () => {
    expect(isComposeButtonDisabled({ mode: 'custom', reason: '' })).toBe(false)
  })
})

describe('requiresGradeSubject（必填星号）', () => {
  it('AI 模式下年级/学科非必填', () => {
    expect(requiresGradeSubject('ai')).toBe(false)
  })
  it('自定义模式下年级/学科必填', () => {
    expect(requiresGradeSubject('custom')).toBe(true)
  })
})

describe('buildComposePayload（提交参数）', () => {
  const base = {
    mode: 'ai', request: '七年级数学期末卷', grade_id: null, subject_id: null,
    standard_id: null, total_score: 100, duration: 90, source: 'bank_first',
    difficulty_ratio: { easy: 70, medium: 20, hard: 10 },
    avoid_recent: true, avoid_duplicate_kp: true,
  }

  it('AI 模式不发送 difficulty_ratio（否则会覆盖 AI 解析出的难度）', () => {
    const p = buildComposePayload(base, { sections: [{ code: 'single', count: 5 }] })
    expect(p.difficulty_ratio).toBeUndefined()
    expect(p.sections).toBeUndefined()
  })

  it('自定义模式正常携带 difficulty_ratio 与 sections', () => {
    const sections = [{ code: 'single', count: 5, score_per: 2 }]
    const p = buildComposePayload({ ...base, mode: 'custom' }, { sections })
    expect(p.difficulty_ratio).toEqual({ easy: 70, medium: 20, hard: 10 })
    expect(p.sections).toBe(sections)
  })

  it('年级/学科留 null 传给后端，由后端决定是否用 AI 解析值填充', () => {
    const p = buildComposePayload(base)
    expect(p.grade_id).toBeNull()
    expect(p.subject_id).toBeNull()
  })

  it('知识点 id 透传', () => {
    const p = buildComposePayload(base, { knowledgePointIds: [11, 12] })
    expect(p.knowledge_point_ids).toEqual([11, 12])
  })

  /**
   * 回归锁：AI 模式的「出题来源」下拉此前是可选的，用户可以在 AI 一键组卷里
   * 选「仅使用 AI 生成」—— 同一请求里就叠加了两轮模型调用（解析 + 逐大题造题），
   * 耗时随大题数线性增长，题库里有同题型的题也不用。现在 UI 禁用该下拉，
   * 且 payload 侧强制归位，避免"界面禁用但残留值仍被发送"的漏网。
   */
  it('AI 模式固定发送 bank_first，即使表单残留 ai_only', () => {
    const p = buildComposePayload({ ...base, mode: 'ai', source: 'ai_only' })
    expect(p.source).toBe(AI_MODE_SOURCE)
    expect(p.source).toBe('bank_first')
  })

  it('AI 模式残留 bank_only 同样被归位（不能靠"只在选 ai_only 时才改"）', () => {
    const p = buildComposePayload({ ...base, mode: 'ai', source: 'bank_only' })
    expect(p.source).toBe('bank_first')
  })

  it('自定义模式原样透传来源（含 ai_only，纯 AI 造题仍可用）', () => {
    const p = buildComposePayload(
      { ...base, mode: 'custom', source: 'ai_only' }, { sections: [] })
    expect(p.source).toBe('ai_only')
  })
})

/**
 * 阶梯分值：真实卷面同一大题内每题分值不同。
 *
 * 数学解答题 6/6/6/8/8/8/10/11/12（合计 75）、化学选择题 8 题×1 分 +
 * 5 题×2 分（合计 18）。若只按 `count * score_per` 算小计，会用平均值×题量，
 * 与规则合计对不上（9×8.33=74.97 ≠ 75），卷面总分校验随之误报。
 */
describe('sectionScoreTotal（大题小计）', () => {
  it('均分结构用 count × score_per', () => {
    expect(sectionScoreTotal({ count: 10, score_per: 3 })).toBe(30)
  })

  it('阶梯结构以分值序列之和为准', () => {
    expect(sectionScoreTotal({
      count: 9, score_per: 8.33,
      score_pattern: [6, 6, 6, 8, 8, 8, 10, 11, 12],
    })).toBe(75)
  })

  it('化学选择分段计分 8×1 + 5×2 = 18', () => {
    expect(sectionScoreTotal({
      count: 13, score_per: 1.38,
      score_pattern: [1, 1, 1, 1, 1, 1, 1, 1, 2, 2, 2, 2, 2],
    })).toBe(18)
  })

  it('空/缺字段不抛异常（试卷还在编辑中）', () => {
    expect(sectionScoreTotal({})).toBe(0)
    expect(sectionScoreTotal(null)).toBe(0)
    expect(sectionScoreTotal({ count: 5 })).toBe(0)
  })

  it('分值序列为空数组时退回均分（不能算出 0 分）', () => {
    expect(sectionScoreTotal({ count: 5, score_per: 2, score_pattern: [] })).toBe(10)
  })
})

describe('sectionScoreLabel（大题结构文案）', () => {
  it('均分显示「N题×M分」', () => {
    expect(sectionScoreLabel({ count: 10, score_per: 3 })).toBe('10题×3分')
  })

  it('阶梯显示完整分值序列，便于教师核对卷面', () => {
    expect(sectionScoreLabel({
      count: 3, score_per: 7, score_pattern: [6, 7, 8],
    })).toBe('3题 6/7/8')
  })
})


/* ---------------- 组卷草稿（6.5 操作流程） ---------------- */
describe('组卷草稿', () => {
  it('save/load 往返保留 form、step 与 savedAt', () => {
    localStorage.clear()
    const form = { mode: 'custom', grade_id: 7, sections: [{ type: 'single', count: 5 }] }
    expect(saveDraft(form, 1, 1000)).toBe(true)
    const d = loadDraft()
    expect(d.form.grade_id).toBe(7)
    expect(d.form.sections).toHaveLength(1)
    expect(d.step).toBe(1)
    expect(d.savedAt).toBe(1000)
    clearDraft()
    expect(localStorage.getItem(DRAFT_STORAGE_KEY)).toBeNull()
  })

  it('脏 JSON 与缺失字段不抛错：返回 null 或补全默认值', () => {
    localStorage.setItem(DRAFT_STORAGE_KEY, '{broken json')
    expect(loadDraft()).toBeNull()
    localStorage.setItem(DRAFT_STORAGE_KEY, JSON.stringify({ form: { grade_id: 7 } }))
    const d = loadDraft()
    expect(d.form.sections).toEqual([])
    expect(d.step).toBe(0)
    clearDraft()
  })

  it('form 缺失或非对象的草稿视为无效', () => {
    localStorage.setItem(DRAFT_STORAGE_KEY, JSON.stringify({ step: 2 }))
    expect(loadDraft()).toBeNull()
    localStorage.setItem(DRAFT_STORAGE_KEY, JSON.stringify({ form: 'oops' }))
    expect(loadDraft()).toBeNull()
    clearDraft()
  })

  it('恢复步骤封顶到参数步：预览/保存步的题目在内存里还原不了', () => {
    expect(DRAFT_RESTORE_MAX_STEP).toBe(1)
  })

  it('draftAgeText 相对时间分档', () => {
    const now = 1000000
    expect(draftAgeText(now - 30, now)).toBe('刚刚')
    expect(draftAgeText(now - 5 * 60000, now)).toBe('5 分钟前')
    expect(draftAgeText(now - 3 * 3600000, now)).toBe('3 小时前')
    expect(draftAgeText(now - 2 * 86400000, now)).toBe('2 天前')
    expect(draftAgeText(null, now)).toBe('未知时间')
    expect(draftAgeText('abc', now)).toBe('未知时间')
  })

  it('draftSummaryText 带模式与保存时间', () => {
    const now = 1000000
    expect(draftSummaryText({ form: { mode: 'ai' }, savedAt: now - 120000 }, now))
      .toBe('2 分钟前保存 · AI 一键模式')
    expect(draftSummaryText({ form: { mode: 'custom' }, savedAt: now }, now))
      .toBe('刚刚保存 · 自定义模式')
  })
})
