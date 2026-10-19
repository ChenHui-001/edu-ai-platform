const { chromium } = require('playwright-core');
const fs = require('fs');
const CRED = JSON.parse(fs.readFileSync('C:/Users/王/AppData/Local/Temp/tea1_login.json', 'utf-8'));
(async () => {
  const browser = await chromium.launch({ channel: 'msedge', headless: true });
  const page = await (await browser.newContext({ viewport: { width: 1440, height: 900 } })).newPage();
  const errs = [];
  page.on('pageerror', e => errs.push(String(e).slice(0, 120)));
  await page.goto('http://localhost:5173/login', { waitUntil: 'domcontentloaded' });
  await page.evaluate(([t, u]) => {
    localStorage.setItem('access_token', t);
    localStorage.setItem('user', u);
  }, [CRED.access_token, JSON.stringify(CRED.user)]);
  await page.goto('http://localhost:5173/dashboard', { waitUntil: 'networkidle', timeout: 20000 });
  await page.waitForTimeout(2500);
  const canvas = await page.$$eval('canvas', cs => cs.map(c => ({ w: c.width, h: c.height })));
  console.log('DASHBOARD canvas:', JSON.stringify(canvas), '| pageerrors:', errs.length);
  errs.slice(0, 3).forEach(e => console.log('ERR:', e));
  await page.screenshot({ path: '../ui_shots/dashboard-1440.png', fullPage: false });
  await browser.close();
})();
