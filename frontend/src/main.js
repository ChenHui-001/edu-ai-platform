import { createApp } from 'vue'
import { createPinia } from 'pinia'
import { ElMessage } from 'element-plus'
// Element Plus 已改为按需引入：模板组件的样式由 unplugin-vue-components 注入，
// 但 ElMessage / ElMessageBox 是函数式调用、不经过模板 resolver，样式必须显式引入。
import 'element-plus/es/components/message/style/css'
import 'element-plus/es/components/message-box/style/css'

import App from './App.vue'
import router from './router'
import TableEmpty from './components/TableEmpty.vue'
import { describeError, isBusinessError } from './utils/errors'
import './styles/index.css'

const app = createApp(App)
// 全局注册表格空态：被 29 个页面、65 张表使用，逐页 import 只会把导入区撑长
app.component('TableEmpty', TableEmpty)

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
// ⚠️ 取消语义**只认白名单**：Element Plus 的消息框被用户「取消 / 关闭」时 reject
// 的是字符串 'cancel' / 'close'，不是 Error。那是用户主动放弃操作，绝非前端崩溃。
// 但**不能反过来把「一切非对象」都当取消**（reaudit3 P2-B）：那样 `throw undefined`
// / `Promise.reject('boom')` 这类真实故障会既不弹提示也不挂红条，只在控制台留一行
// warn —— 在一个装着学生教育数据的后台里，「什么都不知道」比「报个错」更难排查。
// 判据本身搬到了 utils/errors.js：它是全局兜底的唯一分拣点，必须能被单测锁住。
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
    // z-index 3000：略高于 ElMessage（2000 起）与 el-dialog 遮罩，但不再用 99999 ——
    // 原先那档会把同一次错误里自己的 toast 一起压住（reaudit3 P2-G）。
    // 颜色走 EP 的 CSS 变量，避免再造三个硬编码色值。
    el.style.cssText = 'position:fixed;top:0;left:0;right:0;z-index:3000;' +
      'display:flex;align-items:flex-start;gap:12px;' +
      'background:var(--el-color-danger-light-9,#fef0f0);color:var(--el-color-danger,#f56c6c);' +
      'border-bottom:1px solid var(--el-color-danger-light-5,#fbc4c4);' +
      'padding:8px 16px;font-size:13px;font-family:monospace;white-space:pre-wrap'
    const text = document.createElement('span')
    text.id = `${ERROR_BAR_ID}-text`
    text.style.cssText = 'flex:1;min-width:0'
    const close = document.createElement('button')
    close.type = 'button'
    close.textContent = '×'
    close.setAttribute('aria-label', '关闭错误提示')
    close.style.cssText = 'flex:0 0 auto;border:0;background:transparent;' +
      'color:var(--el-color-danger,#f56c6c);font-size:18px;line-height:1;' +
      'cursor:pointer;padding:0 4px'
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
  const msg = describeError(err)
  // 先挂红条再弹 toast：红条占住顶部，toast 必须下移，否则两者叠在一起只看得见一条
  try {
    showErrorBar(msg)
  } catch { /* DOM 不可用时忽略 */ }
  ElMessage.error({ message: `页面出错：${msg.slice(0, 120)}`, offset: 88 })
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