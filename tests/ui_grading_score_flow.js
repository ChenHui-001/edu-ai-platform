// UI 级验证：批改中心页面改分→保存→回读（模拟教师真实操作路径）
const { chromium } = require('playwright-core');
const fs = require('fs');
const T = JSON.parse(fs.readFileSync('C:/Users/王/AppData/Local/Temp/tea1_login.json', 'utf-8'));
(async () => {
  const browser = await chromium.launch({ channel: 'msedge', headless: true });
  const page = await (await browser.newContext({ viewport: { width: 1440, height: 900 } })).newPage();
  const errs = [];
  page.on('pageerror', e => errs.push(String(e).slice(0, 200)));

  await page.goto('http://localhost:5173/login', { waitUntil: 'domcontentloaded' });
  await page.evaluate(([t, u]) => {
    localStorage.setItem('access_token', t);
    localStorage.setItem('user', u);
  }, [T.access_token, JSON.stringify(T.user)]);

  // 当前唯一提交已是 fully_graded（score=100）。include_graded 场景前端没传，
  // 直接调 detail 验证 UI 输入联动：打开批改详情页
  await page.goto('http://localhost:5173/teacher/grading?submission=1', { waitUntil: 'networkidle', timeout: 20000 });
  await page.waitForTimeout(1500);

  // 找所有得分输入框（el-input-number input）
  const inputs = page.locator('.el-input-number input');
  const n = await inputs.count();
  console.log('得分输入框数量:', n);
  if (!n) { console.log('页面无输入框（可能列表为空）'); await page.screenshot({ path: '../ui_shots/grading-ui-empty.png', fullPage: true }); await browser.close(); return; }

  // 记录修改前总分
  const before = await page.locator('b.total').textContent().catch(() => '?');
  console.log('修改前总分:', before);

  // 把第 1 题得分改为 3（原 10/10）
  await inputs.first().fill('3');
  await page.waitForTimeout(500);
  const after1 = await page.locator('b.total').textContent().catch(() => '?');
  console.log('第1题改为3后总分:', after1, '(应为', Number(before) - 10 + 3, ')');

  // 第 2 题改为 5，确认不联动
  await inputs.nth(1).fill('5');
  await page.waitForTimeout(500);
  const after2 = await page.locator('b.total').textContent().catch(() => '?');
  console.log('第2题改为5后总分:', after2, '(应为', Number(before) - 10 - 15 + 3 + 5, ')');

  // 点保存
  await page.click('button:has-text("保存")');
  await page.waitForTimeout(2000);
  const saved = await page.evaluate(() =>
    !!Array.from(document.querySelectorAll('.el-message')).find(m => m.textContent.includes('保存')));

  // API 回读验证真实落库
  const verify = await page.evaluate(async () => {
    const r = await fetch('/api/v1/grading/submissions/1', {
      headers: { Authorization: 'Bearer ' + localStorage.getItem('access_token') } });
    const j = await r.json();
    return { score: j.data?.score, status: j.data?.status };
  });
  console.log('保存提示出现:', saved, '| 回读: score=', verify.score, 'status=', verify.status);
  console.log('pageerrors:', errs.length, errs.slice(0, 2));
  await page.screenshot({ path: '../ui_shots/grading-ui-score-fixed.png', fullPage: true });
  await browser.close();
})();
