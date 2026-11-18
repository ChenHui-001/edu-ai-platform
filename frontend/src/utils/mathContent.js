import katex from 'katex'
import { sanitizeHtml } from './sanitize'

export function renderMathContent(raw) {
  const parsed = new DOMParser().parseFromString(sanitizeHtml(String(raw ?? '')), 'text/html')
  const walker = parsed.createTreeWalker(parsed.body, 4)
  const nodes = []
  while (walker.nextNode()) nodes.push(walker.currentNode)
  const pattern = /\$\$([\s\S]+?)\$\$|\\\[([\s\S]+?)\\\]|\\\(([\s\S]+?)\\\)|\$([^$\n]+?)\$/g
  for (const node of nodes) {
    if (node.parentElement?.closest('pre,code')) continue
    const matches = [...node.textContent.matchAll(pattern)]
    if (!matches.length) continue
    const fragment = parsed.createDocumentFragment()
    let position = 0
    for (const match of matches) {
      fragment.append(parsed.createTextNode(node.textContent.slice(position, match.index)))
      const span = parsed.createElement('span')
      span.innerHTML = katex.renderToString(match[1] || match[2] || match[3] || match[4], {
        throwOnError: false, trust: false, strict: 'warn', maxExpand: 100,
        output: 'html', displayMode: Boolean(match[1] || match[2])
      })
      fragment.append(span)
      position = match.index + match[0].length
    }
    fragment.append(parsed.createTextNode(node.textContent.slice(position)))
    node.replaceWith(fragment)
  }
  return parsed.body.innerHTML
}

export function parseVisual(question) {
  try {
    const extra = typeof question.extra_json === 'string'
      ? JSON.parse(question.extra_json) : (question.extra_json || {})
    const value = question.visual || extra.visual
    if (!value || !['number_line', 'fraction', 'polygon'].includes(value.kind)) return null
    const points = value.points || []
    if (!Array.isArray(points) || points.length > 20) return null
    const finite = number => typeof number === 'number' && Number.isFinite(number)
    if (value.kind === 'number_line') {
      if (!finite(value.min) || !finite(value.max) || value.min < -1000 ||
          value.max > 1000 || value.max - value.min < 0.001 ||
          points.some(point => !finite(point.value) || point.value < value.min || point.value > value.max)) return null
    } else if (value.kind === 'fraction') {
      if (!Number.isInteger(value.numerator) || !Number.isInteger(value.denominator) ||
          value.numerator < 0 || value.denominator < 1 || value.denominator > 20 ||
          value.numerator > value.denominator) return null
    } else if (points.length < 3 || points.some(point => !finite(point.x) || !finite(point.y) ||
        point.x < 0 || point.x > 400 || point.y < 0 || point.y > 240)) return null
    return value
  } catch {
    return null
  }
}

export function renderQuestionFigure(raw) {
  if (typeof raw !== 'string' || raw.length > 100000) return ''
  const parsed = new DOMParser().parseFromString(raw, 'image/svg+xml')
  const root = parsed.documentElement
  if (root.localName !== 'svg' || parsed.querySelector('parsererror')) return ''
  const tags = new Set(['svg', 'g', 'line', 'path', 'polygon', 'polyline', 'circle', 'ellipse', 'rect', 'text', 'tspan'])
  const attrs = new Set(['viewBox', 'x', 'y', 'x1', 'y1', 'x2', 'y2', 'cx', 'cy', 'r', 'rx', 'ry',
    'width', 'height', 'points', 'd', 'fill', 'stroke', 'stroke-width', 'fill-opacity',
    'stroke-dasharray', 'stroke-linejoin', 'stroke-linecap', 'text-anchor', 'font-size', 'transform'])
  if (root.querySelectorAll('*').length > 500) return ''
  for (const element of [root, ...root.querySelectorAll('*')]) {
    if (!tags.has(element.localName)) { element.remove(); continue }
    for (const attribute of [...element.attributes]) {
      if (!attrs.has(attribute.name) || /url\s*\(|javascript:|data:|https?:/i.test(attribute.value)) {
        element.removeAttribute(attribute.name)
      }
    }
  }
  root.setAttribute('role', 'img')
  root.setAttribute('aria-label', '题目示意图')
  return new XMLSerializer().serializeToString(root)
}

export function numberTicks(visual) {
  const min = Number(visual?.min ?? 0)
  const max = Number(visual?.max ?? 10)
  if (!Number.isFinite(min) || !Number.isFinite(max) || max <= min) return []
  const step = Math.max(1, Math.ceil((max - min) / 20))
  const result = []
  for (let value = min; value <= max; value += step) {
    result.push({ value, x: 30 + (value - min) / (max - min) * 340 })
  }
  return result
}
