<template>
  <div>
    <el-card style="margin-bottom:16px">
      <el-row :gutter="12">
        <el-col :span="8">
          <el-input v-model="productName" placeholder="搜索产品名称" clearable @change="fetchData"/>
        </el-col>
        <el-col :span="4">
          <el-button type="primary" @click="fetchData">搜索</el-button>
        </el-col>
      </el-row>
    </el-card>

    <el-table :data="list" stripe v-loading="loading" style="width:100%" table-layout="auto">
  <el-table-column prop="time" label="时间" min-width="160">
    <template #default="{ row }">{{ formatDate(row.time) }}</template>
  </el-table-column>
  <el-table-column prop="product_name" label="产品" min-width="100"/>
  <el-table-column prop="category_name" label="分类" min-width="80"/>
  <el-table-column prop="market_name" label="市场" min-width="100"/>
  <el-table-column prop="avg_price" label="均价" min-width="80">
    <template #default="{ row }">
      <el-tag type="warning">{{ row.avg_price }}</el-tag>
    </template>
  </el-table-column>
  <el-table-column prop="min_price" label="最低价" min-width="80"/>
  <el-table-column prop="max_price" label="最高价" min-width="80"/>
  <el-table-column prop="unit" label="单位" min-width="60"/>
  <el-table-column prop="source" label="来源" min-width="80"/>
  <el-table-column label="操作" min-width="140" fixed="right">
    <template #default="{ row }">
      <el-space>
        <el-button size="small" type="primary" @click="openEdit(row)">编辑</el-button>
        <el-button size="small" type="danger" @click="handleDelete(row)">删除</el-button>
      </el-space>
    </template>
  </el-table-column>
</el-table>

    <!-- 编辑弹窗 -->
    <el-dialog v-model="dialogVisible" title="编辑价格记录" width="420px">
      <el-form :model="form" label-width="80px">
        <el-form-item label="产品">
          <el-input :value="form.product_name" disabled/>
        </el-form-item>
        <el-form-item label="时间">
          <el-input :value="formatDate(form.time)" disabled/>
        </el-form-item>
        <el-form-item label="均价">
          <el-input-number v-model="form.avg_price" :precision="2" :min="0" style="width:100%"/>
        </el-form-item>
        <el-form-item label="最低价">
          <el-input-number v-model="form.min_price" :precision="2" :min="0" style="width:100%"/>
        </el-form-item>
        <el-form-item label="最高价">
          <el-input-number v-model="form.max_price" :precision="2" :min="0" style="width:100%"/>
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="dialogVisible = false">取消</el-button>
        <el-button type="primary" :loading="submitLoading" @click="handleEdit">确定</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { getAdminRecords, deleteRecord, updateRecord } from '../../api/admin'

const list = ref([])
const total = ref(0)
const loading = ref(false)
const submitLoading = ref(false)
const productName = ref('')
const page = ref(1)
const pageSize = ref(20)
const dialogVisible = ref(false)
const form = ref({})

const formatDate = (d) => d ? new Date(d).toLocaleString('zh-CN') : '-'

const fetchData = async () => {
  loading.value = true
  try {
    const res = await getAdminRecords({
      page: page.value,
      page_size: pageSize.value,
      product_name: productName.value || undefined
    })
    list.value = res.list
    total.value = res.total
  } finally {
    loading.value = false
  }
}

const openEdit = (row) => {
  form.value = { ...row }
  dialogVisible.value = true
}

const handleEdit = async () => {
  submitLoading.value = true
  try {
    await updateRecord(form.value)
    ElMessage.success('修改成功')
    dialogVisible.value = false
    fetchData()
  } finally {
    submitLoading.value = false
  }
}

const handleDelete = async (row) => {
  await ElMessageBox.confirm(
    `确认删除「${row.product_name}」在 ${formatDate(row.time)} 的价格记录？`,
    '警告',
    { type: 'warning', confirmButtonText: '确认删除', cancelButtonText: '取消' }
  )
  await deleteRecord(row.product_id, row.time)
  ElMessage.success('删除成功')
  fetchData()
}

onMounted(fetchData)
</script>