import { describe, expect, it } from 'vitest'
import { renderMathContent, parseVisual, numberTicks, renderQuestionFigure } from '../mathContent'
import { escapeGraphText, buildGraphOption } from '../knowledgeGraph'

describe('shared mathematical presentation', () => {
  it('renders inline and display formulas', () => {
    const html = renderMathContent('求 $\\frac{1}{2}$，再看 $$x^2$$')
    expect(html).toContain('katex')
    expect(html).toContain('katex-display')
  })
  it('removes executable HTML before rendering formulas', () => {
    const html = renderMathContent('<img src="/x" onerror="evil()"><script>evil()</script>$1+2$')
    expect(html).not.toContain('onerror')
    expect(html).not.toContain('<script')
    expect(html).toContain('katex')
  })
  it('does not trust executable KaTeX commands', () => {
    expect(renderMathContent('$\\href{javascript:evil()}{x}$')).not.toContain('href="javascript:')
  })
  it('preserves code blocks as literal math', () => {
    expect(renderMathContent('<code>$x$</code>')).not.toContain('katex')
  })
  it('bounds fraction and polygon drawing inputs', () => {
    expect(parseVisual({ visual: { kind: 'fraction', numerator: 1, denominator: 3 } })).not.toBeNull()
    expect(parseVisual({ visual: { kind: 'fraction', numerator: 1.2, denominator: 3 } })).toBeNull()
    expect(parseVisual({ visual: { kind: 'polygon', points: Array(100).fill({ x: 0, y: 0 }) } })).toBeNull()
  })
  it('rejects invalid and non-finite number lines', () => {
    expect(parseVisual({ visual: { kind: 'number_line', min: 1, max: 1 } })).toBeNull()
    expect(parseVisual({ visual: { kind: 'number_line', min: 0, max: Infinity } })).toBeNull()
    expect(parseVisual({ visual: { kind: 'number_line', min: 0, max: 10, points: [{ value: 11 }] } })).toBeNull()
    expect(numberTicks({ min: -1000, max: 1000 }).length).toBeLessThanOrEqual(21)
  })
  it('renders passive upstream SVG while removing active elements and remote references', () => {
    const svg = renderQuestionFigure('<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 100 100" onload="evil()"><script>evil()</script><foreignObject><p>x</p></foreignObject><circle r="10" fill="url(https://evil)" /></svg>')
    expect(svg).toContain('<circle')
    expect(svg).not.toContain('onload')
    expect(svg).not.toContain('script')
    expect(svg).not.toContain('foreignObject')
    expect(svg).not.toContain('url(')
  })
  it('rejects non-SVG figures', () => {
    expect(renderQuestionFigure('<img src=x onerror="evil()">')).toBe('')
  })
  it('escapes every tooltip text field', () => {
    expect(escapeGraphText('<img onerror="x">')).toContain('&lt;')
    const option = buildGraphOption({ nodes: [{ id: 1, name: '<img src=x>', difficulty: '<script>x</script>' }], edges: [] })
    const tooltip = option.tooltip.formatter({ dataType: 'node', data: option.series[0].data[0] })
    expect(tooltip).not.toContain('<img')
    expect(tooltip).not.toContain('<script')
  })
})
