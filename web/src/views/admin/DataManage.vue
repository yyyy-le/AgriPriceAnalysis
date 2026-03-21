<template>
  <div>
    <!-- 搜索栏 -->
    <el-card style="margin-bottom:16px">
      <el-row :gutter="12" align="middle">
        <!-- 产品名称 -->
        <el-col :span="5">
          <el-input v-model="productName" placeholder="搜索产品名称" clearable @change="fetchData"/>
        </el-col>
        <!-- 分类 -->
        <el-col :span="4">
          <el-select v-model="categoryId" placeholder="选择分类" clearable @change="fetchData" style="width:100%">
            <el-option v-for="c in categories" :key="c.id" :label="c.name" :value="c.id"/>
          </el-select>
        </el-col>
        <!-- 日期范围 -->
        <el-col :span="4">
          <el-date-picker
            v-model="startDate"
            type="date"
            placeholder="开始日期"
            style="width:100%"
            value-format="YYYY-MM-DD"
            clearable
            @change="onDateChange"
          />
        </el-col>
        <el-col :span="1" style="text-align:center;color:#c0c4cc;font-size:13px">至</el-col>
        <el-col :span="4">
          <el-date-picker
            v-model="endDate"
            type="date"
            placeholder="结束日期"
            style="width:100%"
            value-format="YYYY-MM-DD"
            clearable
            @change="onDateChange"
          />
        </el-col>
        <!-- 按钮 -->
        <el-col :span="4">
          <el-button type="primary" @click="fetchData">搜索</el-button>
          <el-button @click="handleReset">重置</el-button>
        </el-col>
        <!-- 统计 -->
        <el-col :span="2" style="text-align:right;white-space:nowrap">
          <div style="font-size:12px;color:#909399">共 <b style="color:#409eff">{{ total }}</b> 个产品</div>
          <div style="font-size:12px;color:#909399"><b style="color:#409eff">{{ totalRecords }}</b> 条记录</div>
        </el-col>
      </el-row>
    </el-card>

    <!-- 产品聚合表格 -->
    <el-card>
      <el-table
        :data="list"
        stripe
        v-loading="loading"
        style="width:100%"
        table-layout="fixed"
        :header-cell-style="{ background:'#f8fafc', color:'#374151', fontWeight:'600' }"
        row-key="product_id"
        :expand-row-keys="expandedRowKeys"
        @expand-change="handleExpandChange"
      >
        <!-- 展开行 -->
        <el-table-column type="expand" width="40">
          <template #default="{ row }">
            <div style="padding:12px 16px 16px 16px;background:#f8fafc">
              <div style="font-size:13px;color:#64748b;margin-bottom:10px">
                「{{ row.product_name }}」近期价格记录
              </div>
              <el-table :data="row.records" size="small" style="width:100%" v-loading="row._loading" element-loading-text="加载中..." table-layout="fixed">
                <template #empty>
                  <span style="color:#94a3b8;font-size:13px">正在加载历史记录...</span>
                </template>
                <el-table-column prop="date" label="日期" min-width="100"/>
                <el-table-column prop="market_name" label="市场/产地" min-width="120"/>
                <el-table-column label="均价" min-width="90">
                  <template #default="{ row: r }">
                    <el-tag type="warning" size="small" effect="plain">{{ r.avg_price }}</el-tag>
                  </template>
                </el-table-column>
                <el-table-column label="最低价" min-width="90">
                  <template #default="{ row: r }">
                    <span style="color:#67c23a">{{ r.min_price }}</span>
                  </template>
                </el-table-column>
                <el-table-column label="最高价" min-width="90">
                  <template #default="{ row: r }">
                    <span style="color:#f56c6c">{{ r.max_price }}</span>
                  </template>
                </el-table-column>
                <el-table-column label="操作" min-width="140">
                  <template #default="{ row: r }">
                    <el-button size="small" type="primary" plain @click="openEdit(r, row)">编辑</el-button>
                    <el-button size="small" type="danger" plain @click="handleDelete(r, row)" style="margin-left:4px">删除</el-button>
                  </template>
                </el-table-column>
              </el-table>
            </div>
          </template>
        </el-table-column>

        <el-table-column label="产品名称" min-width="120">
          <template #default="{ row }">
            <span style="font-weight:600;color:#1e293b;font-size:14px">{{ row.product_name }}</span>
          </template>
        </el-table-column>

        <el-table-column label="分类" min-width="80">
          <template #default="{ row }">
            <el-tag size="small" type="info" effect="plain">{{ row.category_name }}</el-tag>
          </template>
        </el-table-column>

        <el-table-column label="单位" min-width="60">
          <template #default="{ row }">
            <span style="color:#94a3b8;font-size:13px">{{ row.unit }}</span>
          </template>
        </el-table-column>

        <el-table-column label="最新日期" min-width="100">
          <template #default="{ row }">
            <span style="color:#64748b;font-size:13px">{{ row.latest_date }}</span>
          </template>
        </el-table-column>

        <el-table-column label="最新均价" min-width="100">
          <template #default="{ row }">
            <el-tag type="warning" effect="plain" style="font-weight:600">
              {{ row.latest_avg }} 元
            </el-tag>
          </template>
        </el-table-column>

        <el-table-column label="历史区间" min-width="130">
          <template #default="{ row }">
            <span style="color:#67c23a;font-size:13px">{{ row.min_price }}</span>
            <span style="color:#c0c4cc;margin:0 4px">~</span>
            <span style="color:#f56c6c;font-size:13px">{{ row.max_price }}</span>
            <span style="color:#94a3b8;font-size:12px;margin-left:2px">元</span>
          </template>
        </el-table-column>

        <el-table-column label="记录数" min-width="80">
          <template #default="{ row }">
            <el-tag type="primary" size="small" effect="plain">{{ row.record_count }} 条</el-tag>
          </template>
        </el-table-column>

        <el-table-column label="来源" min-width="90">
          <template #default="{ row }">
            <el-tag size="small" effect="plain">{{ row.source }}</el-tag>
          </template>
        </el-table-column>


      </el-table>

      <div style="display:flex;align-items:center;justify-content:space-between;margin-top:16px">
        <span style="font-size:13px;color:#94a3b8">
          第 {{ (page - 1) * pageSize + 1 }} - {{ Math.min(page * pageSize, total) }} 个产品
        </span>
        <el-pagination
          :current-page="page"
          :page-size="pageSize"
          :page-sizes="[10, 20, 50]"
          :total="total"
          layout="sizes, prev, pager, next"
          @size-change="(s) => { pageSize = s; page = 1; fetchData() }"
          @current-change="(p) => { page = p; fetchData() }"
        />
      </div>
    </el-card>

    <!-- 编辑弹窗 -->
    <el-dialog v-model="dialogVisible" title="编辑价格记录" width="440px">
      <el-form :model="form" label-width="80px">
        <el-form-item label="产品">
          <el-input :value="form.product_name" disabled/>
        </el-form-item>
        <el-form-item label="日期">
          <el-input :value="form.date" disabled/>
        </el-form-item>
        <el-divider style="margin:8px 0"/>
        <el-form-item label="最低价">
          <el-input-number v-model="form.min_price" :precision="2" :min="0" style="width:100%"/>
        </el-form-item>
        <el-form-item label="最高价">
          <el-input-number v-model="form.max_price" :precision="2" :min="0" style="width:100%"/>
        </el-form-item>
        <el-form-item label="均价">
          <el-input :value="calcAvg" disabled style="width:100%">
            <template #suffix>
              <span style="color:#e6a23c;font-size:12px">自动计算</span>
            </template>
          </el-input>
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="dialogVisible = false">取消</el-button>
        <el-button type="primary" :loading="submitLoading" @click="handleEdit">保存</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import request from '../../utils/request'
