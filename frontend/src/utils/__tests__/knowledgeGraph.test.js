import { describe, expect, it } from 'vitest'

import {
  HARD_COLOR,
  HIERARCHY_COLOR,
  SOFT_COLOR,
  buildGraphOption,
  buildPathOption,
  masteryColor,
  neighborIds,
  nodeColor,
  truncateLabel
} from '../knowledgeGraph'

const nodes = [
  { id: 1, name: '第一单元', level: 1, child_count: 2, question_count: 0 },
  { id: 2, name: '20以内数的认识', level: 2, child_count: 0, difficulty: 'easy', question_count: 4, mastery: 45 },
  { id: 3, name: '凑十法', level: 2, child_count: 0, difficulty: 'hard', question_count: 6, mastery: 92 }
]

const edges = [
  { source: 1, target: 2, kind: 'hierarchy' },
  { source: 2, target: 3, kind: 'prereq', strength: 'hard' },
  { source: 1, target: 3, kind: 'prereq', strength: 'soft' }
]

describe('nodeColor', () => {
  it('容器节点统一灰色，不参与掌握度着色', () => {
    expect(nodeColor(nodes[0], { useMastery: true })).not.toBe(masteryColor(45))
  })

  it('学生视角按掌握度着色，未学过回落灰色', () => {
    expect(nodeColor(nodes[1], { useMastery: true })).toBe(masteryColor(45))
    expect(masteryColor(null)).toBe('#c0c4cc')
  })

  it('非学生视角按难度着色', () => {
    expect(nodeColor(nodes[2], { useMastery: false })).toBe('#e6a23c')
  })

  it('学生还没练过的知识点回落到难度色，避免整图一片灰', () => {
    expect(nodeColor({ difficulty: 'hard', mastery: null }, { useMastery: true }))
      .toBe('#e6a23c')
  })
})

describe('neighborIds', () => {
  it('返回直接相连的节点（双向）', () => {
    expect([...neighborIds(edges, 2)].sort()).toEqual([1, 3])
  })

  it('空入参不抛错', () => {
    expect(neighborIds(null, 1).size).toBe(0)
    expect(neighborIds(edges, null).size).toBe(0)
  })
})

describe('buildGraphOption', () => {
  it('硬先修实线红色、软先修虚线、层级边虚线且可关闭', () => {
    const option = buildGraphOption({ nodes, edges })
    const links = option.series[0].links
    const hard = links.find(link => link.kind === 'prereq' && link.lineStyle.color === HARD_COLOR)
    const soft = links.find(link => link.lineStyle.color === SOFT_COLOR)
    const hierarchy = links.find(link => link.kind === 'hierarchy')
    expect(hard.lineStyle.type).toBe('solid')
    expect(soft.lineStyle.type).toBe('dashed')
    expect(hierarchy.lineStyle.color).toBe(HIERARCHY_COLOR)

    const withoutHierarchy = buildGraphOption({ nodes, edges, showHierarchy: false })
    expect(withoutHierarchy.series[0].links.some(link => link.kind === 'hierarchy')).toBe(false)
  })

  it('选中节点时邻居保持不透明、其余节点淡化', () => {
    const option = buildGraphOption({ nodes, edges, selectedId: 2 })
    const data = option.series[0].data
    const byId = Object.fromEntries(data.map(item => [item.name, item]))
    expect(byId['20以内数的认识'].itemStyle.opacity).toBe(1)
    expect(byId['凑十法'].itemStyle.opacity).toBe(1)
    expect(byId['第一单元'].itemStyle.opacity).toBe(1)

    const isolated = buildGraphOption({
      nodes: [...nodes, { id: 9, name: '孤立节点', level: 2, child_count: 0 }],
      edges,
      selectedId: 2
    })
    const lonely = isolated.series[0].data.find(item => item.name === '孤立节点')
    expect(lonely.itemStyle.opacity).toBeLessThan(1)
  })

  it('节点尺寸随题量增长但有上限，标签会截断', () => {
    const option = buildGraphOption({ nodes, edges })
    const [container, leaf] = option.series[0].data
    expect(container.symbolSize).toBe(26)
    expect(leaf.symbolSize).toBe(14 + 4)
    expect(truncateLabel('一'.repeat(30)).endsWith('…')).toBe(true)
  })

  it('节点过多时隐藏标签、悬停再显示', () => {
    const many = Array.from({ length: 81 }, (_, idx) => ({
      id: idx + 1, name: `节点${idx + 1}`, child_count: 0
    }))
    const option = buildGraphOption({ nodes: many, edges: [] })
    expect(option.series[0].label.show).toBe(false)
    expect(option.series[0].emphasis.label.show).toBe(true)
  })
})

describe('buildPathOption', () => {
  const path = [
    { id: 11, name: '10以内加减法', status: 'weak', is_root: true },
    { id: 12, name: '20以内进位加法', status: 'unknown' }
  ]
  const links = [
    { source: 11, target: 12, strength: 'hard' },
    { source: 11, target: 999, strength: 'hard' }
  ]

  it('只保留两端都在路径内的连边，根因节点描边', () => {
    const option = buildPathOption(path, links)
    expect(option.series[0].links).toHaveLength(1)
    expect(option.series[0].data[0].itemStyle.borderWidth).toBe(2)
    expect(option.series[0].data[1].itemStyle.color).toBe('#909399')
  })

  it('空路径返回空图而不抛错', () => {
    const option = buildPathOption()
    expect(option.series[0].data).toEqual([])
    expect(option.series[0].links).toEqual([])
  })
})
