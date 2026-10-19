const { chromium } = require('playwright-core');
const fs = require('fs');
const CRED = JSON.parse(fs.readFileSync('C:/Users/王/AppData/Local/Temp/tea1_login.json', 'utf-8'));
(async () => {
  const browser = await chromium.launch({ channel: 'msedge', headless: true });
  const page = await (await browser.newContext({ viewport: { width: 1440, height: 900 } })).newPage();
  page.on('response', async r => {
    if (r.url().includes('/api/')) {
      let body = '';
      try { body = (await r.text()).slice(0, 150); } catch (e) {}
      console.log('API', r.status(), r.url().replace('http://localhost:5173', ''), '|', body);
    }
  });
  await page.goto('http://localhost:5173/login', { waitUntil: 'domcontentloaded' });
  await page.evaluate(([t, u]) => {
    localStorage.setItem('access_token', t);
    localStorage.setItem('user', u);
  }, [CRED.access_token, JSON.stringify(CRED.user)]);
  await page.goto('http://localhost:5173/teacher/analysis', { waitUntil: 'networkidle', timeout: 20000 });
  await page.waitForTimeout(2000);
  const state = await page.evaluate(() => ({
    path: location.pathname,
    selects: document.querySelectorAll('.el-select').length,
    statCards: document.querySelectorAll('.stat-card').length,
    canvas: document.querySelectorAll('canvas').length,
    empty: document.querySelector('.el-empty__description')?.textContent || null
  }));
  console.log('STATE:', JSON.stringify(state));
  await browser.close();
})();
