import axios from 'axios'
import { ElMessage } from 'element-plus'
import router from '@/router'

const service = axios.create({
  baseURL: import.meta.env.VITE_API_BASE || '/api/v1',
  timeout: 120000
})

// 请求拦截：注入 Token
service.interceptors.request.use((config) => {
  const token = localStorage.getItem('access_token')
  if (token) {
    config.headers.Authorization = `Bearer ${token}`
  }
  return config
})

// ---------------------------------------------------------------- Token 刷新
// 访问令牌有效期较短（默认 12h），过期后用 refresh_token 换新的。
// 两个必须处理的点：
//  1. 刷新成功后必须**写回 localStorage**。只改内存里的 config.headers
//     的话，本次重放成功、但下次请求又带上已过期的旧 token，
//     紧接着再401、再刷新 —— 用户看到的就是反复「登录已过期」。
//  2. 并发请求同时 401 时必须**排队**，否则会并发打多次 refresh，
//     而 refresh_token 是一次性资源的话会被作废。
let refreshing = null

async function refreshAccessToken() {
  const refreshToken = localStorage.getItem('refresh_token')
  if (!refreshToken) return null

  const { data } = await axios.post(
    `${import.meta.env.VITE_API_BASE || '/api/v1'}/auth/refresh`,
    { refresh_token: refreshToken }
  )
  if (data.code !== 200 || !data.data?.access_token) {
    throw new Error(data.message || '刷新令牌失败')
  }
  // 关键：持久化，否则重放只在本次有效
  localStorage.setItem('access_token', data.data.access_token)
  if (data.data.refresh_token) {
    localStorage.setItem('refresh_token', data.data.refresh_token)
  }
  // 权限快照同步刷新：管理员调整角色权限后，已登录用户无需重登
  // 即可在下一次刷新令牌时拿到最新 perms（按钮显隐即时生效）
  if (data.data.permission) {
    try {
      const stored = JSON.parse(localStorage.getItem('user') || '{}')
      stored.permissions = data.data.permission
      if (data.data.user) stored.userInfo = { ...stored.userInfo, ...data.data.user }
      localStorage.setItem('user', JSON.stringify(stored))
    } catch { /* 本地存储异常不阻断令牌刷新 */ }
    // 只写 localStorage 不够：路由守卫/按钮权限读的是 Pinia 内存态，
    // 不同步会出现「权限已刷新、界面仍是旧权限」。
    // 必须动态 import：request.js ← api ← store/user.js 存在循环依赖，
    // 顶层 import store 会在模块初始化阶段踩到未定义。
    try {
      const { useUserStore } = await import('@/store/user')
      useUserStore().applyPermission(data.data.permission, data.data.user)
    } catch { /* Pinia 尚未安装（极早期刷新）时忽略，下次启动会重新同步 */ }
  }
  return data.data.access_token
}

/** 把并发的同时 401 收敛成一次刷新请求。 */
function ensureRefresh() {
  if (!refreshing) {
    refreshing = refreshAccessToken().finally(() => { refreshing = null })
  }
  return refreshing
}

/**
 * 给「已由拦截器提示过用户」的错误打标记。
 *
 * 业务错误（4xx/5xx、code≠200、网络中断）在拦截器里已经 ElMessage 过一次，
 * 但组件里 await 未 try/catch 时，rejection 会冒泡到 main.js 的
 * app.config.errorHandler，被当成运行时异常再报一次：
 *   「页面出错：Request failed with status code 400」
 * 并在顶部插一条红条。用户看到的是「一句业务提示 + 一句看不懂的英文」，
 * 且红条会一直挂着不消失。打标记后全局兜底可据此跳过。
 */
// axios 的英文原文不要直接丢给教师/学生看：
//   "Request failed with status code 500" / "Network Error" / "timeout of 120000ms exceeded"
// 这些既不可读也不指向下一步动作。后端给的中文 message 优先，其次按类型兜底。
const ERROR_HINTS = [
  [/network error/i, '网络连接失败，请检查网络后重试'],
  [/timeout of \d+ms exceeded/i, '请求超时，请稍后重试'],
  [/request failed with status code 5\d\d/i, '服务暂时不可用，请稍后重试'],
  [/request failed with status code 4\d\d/i, '请求被拒绝，请检查填写内容后重试'],
  [/failed to fetch/i, '网络连接失败，请检查网络后重试']
]

function humanizeError(error, response) {
  const backendMsg = response?.data?.message
  if (backendMsg) return backendMsg
  const raw = String(error?.message || '')
  for (const [pattern, text] of ERROR_HINTS) {
    if (pattern.test(raw)) return text
  }
  return raw || '网络异常'
}

