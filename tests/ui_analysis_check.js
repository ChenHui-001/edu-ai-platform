// 验证学情分析三页在统计口径改造后的渲染
const { chromium } = require('playwright-core');
const fs = require('fs');
const path = require('path');
const A = JSON.parse(fs.readFileSync('C:/Users/王/AppData/Local/Temp/admin_login.json', 'utf-8'));
const T = JSON.parse(fs.readFileSync('C:/Users/王/AppData/Local/Temp/tea1_login.json', 'utf-8'));
const OUT = path.join(__dirname, '..', 'ui_shots');

(async () => {
  const browser = await chromium.launch({ channel: 'msedge', headless: true });

  async function check(cred, label, pages) {
    const page = await (await browser.newContext({ viewport: { width: 1440, height: 900 } })).newPage();
    const errs = [];
    page.on('pageerror', e => errs.push(String(e).slice(0, 140)));
    page.on('console', m => { if (m.type() === 'error') errs.push('C:' + m.text().slice(0, 120)); });
    await page.goto('http://localhost:5173/login', { waitUntil: 'domcontentloaded' });
    await page.evaluate(([t, u]) => {
      localStorage.setItem('access_token', t);
      localStorage.setItem('user', u);
    }, [cred.access_token, JSON.stringify(cred.user)]);

    for (const p of pages) {
      errs.length = 0;
      await page.goto('http://localhost:5173' + p.url, { waitUntil: 'networkidle', timeout: 20000 }).catch(() => {});
      await page.waitForTimeout(1500);
      const info = await page.evaluate(() => ({
        cards: Array.from(document.querySelectorAll('.stat-value, .stat-card .value'))
          .map(x => x.textContent.trim()).slice(0, 8),
        labels: Array.from(document.querySelectorAll('.stat-label, .stat-card .label'))
          .map(x => x.textContent.trim()).slice(0, 8),
        canvas: document.querySelectorAll('canvas').length,
        rows: document.querySelectorAll('.el-table__row').length,
        bodyHasNaN: document.body.textContent.includes('NaN'),
        bodyHasUndef: document.body.textContent.includes('undefined'),
      }));
      console.log(`${label} ${p.url} | 卡=${JSON.stringify(info.cards)} 标签=${JSON.stringify(info.labels)} `
        + `canvas=${info.canvas} rows=${info.rows} NaN=${info.bodyHasNaN} undef=${info.bodyHasUndef} errs=${errs.length}`);
      if (errs.length) console.log('   err:', errs[0]);
      await page.screenshot({ path: path.join(OUT, `analysis-${p.name}.png`), fullPage: true });
    }
    await page.close();
  }

  await check(T, 'TEACHER', [
    { url: '/teacher/analysis', name: 'class' },
    { url: '/teacher/students', name: 'student' },
    { url: '/teacher/reports', name: 'report' },
  ]);
  await check(A, 'ADMIN', [
    { url: '/admin/reports', name: 'admin-report' },
  ]);
  await browser.close();
})();
