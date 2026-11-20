#!/usr/bin/env node
/**
 * 流程待办页（M6 前端）的浏览器端回归。
 *
 * 目的：后端 41 项 HTTP 链路验证与前端 13 项单测都覆盖不到
 * 「浏览器里点一遍」这一层——菜单项是否出现、弹窗能否打开、
 * 审批后列表是否真的少一条、窄屏会不会横向溢出。
 * 这些只有真跑一次浏览器才知道。
 *
 * 依赖：playwright（需 `npm i -D playwright && npx playwright install chromium`）。
 * playwright 不在 package.json 的依赖里是有意的：浏览器二进制约 150MB，
 * 不该塞进每次 `npm install`。本脚本因此**不在** CI 主链路里，按需手动跑。
 *
 * 前置：
 *   - 后端 http://127.0.0.1:8000 已启动（CAPTCHA_ENFORCED=false、
 *     MUST_CHANGE_PASSWORD_ENFORCED=false 仅用于本地验证）
 *   - 前端 http://127.0.0.1:5199 已启动（vite dev）
 *
 * 用法：
 *   node scripts/verify-flow-todo-ui.mjs
 * 环境变量：API_BASE / WEB_BASE / SHOT_DIR 可覆盖默认地址与截图目录。
 */

import fs from 'fs'
import { createRequire } from 'node:module'
import { dirname, resolve } from 'node:path'
import { fileURLToPath } from 'node:url'

const HERE = dirname(fileURLToPath(import.meta.url))

// playwright 不在 frontend/package.json 的依赖里（浏览器二进制约 150MB，
// 不该塞进每次 npm install）。这里从若干常见位置探测已装好的副本，
// 找不到就给出明确的安装指引，而不是抛一个 ERR_MODULE_NOT_FOUND。
function loadPlaywright() {
  const require = createRequire(import.meta.url)
  const candidates = [
    'playwright',
    resolve(HERE, '../node_modules/playwright'),
    resolve(HERE, '../../node_modules/playwright'),
    process.env.PLAYWRIGHT_PATH
  ].filter(Boolean)
  for (const c of candidates) {
    try {
      return require(c)
    } catch { /* 试下一个 */ }
  }
  console.error(
    '[ui] 找不到 playwright。请先安装：\n' +
    '  npm i -D playwright && npx playwright install chromium\n' +
    '（或用 PLAYWRIGHT_PATH 指向已安装的 playwright 目录）')
  process.exit(2)
}

const { chromium } = loadPlaywright()

const API = process.env.API_BASE || 'http://127.0.0.1:8000/api/v1'
const BASE = process.env.WEB_BASE || 'http://127.0.0.1:5199'
const SHOT = process.env.SHOT_DIR || 'E:/codeX/.tmp_ui_check/shots'
fs.mkdirSync(SHOT, { recursive: true })

const errors = []
const browser = await chromium.launch()
const ctx = await browser.newContext({ viewport: { width: 1440, height: 900 } })
const page = await ctx.newPage()

page.on('console', m => { if (m.type() === 'error') errors.push('CONSOLE: ' + m.text()) })
page.on('pageerror', e => errors.push('PAGEERROR: ' + e.message))
page.on('requestfailed', r => errors.push('REQFAIL: ' + r.url() + ' ' + (r.failure()?.errorText || '')))

const step = async (name, fn) => {
  try {
    await fn()
    console.log('[OK] ' + name)
  } catch (e) {
    console.log('[FAIL] ' + name + ' :: ' + e.message)
    await page.screenshot({ path: SHOT + '/fail.png', fullPage: true })
    throw e
  }
}

