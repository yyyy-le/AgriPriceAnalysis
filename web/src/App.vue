<template>
  <div v-if="!appReady" style="height:100vh;display:flex;align-items:center;justify-content:center">
    <el-loading-directive />
  </div>

  <!-- 登录页：无布局 -->
  <div v-else-if="$route.path === '/login'">
    <router-view />
  </div>

  <!-- 主布局 -->
  <el-container v-else style="height:100vh">
    <el-aside width="200px" style="background:#001529">
      <div style="color:white;text-align:center;padding:20px;font-size:16px;font-weight:bold">
        🌾 农产品价格系统
      </div>

      <!-- 用户端菜单 -->
      <el-menu
        v-if="!isAdmin"
        router
        :default-active="$route.path"
        background-color="#001529"
        text-color="#fff"
        active-text-color="#409eff"
      >
        <el-menu-item index="/dashboard">📊 数据概览</el-menu-item>
        <el-menu-item index="/price">📋 价格列表</el-menu-item>
        <el-menu-item index="/analysis">📈 数据分析</el-menu-item>
        <el-menu-item index="/alerts">🔔 价格预警</el-menu-item>
        <el-menu-item index="/profile">👤 个人中心</el-menu-item>
      </el-menu>

      <!-- 管理员端菜单 -->
      <el-menu
        v-else
        router
        :default-active="$route.path"
        background-color="#001529"
        text-color="#fff"
        active-text-color="#409eff"
      >
        <el-menu-item index="/admin/users">👥 用户管理</el-menu-item>
        <el-menu-item index="/admin/crawl">🕷️ 爬虫管理</el-menu-item>
        <el-menu-item index="/admin/data">🗄️ 数据管理</el-menu-item>
        <el-menu-item index="/admin/import">📂 CSV 导入</el-menu-item>
        <el-menu-item index="/admin/logs">📋 系统日志</el-menu-item>
      </el-menu>
    </el-aside>

    <el-container>
      <el-header style="background:#fff;display:flex;align-items:center;justify-content:space-between;border-bottom:1px solid #eee;padding:0 20px">
        <span>农产品价格数据分析系统</span>
        <div style="display:flex;align-items:center;gap:12px">
          <el-tag :type="isAdmin ? 'danger' : 'success'" size="small">
            {{ isAdmin ? '管理员' : '普通用户' }}
          </el-tag>
          <span style="font-size:14px;color:#666">{{ username }}</span>
          <el-button size="small" @click="handleLogout">退出</el-button>
        </div>
      </el-header>
      <el-main style="background:#f0f2f5">
        <router-view />
      </el-main>
    </el-container>
  </el-container>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from './stores/auth'

const appReady = ref(false)
const router = useRouter()
const authStore = useAuthStore()

const isAdmin = computed(() => authStore.role === 'admin')
const username = computed(() => authStore.username)

const handleLogout = () => {
  authStore.logout()
  router.push('/login')
}

onMounted(() => {
  setTimeout(() => { appReady.value = true }, 50)
})
</script>

<style>
* { margin: 0; padding: 0; box-sizing: border-box; }
body { font-family: 'Microsoft YaHei', sans-serif; }
</style>

