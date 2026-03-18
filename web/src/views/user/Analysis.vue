<template>
  <div>
    <el-card style="margin-bottom:20px">
      <el-row :gutter="12" align="middle">
        <el-col :span="8">
          <el-input
            v-model="searchName"
            placeholder="输入产品名称搜索"
            clearable
            @input="onSearchInput"
            @clear="productOptions = []"
          />
        </el-col>
        <el-col :span="8">
          <el-select
            v-model="selectedProductId"
            placeholder="选择产品"
            style="width:100%"
            :disabled="productOptions.length === 0"
          >
            <el-option
              v-for="p in productOptions"
              :key="p.id"
              :label="`${p.product_name}（${p.category_name}）`"
              :value="p.id"
            />
          </el-select>
        </el-col>
        <el-col :span="4">
          <el-select v-model="days" style="width:100%">
            <el-option label="近7天" :value="7"/>
            <el-option label="近30天" :value="30"/>
            <el-option label="近90天" :value="90"/>
          </el-select>
        </el-col>
        <el-col :span="4">
          <el-button type="primary" style="width:100%" :loading="loading" @click="fetchTrend">
            查看趋势
          </el-button>
        </el-col>
      </el-row>
    </el-card>

    <el-card v-if="trendData.length">
      <template #header>
        <span>📈 {{ selectedProductName }} 价格趋势</span>
      </template>
      <div ref="chartRef" style="height:420px"/>
    </el-card>

    <el-empty v-else description="请搜索并选择一个产品，点击查看趋势" style="margin-top:60px"/>
  </div>
</template>

<script setup>
import { ref, nextTick } from 'vue'
import * as echarts from 'echarts'
import { ElMessage } from 'element-plus'
import { searchProducts, getPriceTrend } from '../../api/price'

const searchName = ref('')
const selectedProductId = ref(null)
const selectedProductName = ref('')
const days = ref(30)
const trendData = ref([])
const productOptions = ref([])
const chartRef = ref(null)
const loading = ref(false)
let chart = null
let searchTimer = null

const onSearchInput = () => {
  clearTimeout(searchTimer)
  if (!searchName.value.trim()) {
    productOptions.value = []
    selectedProductId.value = null
    return
  }
  searchTimer = setTimeout(async () => {
    productOptions.value = await searchProducts(searchName.value.trim())
  }, 300)
}

const fetchTrend = async () => {
  if (!selectedProductId.value) {
    ElMessage.warning('请先搜索并选择一个产品')
    return
  }
  loading.value = true
  try {
    const selected = productOptions.value.find(p => p.id === selectedProductId.value)
    selectedProductName.value = selected?.product_name || ''
    const res = await getPriceTrend({ product_id: selectedProductId.value, days: days.value })
    if (!res.length) {
      ElMessage.info('该产品暂无价格数据')
      return
    }
    trendData.value = res
    await nextTick()
    renderChart()
  } finally {
    loading.value = false
  }
}

const renderChart = () => {
  if (!chartRef.value) return
  if (!chart) {
    chart = echarts.init(chartRef.value)
  }
  chart.setOption({
    tooltip: { trigger: 'axis' },
    legend: {
      data: ['均价', '最低价', '最高价'],
      bottom: 0,          // ← 图例移到底部
      left: 'center',
    },
    grid: {
      left: 60,
      right: 20,
      top: 30,
      bottom: 60,         // ← 留出底部图例空间
    },
    xAxis: {
      type: 'category',
      data: trendData.value.map(d => d.date),
      axisLabel: { fontSize: 11 }
    },
    yAxis: {
      type: 'value',
      name: '元/kg',
      nameTextStyle: { fontSize: 11 }
    },
    series: [
      {
        name: '均价', type: 'line', smooth: true,
        data: trendData.value.map(d => Number(d.avg_price).toFixed(2)),
        lineStyle: { color: '#409eff' },
        itemStyle: { color: '#409eff' },
        areaStyle: { opacity: 0.1 }
      },
      {
        name: '最低价', type: 'line', smooth: true,
        data: trendData.value.map(d => Number(d.min_price).toFixed(2)),
        lineStyle: { color: '#67c23a', type: 'dashed' },
        itemStyle: { color: '#67c23a' }
      },
      {
        name: '最高价', type: 'line', smooth: true,
        data: trendData.value.map(d => Number(d.max_price).toFixed(2)),
        lineStyle: { color: '#f56c6c', type: 'dashed' },
        itemStyle: { color: '#f56c6c' }
      }
    ]
  })
}
</script>