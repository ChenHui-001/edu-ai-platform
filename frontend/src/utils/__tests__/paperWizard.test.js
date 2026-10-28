import { describe, it, expect } from 'vitest'
import {
  composeBlockReason, requiresGradeSubject, buildComposePayload
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

  it('AI 模式：描述为空时给出可操作原因', () => {
    expect(composeBlockReason({ mode: 'ai', request: '   ' })).toBe('请先填写组卷需求描述')
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
})
