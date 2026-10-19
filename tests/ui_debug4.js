const { chromium } = require('playwright-core');
const fs = require('fs');
const CRED = JSON.parse(fs.readFileSync('C:/Users/王/AppData/Local/Temp/tea1_login.json', 'utf-8'));
(async () => {
  const browser = await chromium.launch({ channel: 'msedge', headless: true });
  const page = await (await browser.newContext()).newPage();
  page.on('response', r => { if (r.status() >= 400) console.log('HTTP', r.status(), r.url()); });
  page.on('pageerror', e => console.log('PAGEERROR:', String(e).slice(0, 300)));
  page.on('console', m => { if (m.type() === 'error' || m.type() === 'warning') console.log('CONSOLE', m.type(), m.text().slice(0, 200)); });
  await page.goto('http://localhost:5173/login', { waitUntil: 'domcontentloaded' });
  await page.evaluate(([t, u]) => {
    localStorage.setItem('access_token', t);
    localStorage.setItem('user', u);
  }, [CRED.access_token, JSON.stringify(CRED.user)]);
  await page.goto('http://localhost:5173/teacher/analysis', { waitUntil: 'networkidle', timeout: 20000 });
  await page.waitForTimeout(2000);
  await browser.close();
})();
