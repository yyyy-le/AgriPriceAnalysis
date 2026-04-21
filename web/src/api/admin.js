import request from '../utils/request'

// 用户管理
export const getUsers = (params) =>
  request.get('/api/admin/users', { params })

export const createUser = (data) =>
  request.post('/api/admin/users', data)

export const updateUser = (data) =>
  request.put(`/api/admin/users/${data.id}`, data)

export const updateUserState = (userId, state) =>
  request.patch(`/api/admin/users/${userId}/state`, null, { params: { state } })

export const updateUserAdmin = (userId, isAdmin) =>
  request.patch(`/api/admin/users/${userId}/admin`, null, { params: { is_admin: isAdmin } })

export const deleteUser = (userId) =>
  request.delete(`/api/admin/users/${userId}`)

// 数据管理
export const getAdminRecords = (params) =>
  request.get('/api/admin/data/records', { params })

export const updateRecord = (data) =>
  request.put('/api/admin/data/records', data)

export const deleteRecord = (productId, time) =>
  request.delete('/api/admin/data/records', { params: { product_id: productId, time } })

export const importCsv = (file) => {
  const formData = new FormData()
  formData.append('file', file)
  return request.post('/api/admin/data/import-csv', formData, {
    headers: { 'Content-Type': 'multipart/form-data' },
    timeout: 300000 // 5分钟超时，适应大文件导入
  })
}

// 系统日志
export const getLogs = (params) =>
  request.get('/api/admin/logs', { params })