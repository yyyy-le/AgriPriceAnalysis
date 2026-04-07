import request from '../utils/request'

export const register = (data) =>
  request.post('/api/users', data)

export const sendVerificationCode = (cellphone) =>
  request.post('/api/auth/verification-codes/cellphone', { cellphone })