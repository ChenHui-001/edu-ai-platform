/**
 * 知识图谱 ECharts option 构造。
 *
 * 抽成纯函数是为了能单测：视图只负责取数与交互，配色/连线/高亮规则
 * 全在这里，避免"图谱看着对、其实把硬先修画成虚线"这类肉眼难查的问题。
 */

export const HIERARCHY_COLOR = '#c0c4cc'
export const HARD_COLOR = '#f56c6c'
export const SOFT_COLOR = '#909399'
export const CONTAINER_COLOR = '#b1b3b8'

const MASTERY_COLORS = [
  [80, '#67c23a'],
  [60, '#e6a23c'],
  [0, '#f56c6c'],
]

const DIFFICULTY_COLORS = {
  easy: '#67c23a',
  medium: '#409eff',
  hard: '#e6a23c',
  challenge: '#f56c6c'
}

export function isContainer(node) {
  return Number(node?.child_count || 0) > 0
}

export function masteryColor(value) {
  if (value === null || value === undefined) return '#c0c4cc'
  const score = Number(value)
  for (const [threshold, color] of MASTERY_COLORS) {
    if (score >= threshold) return color
  }
  return '#c0c4cc'
}

export function difficultyColor(level) {
  return DIFFICULTY_COLORS[level] || '#909399'
}

export function nodeColor(node, { useMastery = false } = {}) {
  if (isContainer(node)) return CONTAINER_COLOR
  // 学生视角优先按掌握度着色；还没练过的知识点回落到难度色，
  // 否则整张图会是一片灰，看不出哪里难、哪里该先学。
  if (useMastery && node?.mastery !== null && node?.mastery !== undefined) {
    return masteryColor(node.mastery)
  }
  return difficultyColor(node?.difficulty)
}

export function neighborIds(edges, id) {
  const hit = new Set()
  if (id === null || id === undefined) return hit
  const target = Number(id)
  for (const edge of edges || []) {
    if (Number(edge.source) === target) hit.add(Number(edge.target))
    if (Number(edge.target) === target) hit.add(Number(edge.source))
  }
  return hit
}

export function truncateLabel(name, max = 14) {
  const text = String(name ?? '')
  return text.length > max ? `${text.slice(0, max - 1)}…` : text
}

function linkStyle(edge) {
  if (edge.kind === 'hierarchy') {
    return { color: HIERARCHY_COLOR, type: 'dashed', width: 1 }
  }
  if (edge.strength === 'soft') {
    return { color: SOFT_COLOR, type: 'dashed', width: 1.2 }
  }
  return { color: HARD_COLOR, type: 'solid', width: 1.8 }
}

/**
 * @param {object} params
 * @param {Array} params.nodes 后端节点（id/name/difficulty/question_count/mastery/child_count）
 * @param {Array} params.edges 后端边（source/target/kind/strength）
 * @param {number|null} params.selectedId 选中节点：高亮邻居、淡化其余节点
 * @param {boolean} params.useMastery 学生视角按掌握度着色
 * @param {boolean} params.showHierarchy 是否使用层级边
 */
