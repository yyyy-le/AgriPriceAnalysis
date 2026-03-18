<template>
  <div>
    <!-- 第一行：统计卡片 -->
    <el-row :gutter="16" style="margin-bottom:20px">
      <el-col :span="6" v-for="item in stats" :key="item.label">
        <el-card shadow="hover" style="text-align:center;padding:8px 0">
          <div style="font-size:26px;font-weight:bold;color:#409eff">{{ item.value }}</div>
          <div style="color:#999;margin-top:6px;font-size:13px">{{ item.label }}</div>
        </el-card>
      </el-col>
    </el-row>

    <!-- 第二行：折线图 + 饼图 -->
    <el-row :gutter="16" style="margin-bottom:20px">
      <el-col :span="16">
        <el-card shadow="hover">
          <template #header><span>📈 近30天全品类均价走势</span></template>
          <div ref="lineRef" style="height:280px"/>
        </el-card>
      </el-col>
      <el-col :span="8">
        <el-card shadow="hover">
          <template #header><span>🥧 各分类数据占比</span></template>
          <div ref="pieRef" style="height:280px"/>
        </el-card>
      </el-col>
    </el-row>

    <!-- 第三行：最贵 + 最便宜 -->
    <el-row :gutter="16" style="margin-bottom:20px">
      <el-col :span="12">
        <el-card shadow="hover">
          <template #header><span>🔺 今日最贵 Top10（元/kg）</span></template>
          <div ref="expensiveRef" style="height:300px"/>
        </el-card>
      </el-col>
      <el-col :span="12">
        <el-card shadow="hover">
          <template #header><span>🔻 今日最便宜 Top10（元/kg）</span></template>
          <div ref="cheapestRef" style="height:300px"/>
        </el-card>
      </el-col>
    </el-row>

    <!-- 第四行：价格波动 + 市场分布 -->
    <el-row :gutter="16">
      <el-col :span="12">
        <el-card shadow="hover">
          <template #header><span>📊 近30天价格波动最大 Top8（%）</span></template>
          <div ref="volatilityRef" style="height:280px"/>
        </el-card>
      </el-col>
      <el-col :span="12">
        <el-card shadow="hover">
          <template #header><span>🏪 各市场/产地数据量</span></template>
          <div ref="marketRef" style="height:280px"/>
        </el-card>
      </el-col>
    </el-row>
  </div>
</template>

<script setup>
import { ref, onMounted, onUnmounted } from 'vue'
import * as echarts from 'echarts'
import {
  getSummary, getDailyAvg, getCategoryStats,
  getTopExpensive, getTopCheapest, getPriceVolatility, getMarketStats
} from '../../api/price'

const lineRef = ref(null)
const pieRef = ref(null)
const expensiveRef = ref(null)
const cheapestRef = ref(null)
const volatilityRef = ref(null)
const marketRef = ref(null)

const stats = ref([
  { label: '价格记录总数', value: '-' },
  { label: '产品种类', value: '-' },
  { label: '商品分类', value: '-' },
  { label: '最新数据时间', value: '-' },
])

let charts = []

const initChart = (el) => {
  const c = echarts.init(el)
  charts.push(c)
  return c
}

const renderLine = (data) => {
  const c = initChart(lineRef.value)
  c.setOption({
    tooltip: { trigger: 'axis' },
    grid: { left: 50, right: 20, top: 20, bottom: 30 },
    xAxis: { type: 'category', data: data.map(d => d.date), axisLabel: { fontSize: 11 } },
    yAxis: { type: 'value', name: '元/kg', nameTextStyle: { fontSize: 11 } },
    series: [{
      type: 'line', smooth: true,
      data: data.map(d => d.avg_price),
      areaStyle: { opacity: 0.15 },
      lineStyle: { color: '#409eff' },
      itemStyle: { color: '#409eff' }
    }]
  })
}

const renderPie = (data) => {
  const c = initChart(pieRef.value)
  c.setOption({
    tooltip: { trigger: 'item', formatter: '{b}: {c}条 ({d}%)' },
    legend: { orient: 'vertical', left: 'left', textStyle: { fontSize: 11 } },
    series: [{
      type: 'pie', radius: ['35%', '65%'],
      center: ['60%', '50%'],
      data: data.map(d => ({ name: d.category_name, value: d.count })),
      label: { fontSize: 11 }
    }]
  })
}

const renderBar = (el, data, nameKey, valueKey, color) => {
  const c = initChart(el)
  c.setOption({
    tooltip: { trigger: 'axis' },
    grid: { left: 100, right: 30, top: 10, bottom: 30 },
    xAxis: { type: 'value', axisLabel: { fontSize: 11 } },
    yAxis: {
      type: 'category',
      data: data.map(d => d[nameKey]),
      axisLabel: { fontSize: 11, width: 90, overflow: 'truncate' }
    },
    series: [{
      type: 'bar',
      data: data.map(d => d[valueKey]),
      itemStyle: { color },
      label: { show: true, position: 'right', fontSize: 11 }
    }]
  })
}

onMounted(async () => {
  const [summary, daily, category, expensive, cheapest, volatility, market] = await Promise.all([
    getSummary(), getDailyAvg(), getCategoryStats(),
    getTopExpensive(), getTopCheapest(), getPriceVolatility(), getMarketStats()
  ])

  // 统计卡片
  stats.value[0].value = summary.total_records?.toLocaleString() ?? '-'
  stats.value[1].value = summary.total_products?.toLocaleString() ?? '-'
  stats.value[2].value = summary.total_categories?.toLocaleString() ?? '-'
  stats.value[3].value = summary.latest_update
    ? new Date(summary.latest_update).toLocaleDateString('zh-CN')
    : '-'

  // 图表
  renderLine(daily)
  renderPie(category)
  renderBar(expensiveRef.value, expensive.reverse(), 'product_name', 'avg_price', '#f56c6c')
  renderBar(cheapestRef.value, cheapest.reverse(), 'product_name', 'avg_price', '#67c23a')
  renderBar(volatilityRef.value, volatility.reverse(), 'product_name', 'volatility', '#e6a23c')
  renderBar(marketRef.value, market.reverse(), 'market_name', 'count', '#409eff')

  // 响应式
  const resize = () => charts.forEach(c => c.resize())
  window.addEventListener('resize', resize)
})

onUnmounted(() => {
  charts.forEach(c => c.dispose())
})
</script>