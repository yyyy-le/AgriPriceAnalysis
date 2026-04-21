<template>
  <div>
    <!-- 第一行：统计卡片 -->
    <el-row :gutter="16" style="margin-bottom:16px">
      <el-col :span="6" v-for="item in stats" :key="item.label">
        <el-card shadow="never" style="border:1px solid #e8eaf0">
          <div style="display:flex;align-items:center;gap:12px">
            <div :style="`width:44px;height:44px;border-radius:10px;background:${item.bg};display:flex;align-items:center;justify-content:center;flex-shrink:0;font-size:20px`">
              {{ item.icon }}
            </div>
            <div>
              <div :style="`font-size:22px;font-weight:600;color:${item.color}`">{{ item.value }}</div>
              <div style="color:#94a3b8;font-size:12px;margin-top:2px">{{ item.label }}</div>
            </div>
          </div>
        </el-card>
      </el-col>
    </el-row>

    <!-- 第二行：词云 + 产地地图 -->
    <el-row :gutter="16" style="margin-bottom:16px">
      <el-col :span="12">
        <el-card shadow="never" style="border:1px solid #e8eaf0">
          <template #header>
            <span style="font-size:14px;font-weight:500;color:#1e293b">☁️ 产品词云（出现频次）</span>
          </template>
          <div ref="wordcloudRef" style="height:280px"/>
        </el-card>
      </el-col>
      <el-col :span="12">
        <el-card shadow="never" style="border:1px solid #e8eaf0">
          <template #header>
            <div style="display:flex;align-items:center;justify-content:space-between">
              <span style="font-size:14px;font-weight:500;color:#1e293b">🗺️ 产地省份分布</span>
              <span style="font-size:12px;color:#94a3b8">颜色越深数据量越多</span>
            </div>
          </template>
          <div ref="mapRef" style="height:280px"/>
        </el-card>
      </el-col>
    </el-row>

    <!-- 第三行：最贵 + 最便宜 -->
    <el-row :gutter="16" style="margin-bottom:16px">
      <el-col :span="12">
        <el-card shadow="never" style="border:1px solid #e8eaf0">
          <template #header>
            <span style="font-size:14px;font-weight:500;color:#1e293b">🔺 最贵 Top10（元/kg）</span>
          </template>
          <div ref="expensiveRef" style="height:300px"/>
        </el-card>
      </el-col>
      <el-col :span="12">
        <el-card shadow="never" style="border:1px solid #e8eaf0">
          <template #header>
            <span style="font-size:14px;font-weight:500;color:#1e293b">🔻 最便宜 Top10（元/kg）</span>
          </template>
          <div ref="cheapestRef" style="height:300px"/>
        </el-card>
      </el-col>
    </el-row>

    <!-- 第四行：波动折线图（全宽） -->
    <el-row :gutter="16" style="margin-bottom:16px">
      <el-col :span="24">
        <el-card shadow="never" style="border:1px solid #e8eaf0">
          <template #header>
            <span style="font-size:14px;font-weight:500;color:#1e293b">📈 近30天价格波动最大 Top8 走势</span>
          </template>
          <div ref="trendRef" style="height:320px"/>
        </el-card>
      </el-col>
    </el-row>

    <!-- 第五行：进口水果价格排行 -->
    <el-row :gutter="16" style="margin-bottom:16px">
      <el-col :span="24">
        <el-card shadow="never" style="border:1px solid #e8eaf0">
          <template #header>
            <span style="font-size:14px;font-weight:500;color:#1e293b">🍇 进口水果价格排行（元/kg）</span>
          </template>
          <div ref="importedFruitsRef" style="height:520px"/>
        </el-card>
      </el-col>
    </el-row>
  </div>
</template>

<script setup>
import { ref, onMounted, onUnmounted } from 'vue'
import * as echarts from 'echarts'
import 'echarts-wordcloud'
import {
  getSummary,
  getTopExpensive, getTopCheapest,
  getWordCloud, getVolatilityTrend, getProvinceStats,
  getImportedFruits
} from '../../api/price'

const wordcloudRef = ref(null)
const mapRef = ref(null)
const expensiveRef = ref(null)
const cheapestRef = ref(null)
const trendRef = ref(null)
const importedFruitsRef = ref(null)