import { deleteRecord, updateRecord } from '../../api/admin'
import { getCategories } from '../../api/price'

const list = ref([])
const total = ref(0)
const totalRecords = ref(0)
const loading = ref(false)
const submitLoading = ref(false)
const productName = ref('')
const categoryId = ref(null)
const startDate = ref(null)
const endDate = ref(null)
const categories = ref([])
const page = ref(1)
const pageSize = ref(20)
const dialogVisible = ref(false)
const expandedRowKeys = ref([]) // 当前展开行的 key 列表
const form = ref({})

const calcAvg = computed(() => {
  const min = form.value.min_price || 0
  const max = form.value.max_price || 0
  return Math.round((min + max) / 2 * 100) / 100
})

const onDateChange = () => {
  fetchData()
}

const handleReset = () => {
  productName.value = ''
  categoryId.value = null
  startDate.value = null
  endDate.value = null
  page.value = 1
  fetchData()
}

const formatDate = (d) => {
  if (!d) return '-'
  const date = new Date(d)
  return `${date.getFullYear()}/${date.getMonth() + 1}/${date.getDate()}`
}

// 获取按产品聚合的数据
const fetchData = async () => {
  expandedRowKeys.value = [] // 翻页或搜索时收起所有展开行
  loading.value = true
  try {
    const params = { page: page.value, page_size: pageSize.value }
    if (productName.value) params.product_name = productName.value
    if (categoryId.value) params.category_id = categoryId.value
    if (startDate.value) params.start_date = startDate.value
    if (endDate.value) params.end_date = endDate.value

    const res = await request.get('/api/admin/data/products', { params })
    list.value = (res.list || []).map(item => ({ ...item, _expanded: false, records: [], _loading: false }))
    total.value = res.total || 0
    totalRecords.value = res.total_records || 0
  } finally {
    loading.value = false
  }
}

