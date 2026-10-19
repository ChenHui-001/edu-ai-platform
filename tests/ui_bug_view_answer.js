// 复现「查看答卷」422
const { chromium } = require('playwright-core');
const fs = require('fs');
const T = JSON.parse(fs.readFileSync('C:/Users/王/AppData/Local/Temp/tea1_login.json', 'utf-8'));
(async () => {
  const browser = await chromium.launch({ channel: 'msedge', headless: true });
  const page = await (await browser.newContext({ viewport: { width: 1440, height: 900 } })).newPage();
  const bad = [];
  page.on('response', r => {
    if (r.status() >= 400) bad.push(`${r.status()} ${r.request().method()} ${r.url().slice(-70)}`);
  });
  page.on('pageerror', e => console.log('PAGEERROR:', String(e).slice(0, 150)));
  await page.goto('http://localhost:5173/login', { waitUntil: 'domcontentloaded' });
  await page.evaluate(([t, u]) => {
    localStorage.setItem('access_token', t);
    localStorage.setItem('user', u);
  }, [T.access_token, JSON.stringify(T.user)]);
  await page.goto('http://localhost:5173/teacher/tasks', { waitUntil: 'networkidle', timeout: 20000 });
  await page.waitForTimeout(1200);

  const rows = await page.locator('.el-table__body-wrapper .el-table__row').count();
  console.log('任务行数:', rows);
  if (rows) {
    const firstRowText = await page.locator('.el-table__body-wrapper .el-table__row').first().textContent();
    console.log('首行:', firstRowText.replace(/\s+/g, ' ').slice(0, 100));
    // 点「查看答卷」
    await page.locator('button:has-text("查看答卷")').first().click();
    await page.waitForTimeout(1500);
    console.log('=== 4xx 请求 ===');
    bad.forEach(b => console.log(' ', b));
    // 页面是否显示错误
    const err = await page.evaluate(() => {
      const t = document.body.textContent;
      const m = t.match(/页面出错[^。\n]{0,80}/);
      return m ? m[0] : null;
    });
    console.log('页面错误提示:', err);
    await page.screenshot({ path: '../ui_shots/bug-view-answer-422.png', fullPage: true });
  }
  await browser.close();
})();
