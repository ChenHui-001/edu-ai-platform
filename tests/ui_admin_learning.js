// 管理员身份验证学习中心访问控制（UI 层）
const { chromium } = require('playwright-core');
const fs = require('fs');
const path = require('path');
const A = JSON.parse(fs.readFileSync('C:/Users/王/AppData/Local/Temp/admin_login.json', 'utf-8'));
const OUT = path.join(__dirname, '..', 'ui_shots');

(async () => {
  const browser = await chromium.launch({ channel: 'msedge', headless: true });
  const page = await (await browser.newContext({ viewport: { width: 1440, height: 900 } })).newPage();
  const errs = [];
  page.on('pageerror', e => errs.push(String(e).slice(0, 150)));
  page.on('response', r => { if (r.status() >= 400) errs.push(`HTTP ${r.status()} ${r.url().slice(-60)}`); });

  await page.goto('http://localhost:5173/login', { waitUntil: 'domcontentloaded' });
  await page.evaluate(([t, u]) => {
    localStorage.setItem('access_token', t);
    localStorage.setItem('user', u);
  }, [A.access_token, JSON.stringify(A.user)]);

  await page.goto('http://localhost:5173/dashboard', { waitUntil: 'networkidle', timeout: 20000 });
  await page.waitForTimeout(1500);

  // 1) 菜单中是否出现「学习中心」分组
  const menuGroups = await page.evaluate(() =>
    Array.from(document.querySelectorAll('.el-sub-menu__title, .menu-group-title, .el-menu-item'))
      .map(x => x.textContent.trim()).filter(Boolean).slice(0, 40));
  console.log('菜单项:', JSON.stringify(menuGroups));
  console.log('含「学习中心」:', menuGroups.some(x => x.includes('学习中心')));

  // 2) 直接访问学生页面（应被守卫重定向）
  const routes = ['/student/practice', '/student/wrong', '/student/notes', '/student/report', '/student/scores'];
  for (const r of routes) {
    errs.length = 0;
    await page.goto('http://localhost:5173' + r, { waitUntil: 'networkidle', timeout: 20000 }).catch(() => {});
    await page.waitForTimeout(900);
    const info = await page.evaluate(() => ({
      path: location.pathname,
      title: document.querySelector('.page-title')?.textContent?.trim()
        || document.querySelector('h2')?.textContent?.trim() || '',
    }));
    console.log(`${r} -> ${info.path} | ${info.title} | errs=${errs.length}`);
  }

  // 3) 学生成绩中心接口（admin 直接调）
  const api = await page.evaluate(async () => {
    const tk = localStorage.getItem('access_token');
    const out = {};
    for (const p of ['/api/v1/learning/wrong-questions', '/api/v1/task/my/scores',
                     '/api/v1/report/student/overview']) {
      const r = await fetch(p + '?page_size=3', { headers: { Authorization: 'Bearer ' + tk } });
      const j = await r.json().catch(() => ({}));
      out[p] = `${r.status} success=${j.success} total=${(j.data || {}).total ?? '-'}`;
    }
    return out;
  });
  console.log('admin 直达 API:', JSON.stringify(api, null, 1));

  await page.screenshot({ path: path.join(OUT, 'admin-learning-access.png'), fullPage: true });
  await browser.close();
})();
