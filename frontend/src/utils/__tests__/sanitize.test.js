import { describe, it, expect } from 'vitest'
import { sanitizeHtml } from '../sanitize'

// 存储型 XSS 回归：笔记/题干都走 sanitizeHtml 后再 v-html，白名单必须挡住
// script、事件属性、javascript: 协议，同时保留基础排版标签。
describe('sanitizeHtml（XSS 白名单）', () => {
  it('整段丢弃 script，不保留其内容', () => {
    const out = sanitizeHtml('<p>hi</p><script>alert(1)</script>')
    expect(out).toBe('<p>hi</p>')
  })

  it('移除事件属性（onerror 等），保留安全 src', () => {
    const out = sanitizeHtml('<img src="/uploads/x.png" onerror="alert(1)">')
    expect(out).toBe('<img src="/uploads/x.png">')
  })

  it('移除不合规协议的 src（如裸相对路径/data:）', () => {
    expect(sanitizeHtml('<img src="javascript:alert(1)">')).toBe('<img>')
  })

  it('移除 javascript: 协议链接，但保留标签文字', () => {
    const out = sanitizeHtml('<a href="javascript:alert(1)">点我</a>')
    expect(out).toBe('<a>点我</a>')
  })

  it('保留正常排版标签', () => {
    expect(sanitizeHtml('<p><strong>加粗</strong>和<em>斜体</em></p>'))
      .toBe('<p><strong>加粗</strong>和<em>斜体</em></p>')
  })

  it('安全外链补 rel=noopener noreferrer 与 target=_blank', () => {
    const out = sanitizeHtml('<a href="https://example.com">x</a>')
    expect(out).toContain('rel="noopener noreferrer"')
    expect(out).toContain('target="_blank"')
    expect(out).toContain('href="https://example.com"')
  })

  it('未知标签剥壳保内容；空输入返回空串', () => {
    expect(sanitizeHtml('<custom>文本</custom>')).toBe('文本')
    expect(sanitizeHtml('')).toBe('')
    expect(sanitizeHtml(null)).toBe('')
  })

  it('纯文本原样返回，避免多余 DOM 解析', () => {
    expect(sanitizeHtml('没有标签的文本')).toBe('没有标签的文本')
  })
})
