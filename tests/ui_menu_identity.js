// 验证「学习中心」菜单按身份隐藏 + 掌握度空态
const { chromium } = require('playwright-core');
const fs = require('fs');
const path = require('path');
const A = JSON.parse(fs.readFileSync('C:/Users/王/AppData/Local/Temp/admin_login.json', 'utf-8'));
const S = JSON.parse(fs.readFileSync('C:/Users/王/AppData/Local/Temp/stu_login.json', 'utf-8'));
const OUT = path.join(__dirname, '..', 'ui_shots');

async function menusFor(browser, cred, label) {
  const page = await (await browser.newContext({ viewport: { width: 1440, height: 900 } })).newPage();
  const errs = [];
  page.on('pageerror', e => errs.push(String(e).slice(0, 120)));
  await page.goto('http://localhost:5173/login', { waitUntil: 'domcontentloaded' });
  await page.evaluate(([t, u]) => {
    localStorage.setItem('access_token', t);
    localStorage.setItem('user', u);
  }, [cred.access_token, JSON.stringify(cred.user)]);
  await page.goto('http://localhost:5173/dashboard', { waitUntil: 'networkidle', timeout: 20000 });
  await page.waitForTimeout(1500);
  const groups = await page.evaluate(() =>
    Array.from(document.querySelectorAll('.el-sub-menu__title'))
      .map(x => x.textContent.trim()).filter(Boolean));
  const hasLearn = groups.some(g => g.includes('学习中心'));
  console.log(`${label} 菜单分组: ${JSON.stringify(groups)}`);
  console.log(`${label} 含学习中心: ${hasLearn} | errs=${errs.length}`);
  await page.screenshot({ path: path.join(OUT, `menu-${label}.png`), fullPage: false });
  return page;
}

(async () => {
  const browser = await chromium.launch({ channel: 'msedge', headless: true });

  await menusFor(browser, A, 'admin');
  const stuPage = await menusFor(browser, S, 'student');

  // 学生进入掌握图谱（MasteryMap），检查空态
  await stuPage.goto('http://localhost:5173/student/mastery', { waitUntil: 'networkidle', timeout: 20000 });
  await stuPage.waitForTimeout(1500);
  const mm = await stuPage.evaluate(() => ({
    empties: Array.from(document.querySelectorAll('.el-empty__description'))
      .map(x => x.textContent.trim()).slice(0, 3),
    canvas: document.querySelectorAll('canvas').length,
  }));
  console.log('掌握图谱:', JSON.stringify(mm));
  await stuPage.screenshot({ path: path.join(OUT, 'mastery-empty.png'), fullPage: true });

  await browser.close();
})();
