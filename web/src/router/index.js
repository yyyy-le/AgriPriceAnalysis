import { createRouter, createWebHistory } from 'vue-router'

const routes = [
  { path: '/login', component: () => import('../views/Login.vue') },
  { path: '/', redirect: '/dashboard' },
  { path: '/dashboard', component: () => import('../views/Dashboard.vue') },
  { path: '/price', component: () => import('../views/PriceList.vue') },
  { path: '/analysis', component: () => import('../views/Analysis.vue') },
  { path: '/import', component: () => import('../views/Import.vue') },
  { path: '/crawl', component: () => import('../views/Crawl.vue') },
]

const router = createRouter({
  history: createWebHistory(),
  routes
})

router.beforeEach((to, from, next) => {
  const token = localStorage.getItem('token')
  if (to.path !== '/login' && !token) {
    next('/login')
  } else if (to.path === '/login' && token) {
    // 已登录访问登录页，直接跳 dashboard
    next('/dashboard')
  } else {
    next()
  }
})

export default router