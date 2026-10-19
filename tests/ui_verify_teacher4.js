// teacher4（有数据班级）视角的学情页验证
const { chromium } = require('playwright-core');
const fs = require('fs');
const CRED = JSON.parse(fs.readFileSync('C:/Users/王/AppData/Local/Temp/tea4_login.json', 'utf-8'));
(async () => {
  const browser = await chromium.launch({ channel: 'msedge', headless: true });
  const page = await (await browser.newContext({ viewport: { width: 1440, height: 900 } })).newPage();
  await page.goto('http://localhost:5173/login', { waitUntil: 'domcontentloaded' });
  await page.evaluate(([t, u]) => {
    localStorage.setItem('access_token', t);
    localStorage.setItem('user', u);
  }, [CRED.access_token, JSON.stringify(CRED.user)]);
  await page.goto('http://localhost:5173/teacher/analysis', { waitUntil: 'networkidle', timeout: 20000 });
  await page.waitForTimeout(2500);
  const canvas = await page.$$eval('canvas', cs => cs.map(c => ({ w: c.width, h: c.height })));
  const firstRow = await page.locator('.el-table__body-wrapper .el-table__row').first()
    .locator('td').allTextContents().catch(() => []);
  const cards = await page.locator('.stat-card .stat-value').allTextContents().catch(() => []);
  console.log('teacher4 班级学情 | canvas:', canvas.length, '| cards:', JSON.stringify(cards),
    '| 首行:', firstRow.map(c => c.trim()).slice(0, 9).join(' | '));
  await page.screenshot({ path: '../ui_shots/class-analysis-teacher4.png', fullPage: true });
  await browser.close();
})();
