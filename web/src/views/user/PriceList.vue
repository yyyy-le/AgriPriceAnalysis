<template>
  <div style="width:100%">
    <el-card style="margin-bottom:20px">
      <el-row :gutter="12">
        <el-col :span="8">
          <el-input v-model="filters.product_name" placeholder="搜索产品名称" clearable @change="fetchData"/>
        </el-col>
        <el-col :span="5">
          <el-select v-model="filters.parent_category_id" placeholder="一级分类" clearable @change="onParentCatChange" style="width:100%">
            <el-option v-for="c in parentCategories" :key="c.id" :label="c.name" :value="c.id"/>
          </el-select>
        </el-col>
        <el-col :span="5">
          <el-select v-model="filters.category_id" placeholder="二级分类" clearable :disabled="!filters.parent_category_id" @change="fetchData" style="width:100%">
            <el-option v-for="c in childCategories" :key="c.id" :label="c.name" :value="c.id"/>
          </el-select>
        </el-col>
        <el-col :span="4">
          <el-button type="primary" @click="fetchData">查询</el-button>
          <el-button @click="resetFilters" style="margin-left:8px">重置</el-button>
        </el-col>
      </el-row>
    </el-card>

    <el-card style="width:100%">
      <el-table
        :data="list"
        stripe
        v-loading="loading"
        style="width:100%"
        table-layout="fixed"
      >
        <el-table-column prop="time" label="日期" min-width="110">
          <template #default="{ row }">{{ formatDate(row.time) }}</template>
        </el-table-column>
        <el-table-column prop="product_name" label="产品名称" min-width="120"/>
        <el-table-column prop="parent_category_name" label="一级分类" min-width="90"/>
        <el-table-column prop="category_name" label="二级分类" min-width="90"/>
        <el-table-column prop="spec_info" label="规格" min-width="100"/>
        <el-table-column prop="unit_info" label="单位" min-width="70"/>
        <el-table-column prop="market_name" label="市场/产地" min-width="120"/>
        <el-table-column prop="avg_price" label="均价" min-width="90">
          <template #default="{ row }">
            <el-tag type="warning">{{ row.avg_price?.toFixed(2) }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="min_price" label="最低价" min-width="90">
          <template #default="{ row }">{{ row.min_price?.toFixed(2) }}</template>
        </el-table-column>
        <el-table-column prop="max_price" label="最高价" min-width="90">
          <template #default="{ row }">{{ row.max_price?.toFixed(2) }}</template>
        </el-table-column>
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
import { ref, computed, onMounted } from 'vue'
import { getPriceList, getCategories } from '../../api/price'

const loading = ref(false)
const list = ref([])
const total = ref(0)
const allCategories = ref([])
const filters = ref({ page: 1, page_size: 20, product_name: '', parent_category_id: null, category_id: null })

const parentCategories = computed(() => allCategories.value.filter(c => !c.parent_id))
const childCategories = computed(() =>
  filters.value.parent_category_id
    ? allCategories.value.filter(c => c.parent_id === filters.value.parent_category_id)
    : []
)

const onParentCatChange = () => {
  filters.value.category_id = null
  fetchData()
}

const resetFilters = () => {
  filters.value = { page: 1, page_size: 20, product_name: '', parent_category_id: null, category_id: null }
  fetchData()
}

const formatDate = (d) => d ? new Date(d).toLocaleDateString('zh-CN') : '-'

const fetchData = async () => {
  loading.value = true
  try {
    const params = { ...filters.value }
    if (!params.product_name) delete params.product_name
    if (!params.category_id) delete params.category_id
    if (!params.parent_category_id) delete params.parent_category_id
    const res = await getPriceList(params)
    list.value = res.list
    total.value = res.total
  } finally {
    loading.value = false
  }
}

onMounted(async () => {
  allCategories.value = await getCategories()
  await fetchData()
})
</script>