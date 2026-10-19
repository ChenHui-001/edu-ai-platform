// 复现教学报表「选择任务报错」
const { chromium } = require('playwright-core');
const fs = require('fs');
const CRED = JSON.parse(fs.readFileSync('C:/Users/王/AppData/Local/Temp/admin_login.json', 'utf-8'));
(async () => {
  // 用 teacher1
  const T = JSON.parse(fs.readFileSync('C:/Users/王/AppData/Local/Temp/tea1_login.json', 'utf-8'));
  const browser = await chromium.launch({ channel: 'msedge', headless: true });
  const page = await (await browser.newContext({ viewport: { width: 1440, height: 900 } })).newPage();
  const errs = [];
  page.on('pageerror', e => errs.push('PAGEERROR: ' + String(e).slice(0, 250)));
  page.on('console', m => { if (m.type() === 'error') errs.push('CONSOLE: ' + m.text().slice(0, 250)); });
  page.on('response', r => { if (r.status() >= 400) errs.push(`HTTP ${r.status()} ${r.url().slice(-80)}`); });

  await page.goto('http://localhost:5173/login', { waitUntil: 'domcontentloaded' });
  await page.evaluate(([t, u]) => {
    localStorage.setItem('access_token', t);
    localStorage.setItem('user', u);
  }, [T.access_token, JSON.stringify(T.user)]);

  await page.goto('http://localhost:5173/teacher/reports', { waitUntil: 'networkidle', timeout: 20000 });
  await page.waitForTimeout(1500);
  errs.length = 0;  // 清掉加载期噪音，只看选任务后的错

  // 打开任务下拉并选第一个
  const taskSelect = page.locator('.el-select').nth(1);  // 第2个下拉=任务
  await taskSelect.click();
  await page.waitForTimeout(600);
  const opt = page.locator('.el-select-dropdown:visible .el-select-dropdown__item').first();
  const optText = await opt.textContent().catch(() => null);
  console.log('选中任务:', optText?.trim());
  await opt.click();
  await page.waitForTimeout(2000);

  console.log('=== 选择任务后的错误 ===');
  errs.forEach((e, i) => console.log(`[${i}]`, e));
  if (!errs.length) console.log('(无错误)');
  await page.screenshot({ path: '../ui_shots/report-task-error.png', fullPage: true });
  await browser.close();
})();
