// ---------------------------------------------------------------- 鉴权下载工具
// 后端只认 `Authorization: Bearer`（无 Cookie），而 window.open / iframe 直接
// 访问裸 URL 时浏览器不会携带自定义请求头 —— 下载、导出、预览必然 401。
// 统一改为「axios blob 请求 + 本地 objectURL」：
//   1. 请求由 request.js 注入 token（并发 401 还会自动刷新重试）；
//   2. 拿到 Blob 后在本地生成临时 URL，交给 a[download] 或 iframe 使用；
//   3. 用完立即 revokeObjectURL，避免 Blob 常驻内存。

/** 读取响应头（兼容 AxiosHeaders 与普通对象两种形态）。 */
function getHeader(headers, name) {
  if (!headers) return ''
  try {
    if (typeof headers.get === 'function') return headers.get(name) || ''
    return headers[name] || headers[name.toLowerCase()] || ''
  } catch {
    return ''
  }
}

/**
 * 从 Content-Disposition 中解析文件名。
 * 优先 RFC 5987 的 filename*=UTF-8''...（中文名走这个分支），
 * 其次普通 filename="xxx"；解析失败返回空串，由调用方用 fallbackFileName。
 */
function parseFileName(disposition) {
  if (!disposition) return ''
  const star = /filename\*\s*=\s*([^;]+)/i.exec(disposition)
  if (star) {
    const raw = star[1].trim().replace(/^["']|["']$/g, '')
    const idx = raw.indexOf("''")
    const encoded = idx >= 0 ? raw.slice(idx + 2) : raw
    try {
      return decodeURIComponent(encoded)
    } catch {
      return encoded
    }
  }
  const normal = /filename\s*=\s*("?)([^";]+)\1/i.exec(disposition)
  if (normal) {
    const raw = normal[2].trim()
    try {
      return decodeURIComponent(raw)
    } catch {
      return raw
    }
  }
  return ''
}

/** 把 blob 响应归一成 Blob（axios 已配置 responseType: 'blob'，正常情况就是 Blob）。 */
function toBlob(res) {
  if (res?.data instanceof Blob) return res.data
  return new Blob([res?.data])
}

/**
 * 下载导出文件。
 * @param {Promise} requestPromise axios blob 请求的 Promise（由 api helper 发起）
 * @param {string} fallbackFileName 响应头没有文件名时使用的兜底名
 */
export async function downloadBlob(requestPromise, fallbackFileName = 'download') {
  const res = await requestPromise
  const blob = toBlob(res)
  const fileName = parseFileName(getHeader(res?.headers, 'content-disposition'))
    || fallbackFileName

  const url = URL.createObjectURL(blob)
  const a = document.createElement('a')
  a.href = url
  a.download = fileName
  a.style.display = 'none'
  document.body.appendChild(a)
  a.click()
  document.body.removeChild(a)
  URL.revokeObjectURL(url)
  return fileName
}

/**
 * 附件预览：把 blob 请求结果转成 objectURL，可直接给 iframe / img / 新标签页。
 * 注意 objectURL 不会自动释放，调用方必须在页面卸载（onBeforeUnmount）
 * 或关闭预览弹窗时 URL.revokeObjectURL(url)，否则反复预览会累积内存。
 * @param {Promise} requestPromise axios blob 请求的 Promise
 * @returns {Promise<string>} 本地 objectURL
 */
export async function fetchBlobUrl(requestPromise) {
  const res = await requestPromise
  return URL.createObjectURL(toBlob(res))
}
