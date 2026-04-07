<template>
  <div>
    <el-card style="margin-bottom:20px">
      <template #header>
        <span>🔔 价格预警设置</span>
        <el-button type="primary" size="small" style="float:right" @click="openDialog()">新增预警</el-button>
      </template>
      <el-empty v-if="alerts.length===0" description="暂无预警，点击右上角新增"/>
      <el-table v-else :data="alerts" stripe v-loading="loading">
        <el-table-column prop="product_name" label="产品名称" min-width="120"/>
        <el-table-column prop="threshold" label="预警阈值" min-width="100">
          <template #default="{ row }">
            <span style="font-weight:600">{{ row.threshold }}</span> 元
          </template>
        </el-table-column>
        <el-table-column prop="alert_type" label="类型" min-width="130">
          <template #default="{ row }">
            <el-tag :type="row.alert_type==='above'?'danger':'success'">
              {{ row.alert_type==='above' ? '高于阈值预警' : '低于阈值预警' }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="is_active" label="状态" min-width="80">
          <template #default="{ row }">
            <el-tag :type="row.is_active?'success':'info'">
              {{ row.is_active ? '启用' : '禁用' }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="created_at" label="创建时间" min-width="120">
          <template #default="{ row }">
            {{ formatDateOnly(row.created_at) }}
          </template>
        </el-table-column>
        <el-table-column label="操作" width="200" fixed="right">
          <template #default="{ row }">
            <el-button size="small" @click="openDialog(row)">编辑</el-button>
            <el-button size="small" :type="row.is_active?'warning':'success'" @click="toggleActive(row)">
              {{ row.is_active ? '禁用' : '启用' }}
            </el-button>
            <el-button size="small" type="danger" @click="removeAlert(row.id)">删除</el-button>
          </template>
        </el-table-column>
      </el-table>
    </el-card>

    <el-card>
      <template #header>
        <span>📋 预警历史记录</span>
      </template>
      <el-empty v-if="logs.length===0" description="暂无预警记录"/>
      <el-table v-else :data="logs" stripe v-loading="logsLoading">
        <el-table-column prop="product_name" label="产品名称" min-width="120"/>
        <el-table-column prop="alert_type" label="预警类型" min-width="120">
          <template #default="{ row }">
            <el-tag :type="row.alert_type==='above'?'danger':'success'" size="small">
              {{ row.alert_type==='above' ? '高于阈值' : '低于阈值' }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="price_value" label="触发价格" min-width="100">
          <template #default="{ row }">{{ row.price_value }} 元</template>
        </el-table-column>
        <el-table-column prop="threshold_value" label="阈值" min-width="100">
          <template #default="{ row }">{{ row.threshold_value }} 元</template>
        </el-table-column>
        <el-table-column prop="triggered_at" label="触发时间" min-width="160">
          <template #default="{ row }">{{ formatDate(row.triggered_at) }}</template>
        </el-table-column>
        <el-table-column prop="is_read" label="状态" min-width="80">
          <template #default="{ row }">
            <el-tag :type="row.is_read?'info':'warning'" size="small"
              :style="{ cursor: 'pointer' }"
              @click="!row.is_read && markRead(row)">
              {{ row.is_read ? '已读' : '未读' }}
            </el-tag>
          </template>
        </el-table-column>
      </el-table>
      <el-pagination
        v-if="logsTotal > 0"
        style="margin-top:16px;justify-content:flex-end;display:flex"
        :current-page="logsPage"
        :page-size="logsPageSize"
        :total="logsTotal"
        layout="total, prev, pager, next"
        @current-change="(p) => { logsPage = p; fetchLogs() }"
      />
    </el-card>

    <el-dialog v-model="dialogVisible" :title="editingAlert ? '编辑预警' : '新增预警'" width="450px">
      <el-form :model="form" label-width="100px">
        <el-form-item label="产品">
          <el-select
            v-model="form.product_id"
            placeholder="搜索并选择产品"
            filterable
            remote
            :remote-method="searchProducts"
            :loading="searchLoading"
            style="width:100%"
            :disabled="!!editingAlert"
          >
            <el-option
              v-for="p in productOptions"
              :key="p.id"
              :label="p.product_name"
              :value="p.id"
            />
          </el-select>
        </el-form-item>
        <el-form-item label="预警类型">
          <el-radio-group v-model="form.alert_type">
            <el-radio value="above">高于阈值时预警</el-radio>
            <el-radio value="below">低于阈值时预警</el-radio>
          </el-radio-group>
        </el-form-item>
        <el-form-item label="阈值(元)">
          <el-input-number v-model="form.threshold" :min="0" :precision="2" style="width:100%"/>
        </el-form-item>
        <el-form-item v-if="editingAlert" label="创建时间">
          <el-date-picker
            v-model="form.created_at"
            type="datetime"
            placeholder="选择创建时间"
            style="width:100%"
            format="YYYY-MM-DD HH:mm:ss"
            value-format="YYYY-MM-DD HH:mm:ss"
          />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="dialogVisible=false">取消</el-button>
        <el-button type="primary" @click="saveAlert" :loading="saving">确定</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { getAlerts, createAlert, updateAlert, deleteAlert, getAlertLogs, markLogRead } from '../../api/alerts'
import { searchProducts as apiSearchProducts } from '../../api/price'

const alerts = ref([])
const logs = ref([])
const loading = ref(false)
const logsLoading = ref(false)
const logsPage = ref(1)
const logsPageSize = ref(20)
const logsTotal = ref(0)

const dialogVisible = ref(false)
const editingAlert = ref(null)
const form = ref({ product_id: null, alert_type: 'above', threshold: 0 })
const saving = ref(false)

const productOptions = ref([])
const searchLoading = ref(false)

const formatDate = (d) => d ? new Date(d).toLocaleString('zh-CN') : '-'
const formatDateOnly = (d) => d ? new Date(d).toLocaleDateString('zh-CN') : '-'

const fetchAlerts = async () => {
  loading.value = true
  try {
    alerts.value = await getAlerts()
  } finally {
    loading.value = false
  }
}

const fetchLogs = async () => {
  logsLoading.value = true
  try {
    const res = await getAlertLogs({ page: logsPage.value, page_size: logsPageSize.value })
    logs.value = res.list
    logsTotal.value = res.total
  } finally {
    logsLoading.value = false
  }
}

const searchProducts = async (keyword) => {
  if (!keyword) {
    productOptions.value = []
    return
  }
  searchLoading.value = true
  try {
    productOptions.value = await apiSearchProducts(keyword)
  } finally {
    searchLoading.value = false
  }
}

const openDialog = (alert = null) => {
  editingAlert.value = alert
  if (alert) {
    form.value = {
      product_id: alert.product_id,
      alert_type: alert.alert_type,
      threshold: alert.threshold,
      created_at: alert.created_at
    }
    productOptions.value = [{ id: alert.product_id, product_name: alert.product_name }]
  } else {
    form.value = { product_id: null, alert_type: 'above', threshold: 0, created_at: null }
    productOptions.value = []
  }
  dialogVisible.value = true
}

const saveAlert = async () => {
  if (!form.value.product_id) return ElMessage.warning('请选择产品')
  if (form.value.threshold <= 0) return ElMessage.warning('请输入有效阈值')

  saving.value = true
  try {
    if (editingAlert.value) {
      const updateData = {
        alert_type: form.value.alert_type,
        threshold: form.value.threshold
      }
      // 如果修改了创建时间，也传递给后端
      if (form.value.created_at && form.value.created_at !== editingAlert.value.created_at) {
        updateData.created_at = form.value.created_at
      }
      await updateAlert(editingAlert.value.id, updateData)
      ElMessage.success('预警已更新')
    } else {
      const res = await createAlert(form.value)
      if (res.triggered) {
        ElMessage.success(res.message || '预警已添加，今日价格已触发预警')
      } else {
        ElMessage.success('预警已添加')
      }
    }
    dialogVisible.value = false
    await fetchAlerts()
    await fetchLogs()
  } finally {
    saving.value = false
  }
}

const toggleActive = async (alert) => {
  await updateAlert(alert.id, { is_active: !alert.is_active })
  ElMessage.success(alert.is_active ? '已禁用' : '已启用')
  await fetchAlerts()
}

const removeAlert = async (id) => {
  try {
    await ElMessageBox.confirm('确认删除此预警？', '删除确认', {
      type: 'warning',
      confirmButtonText: '确认删除',
      cancelButtonText: '取消',
    })
    await deleteAlert(id)
    ElMessage.success('已删除')
    await fetchAlerts()
  } catch {}
}

const markRead = async (log) => {
  try {
    await markLogRead(log.id)
    ElMessage.success('已标记为已读')
    await fetchLogs()
  } catch {}
}

onMounted(() => {
  fetchAlerts()
  fetchLogs()
})
</script>