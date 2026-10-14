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

    if (response?.status === 401) {
      // Token 过期，尝试刷新
      const refreshToken = localStorage.getItem('refresh_token')
      if (refreshToken && !config?._retried) {
        config._retried = true
        try {
          const { data } = await axios.post(
            `${import.meta.env.VITE_API_BASE || '/api/v1'}/auth/refresh`,
            { refresh_token: refreshToken }
          )
          if (data.code === 200) {
            localStorage.setItem('access_token', data.data.access_token)
            config.headers.Authorization = `Bearer ${data.data.access_token}`
            return service(config)
          }
        } catch (e) {
          // 刷新失败，继续登出
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
