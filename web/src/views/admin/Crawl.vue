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
              <div style="color:#999;font-size:13px;margin-bottom:15px">北京新发地农产品批发市场</div>

              <el-tag v-if="task.status === 'cancelled'" type="info">已取消</el-tag>
              <el-tag v-else-if="task.paused" type="warning">已暂停</el-tag>
              <el-tag v-else-if="task.status === 'running'" type="warning">抓取中...</el-tag>
              <el-tag v-else-if="task.status === 'success'" type="success">上次成功</el-tag>
              <el-tag v-else-if="task.status === 'failed'" type="danger">上次失败</el-tag>
              <el-tag v-else type="info">未运行</el-tag>

              <div v-if="task.status === 'running' || task.status === 'success' || task.status === 'cancelled'"
                style="margin-top:10px;font-size:13px;color:#666">
                <span v-if="task.total_pages > 0">
                  第 {{ task.page }}/{{ task.total_pages }} 页 ·
                </span>
                已存入 <b style="color:#67c23a">{{ task.saved }}</b> 条 ·
                跳过 <b style="color:#e6a23c">{{ task.skipped }}</b> 条
              </div>

              <div style="margin-top:10px;display:flex;align-items:center;justify-content:center;gap:8px">
                <span v-if="task.status !== 'running' || task.paused" style="font-size:13px;color:#666">起始页</span>
                <el-input-number
                  v-if="task.status !== 'running' || task.paused"
                  v-model="startPage"
                  :min="1"
                  :max="9999"
                  size="small"
                  style="width:100px"
                />
              </div>

              <div style="margin-top:10px;display:flex;gap:8px;justify-content:center;flex-wrap:wrap">
                <el-button
                  v-if="task.status !== 'running' || task.paused"
                  type="primary"
                  style="flex:1;min-width:90px"
                  @click="task.paused ? resumeCrawl() : triggerCrawl()"
                >
                  {{ task.paused ? '继续抓取' : '开始抓取' }}
                </el-button>

                <el-button
                  v-if="task.status === 'running' && !task.paused"
                  type="warning"
                  style="flex:1;min-width:90px"
                  @click="pauseCrawl"
                >
                  暂停
                </el-button>

                <el-button
                  v-if="task.status === 'running'"
                  type="danger"
                  style="flex:1;min-width:90px"
                  @click="cancelCrawl"
                >
                  取消
                </el-button>
              </div>
            </div>
          </el-card>
        </el-col>
      </el-row>
    </el-card>

    <el-card style="margin-top:20px">
      <template #header>
        <span>📋 运行日志</span>
        <el-button size="small" style="float:right" @click="clearLogs">清空</el-button>
      </template>
      <div
        ref="logBox"
        style="background:#1e1e1e;padding:15px;border-radius:6px;min-height:150px;max-height:300px;overflow-y:auto"
      >
        <div v-if="logs.length === 0" style="color:#666">暂无日志...</div>
        <div
          v-for="(log, i) in logs"
          :key="i"
          :style="{ color: log.color, fontSize: '13px', marginBottom: '4px' }"
        >
          {{ log.text }}
        </div>
      </div>
    </el-card>
  </div>
</template>