// 注册一个新老师 → sys_admin 名下产生一条「用户注册审批」待办。
// 抽成函数是因为脚本中段会**审批掉**待办，后面造逾期数据时还需要再来一条；
// 之前写成一次性步骤，导致「造逾期」在只有一条待办时必然失败
// （审批已把待办清空，脚本只能靠人工先造数据才能跑完）。
async function registerTeacher() {
  const uname = 'uit' + Date.now().toString().slice(-8)
  // 口令必须**每次随机**：脚本注册的是一次性账号，但口令若写死，
  // 会被 tools/check_plaintext_secrets.py 的 prod_teacher 规则命中
  // （那条规则针对生产教师账号的口令格式），提交时会被门禁拦下。
  // 随机生成既绕开误报，也避免同一口令复用到别的环境。
  // 注意：注释里也不要写出该规则的匹配样例，否则门禁会连注释一起命中。
  const pwd = 'Ui' + crypto.randomUUID().replace(/-/g, '') + '@2026'
  const res = await fetch(API + '/auth/register', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      username: uname, password: pwd, real_name: 'UI 验证老师',
      identity: 'teacher', reason: 'UI 验证'
    })
  })
  const body = await res.json()
  if (body.code !== 200) throw new Error('注册失败: ' + JSON.stringify(body).slice(0, 200))
}

// ---- 0. 造一条新待办（注册新老师 -> sys_admin 待办） ----
await step('注册新老师产生待办', async () => {
  await registerTeacher()
})

// ---- 1. 通过 API 登录，把令牌注入 localStorage ----
await step('API 登录并注入令牌', async () => {
  const res = await fetch(API + '/auth/login', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ username: 'admin', password: 'Admin@123456' })
  })
  const body = await res.json()
  if (body.code !== 200) throw new Error('登录失败: ' + JSON.stringify(body).slice(0, 200))
  const d = body.data
  const user = { ...d.user, permissions: d.permission }
  await ctx.addInitScript(([t, u]) => {
    localStorage.setItem('access_token', t)
    localStorage.setItem('user', u)
  }, [d.access_token, JSON.stringify(user)])
})

// ---- 2. 直接进待办页 ----
await step('打开流程待办页', async () => {
  await page.goto(BASE + '/admin/flow-todo', { waitUntil: 'networkidle' })
  await page.waitForTimeout(1500)
})
await page.screenshot({ path: SHOT + '/01-todo.png', fullPage: true })

await step('页面标题为「流程待办」', async () => {
  const t = await page.locator('.page-title').innerText()
  if (!t.includes('流程待办')) throw new Error('标题异常: ' + t)
})
await step('侧边栏有「我的待办」分组', async () => {
  await page.waitForSelector('text=我的待办', { timeout: 8000 })
})
await step('待办表格显示「管理员审批」', async () => {
  await page.waitForSelector('text=管理员审批', { timeout: 10000 })
})
await step('显示角色标签「系统管理员」', async () => {
  await page.waitForSelector('text=系统管理员', { timeout: 5000 })
})
await step('待办数徽标可见', async () => {
  const badge = await page.locator('.el-tabs__item .el-badge__content').first().textContent().catch(() => null)
  if (!badge) throw new Error('未看到待办数徽标')
})

// ---- 3. 详情弹窗 ----
await step('打开流程详情', async () => {
  await page.locator('button:has-text("详情"):visible').first().click()
  await page.waitForSelector('.el-dialog:visible', { timeout: 8000 })
  await page.waitForTimeout(900)
})
await page.screenshot({ path: SHOT + '/02-detail.png', fullPage: true })
await step('详情含流程名称与留痕', async () => {
  const txt = await page.locator('.el-dialog:visible').innerText()
  if (!txt.includes('用户注册审批')) throw new Error('未显示流程名称: ' + txt.slice(0, 300))
  if (!txt.includes('流转留痕')) throw new Error('未显示留痕')
})
await step('关闭详情', async () => {
  await page.locator('.el-dialog:visible button:has-text("关闭")').click()
  await page.waitForTimeout(500)
})

// ---- 4. 审批通过 ----
// 记下当前列表里的待办条数，审批后应当减少 1 条
let todoCountBefore = 0
await step('记录审批前待办条数', async () => {
  const txt = await page.locator('.el-card').first().innerText()
  const m = txt.match(/共\s*(\d+)\s*条/)
  todoCountBefore = m ? Number(m[1]) : 0
  if (todoCountBefore < 1) throw new Error('审批前没有待办，测不出效果')
})

