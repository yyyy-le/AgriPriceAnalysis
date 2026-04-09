<template>
  <div>
    <!-- 说明 -->
    <el-card style="margin-bottom:16px">
      <template #header><span>CSV 导入说明</span></template>
      <p style="color:#666;font-size:14px;margin-bottom:12px">请按以下格式准备 CSV 文件（UTF-8 编码），第一行为表头：</p>
      <el-table :data="sampleData" border size="small" style="width:100%;margin-bottom:12px">
        <el-table-column prop="产品名称" label="产品名称" min-width="90"/>
        <el-table-column prop="一级分类" label="一级分类" min-width="90"/>
        <el-table-column prop="二级分类" label="二级分类" min-width="90"/>
        <el-table-column prop="市场产地" label="市场/产地" min-width="90"/>
        <el-table-column prop="均价" label="均价" min-width="70"/>
        <el-table-column prop="最低价" label="最低价" min-width="70"/>
        <el-table-column prop="最高价" label="最高价" min-width="70"/>
        <el-table-column prop="单位" label="单位" min-width="60"/>
        <el-table-column prop="日期" label="日期" min-width="110"/>
      </el-table>
      <p style="color:#e6a23c;font-size:13px;margin-bottom:10px">
        ⚠️ 日期格式支持 <b>YYYY-MM-DD</b> 或 <b>YYYY/M/D</b>，如 2026-03-16 或 2026/3/16
      </p>
      <p style="color:#909399;font-size:13px;margin-bottom:10px">
        二级分类为空时，产品将直接归入一级分类。
      </p>
      <el-button type="primary" plain size="small" @click="downloadTemplate">下载模板文件</el-button>
    </el-card>

    <!-- 上传 -->
    <el-card style="margin-bottom:16px">
      <template #header><span>上传文件</span></template>
      <el-upload
        ref="uploadRef"
        :auto-upload="false"
        :limit="1"
        accept=".csv"
        :on-change="handleFileChange"
        :on-exceed="() => ElMessage.warning('每次只能上传一个文件')"
        drag
      >
        <div style="padding:30px 0">
          <div style="font-size:40px">📁</div>
          <div style="margin-top:10px;color:#606266;font-size:14px">拖拽 CSV 文件到此处，或点击选择文件</div>
          <div style="margin-top:4px;font-size:12px;color:#909399">仅支持 .csv 格式</div>
        </div>
      </el-upload>
      <div style="margin-top:16px;display:flex;gap:10px;align-items:center">
        <el-button type="primary" :loading="uploading" :disabled="!selectedFile" @click="handleUpload">
          {{ uploading ? '导入中...' : '开始导入' }}
        </el-button>
        <el-button @click="handleReset">重置</el-button>
        <span v-if="selectedFile" style="font-size:13px;color:#409eff">已选择：{{ selectedFile.name }}</span>
      </div>
    </el-card>

    <!-- 结果 -->
    <el-card v-if="result">
      <template #header><span>导入结果</span></template>
      <el-row :gutter="20" style="margin-bottom:16px">
        <el-col :span="8">
          <el-statistic title="成功导入" :value="result.saved">
            <template #suffix><span style="color:#67c23a"> 条</span></template>
          </el-statistic>
        </el-col>
        <el-col :span="8">
          <el-statistic title="跳过（重复）" :value="result.skipped">
            <template #suffix><span style="color:#e6a23c"> 条</span></template>
          </el-statistic>
        </el-col>
        <el-col :span="8">
          <el-statistic title="错误" :value="result.errors.length">
            <template #suffix><span style="color:#f56c6c"> 条</span></template>
          </el-statistic>
        </el-col>
      </el-row>
      <template v-if="result.errors.length > 0">
        <el-divider/>
        <p style="color:#f56c6c;font-size:14px;margin-bottom:8px">错误详情：</p>
        <el-scrollbar max-height="200px">
          <div v-for="(err, i) in result.errors" :key="i" style="font-size:13px;color:#f56c6c;padding:2px 0">
            {{ err }}
          </div>
        </el-scrollbar>
      </template>
    </el-card>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import { ElMessage } from 'element-plus'
import { importCsv } from '../../api/admin'

const uploadRef = ref()
const selectedFile = ref(null)
const uploading = ref(false)
const result = ref(null)

const sampleData = [
  { 产品名称: '大白菜', 一级分类: '蔬菜', 二级分类: '水菜', 市场产地: '冀鲁', 均价: '1.08', 最低价: '0.95', 最高价: '1.2', 单位: '斤', 日期: '2026-03-16' },
  { 产品名称: '苹果', 一级分类: '水果', 二级分类: '', 市场产地: '陕西', 均价: '3.5', 最低价: '3.0', 最高价: '4.0', 单位: '斤', 日期: '2026-03-16' },
]

const handleFileChange = (file) => {
  selectedFile.value = file.raw
}

const handleUpload = async () => {
  if (!selectedFile.value) return
  uploading.value = true
  result.value = null
  try {
    const res = await importCsv(selectedFile.value)
    result.value = res
    if (res.saved > 0) {
      ElMessage.success(`导入完成，成功 ${res.saved} 条`)
    } else {
      ElMessage.warning('没有新增数据，可能全部重复或存在错误')
    }
  } finally {
    uploading.value = false
  }
}

const handleReset = () => {
  selectedFile.value = null
  result.value = null
  uploadRef.value?.clearFiles()
}

const downloadTemplate = () => {
  const header = '产品名称,一级分类,二级分类,市场/产地,均价,最低价,最高价,单位,日期'
  const row1 = '大白菜,蔬菜,水菜,冀鲁,1.08,0.95,1.2,斤,2026-03-16'
  const row2 = '苹果,水果,,陕西,3.5,3.0,4.0,斤,2026-03-16'
  const csv = [header, row1, row2].join('\n')
  const blob = new Blob(['\ufeff' + csv], { type: 'text/csv;charset=utf-8' })
  const url = URL.createObjectURL(blob)
  const a = document.createElement('a')
  a.href = url
  a.download = '价格数据导入模板.csv'
  a.click()
  URL.revokeObjectURL(url)
}
</script>
