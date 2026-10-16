import { createApp } from 'vue'
import { createPinia } from 'pinia'
import ElementPlus from 'element-plus'
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
// 排查成本极高。这里把错误显式呈现（红条 + 提示），并保留 console 输出。
app.config.errorHandler = (err, instance, info) => {
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

// 全局错误捕获：组件 setup / 渲染异常此前只会让内容区白屏、无任何提示，
// 排查成本极高。这里把错误显式呈现（红条 + 提示），并保留 console 输出。
app.config.errorHandler = (err, instance, info) => {
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
