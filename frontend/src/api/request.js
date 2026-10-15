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
  return data.data.access_token
}

/** 把并发的同时 401 收敛成一次刷新请求。 */
function ensureRefresh() {
  if (!refreshing) {
    refreshing = refreshAccessToken().finally(() => { refreshing = null })
  }
  return refreshing
}

// 响应拦截：统一错误处理
service.interceptors.response.use(
  (response) => {
    // 文件下载直接返回
    if (response.config.responseType === 'blob') return response
    const res = response.data
    if (res.code !== 200) {
      ElMessage.error(res.message || '请求失败')
      return Promise.reject(new Error(res.message || '请求失败'))
    }
    return res
  },
  async (error) => {
    const { response, config } = error

    // 登录接口自身返回 401 不应触发刷新循环
    const isAuthRequest = (config?.url || '').includes('/auth/login')
      || (config?.url || '').includes('/auth/refresh')

    if (response?.status === 401 && !isAuthRequest) {
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