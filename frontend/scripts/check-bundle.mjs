#!/usr/bin/env node
/**
 * 构建产物预算/回归检查（在 `npm run build` 之后运行）。
 *
 * 目的：
 *  1) 防止 @element-plus/icons-vue 重新退化为“整套图标入库”：
 *     barrel 导入本身是 tree-shakable 的，但一旦有人改成 `import * as Icons`
 *     或重新全局注册图标，未使用的图标也会进包。这里抽查若干未使用图标名
 *     不应出现在 dist 的 JS 中。
 *  2) 防止单个 chunk 重新膨胀（本轮 Element Plus 按需化 + ECharts 按需后，
 *     最大 chunk 约 518KB；超过 650KB 视为回归）。
 */
import { readdirSync, readFileSync, statSync } from 'node:fs'
import { join } from 'node:path'

const DIST = 'dist/assets'
const UNUSED_ICONS = ['Watermelon', 'Football', 'Basketball', 'IceCream', 'Mug']
const MAX_CHUNK_BYTES = 650 * 1024

let errors = 0
const files = readdirSync(DIST).filter((f) => f.endsWith('.js'))

const joined = files.map((f) => readFileSync(join(DIST, f), 'utf8')).join('\n')
for (const name of UNUSED_ICONS) {
  if (joined.includes(name)) {
    console.error(`[bundle] 未使用图标 "${name}" 出现在产物中：图标按需/tree-shaking 回归`)
    errors++
  }
}

let maxFile = ''
let maxSize = 0
for (const f of files) {
  const size = statSync(join(DIST, f)).size
  if (size > maxSize) { maxSize = size; maxFile = f }
  if (size > MAX_CHUNK_BYTES) {
    console.error(`[bundle] chunk ${f} 超过预算：${(size / 1024).toFixed(1)}KB > 650KB`)
    errors++
  }
}

if (errors) process.exit(1)
console.log(`[bundle] OK - ${files.length} 个 JS chunk，最大 ${maxFile} ${(maxSize / 1024).toFixed(1)}KB，未使用图标未入库`)
