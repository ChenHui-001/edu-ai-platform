// 学科按年级视图 UI 验证
const { chromium } = require('playwright-core');
const fs = require('fs');
const path = require('path');
const CRED = JSON.parse(fs.readFileSync('C:/Users/王/AppData/Local/Temp/admin_login.json', 'utf-8'));
const OUT = path.join(__dirname, '..', 'ui_shots');
fs.mkdirSync(OUT, { recursive: true });

(async () => {
  const browser = await chromium.launch({ channel: 'msedge', headless: true });
  const page = await (await browser.newContext({ viewport: { width: 1440, height: 900 } })).newPage();
  const errs = [];
  page.on('pageerror', e => errs.push(String(e).slice(0, 200)));
  page.on('console', m => { if (m.type() === 'error') errs.push(m.text().slice(0, 200)); });

  await page.goto('http://localhost:5173/login', { waitUntil: 'domcontentloaded' });
  await page.evaluate(([t, u]) => {
    localStorage.setItem('access_token', t);
    localStorage.setItem('user', u);
  }, [CRED.access_token, JSON.stringify(CRED.user)]);

  // 进入学科管理（默认按年级视图）
  await page.goto('http://localhost:5173/admin/subjects', { waitUntil: 'networkidle', timeout: 20000 });
  await page.waitForTimeout(1500);
  const state = await page.evaluate(() => ({
    title: document.querySelector('.page-title')?.textContent,
    gradeItems: document.querySelectorAll('.grade-item').length,
    activeGrade: document.querySelector('.grade-item.active .gname')?.textContent,
    rightRows: document.querySelectorAll('.el-table__body-wrapper .el-table__row').length,
    firstRow: Array.from(document.querySelectorAll('.el-table__body-wrapper .el-table__row')[0]?.querySelectorAll('td') || [])
      .map(c => c.textContent?.trim()).slice(0, 5),
    radioMode: document.querySelectorAll('.el-radio-button__inner').length,
  }));
  console.log('初始按年级视图:', JSON.stringify(state));
  await page.screenshot({ path: path.join(OUT, 'admin-subject-by-grade.png'), fullPage: true });

  // 切换到平铺视图
  await page.click('.el-radio-button:nth-child(2)');
  await page.waitForTimeout(800);
  const flat = await page.evaluate(() => ({
    gradeItems: document.querySelectorAll('.grade-item').length,
    tableRows: document.querySelectorAll('.el-table__body-wrapper .el-table__row').length,
  }));
  console.log('平铺视图:', JSON.stringify(flat));
  await page.screenshot({ path: path.join(OUT, 'admin-subject-flat.png'), fullPage: true });

  // 切回按年级，点另一年级
  await page.click('.el-radio-button:nth-child(1)');
  await page.waitForTimeout(500);
  await page.click('.grade-item:nth-child(3)');  // 点第三个年级
  await page.waitForTimeout(800);
  const switch2 = await page.evaluate(() => ({
    activeGrade: document.querySelector('.grade-item.active .gname')?.textContent,
    rightRows: document.querySelectorAll('.el-table__body-wrapper .el-table__row').length,
    firstRow: Array.from(document.querySelectorAll('.el-table__body-wrapper .el-table__row')[0]?.querySelectorAll('td') || [])
      .map(c => c.textContent?.trim()).slice(0, 4),
  }));
  console.log('切到第3年级:', JSON.stringify(switch2));
  await page.screenshot({ path: path.join(OUT, 'admin-subject-grade3.png'), fullPage: true });

  // 打开跨年级复制弹窗
  await page.click('button:has-text("跨年级复制")');
  await page.waitForTimeout(500);
  const cloneDlg = await page.evaluate(() => ({
    title: document.querySelector('.el-dialog__title')?.textContent,
    checked: document.querySelectorAll('.el-checkbox__input.is-checked').length,
    total: document.querySelectorAll('.el-checkbox__input').length,
  }));
  console.log('复制弹窗:', JSON.stringify(cloneDlg));
  await page.screenshot({ path: path.join(OUT, 'admin-subject-clone-dlg.png'), fullPage: true });

  // 响应式
  await page.keyboard.press('Escape');
  for (const w of [768, 375]) {
    await page.setViewportSize({ width: w, height: 900 });
    await page.goto('http://localhost:5173/admin/subjects', { waitUntil: 'networkidle' });
    await page.waitForTimeout(800);
    const overflow = await page.evaluate(() =>
      document.documentElement.scrollWidth > document.documentElement.clientWidth + 2);
    console.log(`按年级视图 视口 ${w}px: 横向溢出=${overflow}`);
    await page.screenshot({ path: path.join(OUT, `admin-subject-by-grade-${w}.png`), fullPage: true });
  }

  console.log('pageerrors:', errs.length);
  errs.slice(0, 3).forEach(e => console.log(' ERR:', e));
  await browser.close();
})();
