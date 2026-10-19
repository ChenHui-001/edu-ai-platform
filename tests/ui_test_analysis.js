// 学情分析模块 UI 自动化测试
// 用法: node ui_test_analysis.js
// 产出: ui_shots/*.png + ui_result.json（布局/控制台/响应式检查结果）
const { chromium } = require('playwright-core');
const fs = require('fs');
const path = require('path');

const CRED = JSON.parse(fs.readFileSync('C:/Users/王/AppData/Local/Temp/tea1_login.json', 'utf-8'));
const BASE = 'http://localhost:5173';
const OUT = path.join(__dirname, '..', 'ui_shots');
fs.mkdirSync(OUT, { recursive: true });

const result = { pages: [], consoleErrors: [], failedRequests: [], responsive: [] };

(async () => {
  const browser = await chromium.launch({
    channel: 'msedge', headless: true,
  });
  const ctx = await browser.newContext({ viewport: { width: 1440, height: 900 } });
  const page = await ctx.newPage();

  // 收集控制台错误与失败请求
  page.on('console', (m) => {
    if (m.type() === 'error') result.consoleErrors.push(m.text().slice(0, 200));
  });
  page.on('requestfailed', (r) => result.failedRequests.push(`${r.method()} ${r.url()} ${r.failure()?.errorText}`));
  page.on('response', (r) => {
    if (r.status() >= 400 && r.url().includes('/api/'))
      result.failedRequests.push(`${r.request().method()} ${r.url()} -> ${r.status()}`);
  });

  // 1) 注入登录态
  await page.goto(BASE + '/login', { waitUntil: 'domcontentloaded' });
  await page.evaluate(([t, u]) => {
    localStorage.setItem('access_token', t);
    localStorage.setItem('user', u);
  }, [CRED.access_token, JSON.stringify(CRED.user)]);

  const pages = [
    { name: 'class-analysis', url: '/teacher/analysis' },
    { name: 'student-analysis', url: '/teacher/students' },
    { name: 'teacher-report', url: '/teacher/reports' },
  ];

  for (const p of pages) {
    const rec = { name: p.name, url: p.url, checks: {} };
    await page.goto(BASE + p.url, { waitUntil: 'networkidle', timeout: 20000 }).catch(e => { rec.checks.navError = String(e).slice(0, 100); });
    await page.waitForTimeout(1200); // 等图表渲染

    // 页面标题
    rec.checks.title = await page.locator('.page-title').first().textContent().catch(() => null);

    // 统计卡片数量与内容
    rec.checks.statCards = await page.locator('.stat-card').count();
    rec.checks.statValues = await page.locator('.stat-card .stat-value').allTextContents().catch(() => []);

    // echarts canvas 渲染数量
    rec.checks.echartsCanvas = await page.locator('canvas').count();
    // echarts 内部是否有内容（宽高>0）
    rec.checks.canvasSizes = await page.$$eval('canvas', cs =>
      cs.map(c => ({ w: c.width, h: c.height }))).catch(() => []);

    // 空状态组件
    rec.checks.emptyCount = await page.locator('.el-empty').count();
    rec.checks.emptyTexts = await page.locator('.el-empty__description').allTextContents().catch(() => []);

    // 表格行数与首行单元格内容（检测字段漂移导致的空白列）
    const tbl = page.locator('.el-table').first();
    if (await tbl.count()) {
      const cells = await tbl.locator('.el-table__body-wrapper .el-table__row').first()
        .locator('td').allTextContents().catch(() => []);
      rec.checks.firstRowCells = cells.map(c => c.trim());
      rec.checks.bodyRowCount = await tbl.locator('.el-table__body-wrapper .el-table__row').count();
    }

    // 下拉数量（筛选器）
    rec.checks.selects = await page.locator('.el-select').count();

    // 截图（桌面）
    await page.screenshot({ path: path.join(OUT, `${p.name}-1440.png`), fullPage: true });
    result.pages.push(rec);
  }

  // 2) 响应式：平板 768 / 手机 375，检查横向溢出与卡片堆叠
  for (const w of [768, 375]) {
    await page.setViewportSize({ width: w, height: 900 });
    await page.goto(BASE + '/teacher/analysis', { waitUntil: 'networkidle', timeout: 20000 }).catch(() => {});
    await page.waitForTimeout(800);
    const overflow = await page.evaluate(() =>
      document.documentElement.scrollWidth > document.documentElement.clientWidth + 2);
    // el-row 是否堆叠（列宽是否超过一半视口）
    const colW = await page.$$eval('.el-col', cs => cs.slice(0, 6).map(c => c.getBoundingClientRect().width));
    await page.screenshot({ path: path.join(OUT, `class-analysis-${w}.png`), fullPage: true });
    result.responsive.push({ width: w, horizontalOverflow: overflow, colWidths: colW.map(x => Math.round(x)) });
  }

  fs.writeFileSync(path.join(OUT, 'ui_result.json'), JSON.stringify(result, null, 2));
  console.log('DONE. pages=', result.pages.length, 'consoleErrors=', result.consoleErrors.length,
    'failedReq=', result.failedRequests.length);
  await browser.close();
})();