await step('点「通过」打开对话框', async () => {
  await page.locator('button:has-text("通过"):visible').first().click()
  await page.waitForSelector('.el-dialog:visible', { timeout: 8000 })
  await page.waitForTimeout(700)
})
await page.screenshot({ path: SHOT + '/03-approve.png', fullPage: true })
await step('填写意见并提交', async () => {
  await page.locator('.el-dialog:visible textarea').fill('材料齐全，同意通过（UI 验证）')
  await page.locator('.el-dialog:visible button:has-text("确定")').click()
  await page.waitForTimeout(2200)
})
await page.screenshot({ path: SHOT + '/04-after.png', fullPage: true })
await step('审批后待办减少 1 条', async () => {
  // 不能断言「列表为空」——库里可能还有别的待办（每次注册都会新增一条）。
  // 正确的断言是：审批掉的那一条不再出现在待办里。
  const txt = await page.locator('.el-card').first().innerText()
  const m = txt.match(/共\s*(\d+)\s*条/)
  const after = m ? Number(m[1]) : 0
  if (after !== todoCountBefore - 1) {
    throw new Error(`待办数未减少: ${todoCountBefore} -> ${after}`)
  }
})

// ---- 5. 已办 ----
await step('切到已办', async () => {
  await page.locator('.el-tabs__item:has-text("已办")').click()
  await page.waitForTimeout(1800)
})
await page.screenshot({ path: SHOT + '/05-done.png', fullPage: true })
await step('已办列表有记录', async () => {
  const body = await page.locator('.el-card').first().innerText()
  if (!body.includes('管理员审批')) throw new Error('已办为空: ' + body.slice(0, 250))
})

// ---- 6. 我发起的 ----
await step('切到我发起的', async () => {
  await page.locator('.el-tabs__item:has-text("我发起的")').click()
  await page.waitForTimeout(1800)
})
await page.screenshot({ path: SHOT + '/06-mine.png', fullPage: true })

// ---- 6.5 逾期标签页 ----
await step('切到逾期标签页', async () => {
  // 先回到「待办」再点「逾期」：直接从「我发起的」跳过来时，
  // tab-change 与表格渲染不同步，断言会读到尚未切换的表格。
  await page.locator('.el-tabs__item:has-text("待办")').click()
  await page.waitForTimeout(1500)
  await page.locator('.el-tabs__item:has-text("逾期")').click()
  await page.waitForTimeout(2200)
})
await step('逾期页显示「逾期待办不会自动关闭」提示', async () => {
  await page.waitForTimeout(500)
  const body = await page.locator('.el-card').first().innerText()
  if (!body.includes('逾期待办不会自动关闭')) {
    throw new Error('未看到逾期说明: ' + body.slice(0, 200))
  }
})

// ---- 6.5b 造一条逾期待办，确认逾期页真的能显示数据 ----
// 只验空态不够：空态只说明页面能打开，说不清逾期数据真的查得出来。
await step('把一条待办的截止时间推到过去', async () => {
  const token = await page.evaluate(() => localStorage.getItem('access_token'))
  // 第 4 步的「审批通过」会把当时那条待办审掉。若脚本启动时待办池里
  // 只有一开始注册出来的那一条，这里就一条都不剩了 —— 造逾期必然失败。
  // 所以先保证待办池非空：不够就再注册一个老师补一条。
  let items = []
  {
    const res0 = await fetch(API + '/flow/todo', {
      headers: { Authorization: 'Bearer ' + token }
    })
    const body0 = await res0.json()
    items = body0.data?.items || []
  }
  if (!items.length) {
    await registerTeacher()
    const res0 = await fetch(API + '/flow/todo', {
      headers: { Authorization: 'Bearer ' + token }
    })
    const body0 = await res0.json()
    items = body0.data?.items || []
  }
  if (!items.length) throw new Error('没有可用的待办来造逾期')
  const taskId = items[0].id
  const past = new Date(Date.now() - 3600 * 1000)
    .toISOString().slice(0, 19).replace('T', ' ')
  const res = await fetch(API + `/flow/tasks/${taskId}/deadline`, {
    method: 'PUT',
    headers: {
      'Content-Type': 'application/json',
      Authorization: 'Bearer ' + token
    },
    body: JSON.stringify({ deadline: past })
  })
  if (res.status !== 200) {
    throw new Error('设置截止时间失败: ' + res.status + ' ' + (await res.text()).slice(0, 200))
  }
})

