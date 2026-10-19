// 复测：/teacher/grading?submission=1 直达不再误报「未找到该提交记录」
const { chromium } = require('playwright-core');
const fs = require('fs');
const T = JSON.parse(fs.readFileSync('C:/Users/王/AppData/Local/Temp/tea1_login.json', 'utf-8'));
(async () => {
  const browser = await chromium.launch({ channel: 'msedge', headless: true });
  const page = await (await browser.newContext({ viewport: { width: 1440, height: 900 } })).newPage();
  const msgs = [];
  page.on('console', m => { if (m.type() === 'error' || m.type() === 'warning') msgs.push(m.text().slice(0, 150)); });

  await page.goto('http://localhost:5173/login', { waitUntil: 'domcontentloaded' });
  await page.evaluate(([t, u]) => {
    localStorage.setItem('access_token', t);
    localStorage.setItem('user', u);
  }, [T.access_token, JSON.stringify(T.user)]);

  // 模拟从工作台点批改：带 submission 参数直达
  await page.goto('http://localhost:5173/teacher/grading?submission=1', { waitUntil: 'networkidle', timeout: 20000 });
  await page.waitForTimeout(2000);

  // 检查右侧详情是否渲染（题干/学生名）
  const state = await page.evaluate(() => ({
    hasWarning: !!Array.from(document.querySelectorAll('.el-message')).find(m => m.textContent.includes('未找到')),
    detailStems: Array.from(document.querySelectorAll('.el-card__body')).length,
    studentNameVisible: document.body.textContent.includes('学生731'),
    taskTitleVisible: document.body.textContent.includes('七年级数学单元测试'),
    questionCount: document.body.textContent.includes('题') ? '有题目区' : '无',
  }));
  console.log('详情渲染:', JSON.stringify(state));
  console.log('console 消息:', msgs.length ? msgs : '(无 error/warning)');
  await page.screenshot({ path: '../ui_shots/grading-direct-fixed.png', fullPage: true });
  await browser.close();
})();
