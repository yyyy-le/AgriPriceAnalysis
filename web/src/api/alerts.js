import request from '../utils/request'

export const getAlerts = () => request.get('/api/alerts/list')

export const createAlert = (data) => request.post('/api/alerts/create', data)

export const updateAlert = (id, data) => request.put(`/api/alerts/update/${id}`, data)

export const deleteAlert = (id) => request.delete(`/api/alerts/delete/${id}`)

export const getAlertLogs = (params) => request.get('/api/alerts/logs', { params })

export const markLogRead = (id) => request.post(`/api/alerts/logs/${id}/mark-read`)