await step('逾期页出现该待办且标记为已逾期', async () => {
  await page.locator('.el-tabs__item:has-text("待办")').click()
  await page.waitForTimeout(1200)
  await page.locator('.el-tabs__item:has-text("逾期")').click()
  await page.waitForTimeout(2500)
  const body = await page.locator('.el-card').first().innerText()
  if (!body.includes('已逾期')) {
    throw new Error('逾期页没有「已逾期」标记: ' + body.slice(0, 300))
  }
  if (!body.includes('已逾期 ')) {
    throw new Error('逾期页没有逾期时长文案: ' + body.slice(0, 300))
  }
})
await page.screenshot({ path: SHOT + '/08-overdue.png', fullPage: true })

// ---- 6.6 转办 ----
await step('切回待办', async () => {
  await page.locator('.el-tabs__item:has-text("待办")').click()
  await page.waitForTimeout(1500)
})
await step('点「转办」打开对话框', async () => {
  await page.locator('button:has-text("转办"):visible').first().click()
  await page.waitForSelector('.el-dialog:visible', { timeout: 8000 })
  await page.waitForTimeout(1200)
})
await page.screenshot({ path: SHOT + '/09-transfer.png', fullPage: true })
await step('转办对话框含候选下拉与理由框', async () => {
  const txt = await page.locator('.el-dialog:visible').innerText()
  if (!txt.includes('转办给')) throw new Error('缺转办对象: ' + txt.slice(0, 200))
  if (!txt.includes('转办理由')) throw new Error('缺转办理由: ' + txt.slice(0, 200))
})
await step('关闭转办对话框', async () => {
  await page.locator('.el-dialog:visible button:has-text("取消")').click()
  await page.waitForTimeout(600)
})

// ---- 6.7 催办 ----
await step('点「催办」打开对话框', async () => {
  await page.locator('button:has-text("催办"):visible').first().click()
  await page.waitForSelector('.el-dialog:visible', { timeout: 8000 })
  await page.waitForTimeout(900)
})
await page.screenshot({ path: SHOT + '/10-urge.png', fullPage: true })
await step('催办对话框含留言框与频次提示', async () => {
  const txt = await page.locator('.el-dialog:visible').innerText()
  if (!txt.includes('催办留言')) throw new Error('缺催办留言: ' + txt.slice(0, 200))
  if (!txt.includes('30 分钟')) throw new Error('缺频次提示: ' + txt.slice(0, 200))
})
await step('关闭催办对话框', async () => {
  await page.locator('.el-dialog:visible button:has-text("取消")').click()
  await page.waitForTimeout(600)
})

// ---- 6.8 催交考试 ----
await step('点「催交考试」打开选任务弹窗', async () => {
  await page.locator('button:has-text("催交考试"):visible').first().click()
  await page.waitForSelector('.el-dialog:visible', { timeout: 8000 })
  await page.waitForTimeout(1500)
})
await page.screenshot({ path: SHOT + '/11-urge-exam.png', fullPage: true })
await step('选任务弹窗标题正确', async () => {
  const txt = await page.locator('.el-dialog:visible').innerText()
  if (!txt.includes('选择要催交')) throw new Error('弹窗标题异常: ' + txt.slice(0, 200))
})
await step('关闭选任务弹窗', async () => {
  await page.locator('.el-dialog:visible button:has-text("关闭")').click()
  await page.waitForTimeout(600)
})

// ---- 7. 窄屏 ----
await step('窄屏(390px)不溢出', async () => {
  await page.setViewportSize({ width: 390, height: 844 })
  await page.waitForTimeout(900)
  await page.screenshot({ path: SHOT + '/07-mobile.png', fullPage: true })
  const w = await page.evaluate(() => document.documentElement.scrollWidth)
  if (w > 420) throw new Error('横向溢出 scrollWidth=' + w)
})

console.log('\n--- console/page errors ---')
console.log(errors.length ? errors.join('\n') : '(none)')
await browser.close()
