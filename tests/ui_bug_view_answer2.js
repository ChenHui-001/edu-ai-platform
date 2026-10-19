// 验证「查看答卷」修复：任务管理 → 提交抽屉 → 查看答卷
const { chromium } = require('playwright-core');
const fs = require('fs');
const T = JSON.parse(fs.readFileSync('C:/Users/王/AppData/Local/Temp/tea1_login.json', 'utf-8'));
(async () => {
  const browser = await chromium.launch({ channel: 'msedge', headless: true });
  const page = await (await browser.newContext({ viewport: { width: 1440, height: 900 } })).newPage();
  const bad = [];
  page.on('response', r => { if (r.status() >= 400) bad.push(`${r.status()} ${r.url().slice(-60)}`); });
  page.on('pageerror', e => console.log('PAGEERROR:', String(e).slice(0, 150)));

  await page.goto('http://localhost:5173/login', { waitUntil: 'domcontentloaded' });
  await page.evaluate(([t, u]) => {
    localStorage.setItem('access_token', t);
    localStorage.setItem('user', u);
  }, [T.access_token, JSON.stringify(T.user)]);
  await page.goto('http://localhost:5173/teacher/tasks', { waitUntil: 'networkidle', timeout: 20000 });
  await page.waitForTimeout(1500);

  const rows = await page.locator('.el-table__body-wrapper .el-table__row').count();
  console.log('任务行数:', rows);
  if (!rows) { console.log('无任务数据，无法验证'); await browser.close(); return; }

  // 打开「提交情况」抽屉（找按钮文案）
  const btnTexts = await page.locator('.el-table__body-wrapper .el-table__row').first()
    .locator('button').allTextContents();
  console.log('行内按钮:', JSON.stringify(btnTexts));

  const subBtn = page.locator('button:has-text("提交"), button:has-text("答卷情况"), button:has-text("详情")').first();
  if (await subBtn.count()) {
    await subBtn.click();
    await page.waitForTimeout(1500);
    const subs = await page.locator('.el-drawer .el-table__row').count();
    console.log('抽屉内提交行数:', subs);
    const subRowText = subs ? (await page.locator('.el-drawer .el-table__row').first().textContent()) : '';
    console.log('提交行:', subRowText.replace(/\s+/g, ' ').slice(0, 120));

    // 点「查看答卷」
    const va = page.locator('.el-drawer button:has-text("查看答卷")').first();
    if (await va.count()) {
      await va.click();
      await page.waitForTimeout(1500);
      const st = await page.evaluate(() => ({
        dialogOpen: !!document.querySelector('.el-dialog'),
        items: document.querySelectorAll('.el-dialog .answer-item, .el-dialog .q-item').length,
        bodyText: document.body.textContent.slice(0, 200),
      }));
      const has422 = await page.evaluate(() => document.body.textContent.includes('422'));
      console.log('答卷弹窗:', JSON.stringify(st));
      console.log('422 错误:', has422);
      console.log('4xx 请求:', bad.length ? bad : '(无)');
      await page.screenshot({ path: '../ui_shots/bug-view-answer-fixed.png', fullPage: true });
    } else {
      console.log('未找到「查看答卷」按钮');
    }
  } else {
    console.log('未找到提交情况按钮');
  }
  await browser.close();
})();
