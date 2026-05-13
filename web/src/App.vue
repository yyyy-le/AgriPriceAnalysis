<template>
  <div v-if="!appReady" style="height:100vh;display:flex;align-items:center;justify-content:center">
    <span style="color:#6366f1;font-size:14px">加载中...</span>
  </div>

  <div v-else-if="$route.path === '/login'">
    <router-view />
  </div>

  <div v-else style="display:flex;height:100vh;overflow:hidden">

    <!-- 侧边栏 -->
    <div style="width:220px;background:#1e3a5f;display:flex;flex-direction:column;flex-shrink:0">

      <!-- Logo -->
      <div style="padding:24px 20px 20px;border-bottom:1px solid rgba(255,255,255,0.08)">
        <div style="font-size:15px;font-weight:700;color:#f8fafc;letter-spacing:0.5px;line-height:1.5">农产品物价数据分析系统</div>
      </div>

      <!-- 菜单 -->
      <div style="flex:1;padding:16px 10px;overflow-y:auto">
        <template v-if="!isAdmin">
          <router-link v-for="item in userMenus" :key="item.path" :to="item.path" style="text-decoration:none">
            <div :style="`
              padding:12px 16px;
              border-radius:8px;
              margin-bottom:4px;
              font-size:${$route.path === item.path ? '18px' : '15px'};
              font-weight:${$route.path === item.path ? '600' : '500'};
              cursor:pointer;
              transition:all 0.2s;
              color:${$route.path === item.path ? '#ffffff' : '#93c5fd'};
              background:${$route.path === item.path ? 'rgba(59,130,246,0.25)' : 'transparent'};
              border-left:${$route.path === item.path ? '3px solid #3b82f6' : '3px solid transparent'};
            `">
              {{ item.label }}
            </div>
          </router-link>
        </template>

        <template v-else>
          <router-link v-for="item in adminMenus" :key="item.path" :to="item.path" style="text-decoration:none">
            <div :style="`
              padding:12px 16px;
              border-radius:8px;
              margin-bottom:4px;
              font-size:${$route.path === item.path ? '18px' : '15px'};
              font-weight:${$route.path === item.path ? '600' : '500'};
              cursor:pointer;
              transition:all 0.2s;
              color:${$route.path === item.path ? '#ffffff' : '#93c5fd'};
              background:${$route.path === item.path ? 'rgba(59,130,246,0.25)' : 'transparent'};
              border-left:${$route.path === item.path ? '3px solid #3b82f6' : '3px solid transparent'};
            `">
              {{ item.label }}
            </div>
          </router-link>
        </template>
      </div>

      <!-- 底部用户信息 -->
      <div style="padding:16px 20px;border-top:1px solid rgba(255,255,255,0.08)">
        <div style="display:flex;align-items:center;gap:10px">
          <div
            style="display:flex;align-items:center;gap:10px;flex:1;min-width:0;cursor:pointer"
            @click="goProfile"
          >
            <div :style="`
              width:34px;height:34px;border-radius:50%;
              background:${$route.path === '/profile' ? 'linear-gradient(135deg,#3b82f6,#60a5fa)' : 'linear-gradient(135deg,#1e3a5f,#2d5a8e)'};
              display:flex;align-items:center;justify-content:center;
              color:#fff;font-size:14px;font-weight:600;flex-shrink:0;
              transition:all 0.2s;
            `">
              {{ username?.charAt(0)?.toUpperCase() }}
            </div>
            <div style="min-width:0">
              <div :style="`
                font-size:${$route.path === '/profile' ? '15px' : '14px'};
                font-weight:${$route.path === '/profile' ? '600' : '500'};
                color:${$route.path === '/profile' ? '#ffffff' : '#f8fafc'};
                overflow:hidden;text-overflow:ellipsis;white-space:nowrap;
                transition:all 0.2s;
              `">
                {{ username }}
              </div>
              <div style="font-size:13px;color:#94a3b8;margin-top:2px">
                {{ isAdmin ? '管理员' : '普通用户' }}
              </div>
            </div>
          </div>
          <div class="logout-btn" @click="handleLogout">退出</div>
        </div>
      </div>

    </div>

    <!-- 主内容区 -->
    <div style="flex:1;display:flex;flex-direction:column;overflow:hidden">

      <!-- 顶部 Header -->
      <div style="
        height:60px;background:#fff;
        display:flex;align-items:center;
        padding:0 28px;border-bottom:1px solid #e5e7eb;flex-shrink:0
      ">
        <span style="font-size:20px;font-weight:700;color:#1f2937;letter-spacing:0.3px">{{ currentTitle }}</span>
      </div>

      <!-- 页面内容 -->
      <div style="flex:1;overflow-y:auto;background:#f8fafc;padding:20px">
        <router-view />
      </div>

    </div>

  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { useAuthStore } from './stores/auth'

const appReady = ref(false)
const router = useRouter()
const route = useRoute()
const authStore = useAuthStore()

const isAdmin = computed(() => authStore.role === 'admin')
const username = computed(() => authStore.username)

const userMenus = [
  { path: '/dashboard', label: '数据概览' },
  { path: '/price',     label: '价格列表' },
  { path: '/analysis',  label: '数据分析' },
  { path: '/alerts',    label: '价格预警' },
  { path: '/ai',        label: 'AI 助手' },
]

const adminMenus = [
  { path: '/admin/users',  label: '用户管理' },
  { path: '/admin/crawl',  label: '爬虫管理' },
  { path: '/admin/data',   label: '数据管理' },
  { path: '/admin/import', label: '数据导入' },
  { path: '/admin/logs',   label: '系统日志' },
]

const titleMap = {
  '/dashboard':    '数据概览',
  '/price':        '价格列表',
  '/analysis':     '数据分析',
  '/alerts':       '价格预警',
  '/ai':           'AI 助手',
  '/profile':      '个人中心',
  '/admin/users':  '用户管理',
  '/admin/crawl':  '爬虫管理',
  '/admin/data':   '数据管理',
  '/admin/import': '数据导入',
  '/admin/logs':   '系统日志',
}

const currentTitle = computed(() => titleMap[route.path] || '农产品价格系统')

const goProfile = () => {
  router.push('/profile')
}

const handleLogout = async () => {
  await authStore.logout()
  window.location.href = '/login'
}

onMounted(() => {
  setTimeout(() => { appReady.value = true }, 50)
})
</script>

<style>
@import url('https://fonts.googleapis.com/css2?family=Poppins:wght@400;500;600;700&display=swap');
* { margin: 0; padding: 0; box-sizing: border-box; }
body { font-family: 'Poppins', 'Microsoft YaHei', sans-serif; }
a { text-decoration: none; }
::-webkit-scrollbar { width: 4px; height: 4px; }
::-webkit-scrollbar-track { background: transparent; }
::-webkit-scrollbar-thumb { background: #cbd5e1; border-radius: 2px; }
::-webkit-scrollbar-thumb:hover { background: #94a3b8; }

/* 退出按钮 */
.logout-btn {
  font-size: 13px;
  color: #64748b;
  cursor: pointer;
  padding: 5px 10px;
  border-radius: 6px;
  border: 1px solid rgba(255, 255, 255, 0.10);
  white-space: nowrap;
  flex-shrink: 0;
  transition: color 0.2s, background 0.2s, border-color 0.2s;
}
.logout-btn:hover {
  color: #f87171;
  background: rgba(248, 113, 113, 0.12);
  border-color: rgba(248, 113, 113, 0.35);
}
</style>