import axios from 'axios'
import { ElMessage } from 'element-plus'

const request = axios.create({
  baseURL: 'http://localhost:8000',
  timeout: 10000
})

// 请求拦截：自动带上 Token
request.interceptors.request.use(config => {
  const token = localStorage.getItem('token')
  if (token) {
    config.headers.Authorization = `Bearer ${token}`
  }
  return config
})

// 响应拦截
request.interceptors.response.use(
  res => res.data,
  err => {
    if (err.response?.status === 401) {
      localStorage.clear()
      window.location.href = '/login'
      return Promise.reject(err)
    }

    const data = err.response?.data
    let msg = '请求失败，请稍后重试'

    if (typeof data === 'string') {
      msg = data
    } else if (data?.message) {
      // 后端直接返回 { code, message } 格式
      msg = data.message
    } else if (data?.detail) {
      // FastAPI HTTPException 格式 { detail: { code, message } }
      if (typeof data.detail === 'string') {
        msg = data.detail
      } else if (data.detail?.message) {
        msg = data.detail.message
      }
    }

    ElMessage.error(msg)
    return Promise.reject(err)
  }
)

export default request