// el-table expand-change 事件：row=当前行, expandedRows=所有展开行
const handleExpandChange = async (row, expandedRows) => {
  const isExpanded = expandedRows.some(r => r.product_id === row.product_id)
  row._expanded = isExpanded
  // 同步维护展开行 key 列表，支持多行同时展开
  if (isExpanded) {
    if (!expandedRowKeys.value.includes(row.product_id)) {
      expandedRowKeys.value.push(row.product_id)
    }
  } else {
    expandedRowKeys.value = expandedRowKeys.value.filter(k => k !== row.product_id)
  }
  // 已有数据不重复请求
  if (!isExpanded || row.records.length > 0) return

  row._loading = true
  try {
    const res = await request.get('/api/admin/data/records', {
      params: {
          product_id: row.product_id,
          page: 1,
          page_size: 30,
          ...(startDate.value ? { start_date: startDate.value } : {}),
          ...(endDate.value ? { end_date: endDate.value } : {})
        }
    })
    row.records = (res.list || []).map(r => ({
      ...r,
      date: formatDate(r.time),
      product_name: row.product_name,
      unit: row.unit,
    }))
  } catch (e) {
    row.records = []
  } finally {
    row._loading = false
  }
}

const openEdit = (record, parentRow) => {
  form.value = { ...record, _parentRow: parentRow }
  dialogVisible.value = true
}

const handleEdit = async () => {
  submitLoading.value = true
  try {
    form.value.avg_price = calcAvg.value
    await updateRecord(form.value)
    ElMessage.success('修改成功')
    dialogVisible.value = false
    const parent = form.value._parentRow
    if (parent) { parent.records = []; parent._expanded = false }
    fetchData()
  } finally {
    submitLoading.value = false
  }
}

const handleDelete = async (record, parentRow) => {
  await ElMessageBox.confirm(
    `确认删除「${record.product_name}」在 ${record.date} 的价格记录？`,
    '警告',
    { type: 'warning', confirmButtonText: '确认删除', cancelButtonText: '取消' }
  )
  await deleteRecord(record.product_id, record.time)
  ElMessage.success('删除成功')
  parentRow.records = []
  parentRow._expanded = false
  fetchData()
}

onMounted(async () => {
  categories.value = await getCategories()
  await fetchData()
})
</script>

<style>
/* 展开行：去掉内边距，撑满整行 */
.el-table__expanded-cell {
  padding: 0 !important;
}
/* 展开行内的滚动容器撑满 */
.el-table__expanded-cell .el-scrollbar__wrap {
  overflow: visible !important;
  width: 100% !important;
}
.el-table__expanded-cell .el-scrollbar {
  width: 100% !important;
}
/* 展开行内嵌套表格撑满 */
.el-table__expanded-cell .el-table {
  width: 100% !important;
}
.el-table__expanded-cell .el-table__inner-wrapper {
  width: 100% !important;
}
/* 展开行外层 div 撑满 */
.el-table__expanded-cell > div {
  width: 100% !important;
  padding: 12px 16px !important;
  box-sizing: border-box !important;
}
</style>