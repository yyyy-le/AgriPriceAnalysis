<template>
  <div>
    <el-card>
      <template #header><span>📋 爬虫数据来源统计</span></template>
      <el-table :data="list" stripe v-loading="loading" style="width:100%">
        <el-table-column prop="source" label="数据来源" width="200"/>
        <el-table-column prop="total_records" label="总记录数" width="150"/>
        <el-table-column prop="last_run" label="最后更新时间">
          <template #default="{ row }">{{ formatDate(row.last_run) }}</template>
        </el-table-column>
        <el-table-column label="状态" width="100">
          <template #default="{ row }">
            <el-tag type="success">正常</el-tag>
          </template>
        </el-table-column>
      </el-table>
    </el-card>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { getLogs } from '../../api/admin'

const list = ref([])
const loading = ref(false)

const formatDate = (d) => d ? new Date(d).toLocaleString('zh-CN') : '-'

onMounted(async () => {
  loading.value = true
  try {
    list.value = await getLogs()
  } finally {
    loading.value = false
  }
})
</script>