<script setup>
import { ref, nextTick, onMounted, onUnmounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import request from '../../utils/request'

const startPage = ref(1)
const task = ref({
  status: 'idle',
  result: null,
  saved: 0,
  skipped: 0,
  page: 0,
  total_pages: 0,
  paused: false,
})
const logs = ref([])
const logBox = ref()
let pollTimer = null
let currentTaskId = null

// 页面恢复：从 sessionStorage 读取上次正在运行的 task_id
const restoreTaskId = async () => {
  restoreLogs()
  const saved = sessionStorage.getItem('crawl_task_id')
  if (saved) {
    currentTaskId = saved
    // 立即获取一次状态，避免显示空状态
    try {
      const status = await request.get(`/api/crawl/status/${currentTaskId}`)
      task.value = { ...task.value, ...status }
      // 任务已结束则不再轮询
      if (['success', 'cancelled', 'failed'].includes(status.status)) {
        clearSavedTaskId()
        return
      }
    } catch {
      clearSavedTaskId()
      return
    }
    startPolling(currentTaskId)
  }
}

onMounted(() => {
  restoreTaskId()
})

onUnmounted(() => {
  // 导航离开前清理定时器，保存 task_id
  if (pollTimer) clearInterval(pollTimer)
})

const saveTaskId = (id) => {
  sessionStorage.setItem('crawl_task_id', id)
}

const clearSavedTaskId = () => {
  sessionStorage.removeItem('crawl_task_id')
  sessionStorage.removeItem('crawl_logs')
}

const saveLogs = () => {
  if (sessionStorage.getItem('crawl_logs_cleared') === '1') return
  const slice = logs.value.slice(-200)
  sessionStorage.setItem('crawl_logs', JSON.stringify(slice))
}

const restoreLogs = () => {
  if (sessionStorage.getItem('crawl_logs_cleared') === '1') return
  const saved = sessionStorage.getItem('crawl_logs')
  if (saved) {
    try {
      logs.value = JSON.parse(saved)
    } catch {}
  }
}

const clearLogs = () => {
  logs.value = []
  sessionStorage.removeItem('crawl_logs')
  sessionStorage.setItem('crawl_logs_cleared', '1')
}

const addLog = (text, color = '#fff') => {
  const time = new Date().toLocaleTimeString()
  logs.value.push({ text: `[${time}] ${text}`, color })
  saveLogs()
  nextTick(() => {
    if (logBox.value) logBox.value.scrollTop = logBox.value.scrollHeight
  })
}

const startPolling = (taskId) => {
  clearInterval(pollTimer)
  let lastProgress = ''
  pollTimer = setInterval(async () => {
    const status = await request.get(`/api/crawl/status/${taskId}`)
    task.value = { ...task.value, ...status }

    if (status.status === 'running') {
      if (!status.paused && status.total_pages > 0) {
        const progress = `${status.page}/${status.total_pages}/${status.saved}/${status.skipped}`
        if (progress !== lastProgress) {
          lastProgress = progress
          addLog(
            `第 ${status.page}/${status.total_pages} 页 · 已存入 ${status.saved} 条 · 跳过 ${status.skipped} 条`,
            '#e6a23c'
          )
        }
      }
    } else if (status.status === 'success') {
      clearInterval(pollTimer)
      clearSavedTaskId()
      addLog(`✅ 抓取完成！共存入 ${status.saved} 条，跳过 ${status.skipped} 条`, '#67c23a')
      ElMessage.success('抓取成功')
    } else if (status.status === 'cancelled') {
      clearInterval(pollTimer)
      clearSavedTaskId()
      addLog(`⛔ 已取消，本次共存入 ${status.saved} 条，跳过 ${status.skipped} 条`, '#909399')
      ElMessage.info('已取消抓取')
    } else if (status.status === 'failed') {
      clearInterval(pollTimer)
      clearSavedTaskId()
      addLog(`❌ 抓取失败: ${status.result}`, '#f56c6c')
      ElMessage.error('抓取失败')
    }
  }, 2000)
}

const triggerCrawl = async () => {
  try {
    task.value = { status: 'running', result: null, saved: 0, skipped: 0, page: 0, total_pages: 0, paused: false }
    addLog('开始触发新发地爬虫...', '#67c23a')
    const res = await request.post('/api/crawl/xinfadi', { start_page: startPage.value })
    currentTaskId = res.task_id
    saveTaskId(currentTaskId)
    addLog(`任务ID: ${currentTaskId}`, '#909399')
    startPolling(currentTaskId)
  } catch (e) {
    task.value.status = 'failed'
    addLog('请求失败，请检查后端服务', '#f56c6c')
    ElMessage.error('请求失败')
  }
}

const pauseCrawl = async () => {
  if (!currentTaskId) return
  await request.post(`/api/crawl/pause/${currentTaskId}`)
  task.value.paused = true
  addLog('⏸ 已暂停抓取', '#e6a23c')
}

const resumeCrawl = async () => {
  if (!currentTaskId) return
  await request.post(`/api/crawl/resume/${currentTaskId}`)
  task.value.paused = false
  addLog('▶️ 继续抓取...', '#67c23a')
}

const cancelCrawl = async () => {
  if (!currentTaskId) return
  try {
    await ElMessageBox.confirm('确认取消本次抓取任务？已存入的数据不会丢失。', '取消确认', {
      type: 'warning',
      confirmButtonText: '确认取消',
      cancelButtonText: '继续抓取',
    })
    await request.post(`/api/crawl/cancel/${currentTaskId}`)
    clearInterval(pollTimer)
    // 取消后再拉一次最终状态，确保 saved/skipped 是最新值
    try {
      const final = await request.get(`/api/crawl/status/${currentTaskId}`)
      task.value = { ...task.value, ...final }
    } catch {}
    clearSavedTaskId()
    task.value.status = 'cancelled'
    task.value.paused = false
    addLog(`⛔ 用户取消了抓取任务，本次共存入 ${task.value.saved} 条，跳过 ${task.value.skipped} 条`, '#909399')
    ElMessage.info('已取消')
  } catch {
    // 用户点了"继续抓取"，不做任何处理
  }
}
</script>