export function buildGraphOption({
  nodes = [],
  edges = [],
  selectedId = null,
  useMastery = false,
  showHierarchy = true
} = {}) {
  const visibleEdges = showHierarchy
    ? edges
    : edges.filter(edge => edge.kind !== 'hierarchy')
  const focus = neighborIds(visibleEdges, selectedId)
  const hasFocus = selectedId !== null && selectedId !== undefined
  // 节点一多，标签会糊成一片：超过阈值只保留悬停/选中时的高亮标签。
  const showLabels = nodes.length <= 80
  const repulsion = Math.min(900, 220 + nodes.length * 7)

  const data = nodes.map(node => {
    const id = Number(node.id)
    const dimmed = hasFocus && id !== Number(selectedId) && !focus.has(id)
    const size = isContainer(node)
      ? 26
      : 14 + Math.min(Number(node.question_count || 0), 8)
    return {
      id: String(id),
      name: node.name,
      shortName: truncateLabel(node.name),
      category: isContainer(node) ? 0 : 1,
      symbolSize: size,
      value: Number(node.question_count || 0),
      raw: node,
      itemStyle: {
        color: nodeColor(node, { useMastery }),
        opacity: dimmed ? 0.2 : 1,
        borderColor: id === Number(selectedId) ? '#303133' : 'transparent',
        borderWidth: id === Number(selectedId) ? 2 : 0
      },
      label: { opacity: dimmed ? 0.15 : 1 }
    }
  })

  const links = visibleEdges.map(edge => {
    const style = linkStyle(edge)
    const dimmed = hasFocus
      && Number(edge.source) !== Number(selectedId)
      && Number(edge.target) !== Number(selectedId)
    return {
      source: String(edge.source),
      target: String(edge.target),
      kind: edge.kind,
      lineStyle: { ...style, opacity: dimmed ? 0.12 : 0.85 }
    }
  })

  return {
    tooltip: {
      confine: true,
      formatter: params => {
        if (params.dataType === 'edge') {
          if (params.data.kind === 'hierarchy') return '教材层级'
          const strength = params.data.lineStyle?.color === HARD_COLOR ? '硬先修' : '软先修'
          return `先修关系（${strength}）`
        }
        const node = params.data.raw || {}
        const lines = [`<b>${node.name || ''}</b>`]
        if (node.grade_name) lines.push(`年级：${node.grade_name}`)
        if (node.difficulty) lines.push(`难度：${node.difficulty}`)
        lines.push(`题目：${node.question_count || 0} 道`)
        if (node.mastery !== null && node.mastery !== undefined) {
          lines.push(`掌握度：${node.mastery}`)
        }
        return lines.join('<br/>')
      }
    },
    legend: [{
      bottom: 6,
      data: ['单元 / 章节', '知识点'],
      textStyle: { fontSize: 11 }
    }],
    series: [{
      type: 'graph',
      layout: 'force',
      roam: true,
      draggable: true,
      animationDuration: 600,
      force: {
        repulsion,
        edgeLength: [80, 170],
        gravity: 0.05,
        friction: 0.2,
        layoutAnimation: true
      },
      categories: [{ name: '单元 / 章节' }, { name: '知识点' }],
      label: {
        show: showLabels,
        position: 'right',
        fontSize: 11,
        color: '#303133',
        formatter: params => params.data.shortName || params.name
      },
      emphasis: {
        focus: 'adjacency',
        label: { show: true },
        lineStyle: { width: 3 }
      },
      edgeSymbol: ['none', 'arrow'],
      edgeSymbolSize: [0, 6],
      lineStyle: { curveness: 0.06 },
      data,
      links
    }]
  }
}

/** 诊断结果页：把「建议学习顺序」画成迷你图谱。 */
export function buildPathOption(path = [], pathLinks = []) {
  const statusColor = {
    mastered: '#67c23a',
    shaky: '#e6a23c',
    weak: '#f56c6c',
    unknown: '#909399'
  }
  const nodes = path.map(item => ({
    id: String(item.id),
    name: item.name,
    label: truncateLabel(item.name, 12),
    category: 0,
    symbolSize: 18,
    raw: item,
    itemStyle: {
      color: statusColor[item.status] || '#909399',
      borderColor: item.is_root ? '#f56c6c' : 'transparent',
      borderWidth: item.is_root ? 2 : 0
    }
  }))
  const index = new Map(path.map((item, pos) => [Number(item.id), pos]))
  const links = (pathLinks || [])
    .filter(link => index.has(Number(link.source)) && index.has(Number(link.target)))
    .map(link => ({
      source: String(link.source),
      target: String(link.target),
      lineStyle: link.strength === 'soft'
        ? { color: SOFT_COLOR, type: 'dashed', width: 1.2 }
        : { color: HARD_COLOR, type: 'solid', width: 1.8 }
    }))

  return {
    tooltip: { confine: true },
    series: [{
      type: 'graph',
      layout: 'force',
      roam: true,
      draggable: true,
      force: { repulsion: 160, edgeLength: [60, 110], gravity: 0.1 },
      categories: [{ name: '知识点' }],
      label: { show: true, position: 'right', fontSize: 11 },
      edgeSymbol: ['none', 'arrow'],
      edgeSymbolSize: [0, 6],
      data: nodes,
      links
    }]
  }
}
