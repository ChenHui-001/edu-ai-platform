// 全站冒烟：res.data.data 修复后的受影响页面抽查
const { chromium } = require('playwright-core');
const fs = require('fs');
const A = JSON.parse(fs.readFileSync('C:/Users/王/AppData/Local/Temp/admin_login.json', 'utf-8'));
const T = JSON.parse(fs.readFileSync('C:/Users/王/AppData/Local/Temp/tea1_login.json', 'utf-8'));

(async () => {
  const browser = await chromium.launch({ channel: 'msedge', headless: true });

  async function smoke(cred, pages, label) {
    const page = await (await browser.newContext({ viewport: { width: 1440, height: 900 } })).newPage();
    const errs = [];
    page.on('pageerror', e => errs.push('PAGEERROR: ' + String(e).slice(0, 150)));
    await page.goto('http://localhost:5173/login', { waitUntil: 'domcontentloaded' });
    await page.evaluate(([t, u]) => {
      localStorage.setItem('access_token', t);
      localStorage.setItem('user', u);
    }, [cred.access_token, JSON.stringify(cred.user)]);

    for (const p of pages) {
      errs.length = 0;
      let rows = 0, empty = 0;
      await page.goto('http://localhost:5173' + p.url, { waitUntil: 'networkidle', timeout: 20000 }).catch(() => {});
      await page.waitForTimeout(1200);
      rows = await page.locator('.el-table__body-wrapper .el-table__row').count();
      empty = await page.locator('.el-empty').count();
      const tag = errs.length ? 'ERR:' + errs[0].slice(0, 80) : 'OK';
      console.log(`${label} ${p.url} | rows=${rows} empty=${empty} | ${tag}`);
    }
    await page.close();
  }

  await smoke(A, [
    { url: '/admin/users' },
    { url: '/admin/agent-logs' },
    { url: '/admin/ai-config' },
    { url: '/admin/attachments' },
    { url: '/admin/logs' },
    { url: '/admin/roles' },
    { url: '/admin/settings' },
    { url: '/admin/reports' },
    { url: '/admin/jobs' },
    { url: '/admin/registration' },
  ], 'ADMIN');

  await smoke(T, [
    { url: '/teacher/papers' },
    { url: '/teacher/tasks' },
    { url: '/teacher/grading?submission=1' },
  ], 'TEACHER');

  await browser.close();
})();
