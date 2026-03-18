import request from '../utils/request'

export const login = (username, password) => {
  const formData = new URLSearchParams()
  formData.append('username', username)
  formData.append('password', password)
  formData.append('grant_type', 'password')

  return request.post('/api/auth/token/password', formData)
}

export const logout = () => {
  return request.delete('/api/auth/token')
}

export const getTokenStatus = () => {
  return request.get('/api/auth/token/status')
}