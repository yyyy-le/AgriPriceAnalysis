<template>
  <div>
    <!-- 搜索栏 -->
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

    <!-- 趋势图 -->
    <el-card v-if="trendData.length" style="margin-bottom:20px">
      <template #header>
        <span>📈 {{ selectedProductName }} 价格趋势</span>
      </template>
      <div ref="chartRef" style="height:380px"/>
    </el-card>

    <!-- 价格预测 -->
    <template v-if="trendData.length">
      <el-card style="margin-bottom:20px">
        <template #header>
          <div style="display:flex;align-items:center;justify-content:space-between">
            <span>🔮 价格预测（未来{{ predictDays }}天）</span>
            <div style="display:flex;align-items:center;gap:12px">
              <el-select v-model="predictDays" size="small" style="width:100px">
                <el-option label="未来7天" :value="7"/>
                <el-option label="未来14天" :value="14"/>
                <el-option label="未来30天" :value="30"/>
              </el-select>
              <el-button type="primary" size="small" :loading="predictLoading" @click="fetchPredict">
                开始预测
              </el-button>
            </div>
          </div>
        </template>

        <!-- 预测结果 -->
        <div v-if="predictData">
          <!-- 趋势摘要 -->
          <el-row :gutter="16" style="margin-bottom:20px">
            <el-col :span="8">
              <el-card shadow="never" style="text-align:center;background:#f8f9fa">
                <div style="font-size:13px;color:#999;margin-bottom:4px">当前价格</div>
                <div style="font-size:24px;font-weight:bold;color:#303133">
                  {{ predictData.current_price }}
                  <span style="font-size:13px;color:#999">元/{{ predictData.unit }}</span>
                </div>
              </el-card>
            </el-col>
            <el-col :span="8">
              <el-card shadow="never" style="text-align:center;background:#f8f9fa">
                <div style="font-size:13px;color:#999;margin-bottom:4px">{{ predictDays }}天后预计</div>
                <div style="font-size:24px;font-weight:bold" :style="{color: predictData.trend === '上涨' ? '#f56c6c' : '#67c23a'}">
                  {{ predictData.predictions[predictData.predictions.length-1]?.predicted_price }}
                  <span style="font-size:13px;color:#999">元/{{ predictData.unit }}</span>
                </div>
              </el-card>
            </el-col>
            <el-col :span="8">
              <el-card shadow="never" style="text-align:center;background:#f8f9fa">
                <div style="font-size:13px;color:#999;margin-bottom:4px">预测趋势</div>
                <div style="font-size:24px;font-weight:bold" :style="{color: predictData.trend === '上涨' ? '#f56c6c' : '#67c23a'}">
                  {{ predictData.trend === '上涨' ? '📈' : '📉' }}
                  {{ predictData.trend }} {{ Math.abs(predictData.change_pct) }}%
                </div>
              </el-card>
            </el-col>
          </el-row>

          <!-- 预测图表 -->
          <div ref="predictChartRef" style="height:320px"/>

          <!-- 预测明细表 -->
          <el-table :data="predictData.predictions" stripe size="small" style="margin-top:16px">
            <el-table-column prop="date" label="日期" width="120"/>
            <el-table-column label="预测均价" width="120">
              <template #default="{ row }">
                <el-tag type="warning">{{ row.predicted_price }} 元</el-tag>
              </template>
            </el-table-column>
            <el-table-column label="预测区间">
              <template #default="{ row }">
                <span style="color:#999;font-size:13px">
                  {{ row.lower_bound }} ~ {{ row.upper_bound }} 元
                </span>
              </template>
            </el-table-column>
            <el-table-column label="与当前比较" width="140">
              <template #default="{ row }">
                <span :style="{color: row.predicted_price > predictData.current_price ? '#f56c6c' : '#67c23a'}">
                  {{ row.predicted_price > predictData.current_price ? '▲' : '▼' }}
                  {{ Math.abs(row.predicted_price - predictData.current_price).toFixed(2) }} 元
                </span>
              </template>
            </el-table-column>
          </el-table>
        </div>

        <el-empty v-else-if="!predictLoading" description="点击「开始预测」查看价格预测" :image-size="80"/>
        <div v-else style="text-align:center;padding:40px;color:#999">
          <el-icon style="font-size:32px;animation:spin 1s linear infinite"><Loading/></el-icon>
          <div style="margin-top:12px">正在运行预测模型...</div>
        </div>
      </el-card>

      <!-- AI 分析报告 -->
      <el-card v-if="predictData">
        <template #header>
          <div style="display:flex;align-items:center;justify-content:space-between">
            <span>🤖 AI 分析报告</span>
            <el-button type="success" size="small" :loading="analysisLoading" @click="fetchAnalysis">
              {{ analysisText ? '重新生成' : '生成报告' }}
            </el-button>
          </div>
        </template>

        <!-- 加载中 -->
        <div v-if="analysisLoading && !analysisText" style="text-align:center;padding:40px;color:#999">
          <div style="margin-top:12px">AI 正在分析中...</div>
        </div>

        <!-- 渲染 Markdown 内容 -->
        <div v-else-if="analysisText || analysisLoading" class="ai-report-content" v-html="renderedAnalysis"></div>

        <el-empty v-else description="点击「生成报告」获取AI分析" :image-size="80"/>
      </el-card>
    </template>

    <el-empty v-else description="请搜索并选择一个产品，点击查看趋势" style="margin-top:60px"/>
  </div>