function markHandled(err) {
  try {
    if (err && typeof err === 'object') err.__handled = true
  } catch { /* 冻结对象等极端情况忽略 */ }
  return err
}
// 响应拦截：统一错误处理
// 非 JSON 响应类型：这些接口返回的不是统一信封，而是原始内容。
// 只豁免 blob 会让 `responseType: 'text'` 的 HTML 打印视图 100% 失败：
// HTML 字符串被当成信封读 `res.code` → undefined ≠ 200 → 弹「请求失败」
// 并 reject，PaperEdit 拿到的永远是异常而不是页面内容。
const RAW_RESPONSE_TYPES = new Set(['blob', 'text', 'arraybuffer', 'document', 'stream'])

function isRawResponse(response) {
  const declared = response?.config?.responseType
  if (declared && RAW_RESPONSE_TYPES.has(declared)) return true
  // 兜底：后端返回 text/html、application/pdf、text/markdown 等但调用方
  // 没声明 responseType 时，axios 会给出字符串；不能拿它当 JSON 信封解析。
  const ct = String(response?.headers?.['content-type'] || '').toLowerCase()
  if (ct && !ct.includes('application/json') && !ct.includes('+json')) return true
  // 已成功解析成对象才有资格走信封判定；字符串一律视为原始内容。
  return typeof response?.data === 'string'
}

service.interceptors.response.use(
  (response) => {
    // 文件下载 / HTML 打印视图直接返回**整个 axios response**，不套用统一信封。
    // 必须保留 headers：downloadBlob 靠 content-disposition 取文件名；
    // 调用方按需取 res.data（Blob 或 HTML 字符串）。
    if (isRawResponse(response)) return response
    const res = response.data
    if (res.code !== 200) {
      ElMessage.error(res.message || '请求失败')
      return Promise.reject(markHandled(new Error(res.message || '请求失败')))
    }
    return res
  },
  async (error) => {
    // 进门先标记：本拦截器所有出口都自带用户提示
    markHandled(error)
    const { response, config } = error

    // 把中文文案**回写进 error.message**（reaudit3 P2-13）。
    // 只改 toast 不够：组件里 `catch (e) { ElMessage.error(e.message) }` 拿到的
    // 还是 "Request failed with status code 400"，于是用户先看到一句中文、
    // 再看到一句英文原文。回写之后组件层即便还留着二次提示也是中文。
    // 组件侧同时已统一改用 toastIfUnhandled，正常路径只会弹一次。
    const friendly = humanizeError(error, response)
    try {
      if (error && typeof error === 'object') error.message = friendly
    } catch { /* 只读对象忽略 */ }

    // 登录接口自身返回 401 不应触发刷新循环
    const isAuthRequest = (config?.url || '').includes('/auth/login')
      || (config?.url || '').includes('/auth/refresh')

    if (response?.status === 401 && !isAuthRequest) {
      // 公共页（/login、/register）上的 401 不能当成「登录已过期」：
      // 未登录用户访问注册页时，页面内任何一个需登录的辅助接口（班级下拉、
      // 附件上传）返回 401，都会把用户直接弹回登录页 —— 注册入口彻底打不开。
      // 公共页只把错误抛给调用方，由页面自己降级处理。
      const onPublicPage = router.currentRoute.value?.meta?.public === true
      if (onPublicPage) {
        return Promise.reject(error)
      }
      // 本次失败时用的令牌：后面判断"有没有被别的标签页换掉"全靠它
      const tokenBefore = localStorage.getItem('access_token')
      if (!config?._retried) {
        config._retried = true
        try {
          const fresh = await ensureRefresh()
          if (fresh) {
            config.headers.Authorization = `Bearer ${fresh}`
            return service(config)
          }
        } catch (e) {
          // 跨标签页竞态：refresh_token 是一次性轮换的，两个标签页同时 401
          // 时只有先到的那个能换成功，另一个必然拿到 401。旧实现在这里直接
          // 清空 localStorage —— 会把对端刚写入的**新 refresh_token 一起删掉**，
          // 于是两个标签页同时被踢出登录。
          // 这里等一拍再看存储：若已被换成新令牌，直接复用它重放，不再刷新。
          await new Promise((resolve) => setTimeout(resolve, 200))
          const latest = localStorage.getItem('access_token')
          if (latest && latest !== tokenBefore && !config._tabRetry) {
            config._tabRetry = true
            config.headers.Authorization = `Bearer ${latest}`
            return service(config)
          }
        }
      }
      // 两条路都走不通才登出。清理前再确认一次：如果存储里的令牌已经不是我
      // 这次失败的令牌，说明另一页刷新成功，清掉等于误伤。
      const latestNow = localStorage.getItem('access_token')
      if (!latestNow || latestNow === tokenBefore) {
        localStorage.removeItem('access_token')
        localStorage.removeItem('refresh_token')
        localStorage.removeItem('user')
        ElMessage.error('登录已过期，请重新登录')
        router.push('/login')
      }
      return Promise.reject(error)
    }

    ElMessage.error(friendly)
    return Promise.reject(error)
  }
)

export default service