<template>
  <div>
    <el-card style="margin-bottom:16px">
      <el-row :gutter="12">
        <el-col :span="6">
          <el-select v-model="filters.action" placeholder="操作类型" clearable @change="fetchData" style="width:100%">
            <el-option v-for="a in actions" :key="a" :label="actionLabel(a)" :value="a"/>
          </el-select>
        </el-col>
        <el-col :span="6">
          <el-input v-model="filters.admin_name" placeholder="管理员名称" clearable @change="fetchData"/>
        </el-col>
        <el-col :span="4">
          <el-button type="primary" @click="fetchData">查询</el-button>
          <el-button @click="reset" style="margin-left:8px">重置</el-button>
        </el-col>
      </el-row>
    </el-card>

    <el-card>
      <el-table :data="list" stripe v-loading="loading" style="width:100%">
        <el-table-column prop="created_at" label="时间" min-width="170">
          <template #default="{ row }">{{ formatDate(row.created_at) }}</template>
        </el-table-column>
        <el-table-column prop="admin_name" label="管理员" min-width="100"/>
        <el-table-column prop="action" label="操作" min-width="140">
          <template #default="{ row }">
            <el-tag :type="actionType(row.action)">{{ actionLabel(row.action) }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="target" label="对象" min-width="160"/>
        <el-table-column prop="detail" label="详情" min-width="200"/>
        <el-table-column prop="ip" label="IP" min-width="120"/>
      </el-table>

      <el-pagination
        style="margin-top:16px;justify-content:flex-end;display:flex"
        :current-page="filters.page"
        :page-size="filters.page_size"
        :total="total"
        layout="total, prev, pager, next"
        @current-change="(p) => { filters.page = p; fetchData() }"
      />
    </el-card>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { getLogs } from '../../api/admin'

const loading = ref(false)
const list = ref([])
const total = ref(0)
const actions = ref([])
const filters = ref({ page: 1, page_size: 20, action: '', admin_name: '' })

const ACTION_LABELS = {
  create_user: '新增用户',
  update_user: '编辑用户',
  update_user_state: '修改用户状态',
  update_user_admin: '设置管理员',
  delete_user: '删除用户',
  delete_price_record: '删除价格记录',
  update_price_record: '编辑价格记录',
  import_csv: 'CSV导入',
  start_crawl: '启动爬虫',
  pause_crawl: '暂停爬虫',
  resume_crawl: '继续爬虫',
  cancel_crawl: '取消爬虫',
}

const ACTION_TYPES = {
  delete_user: 'danger',
  delete_price_record: 'danger',
  start_crawl: 'success',
  import_csv: 'success',
  pause_crawl: 'warning',
  cancel_crawl: 'warning',
}

const actionLabel = (a) => ACTION_LABELS[a] || a
const actionType = (a) => ACTION_TYPES[a] || 'info'
const formatDate = (d) => d ? new Date(d).toLocaleString('zh-CN') : '-'

const fetchData = async () => {
  loading.value = true
  try {
    const params = { ...filters.value }
    if (!params.action) delete params.action
    if (!params.admin_name) delete params.admin_name
    const res = await getLogs(params)
    list.value = res.list
    total.value = res.total
    if (res.actions?.length) actions.value = res.actions
  } finally {
    loading.value = false
  }
}

const reset = () => {
  filters.value = { page: 1, page_size: 20, action: '', admin_name: '' }
  fetchData()
}

onMounted(fetchData)
</script>
