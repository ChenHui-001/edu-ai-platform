// 全链路现状截图：批改中心 + 考试页
const { chromium } = require('playwright-core');
const fs = require('fs');
const path = require('path');
const T = JSON.parse(fs.readFileSync('C:/Users/王/AppData/Local/Temp/tea1_login.json', 'utf-8'));
const S = JSON.parse(fs.readFileSync('C:/Users/王/AppData/Local/Temp/stu_login.json', 'utf-8'));
const OUT = path.join(__dirname, '..', 'ui_shots');
fs.mkdirSync(OUT, { recursive: true });

(async () => {
  const browser = await chromium.launch({ channel: 'msedge', headless: true });

  // 教师批改中心
  const p1 = await (await browser.newContext({ viewport: { width: 1440, height: 900 } })).newPage();
  await p1.goto('http://localhost:5173/login', { waitUntil: 'domcontentloaded' });
  await p1.evaluate(([t, u]) => {
    localStorage.setItem('access_token', t);
    localStorage.setItem('user', u);
  }, [T.access_token, JSON.stringify(T.user)]);
  await p1.goto('http://localhost:5173/teacher/grading', { waitUntil: 'networkidle', timeout: 20000 });
  await p1.waitForTimeout(1200);
  // 点第一条待批
  const item = p1.locator('.sub-item').first();
  if (await item.count()) { await item.click(); await p1.waitForTimeout(1200); }
  await p1.screenshot({ path: path.join(OUT, 'before-grading-center.png'), fullPage: true });

  // 学生考试页
  const p2 = await (await browser.newContext({ viewport: { width: 1440, height: 900 } })).newPage();
  await p2.goto('http://localhost:5173/login', { waitUntil: 'domcontentloaded' });
  await p2.evaluate(([t, u]) => {
    localStorage.setItem('access_token', t);
    localStorage.setItem('user', u);
  }, [S.access_token, JSON.stringify(S.user)]);
  await p2.goto('http://localhost:5173/student/exam/2', { waitUntil: 'networkidle', timeout: 20000 });
  await p2.waitForTimeout(1500);
  const st = await p2.evaluate(() => ({
    title: document.querySelector('.title')?.textContent,
    navItems: document.querySelectorAll('.nav-item').length,
    qCards: document.querySelectorAll('.q-card').length,
    hasSubmitBtn: !!Array.from(document.querySelectorAll('button')).find(b => b.textContent.includes('交卷')),
  }));
  console.log('考试页:', JSON.stringify(st));
  await p2.screenshot({ path: path.join(OUT, 'before-exam-page.png'), fullPage: true });

  await browser.close();
})();
