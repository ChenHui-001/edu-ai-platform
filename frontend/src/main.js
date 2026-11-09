import { createApp } from 'vue'
import { createPinia } from 'pinia'
import { ElMessage } from 'element-plus'
// Element Plus 已改为按需引入：模板组件的样式由 unplugin-vue-components 注入，
// 但 ElMessage / ElMessageBox 是函数式调用、不经过模板 resolver，样式必须显式引入。
import 'element-plus/es/components/message/style/css'
import 'element-plus/es/components/message-box/style/css'

import App from './App.vue'
import router from './router'
import './styles/index.css'

const app = createApp(App)

// 全局错误捕获：组件 setup / 渲染异常此前只会让内容区白屏、无任何提示，
// 排查成本极高。现将错误显式呈现（顶部红条 + 提示），并保留 console 输出。
//
// 但**业务错误不能走这里**：request.js 拦截器已经 ElMessage 过一次，
// 组件里 await 未 catch 时 rejection 会冒泡到这里，于是用户看到
// 「该题目已被 6 份试卷引用」后面又跟一句「页面出错：Request failed with
// status code 400」，顶部还挂一条不消失的红条 —— 把可预期的业务校验
// 伪装成前端崩溃，既误导用户也掩盖真问题。
// request.js 抛出的错误都带 __handled 标记，axios 原生错误靠 isAxiosError 兜底识别。
//
// ⚠️ Element Plus 的 ElMessageBox 被用户「取消 / 关闭」时，reject 的是**字符串**
// 'cancel' / 'close'，不是 Error。那是用户主动放弃操作，绝非前端崩溃 —— 全站
// 有 43 处 ElMessageBox，其中相当一部分没有 try 保护，一旦落进这里，用户每次点
// 「取消」都会看到「页面运行时错误： cancel」+ 一条盖住 60px 页头、切路由也不消失
// 的红条，体感就是「这系统会崩」。因此：**任何非对象类型的 rejection 一律视为
// 用户取消**（业务异常统一是 Error / axios 错误，不会是裸字符串）。
const CANCEL_REASONS = ['cancel', 'close']

function isBusinessError(err) {
  if (err === undefined || err === null) return true
  if (typeof err !== 'object') {
    if (!CANCEL_REASONS.includes(err)) {
      console.warn('[app error][非 Error 的 rejection]', err)
    }
    return true
  }
  return err.__handled === true || err.isAxiosError === true || !!err.response
}

const ERROR_BAR_ID = 'global-error-bar'
const ERROR_BAR_TTL_MS = 10000
let errorBarTimer = null

/** 关闭红条。致命错误横幅不能是「只能刷新页面才消失」的永久遮挡。 */
function clearErrorBar() {
  if (errorBarTimer) {
    clearTimeout(errorBarTimer)
    errorBarTimer = null
  }
  const el = document.getElementById(ERROR_BAR_ID)
  if (el) el.remove()
}

function showErrorBar(msg) {
  let el = document.getElementById(ERROR_BAR_ID)
  if (!el) {
    el = document.createElement('div')
    el.id = ERROR_BAR_ID
    el.style.cssText = 'position:fixed;top:0;left:0;right:0;z-index:99999;' +
      'display:flex;align-items:flex-start;gap:12px;' +
      'background:#fef0f0;color:#f56c6c;border-bottom:1px solid #fbc4c4;' +
      'padding:8px 16px;font-size:13px;font-family:monospace;white-space:pre-wrap'
    const text = document.createElement('span')
    text.id = `${ERROR_BAR_ID}-text`
    text.style.cssText = 'flex:1;min-width:0'
    const close = document.createElement('button')
    close.type = 'button'
    close.textContent = '×'
    close.setAttribute('aria-label', '关闭错误提示')
    close.style.cssText = 'flex:0 0 auto;border:0;background:transparent;' +
      'color:#f56c6c;font-size:18px;line-height:1;cursor:pointer;padding:0 4px'
    close.addEventListener('click', clearErrorBar)
    el.appendChild(text)
    el.appendChild(close)
    document.body.appendChild(el)
  }
  const text = document.getElementById(`${ERROR_BAR_ID}-text`)
  if (text) text.textContent = `页面运行时错误：${msg}`
  if (errorBarTimer) clearTimeout(errorBarTimer)
  errorBarTimer = setTimeout(clearErrorBar, ERROR_BAR_TTL_MS)
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
    showErrorBar(msg)
  } catch { /* DOM 不可用时忽略 */ }
}

router.onError((err) => {
  console.error('[router error]', err)
  ElMessage.error(`路由加载失败：${String(err?.message || err).slice(0, 120)}`)
})

// 切路由时清掉红条：用户已经离开出问题的页面，错误横幅没有理由继续盖着页头
router.afterEach(() => clearErrorBar())

app.use(createPinia())
app.use(router)
app.mount('#app')