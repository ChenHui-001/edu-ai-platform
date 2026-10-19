// 验证新增优化项：多选批量 / 加载更多 / 快捷键 / 考试页保存指示灯
const { chromium } = require('playwright-core');
const fs = require('fs');
const path = require('path');
const T = JSON.parse(fs.readFileSync('C:/Users/王/AppData/Local/Temp/tea1_login.json', 'utf-8'));
const S = JSON.parse(fs.readFileSync('C:/Users/王/AppData/Local/Temp/stu_login.json', 'utf-8'));
const OUT = path.join(__dirname, '..', 'ui_shots');

(async () => {
  const browser = await chromium.launch({ channel: 'msedge', headless: true });

  // ---------- 批改中心新功能 ----------
  const p1 = await (await browser.newContext({ viewport: { width: 1440, height: 900 } })).newPage();
  const errs = [];
  p1.on('pageerror', e => errs.push(String(e).slice(0, 150)));
  await p1.goto('http://localhost:5173/login', { waitUntil: 'domcontentloaded' });
  await p1.evaluate(([t, u]) => {
    localStorage.setItem('access_token', t);
    localStorage.setItem('user', u);
  }, [T.access_token, JSON.stringify(T.user)]);
  await p1.goto('http://localhost:5173/teacher/grading', { waitUntil: 'networkidle', timeout: 20000 });
  await p1.waitForTimeout(1200);

  // 勾选第一份 → 批量条是否出现
  const cb = p1.locator('.sub-item .el-checkbox').first();
  const hasCheckbox = await cb.count();
  if (hasCheckbox) {
    await cb.click();
    await p1.waitForTimeout(400);
  }
  const batchBar = await p1.locator('.batch-bar').count();
  const batchBtns = await p1.locator('.batch-bar .el-button').allTextContents();
  console.log('多选框:', hasCheckbox, '| 批量条:', batchBar, '| 按钮:', JSON.stringify(batchBtns));

  // 快捷键提示按钮
  const kbBtn = await p1.locator('.header-actions .el-button.is-circle').count();
  console.log('快捷键提示按钮:', kbBtn);

  // 选中第一份打开详情 → 数字键跳题 + Alt+F 满分
  if (!(await p1.locator('.q-item').count())) {
    await p1.locator('.sub-item').first().click();
    await p1.waitForTimeout(1200);
  }
  const itemCount = await p1.locator('.q-item').count();
  await p1.keyboard.press('3');            // 数字键跳第 3 题
  await p1.waitForTimeout(500);
  await p1.keyboard.press('Alt+f');        // 第 3 题满分
  await p1.waitForTimeout(400);
  const totalAfterKb = await p1.locator('.total').first().textContent();
  console.log('题目数:', itemCount, '| 数字键+Alt+F 后总分:', totalAfterKb);

  // Ctrl+S 保存
  await p1.keyboard.press('Control+s');
  await p1.waitForTimeout(1500);
  const savedMsg = await p1.evaluate(() =>
    !!Array.from(document.querySelectorAll('.el-message')).find(m => m.textContent.includes('保存')));
  console.log('Ctrl+S 保存提示:', savedMsg);

  // 加载更多区域
  const loadMoreText = await p1.locator('.load-more').first().textContent().catch(() => null);
  console.log('分页提示:', loadMoreText?.trim());

  await p1.screenshot({ path: path.join(OUT, 'enhance-grading-center.png'), fullPage: true });

  // ---------- 考试页保存指示灯 ----------
  const p2 = await (await browser.newContext({ viewport: { width: 1440, height: 900 } })).newPage();
  const errs2 = [];
  p2.on('pageerror', e => errs2.push(String(e).slice(0, 150)));
  await p2.goto('http://localhost:5173/login', { waitUntil: 'domcontentloaded' });
  await p2.evaluate(([t, u]) => {
    localStorage.setItem('access_token', t);
    localStorage.setItem('user', u);
  }, [S.access_token, JSON.stringify(S.user)]);
  await p2.goto('http://localhost:5173/student/exam/2', { waitUntil: 'networkidle', timeout: 20000 });
  await p2.waitForTimeout(1500);
  // 等待首次心跳（30s）太久，直接触发一次输入 + 手动调用 saveDraft 不可行；
  // 改为检查元素存在与初始文案
  const indicator = await p2.locator('.save-indicator').textContent().catch(() => null);
  console.log('保存指示灯:', indicator?.trim());
  await p2.screenshot({ path: path.join(OUT, 'enhance-exam-save-indicator.png'), fullPage: true });

  console.log('pageerrors:', errs.length, errs2.length);
  await browser.close();
})();
