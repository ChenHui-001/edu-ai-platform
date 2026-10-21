import { createApp } from 'vue'
import { createPinia } from 'pinia'
import ElementPlus, { ElMessage } from 'element-plus'
import zhCn from 'element-plus/es/locale/lang/zh-cn'
import * as ElementPlusIconsVue from '@element-plus/icons-vue'
import 'element-plus/dist/index.css'

import App from './App.vue'
import router from './router'
import './styles/index.css'

const app = createApp(App)

for (const [key, component] of Object.entries(ElementPlusIconsVue)) {
  app.component(key, component)
}

// 全局错误捕获：组件 setup / 渲染异常此前只会让内容区白屏、无任何提示，
// 排查成本极高。现将错误显式呈现（顶部红条 + 提示），并保留 console 输出。
//
// 但**业务错误不能走这里**：request.js 拦截器已经 ElMessage 过一次，
// 组件里 await 未 catch 时 rejection 会冒泡到这里，于是用户看到
// 「该题目已被 6 份试卷引用」后面又跟一句「页面出错：Request failed with
// status code 400」，顶部还挂一条不消失的红条 —— 把可预期的业务校验
// 伪装成前端崩溃，既误导用户也掩盖真问题。
// request.js 抛出的错误都带 __handled 标记，axios 原生错误靠 isAxiosError 兜底识别。
function isBusinessError(err) {
  return !!err && (err.__handled === true || err.isAxiosError === true || !!err.response)
}

app.config.errorHandler = (err, instance, info) => {
  if (isBusinessError(err)) {
    // 已提示过用户，只留控制台痕迹便于排查
    console.warn('[app error][已忽略:业务错误]', err?.message || err, info)
    return
  }
  console.error('[app error]', err, info)
  const msg = err?.message || String(err)
  ElMessage.error(`页面出错：${msg.slice(0, 120)}`)
  try {
    let el = document.getElementById('global-error-bar')
    if (!el) {
      el = document.createElement('div')
      el.id = 'global-error-bar'
      el.style.cssText = 'position:fixed;top:0;left:0;right:0;z-index:99999;' +
        'background:#fef0f0;color:#f56c6c;border-bottom:1px solid #fbc4c4;' +
        'padding:10px 16px;font-size:13px;font-family:monospace;white-space:pre-wrap'
      document.body.appendChild(el)
    }
    el.textContent = `页面运行时错误：${msg}`
  } catch { /* DOM 不可用时忽略 */ }
}

router.onError((err) => {
  console.error('[router error]', err)
  ElMessage.error(`路由加载失败：${String(err?.message || err).slice(0, 120)}`)
})

app.use(createPinia())
app.use(router)
app.use(ElementPlus, { locale: zhCn })
app.mount('#app')