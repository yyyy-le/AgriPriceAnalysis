import { defineStore } from 'pinia'
import { login, logout } from '../api/auth'

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
      this.username = username
      localStorage.setItem('token', res.access_token)
      localStorage.setItem('username', username)
    },

    async logout() {
      await logout()
      this.token = null
      this.role = null
      this.username = null
      localStorage.clear()
    }
  }
})