</template>

<script setup>
import { ref, nextTick, watch, computed } from 'vue'
import * as echarts from 'echarts'
import { ElMessage } from 'element-plus'
import { Loading } from '@element-plus/icons-vue'
import { searchProducts, getPriceTrend, predictPrice, predictAnalysis } from '../../api/price'

const searchName = ref('')
const selectedProductId = ref(null)
const selectedProductName = ref('')
const days = ref(7)
const trendData = ref([])
const productOptions = ref([])
const chartRef = ref(null)
const predictChartRef = ref(null)
const loading = ref(false)
const predictLoading = ref(false)
const analysisLoading = ref(false)
const predictDays = ref(7)
const predictData = ref(null)
const analysisText = ref('')
let chart = null
let predictChart = null
let searchTimer = null

// 简单的 Markdown 转 HTML 函数
function renderMarkdown(text) {
  if (!text) return ''

  let html = text
    // 转义 HTML 特殊字符（防 XSS），但保留我们自己插入的标签
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')

  // 处理标题 ### ## #
  html = html.replace(/^### (.+)$/gm, '<h3>$1</h3>')
  html = html.replace(/^## (.+)$/gm, '<h2>$1</h2>')
  html = html.replace(/^# (.+)$/gm, '<h1>$1</h1>')

  // 处理分割线 ---
  html = html.replace(/^---+$/gm, '<hr/>')

  // 处理加粗 **text**
  html = html.replace(/\*\*(.+?)\*\*/g, '<strong>$1</strong>')

  // 处理斜体 *text*（单个*，排除已处理的**）
  html = html.replace(/(?<!\*)\*(?!\*)(.+?)(?<!\*)\*(?!\*)/g, '<em>$1</em>')

  // 处理无序列表项（- 开头）
  html = html.replace(/^[-•] (.+)$/gm, '<li>$1</li>')

  // 将连续的 li 包裹在 ul 中
  html = html.replace(/(<li>[\s\S]*?<\/li>)(\n<li>[\s\S]*?<\/li>)*/g, (match) => {
    return '<ul>' + match + '</ul>'
  })

  // 处理段落：将空行分隔的文本块包裹在 <p> 中
  // 先按两个以上换行符分割成段落
  const blocks = html.split(/\n{2,}/)
  html = blocks.map(block => {
    block = block.trim()
    if (!block) return ''
    // 如果已经是 HTML 标签开头，不再包裹
    if (/^<(h[1-6]|ul|ol|li|hr|blockquote|div|p)/.test(block)) {
      return block
    }
    // 处理段落内的换行为 <br>
    block = block.replace(/\n/g, '<br/>')
    return '<p>' + block + '</p>'
  }).join('\n')

  return html
}

// 计算属性：渲染后的分析文本（流式追加时实时更新）
const renderedAnalysis = computed(() => {
  const text = analysisText.value
  if (!text) return ''
  // 流式加载时末尾加光标
  const cursor = analysisLoading.value ? '<span class="ai-cursor">▋</span>' : ''
  return renderMarkdown(text) + cursor
})

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
  predictData.value = null
  analysisText.value = ''
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
    renderTrendChart()
  } finally {
    loading.value = false
  }
}

const fetchPredict = async () => {
  if (!selectedProductId.value) return
  predictLoading.value = true
  predictData.value = null
  analysisText.value = ''
  try {
    const res = await predictPrice({
      product_id: selectedProductId.value,
      days: predictDays.value
    })
    if (res.error) {
      ElMessage.warning(res.error)
      return
    }
    predictData.value = res
    await nextTick()
    renderPredictChart()
  } catch (e) {
    ElMessage.error('预测失败，请稍后重试')
  } finally {
    predictLoading.value = false
  }
}

const fetchAnalysis = async () => {
  if (!selectedProductId.value || !predictData.value) return
  analysisLoading.value = true
  analysisText.value = ''
  try {
    await predictAnalysis(
      { product_id: selectedProductId.value, days: predictDays.value },
      (chunk) => { analysisText.value += chunk }
    )
  } catch (e) {
    ElMessage.error('生成报告失败')
  } finally {
    analysisLoading.value = false
  }
}

const renderTrendChart = () => {
  if (!chartRef.value) return
  if (!chart) chart = echarts.init(chartRef.value)
  chart.setOption({
    tooltip: { trigger: 'axis' },
    legend: { data: ['均价', '最低价', '最高价'], bottom: 0, left: 'center' },
    grid: { left: 60, right: 20, top: 30, bottom: 60 },
    xAxis: {
      type: 'category',
      data: trendData.value.map(d => d.date),
      axisLabel: { fontSize: 11 }
    },
    yAxis: { type: 'value', name: '元/kg', nameTextStyle: { fontSize: 11 } },
    series: [
      {
        name: '均价', type: 'line', smooth: true,
        data: trendData.value.map(d => Number(d.avg_price).toFixed(2)),
        lineStyle: { color: '#409eff' }, itemStyle: { color: '#409eff' },
        areaStyle: { opacity: 0.1 }
      },
      {
        name: '最低价', type: 'line', smooth: true,
        data: trendData.value.map(d => Number(d.min_price).toFixed(2)),
        lineStyle: { color: '#67c23a', type: 'dashed' }, itemStyle: { color: '#67c23a' }
      },
      {
        name: '最高价', type: 'line', smooth: true,
        data: trendData.value.map(d => Number(d.max_price).toFixed(2)),
        lineStyle: { color: '#f56c6c', type: 'dashed' }, itemStyle: { color: '#f56c6c' }
      }
    ]
  })
}

const renderPredictChart = () => {
  if (!predictChartRef.value || !predictData.value) return
  if (!predictChart) predictChart = echarts.init(predictChartRef.value)

  const historyDates = predictData.value.history.map(d => d.date)
  const historyPrices = predictData.value.history.map(d => d.price)
  const predictDates = predictData.value.predictions.map(d => d.date)
  const predictPrices = predictData.value.predictions.map(d => d.predicted_price)
  const upperBound = predictData.value.predictions.map(d => d.upper_bound)
  const lowerBound = predictData.value.predictions.map(d => d.lower_bound)

  const allDates = [...historyDates, ...predictDates]

  predictChart.setOption({
    tooltip: { trigger: 'axis' },
    legend: { data: ['历史价格', '预测价格', '置信区间上限', '置信区间下限'], bottom: 0 },
    grid: { left: 60, right: 20, top: 30, bottom: 60 },
    xAxis: { type: 'category', data: allDates, axisLabel: { fontSize: 10, rotate: 30 } },
    yAxis: { type: 'value', name: '元', nameTextStyle: { fontSize: 11 } },
    series: [
      {
        name: '历史价格', type: 'line', smooth: true,
        data: [...historyPrices, ...new Array(predictDates.length).fill(null)],
        lineStyle: { color: '#409eff' }, itemStyle: { color: '#409eff' },
        symbol: 'none'
      },
      {
        name: '预测价格', type: 'line', smooth: true,
        data: [...new Array(historyDates.length - 1).fill(null), historyPrices[historyPrices.length - 1], ...predictPrices],
        lineStyle: { color: '#e6a23c', type: 'dashed', width: 2 },
        itemStyle: { color: '#e6a23c' },
        symbol: 'circle', symbolSize: 5
      },
      {
        name: '置信区间上限', type: 'line', smooth: true,
        data: [...new Array(historyDates.length).fill(null), ...upperBound],
        lineStyle: { color: '#f56c6c', opacity: 0.4, type: 'dotted' },
        itemStyle: { color: '#f56c6c' }, symbol: 'none', areaStyle: { opacity: 0.05 }
      },
      {
        name: '置信区间下限', type: 'line', smooth: true,
        data: [...new Array(historyDates.length).fill(null), ...lowerBound],
        lineStyle: { color: '#67c23a', opacity: 0.4, type: 'dotted' },
        itemStyle: { color: '#67c23a' }, symbol: 'none'
      },
    ]
  })
}

// 切换产品时重置
watch(selectedProductId, () => {
  predictData.value = null
  analysisText.value = ''
})
</script>

<style scoped>
@keyframes spin {
  from { transform: rotate(0deg) }
  to { transform: rotate(360deg) }
}

@keyframes blink {
  0%, 100% { opacity: 1 }
  50% { opacity: 0 }
}

/* AI 分析报告样式 */
.ai-report-content {
  font-size: 14px;
  line-height: 1.9;
  color: #303133;
}

.ai-report-content :deep(h1),
.ai-report-content :deep(h2),
.ai-report-content :deep(h3) {
  font-weight: 600;
  color: #1e293b;
  margin: 16px 0 8px;
}

.ai-report-content :deep(h1) { font-size: 20px; }
.ai-report-content :deep(h2) { font-size: 17px; }
.ai-report-content :deep(h3) { font-size: 15px; }

.ai-report-content :deep(p) {
  margin: 0 0 12px;
}

.ai-report-content :deep(strong) {
  font-weight: 600;
  color: #1e293b;
}

.ai-report-content :deep(em) {
  font-style: italic;
  color: #555;
}

.ai-report-content :deep(ul) {
  padding-left: 20px;
  margin: 8px 0 12px;
}

.ai-report-content :deep(li) {
  margin-bottom: 4px;
  list-style-type: disc;
}

.ai-report-content :deep(hr) {
  border: none;
  border-top: 1px solid #e8eaf0;
  margin: 16px 0;
}

.ai-cursor {
  display: inline-block;
  animation: blink 1s infinite;
  color: #409eff;
  font-weight: bold;
}
</style>