// 工作台显示问题复现
const { chromium } = require('playwright-core');
const fs = require('fs');
const T = JSON.parse(fs.readFileSync('C:/Users/王/AppData/Local/Temp/tea1_login.json', 'utf-8'));
(async () => {
  const browser = await chromium.launch({ channel: 'msedge', headless: true });
  const page = await (await browser.newContext({ viewport: { width: 1440, height: 900 } })).newPage();
  const errs = [];
  page.on('pageerror', e => errs.push('PAGEERROR: ' + String(e).slice(0, 250)));
  page.on('console', m => { if (m.type() === 'error') errs.push('CONSOLE: ' + m.text().slice(0, 250)); });
  page.on('response', r => { if (r.status() >= 400) errs.push(`HTTP ${r.status()} ${r.url().slice(-70)}`); });

  await page.goto('http://localhost:5173/login', { waitUntil: 'domcontentloaded' });
  await page.evaluate(([t, u]) => {
    localStorage.setItem('access_token', t);
    localStorage.setItem('user', u);
  }, [T.access_token, JSON.stringify(T.user)]);

  await page.goto('http://localhost:5173/dashboard', { waitUntil: 'networkidle', timeout: 20000 });
  await page.waitForTimeout(2500);
  const state = await page.evaluate(() => ({
    title: document.querySelector('.page-title, h2')?.textContent?.trim(),
    cards: document.querySelectorAll('.stat-card').length,
    cardValues: Array.from(document.querySelectorAll('.stat-card .stat-value')).map(x => x.textContent?.trim()).slice(0, 8),
    canvas: document.querySelectorAll('canvas').length,
    canvasSizes: Array.from(document.querySelectorAll('canvas')).map(c => `${c.width}x${c.height}`),
    emptyCount: document.querySelectorAll('.el-empty').length,
    emptyTexts: Array.from(document.querySelectorAll('.el-empty__description')).map(x => x.textContent?.trim()).slice(0, 5),
    tables: document.querySelectorAll('.el-table').length,
    listItems: document.querySelectorAll('.el-timeline-item, .el-table__row').length,
  }));
  console.log('工作台状态:', JSON.stringify(state, null, 1));
  console.log('=== 错误 ===');
  errs.forEach((e, i) => console.log(`[${i}]`, e));
  if (!errs.length) console.log('(无)');
  await page.screenshot({ path: '../ui_shots/dashboard-check.png', fullPage: true });
  await browser.close();
})();
