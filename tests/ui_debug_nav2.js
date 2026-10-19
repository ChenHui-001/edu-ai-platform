const { chromium } = require('playwright-core');
const fs = require('fs');
const S = JSON.parse(fs.readFileSync('C:/Users/王/AppData/Local/Temp/stu_login.json', 'utf-8'));
(async () => {
  const browser = await chromium.launch({ channel: 'msedge', headless: true });
  const page = await (await browser.newContext({ viewport: { width: 1440, height: 900 } })).newPage();
  await page.goto('http://localhost:5173/login', { waitUntil: 'domcontentloaded' });
  await page.evaluate(([t, u]) => {
    localStorage.setItem('access_token', t);
    localStorage.setItem('user', u);
  }, [S.access_token, JSON.stringify(S.user)]);
  await page.goto('http://localhost:5173/student/exam/2', { waitUntil: 'networkidle' });
  await page.waitForTimeout(1500);
  // 在页面内直接验证：el-main 上的 scroll 事件是否能收到
  const t = await page.evaluate(() => new Promise(res => {
    const el = document.querySelector('.el-main');
    let got = 0;
    el.addEventListener('scroll', () => { got++; }, { passive: true });
    window.addEventListener('scroll', () => { got += 100; }, true);
    el.scrollTo(0, 800);
    setTimeout(() => res({ got }), 500);
  }));
  console.log('scroll 事件（el-main 直接监听 vs window 捕获）:', JSON.stringify(t));
  await browser.close();
})();
