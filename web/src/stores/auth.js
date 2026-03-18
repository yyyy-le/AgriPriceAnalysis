import { defineStore } from 'pinia'
import { login, logout } from '../api/auth'   // ← 必须从 api/auth 引入

export const useAuthStore = defineStore('auth', {
  state: () => ({
    token: localStorage.getItem('token') || null,
    role: localStorage.getItem('role') || null,
    username: localStorage.getItem('username') || null,
  }),

  getters: {
    isLoggedIn: (state) => !!state.token,
    isAdmin: (state) => state.role === 'admin',
  },

  actions: {
    async login(username, password) {
      const res = await login(username, password)
      this.token = res.access_token
      this.role = res.role              // 存后端返回的 role
      this.username = username
      localStorage.setItem('token', res.access_token)
      localStorage.setItem('role', res.role)
      localStorage.setItem('username', username)
    },

    async logout() {
      try {
        await logout()
      } catch (e) {
        // 即使接口失败也清本地
      }
      this.token = null
      this.role = null
      this.username = null
      localStorage.clear()
    }
  }
})