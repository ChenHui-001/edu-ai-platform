const { chromium } = require('playwright-core');
const fs = require('fs');
const CRED = JSON.parse(fs.readFileSync('C:/Users/王/AppData/Local/Temp/tea1_login.json', 'utf-8'));
(async () => {
  const browser = await chromium.launch({ channel: 'msedge', headless: true });
  const page = await (await browser.newContext()).newPage();
  await page.goto('http://localhost:5173/login', { waitUntil: 'domcontentloaded' });
  // 直接拉取 Vite 编译后的 ClassAnalysis 模块
  const mod = await page.evaluate(async () => {
    const r = await fetch('/src/views/teacher/ClassAnalysis.vue');
    return await r.text();
  });
  const i = mod.indexOf('const _d');
  console.log('contains fix:', i >= 0);
  console.log('---onMounted 片段---');
  const j = mod.indexOf('onMounted');
  console.log(mod.slice(j, j + 400));
  await browser.close();
})();
