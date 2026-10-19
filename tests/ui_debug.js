const { chromium } = require('playwright-core');
const fs = require('fs');
const CRED = JSON.parse(fs.readFileSync('C:/Users/王/AppData/Local/Temp/tea1_login.json', 'utf-8'));
(async () => {
  const browser = await chromium.launch({ channel: 'msedge', headless: true });
  const page = await (await browser.newContext({ viewport: { width: 1440, height: 900 } })).newPage();
  page.on('response', r => { if (r.status() >= 400) console.log('HTTP', r.status(), r.url().slice(0, 110)); });
  page.on('console', m => { if (m.type() === 'error') console.log('CONSOLE', m.text().slice(0, 140)); });
  await page.goto('http://localhost:5173/login', { waitUntil: 'domcontentloaded' });
  await page.evaluate(([t, u]) => {
    localStorage.setItem('access_token', t);
    localStorage.setItem('user', u);
  }, [CRED.access_token, JSON.stringify(CRED.user)]);
  await page.goto('http://localhost:5173/teacher/analysis', { waitUntil: 'networkidle', timeout: 20000 });
  await page.waitForTimeout(1500);
  // 页面内直接调 classes 接口看结果
  const api = await page.evaluate(async () => {
    const r = await fetch('/api/v1/edu/classes?page_size=100', {
      headers: { Authorization: 'Bearer ' + localStorage.getItem('access_token') }
    });
    const j = await r.json().catch(() => null);
    return { status: r.status, ok: j && j.success, n: j && j.data ? (j.data.items || j.data).length : null };
  });
  console.log('CLASSES API:', JSON.stringify(api));
  const ls = await page.evaluate(() => ({
    hasToken: !!localStorage.getItem('access_token'),
    user: (localStorage.getItem('user') || '').slice(0, 120),
    path: location.pathname
  }));
  console.log('LS:', JSON.stringify(ls));
  await browser.close();
})();
