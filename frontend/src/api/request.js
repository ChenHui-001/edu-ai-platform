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
function markHandled(err) {
  try {
    if (err && typeof err === 'object') err.__handled = true
  } catch { /* 冻结对象等极端情况忽略 */ }
  return err
}

// 响应拦截：统一错误处理
service.interceptors.response.use(
  (response) => {
    // 文件下载直接返回
    if (response.config.responseType === 'blob') return response
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
      if (!config?._retried) {
        config._retried = true
        try {
          const fresh = await ensureRefresh()
          if (fresh) {
            config.headers.Authorization = `Bearer ${fresh}`
            return service(config)
          }
        } catch (e) {
          // 刷新失败，走登出
        }
      }
      localStorage.removeItem('access_token')
      localStorage.removeItem('refresh_token')
      localStorage.removeItem('user')
      ElMessage.error('登录已过期，请重新登录')
      router.push('/login')
      return Promise.reject(error)
    }

    const msg = response?.data?.message || error.message || '网络异常'
    ElMessage.error(msg)
    return Promise.reject(error)
  }
)

export default service