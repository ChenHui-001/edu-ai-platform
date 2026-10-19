const { chromium } = require('playwright-core');
const fs = require('fs');
const S = JSON.parse(fs.readFileSync('C:/Users/王/AppData/Local/Temp/stu_login.json', 'utf-8'));
(async () => {
  const browser = await chromium.launch({ channel: 'msedge', headless: true });
  const page = await (await browser.newContext({ viewport: { width: 1440, height: 900 } })).newPage();
  page.on('pageerror', e => console.log('PAGEERROR:', String(e).slice(0, 200)));
  await page.goto('http://localhost:5173/login', { waitUntil: 'domcontentloaded' });
  await page.evaluate(([t, u]) => {
    localStorage.setItem('access_token', t);
    localStorage.setItem('user', u);
  }, [S.access_token, JSON.stringify(S.user)]);
  await page.goto('http://localhost:5173/student/exam/2', { waitUntil: 'networkidle', timeout: 20000 });
  await page.waitForTimeout(2000);

  const info = await page.evaluate(() => {
    const cards = document.querySelectorAll('.q-card');
    const navs = document.querySelectorAll('.nav-item');
    // 找滚动容器
    const scrollers = [];
    document.querySelectorAll('*').forEach(el => {
      if (el.scrollHeight > el.clientHeight + 50 && ['auto', 'scroll'].includes(getComputedStyle(el).overflowY)) {
        scrollers.push(`${el.tagName}.${el.className.toString().slice(0, 40)} h=${el.clientHeight} sh=${el.scrollHeight}`);
      }
    });
    return {
      cards: cards.length, navs: navs.length,
      currentNav: document.querySelector('.nav-item.current')?.textContent,
      scrollers: scrollers.slice(0, 5),
      cardTops: Array.from(cards).slice(0, 3).map(c => Math.round(c.getBoundingClientRect().top)),
    };
  });
  console.log('初始:', JSON.stringify(info, null, 1));

  // 手动滚到第 3 题位置
  const r = await page.evaluate(() => {
    const c = document.querySelectorAll('.q-card')[2];
    c.scrollIntoView({ block: 'start' });
    return { afterScrollTop: Math.round(c.getBoundingClientRect().top) };
  });
  await page.waitForTimeout(800);
  const after = await page.evaluate(() => ({
    currentNav: document.querySelector('.nav-item.current')?.textContent,
    cardTops: Array.from(document.querySelectorAll('.q-card')).slice(0, 4).map(c => Math.round(c.getBoundingClientRect().top)),
  }));
  console.log('滚动后:', JSON.stringify({ ...r, ...after }));
  await browser.close();
})();
