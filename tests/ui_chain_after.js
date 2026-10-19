// 优化后 UI 验证：批改中心新布局 + 考试页增强
const { chromium } = require('playwright-core');
const fs = require('fs');
const path = require('path');
const T = JSON.parse(fs.readFileSync('C:/Users/王/AppData/Local/Temp/tea1_login.json', 'utf-8'));
const S = JSON.parse(fs.readFileSync('C:/Users/王/AppData/Local/Temp/stu_login.json', 'utf-8'));
const OUT = path.join(__dirname, '..', 'ui_shots');

(async () => {
  const browser = await chromium.launch({ channel: 'msedge', headless: true });

  // ---------- 批改中心 ----------
  const p1 = await (await browser.newContext({ viewport: { width: 1440, height: 900 } })).newPage();
  const errs1 = [];
  p1.on('pageerror', e => errs1.push(String(e).slice(0, 150)));
  await p1.goto('http://localhost:5173/login', { waitUntil: 'domcontentloaded' });
  await p1.evaluate(([t, u]) => {
    localStorage.setItem('access_token', t);
    localStorage.setItem('user', u);
  }, [T.access_token, JSON.stringify(T.user)]);
  await p1.goto('http://localhost:5173/teacher/grading', { waitUntil: 'networkidle', timeout: 20000 });
  await p1.waitForTimeout(1200);
  const item = p1.locator('.sub-item').first();
  if (await item.count()) { await item.click(); await p1.waitForTimeout(1500); }

  const g = await p1.evaluate(() => {
    const stds = Array.from(document.querySelectorAll('.correct .std')).map(x => x.textContent.trim());
    return {
      stdAnswers: stds,                       // 标准答案必须非空
      stdEmpty: stds.filter(x => !x || x === '—').length,
      quickBtns: document.querySelectorAll('.q-score-panel .el-button').length,
      progressText: document.querySelector('.progress-info span')?.textContent.trim(),
      statusTag: Array.from(document.querySelectorAll('.head-tags .el-tag')).map(x => x.textContent.trim()),
      publishDisabled: (() => {
        const b = Array.from(document.querySelectorAll('button')).find(x => x.textContent.includes('发布成绩'));
        return b ? b.disabled : null;
      })(),
      saveNextBtn: !!Array.from(document.querySelectorAll('button')).find(x => x.textContent.includes('保存并批下一份')),
      timeFormatted: (() => {
        const t = document.querySelector('.sub-item .tip')?.textContent.trim();
        return t && t.length <= 16 && !t.includes('T');
      })(),
      queueFilters: document.querySelectorAll('.queue-filters .el-radio-button').length,
    };
  });
  console.log('批改中心:', JSON.stringify(g, null, 1));
  console.log('pageerrors:', errs1.length);
  await p1.screenshot({ path: path.join(OUT, 'after-grading-center.png'), fullPage: true });

  // 快捷按钮实测：点第1题「零分」→ 总分变化
  const beforeTotal = await p1.locator('.total').first().textContent();
  await p1.locator('.q-score-panel .el-button').first().click();  // 满分
  await p1.waitForTimeout(300);
  const afterFull = await p1.locator('.total').first().textContent();
  await p1.locator('.q-score-panel .el-button').nth(1).click();  // 零分
  await p1.waitForTimeout(300);
  const afterZero = await p1.locator('.total').first().textContent();
  console.log(`快捷按钮: 初始=${beforeTotal} 点满分=${afterFull} 点零分=${afterZero}`);

  // ---------- 考试页 ----------
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
  const e = await p2.evaluate(() => ({
    cdLabel: document.querySelector('.cd-label')?.textContent,
    submitBadge: document.querySelector('.el-badge__content')?.textContent,
    activeNav: document.querySelector('.nav-item.current')?.textContent,
  }));
  console.log('考试页:', JSON.stringify(e));
  // 滚动到第3题验证导航同步
  await p2.evaluate(() => document.querySelectorAll('.q-card')[2].scrollIntoView({ block: 'start' }));
  await p2.waitForTimeout(700);
  const cur = await p2.evaluate(() => document.querySelector('.nav-item.current')?.textContent);
  console.log('滚动到第3题后导航高亮:', cur);
  await p2.screenshot({ path: path.join(OUT, 'after-exam-page.png'), fullPage: true });
  console.log('pageerrors:', errs2.length);

  // 响应式
  await p1.setViewportSize({ width: 1280, height: 900 });
  await p1.waitForTimeout(500);
  const overflow = await p1.evaluate(() =>
    document.documentElement.scrollWidth > document.documentElement.clientWidth + 2);
  console.log('批改中心 1280px 横向溢出:', overflow);

  await browser.close();
})();