const stats = ref([
  { label: '价格记录总数', value: '-', icon: '📋', color: '#6366f1', bg: '#ede9fe' },
  { label: '产品种类',     value: '-', icon: '🥬', color: '#10b981', bg: '#d1fae5' },
  { label: '商品分类',     value: '-', icon: '🏷️', color: '#f59e0b', bg: '#fef3c7' },
  { label: '最新数据时间', value: '-', icon: '🕐', color: '#ec4899', bg: '#fce7f3' },
])

let charts = []
let resizeHandler = null

const initChart = (el) => {
  const c = echarts.init(el)
  charts.push(c)
  return c
}

const renderWordCloud = (data) => {
  const c = initChart(wordcloudRef.value)
  c.setOption({
    tooltip: { show: true },
    series: [{
      type: 'wordCloud',
      shape: 'circle',
      left: 'center',
      top: 'center',
      width: '90%',
      height: '90%',
      sizeRange: [12, 48],
      rotationRange: [-45, 45],
      rotationStep: 15,
      gridSize: 8,
      drawOutOfBound: false,
      textStyle: {
        fontFamily: 'Microsoft YaHei, sans-serif',
        fontWeight: 'bold',
        color: () => {
          const colors = ['#6366f1', '#8b5cf6', '#10b981', '#3b82f6', '#f59e0b', '#ec4899', '#14b8a6', '#f97316']
          return colors[Math.floor(Math.random() * colors.length)]
        }
      },
      emphasis: {
        textStyle: { shadowBlur: 10, shadowColor: '#6366f1' }
      },
      data: data.map(d => ({ name: d.name, value: d.value }))
    }]
  })
}

const renderMap = async (data) => {
  const res = await fetch('/china.json')
  const chinaJson = await res.json()
  echarts.registerMap('china', chinaJson)
  const c = initChart(mapRef.value)
  c.setOption({
    tooltip: {
      trigger: 'item',
      formatter: (p) => p.value ? `${p.name}：${p.value} 条` : `${p.name}：暂无数据`
    },
    visualMap: {
      min: 0,
      max: Math.max(...data.map(d => d.value), 1),
      left: 'left',
      bottom: 10,
      text: ['多', '少'],
      textStyle: { fontSize: 11, color: '#64748b' },
      inRange: { color: ['#e0e7ff', '#6366f1'] },
      calculable: true,
      itemWidth: 12,
      itemHeight: 80,
    },
    series: [{
      type: 'map',
      map: 'china',
      roam: false,
      zoom: 1.1,
      label: { show: false },
      emphasis: {
        label: { show: true, fontSize: 11 },
        itemStyle: { areaColor: '#818cf8' }
      },
      itemStyle: {
        areaColor: '#f1f5f9',
        borderColor: '#cbd5e1',
        borderWidth: 0.5,
      },
      data,
    }]
  })
}

const renderBar = (el, data, nameKey, valueKey, color) => {
  const c = initChart(el)
  c.setOption({
    tooltip: { trigger: 'axis' },
    grid: { left: 100, right: 50, top: 10, bottom: 30 },
    xAxis: { type: 'value', axisLabel: { fontSize: 11 } },
    yAxis: {
      type: 'category',
      data: data.map(d => d[nameKey]),
      axisLabel: { fontSize: 11, width: 90, overflow: 'truncate' }
    },
    series: [{
      type: 'bar',
      barMaxWidth: 20,
      data: data.map(d => d[valueKey]),
      itemStyle: { color, borderRadius: [0, 4, 4, 0] },
      label: { show: true, position: 'right', fontSize: 11 }
    }]
  })
}

