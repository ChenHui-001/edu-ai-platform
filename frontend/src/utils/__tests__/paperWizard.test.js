import { describe, it, expect } from 'vitest'
import {
  composeBlockReason, requiresGradeSubject, buildComposePayload,
  isComposeButtonDisabled, AI_MODE_SOURCE,
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
