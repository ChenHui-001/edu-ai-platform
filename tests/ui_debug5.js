const { chromium } = require('playwright-core');
const fs = require('fs');
const CRED = JSON.parse(fs.readFileSync('C:/Users/王/AppData/Local/Temp/tea1_login.json', 'utf-8'));
(async () => {
  const browser = await chromium.launch({ channel: 'msedge', headless: true });
  const page = await (await browser.newContext({ viewport: { width: 1440, height: 900 } })).newPage();
  const errs = [];
  page.on('console', m => { if (m.type() === 'error') errs.push(m.text().slice(0, 400)); });
  page.on('pageerror', e => errs.push('PAGEERROR: ' + String(e).slice(0, 400)));
  await page.goto('http://localhost:5173/login', { waitUntil: 'domcontentloaded' });
  await page.evaluate(([t, u]) => {
    localStorage.setItem('access_token', t);
    localStorage.setItem('user', u);
  }, [CRED.access_token, JSON.stringify(CRED.user)]);
  await page.goto('http://localhost:5173/teacher/analysis', { waitUntil: 'networkidle' });
  await page.waitForTimeout(2500);
  console.log('=== 全部错误 ===');
  errs.forEach((e, i) => console.log(`[${i}]`, e, '\n'));
  await browser.close();
})();
