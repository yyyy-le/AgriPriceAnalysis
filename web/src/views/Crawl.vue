<template>
  <div>
    <el-card>
      <template #header>
        <span>🕷️ 爬虫管理</span>
      </template>

      <el-row :gutter="20">
        <el-col :span="8">
          <el-card shadow="hover">
            <div style="text-align:center">
              <div style="font-size:32px">🏪</div>
              <div style="font-size:16px;font-weight:bold;margin:10px 0">新发地批发市场</div>
              <div style="color:#999;font-size:13px;margin-bottom:15px">
                北京新发地农产品批发市场
              </div>
              <el-tag v-if="task.status === 'running'" type="warning">抓取中...</el-tag>
              <el-tag v-else-if="task.status === 'success'" type="success">上次成功</el-tag>
              <el-tag v-else-if="task.status === 'failed'" type="danger">上次失败</el-tag>
              <el-tag v-else type="info">未运行</el-tag>

              <div v-if="task.result" style="margin-top:10px;font-size:13px;color:#666">
                新增 {{ task.result.total_saved }} 条 / 跳过 {{ task.result.total_skipped }} 条
              </div>

              <el-button
                type="primary"
                style="width:100%;margin-top:15px"
                :loading="task.status === 'running'"
                @click="triggerCrawl"
              >
                {{ task.status === 'running' ? '抓取中...' : '开始抓取' }}
              </el-button>
            </div>
          </el-card>
        </el-col>
      </el-row>
    </el-card>

    <!-- 日志输出 -->
    <el-card style="margin-top:20px">
      <template #header>
        <span>📋 运行日志</span>
      </template>
      <div style="background:#1e1e1e;padding:15px;border-radius:6px;min-height:150px;max-height:300px;overflow-y:auto">
        <div v-if="logs.length === 0" style="color:#666">暂无日志...</div>
        <div v-for="(log, i) in logs" :key="i" :style="{color: log.color, fontSize:'13px', marginBottom:'4px'}">
          {{ log.text }}
        </div>
      </div>
    </el-card>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import { ElMessage } from 'element-plus'
import request from '../utils/request'

const task = ref({ status: 'idle', result: null })
const logs = ref([])
let pollTimer = null

const addLog = (text, color = '#fff') => {
  const time = new Date().toLocaleTimeString()
  logs.value.push({ text: `[${time}] ${text}`, color })
}

const triggerCrawl = async () => {
  try {
    task.value = { status: 'running', result: null }
    addLog('开始触发新发地爬虫...', '#67c23a')

    const res = await request.post('/api/crawl/xinfadi')
    const taskId = res.task_id
    addLog(`任务ID: ${taskId}`, '#909399')

    // 轮询状态
    pollTimer = setInterval(async () => {
      const status = await request.get(`/api/crawl/status/${taskId}`)
      
      if (status.status === 'success') {
        clearInterval(pollTimer)
        task.value = { status: 'success', result: status.result }
        addLog(`抓取完成！新增 ${status.result.total_saved} 条，跳过 ${status.result.total_skipped} 条`, '#67c23a')
        ElMessage.success('抓取成功')
      } else if (status.status === 'failed') {
        clearInterval(pollTimer)
        task.value = { status: 'failed', result: null }
        addLog(`抓取失败: ${status.result}`, '#f56c6c')
        ElMessage.error('抓取失败')
      } else {
        addLog('正在抓取中...', '#e6a23c')
      }
    }, 2000)

  } catch (e) {
    task.value = { status: 'failed', result: null }
    addLog('请求失败，请检查后端服务', '#f56c6c')
    ElMessage.error('请求失败')
  }
}
</script>