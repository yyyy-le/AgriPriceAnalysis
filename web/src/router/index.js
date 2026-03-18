import { createRouter, createWebHistory } from 'vue-router'

const routes = [
  // 公共页
  { path: '/login', component: () => import('../views/Login.vue'), meta: { public: true } },
  { path: '/', redirect: '/dashboard' },

  // ===== 用户端 =====
  {
    path: '/dashboard',
    component: () => import('../views/user/Dashboard.vue'),
    meta: { role: 'user' }
  },
  {
    path: '/price',
    component: () => import('../views/user/PriceList.vue'),
    meta: { role: 'user' }
  },
  {
    path: '/analysis',
    component: () => import('../views/user/Analysis.vue'),
    meta: { role: 'user' }
  },
  {
    path: '/alerts',
    component: () => import('../views/user/Alerts.vue'),
    meta: { role: 'user' }
  },
  {
    path: '/profile',
    component: () => import('../views/user/Profile.vue'),
    meta: { role: 'user' }
  },

  // ===== 管理员端 =====
  {
    path: '/admin/users',
    component: () => import('../views/admin/UserManage.vue'),
    meta: { role: 'admin' }
  },
  {
    path: '/admin/crawl',
    component: () => import('../views/admin/Crawl.vue'),
    meta: { role: 'admin' }
  },
  {
    path: '/admin/data',
    component: () => import('../views/admin/DataManage.vue'),
    meta: { role: 'admin' }
  },
  {
    path: '/admin/import',
    component: () => import('../views/admin/Import.vue'),
    meta: { role: 'admin' }
  },
  {
    path: '/admin/logs',
    component: () => import('../views/admin/Logs.vue'),
    meta: { role: 'admin' }
  },

  // 兜底 404
  { path: '/:pathMatch(.*)*', redirect: '/dashboard' }
]

const router = createRouter({
  history: createWebHistory(),
  routes
})

router.beforeEach((to, from, next) => {
  const token = localStorage.getItem('token')
  const role = localStorage.getItem('role')

  // 公共页直接放行（已登录则跳到对应首页）
  if (to.meta.public) {
    if (token) {
      return next(role === 'admin' ? '/admin/users' : '/dashboard')
    }
    return next()
  }

  // 未登录，全部跳登录页
  if (!token) return next('/login')

  // role 守卫：admin 访问用户页 → 跳到管理首页；user 访问 admin 页 → 跳到用户首页
  if (to.meta.role === 'admin' && role !== 'admin') return next('/dashboard')
  if (to.meta.role === 'user' && role === 'admin') return next('/admin/users')

  next()
})

export default router