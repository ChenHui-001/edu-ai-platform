/**
 * 轻量 HTML 净化器（白名单）。
 *
 * 背景：学习笔记由学生自由输入，后端原样存储，前端 `v-html` 直接渲染。
 * 这使得 `<script>alert(1)</script>`、`<img src=x onerror=...>` 这类内容
 * 可以存储并执行 —— 典型存储型 XSS，受害者是打开该笔记的本人/教师。
 *
 * 项目未引入 DOMPurify，这里用 DOMParser + 标签/属性白名单做净化：
 *   - 只保留基础排版标签（p / br / strong / em / ul / ol / li / code / pre ...）
 *   - 属性只保留 href / src 且协议必须是 http(s) / mailto / 相对路径
 *   - script / style / iframe / object / embed 等整体丢弃（连内容一起）
 *   - 事件属性（on*）一律移除
 *
 * 注意：净化结果仍是 HTML 字符串，交给 v-html 是安全的；但绝不能把
 * 未净化的原始内容拼进去。
 */

// 允许保留的标签（其余标签剥壳保内容，危险标签整体丢弃）
const ALLOWED_TAGS = new Set([
  'A', 'B', 'BLOCKQUOTE', 'BR', 'CODE', 'DEL', 'DIV', 'EM', 'H1', 'H2', 'H3',
  'H4', 'H5', 'H6', 'HR', 'I', 'IMG', 'LI', 'OL', 'P', 'PRE', 'S', 'SPAN',
  'STRONG', 'SUB', 'SUP', 'TABLE', 'TBODY', 'TD', 'TH', 'THEAD', 'TR', 'U', 'UL'
])

// 连内容一起丢弃的标签（它们的文本内容同样有风险/无意义）
const DROP_TAGS = new Set([
  'SCRIPT', 'STYLE', 'IFRAME', 'OBJECT', 'EMBED', 'LINK', 'META', 'BASE',
  'FORM', 'INPUT', 'BUTTON', 'TEXTAREA', 'SELECT', 'OPTION', 'SVG', 'MATH',
  'TEMPLATE', 'NOSCRIPT', 'FRAME', 'FRAMESET', 'APPLET'
])

// 允许保留的属性
const ALLOWED_ATTRS = new Set(['href', 'src', 'alt', 'title', 'colspan', 'rowspan'])

// 安全协议；javascript:/data: 等一律拒绝
const SAFE_URL = /^(https?:|mailto:|tel:|\/|#|\.\/|\.\.\/)/i

function cleanNode(node, doc) {
  // 从后往前遍历，删除时不影响索引
  const children = Array.from(node.childNodes)
  for (const child of children) {
    if (child.nodeType === 3) continue // 文本节点：DOMParser 不会执行其中的标签

    if (child.nodeType !== 1) {
      // 注释 / CDATA 等一律删除（注释里可藏条件注释攻击）
      child.remove()
      continue
    }

    const tag = child.tagName
    if (DROP_TAGS.has(tag)) {
      child.remove()
      continue
    }

    if (!ALLOWED_TAGS.has(tag)) {
      // 未知标签：剥掉外壳，保留（已净化的）子内容
      cleanNode(child, doc)
      const frag = doc.createDocumentFragment()
      while (child.firstChild) frag.appendChild(child.firstChild)
      child.replaceWith(frag)
      continue
    }

    // 属性白名单 + 事件属性 + URL 协议校验
    for (const attr of Array.from(child.attributes)) {
      const name = attr.name.toLowerCase()
      const value = attr.value || ''
      const isEvent = name.startsWith('on')
      const isBadUrl = (name === 'href' || name === 'src') && !SAFE_URL.test(value.trim())
      if (isEvent || isBadUrl || !ALLOWED_ATTRS.has(name)) {
        child.removeAttribute(attr.name)
      }
    }

    // <a> 统一加 rel/noopener，避免 target 被滥用
    if (tag === 'A' && child.getAttribute('href')) {
      child.setAttribute('rel', 'noopener noreferrer')
      child.setAttribute('target', '_blank')
    }

    cleanNode(child, doc)
  }
  return node
}

/**
 * 把不可信 HTML 净化为可安全用于 v-html 的字符串。
 * @param {string} raw 原始内容
 * @returns {string} 净化后的 HTML
 */
export function sanitizeHtml(raw) {
  if (!raw) return ''
  const src = String(raw)
  // 没有标签时直接返回转义后的纯文本，省掉 DOM 解析开销
  if (!/[<>]/.test(src)) return src

  const parser = new DOMParser()
  const doc = parser.parseFromString(`<body>${src}</body>`, 'text/html')
  const body = doc.body
  cleanNode(body, doc)
  return body.innerHTML
}
