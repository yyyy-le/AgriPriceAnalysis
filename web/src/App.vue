<template>
  <div v-if="!appReady" style="height:100vh;display:flex;align-items:center;justify-content:center;background:#f0f2f5">
    <el-loading-directive />
  </div>

  <div v-else-if="$route.path === '/login'">
    <router-view />
  </div>

  <el-container v-else style="height: 100vh">
    <el-aside width="200px" style="background:#001529">
      <div style="color:white;text-align:center;padding:20px;font-size:16px;font-weight:bold">
        🌾 农产品价格系统
      </div>
      <el-menu
        router
        :default-active="$route.path"
        background-color="#001529"
        text-color="#fff"
        active-text-color="#409eff"
      >
        <el-menu-item index="/dashboard">📊 数据概览</el-menu-item>
        <el-menu-item index="/price">📋 价格列表</el-menu-item>
        <el-menu-item index="/analysis">📈 数据分析</el-menu-item>
        <el-menu-item index="/import">📂 CSV 导入</el-menu-item>
        <el-menu-item index="/crawl">🕷️ 爬虫管理</el-menu-item>
      </el-menu>
    </el-aside>

    <el-container>
      <el-header style="background:#fff;line-height:60px;border-bottom:1px solid #eee">
        农产品价格数据分析系统
      </el-header>
      <el-main style="background:#f0f2f5">
        <router-view />
      </el-main>
    </el-container>
  </el-container>
</template>

<script setup>
import { ref, onMounted } from 'vue'

const appReady = ref(false)

onMounted(() => {
  // 等路由守卫执行完再渲染
  setTimeout(() => {
    appReady.value = true
  }, 50)
})
</script>

<style>
* { margin: 0; padding: 0; box-sizing: border-box; }
body { font-family: 'Microsoft YaHei', sans-serif; }
</style>