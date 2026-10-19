// 教学资源模块（管理员）UI 自动化测试
const { chromium } = require('playwright-core');
const fs = require('fs');
const path = require('path');

const CRED = JSON.parse(fs.readFileSync('C:/Users/王/AppData/Local/Temp/admin_login.json', 'utf-8'));
const BASE = 'http://localhost:5173';
const OUT = path.join(__dirname, '..', 'ui_shots');
fs.mkdirSync(OUT, { recursive: true });

const result = { pages: [], consoleErrors: [], failedRequests: [] };

(async () => {
  const browser = await chromium.launch({ channel: 'msedge', headless: true });
  const page = await (await browser.newContext({ viewport: { width: 1440, height: 900 } })).newPage();

  page.on('console', m => { if (m.type() === 'error') result.consoleErrors.push(m.text().slice(0, 200)); });
  page.on('pageerror', e => result.consoleErrors.push('PAGEERROR: ' + String(e).slice(0, 200)));
  page.on('requestfailed', r => result.failedRequests.push(`${r.method()} ${r.url()}`));
  page.on('response', r => {
    if (r.status() >= 400 && r.url().includes('/api/'))
      result.failedRequests.push(`${r.request().method()} ${r.url()} -> ${r.status()}`);
  });

  await page.goto(BASE + '/login', { waitUntil: 'domcontentloaded' });
  await page.evaluate(([t, u]) => {
    localStorage.setItem('access_token', t);
    localStorage.setItem('user', u);
  }, [CRED.access_token, JSON.stringify(CRED.user)]);

  const pages = [
    { name: 'grade', url: '/admin/grades' },
    { name: 'subject', url: '/admin/subjects' },
    { name: 'knowledge', url: '/admin/knowledge' },
    { name: 'class', url: '/admin/classes' },
  ];

  for (const pg of pages) {
    const rec = { name: pg.name, url: pg.url, checks: {} };
    await page.goto(BASE + pg.url, { waitUntil: 'networkidle', timeout: 25000 }).catch(e => {
      rec.checks.navError = String(e).slice(0, 100);
    });
    await page.waitForTimeout(1500);

    rec.checks.title = await page.locator('.page-title').first().textContent().catch(() => null);
    rec.checks.selects = await page.locator('.el-select').count();
    rec.checks.tableRows = await page.locator('.el-table__body-wrapper .el-table__row').count();
    rec.checks.toolbarBtns = await page.locator('.page-header .el-button').count();
    // 树形（仅 knowledge 页有 el-tree）
    rec.checks.treeCount = await page.locator('.el-tree').count();
    if (rec.checks.tableRows > 0) {
      rec.checks.firstRow = await page.locator('.el-table__body-wrapper .el-table__row')
        .first().locator('td').allTextContents().catch(() => []);
    }
    await page.screenshot({ path: path.join(OUT, `admin-${pg.name}-1440.png`), fullPage: true });
    result.pages.push(rec);
  }

  // 响应式
  for (const w of [768, 375]) {
    await page.setViewportSize({ width: w, height: 900 });
    await page.goto(BASE + '/admin/classes', { waitUntil: 'networkidle' });
    await page.waitForTimeout(800);
    const overflow = await page.evaluate(() =>
      document.documentElement.scrollWidth > document.documentElement.clientWidth + 2);
    result.responsive = result.responsive || [];
    result.responsive.push({ width: w, horizontalOverflow: overflow });
    await page.screenshot({ path: path.join(OUT, `admin-class-${w}.png`), fullPage: true });
  }

  fs.writeFileSync(path.join(OUT, 'ui_resource_result.json'), JSON.stringify(result, null, 2));
  console.log('DONE. pages=', result.pages.length, 'consoleErr=', result.consoleErrors.length);
  await browser.close();
})();
