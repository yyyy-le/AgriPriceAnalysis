<template>
  <div>
    <el-card style="margin-bottom:20px">
      <template #header>
        <span>🔔 价格预警设置</span>
        <el-button type="primary" size="small" style="float:right" @click="dialogVisible=true">新增预警</el-button>
      </template>
      <el-empty v-if="alerts.length===0" description="暂无预警，点击右上角新增"/>
      <el-table v-else :data="alerts" stripe>
        <el-table-column prop="product_name" label="产品名称"/>
        <el-table-column prop="threshold" label="预警阈值(元/kg)"/>
        <el-table-column prop="type" label="类型">
          <template #default="{ row }">
            <el-tag :type="row.type==='above'?'danger':'success'">
              {{ row.type==='above' ? '高于阈值' : '低于阈值' }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column label="操作" width="100">
          <template #default="{ $index }">
            <el-button size="small" type="danger" @click="removeAlert($index)">删除</el-button>
          </template>
        </el-table-column>
      </el-table>
    </el-card>

    <el-dialog v-model="dialogVisible" title="新增价格预警" width="400px">
      <el-form :model="form" label-width="90px">
        <el-form-item label="产品名称">
          <el-input v-model="form.product_name" placeholder="输入产品名称"/>
        </el-form-item>
        <el-form-item label="预警类型">
          <el-radio-group v-model="form.type">
            <el-radio value="above">高于阈值时预警</el-radio>
            <el-radio value="below">低于阈值时预警</el-radio>
          </el-radio-group>
        </el-form-item>
        <el-form-item label="阈值(元/kg)">
          <el-input-number v-model="form.threshold" :min="0" :precision="2"/>
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="dialogVisible=false">取消</el-button>
        <el-button type="primary" @click="addAlert">确定</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import { ElMessage } from 'element-plus'

const alerts = ref(JSON.parse(localStorage.getItem('price_alerts') || '[]'))
const dialogVisible = ref(false)
const form = ref({ product_name: '', type: 'above', threshold: 0 })

const addAlert = () => {
  if (!form.value.product_name) return ElMessage.warning('请输入产品名称')
  alerts.value.push({ ...form.value })
  localStorage.setItem('price_alerts', JSON.stringify(alerts.value))
  dialogVisible.value = false
  form.value = { product_name: '', type: 'above', threshold: 0 }
  ElMessage.success('预警已添加')
}

const removeAlert = (idx) => {
  alerts.value.splice(idx, 1)
  localStorage.setItem('price_alerts', JSON.stringify(alerts.value))
}
</script>