const renderTrend = (trendData) => {
  if (!trendData || !trendData.dates) return
  const colors = ['#6366f1', '#10b981', '#f59e0b', '#ec4899', '#3b82f6', '#14b8a6', '#8b5cf6', '#f97316']
  const c = initChart(trendRef.value)
  c.setOption({
    tooltip: {
      trigger: 'axis',
      formatter: (params) => {
        let str = `${params[0].axisValue}<br/>`
        params.forEach(p => {
          if (p.value != null) {
            str += `${p.marker}${p.seriesName}：${p.value} 元<br/>`
          }
        })
        return str
      }
    },
    legend: {
      bottom: 0,
      textStyle: { fontSize: 11 },
      itemWidth: 12,
      itemHeight: 8,
    },
    grid: { left: 50, right: 20, top: 20, bottom: 60 },
    xAxis: {
      type: 'category',
      data: trendData.dates,
      axisLabel: { fontSize: 10, rotate: 30 }
    },
    yAxis: {
      type: 'value',
      name: '元/kg',
      nameTextStyle: { fontSize: 11 },
      axisLabel: { fontSize: 11 }
    },
    series: trendData.series.map((s, i) => ({
      name: s.name,
      type: 'line',
      smooth: true,
      symbol: 'none',
      data: trendData.dates.map(date => {
        const found = s.data.find(d => d.date === date)
        return found ? found.price : null
      }),
      lineStyle: { color: colors[i % colors.length], width: 2 },
      itemStyle: { color: colors[i % colors.length] },
      connectNulls: false,
    }))
  })
}

const renderImportedFruits = (data) => {
  const c = initChart(importedFruitsRef.value)
  const names = data.map(d => d.product_name)
  const avgPrices = data.map(d => Number(d.avg_price))
  const minPrices = data.map(d => Number(d.min_price))
  const maxPrices = data.map(d => Number(d.max_price))
  c.setOption({
    tooltip: {
      trigger: 'axis',
      axisPointer: { type: 'shadow' },
      formatter: (params) => {
        const name = params[0].axisValue
        const avg = params.find(p => p.seriesName === '均价')?.value ?? '-'
        const min = params.find(p => p.seriesName === '最低价')?.value ?? '-'
        const max = params.find(p => p.seriesName === '最高价')?.value ?? '-'
        return `${name}<br/>均价：${avg} 元/kg<br/>最低：${min}<br/>最高：${max}`
      }
    },
    legend: { data: ['最低价', '均价', '最高价'], top: 0, textStyle: { fontSize: 11 } },
    grid: { left: 80, right: 20, top: 30, bottom: 20 },
    xAxis: { type: 'value', name: '元/kg', nameTextStyle: { fontSize: 11 }, axisLabel: { fontSize: 10 } },
    yAxis: { type: 'category', data: names, axisLabel: { fontSize: 11 } },
    series: [
      { name: '最低价', type: 'bar', data: minPrices, itemStyle: { color: '#10b981' }, barMaxWidth: 12 },
      { name: '均价',   type: 'bar', data: avgPrices, itemStyle: { color: '#6366f1' }, barMaxWidth: 12 },
      { name: '最高价', type: 'bar', data: maxPrices, itemStyle: { color: '#f56c6c' }, barMaxWidth: 12 },
    ]
  })
}

onMounted(async () => {
  const [summary, expensive, cheapest, wordcloud, trend, province, importedFruits] = await Promise.all([
    getSummary(),
    getTopExpensive(),
    getTopCheapest(),
    getWordCloud(),
    getVolatilityTrend(),
    getProvinceStats(),
    getImportedFruits(),
  ])

  stats.value[0].value = summary.total_records?.toLocaleString() ?? '-'
  stats.value[1].value = summary.total_products?.toLocaleString() ?? '-'
  stats.value[2].value = summary.total_categories?.toLocaleString() ?? '-'
  stats.value[3].value = summary.latest_update
    ? new Date(summary.latest_update).toLocaleDateString('zh-CN')
    : '-'

  renderWordCloud(wordcloud)
  await renderMap(province)
  renderBar(expensiveRef.value, expensive.reverse(), 'product_name', 'avg_price', '#f56c6c')
  renderBar(cheapestRef.value, cheapest.reverse(), 'product_name', 'avg_price', '#10b981')
  renderTrend(trend)
  renderImportedFruits(importedFruits.reverse())

  resizeHandler = () => charts.forEach(c => c.resize())
  window.addEventListener('resize', resizeHandler)
})

onUnmounted(() => {
  if (resizeHandler) window.removeEventListener('resize', resizeHandler)
  charts.forEach(c => c.dispose())
})
</script>