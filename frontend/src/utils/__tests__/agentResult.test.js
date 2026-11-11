import { describe, expect, it } from 'vitest'

import { hasNoOutput } from '../agentResult'

/**
 * 守 reaudit P1-2：后端如实返回 0 条，前端却弹"生成完成"。
 * 三个能力的载荷键不同，缺一个就会漏判。
 */
describe('hasNoOutput', () => {
  it('出题返回空 questions → 空产出', () => {
    expect(hasNoOutput({ questions: [], total: 0, saved: 0 })).toBe(true)
  })

  it('出题返回有内容 → 有产出', () => {
    expect(hasNoOutput({ questions: [{ id: 1 }], total: 1 })).toBe(false)
  })

  it('补题 / 变式空 items → 空产出', () => {
    expect(hasNoOutput({ items: [], filled: 0 })).toBe(true)
  })

  it('补题 / 变式有 items → 有产出', () => {
    expect(hasNoOutput({ items: [{ stem: 'x' }] })).toBe(false)
  })

  it('组卷预览态（无 id 有 items）按 items 判', () => {
    expect(hasNoOutput({ paper: { items: [] } })).toBe(true)
    expect(hasNoOutput({ paper: { items: [{ question_id: 1 }] } })).toBe(false)
  })

  it('组卷保存态（有 id 无 items）按 id 判', () => {
    expect(hasNoOutput({ paper: { id: 9 } })).toBe(false)
    expect(hasNoOutput({ paper: {} })).toBe(true)
  })

  it('paper 键存在但内容为空 → 空产出（哪怕还带了 report）', () => {
    expect(hasNoOutput({ paper: null, report: { distribution: {} } })).toBe(true)
  })

  it('载荷键存在但不是数组（残缺结构）→ 按空产出处理', () => {
    expect(hasNoOutput({ items: null })).toBe(true)
    expect(hasNoOutput({ questions: 'oops' })).toBe(true)
    expect(hasNoOutput({ questions: { 0: { id: 1 } } })).toBe(true)
  })

  it('非对象一律算空产出', () => {
    expect(hasNoOutput(null)).toBe(true)
    expect(hasNoOutput(undefined)).toBe(true)
    expect(hasNoOutput('')).toBe(true)
    expect(hasNoOutput([])).toBe(true)
  })

  it('空对象算空产出', () => {
    expect(hasNoOutput({})).toBe(true)
  })

  it('is_fallback 是标记键不是产出：单独存在仍算空产出（2026-11-11 回归）', () => {
    // 后端降级时把 is_fallback 合进 data，不能因此把空结果判成"有产出"
    expect(hasNoOutput({ is_fallback: true })).toBe(true)
    expect(hasNoOutput({ is_fallback: false })).toBe(true)
    expect(hasNoOutput({ is_fallback: true, questions: [{ stem: 'x' }] })).toBe(false)
  })
})
