<template>
  <div style="max-width:500px;margin:0 auto">
    <el-card>
      <template #header><span>👤 个人信息</span></template>
      <el-descriptions :column="1" border>
        <el-descriptions-item label="用户名">{{ username }}</el-descriptions-item>
        <el-descriptions-item label="角色">
          <el-tag type="success">普通用户</el-tag>
        </el-descriptions-item>
      </el-descriptions>
    </el-card>

    <el-card style="margin-top:20px">
      <template #header><span>🔒 修改密码</span></template>
      <el-form :model="form" label-width="90px">
        <el-form-item label="原密码">
          <el-input v-model="form.old_password" type="password" show-password/>
        </el-form-item>
        <el-form-item label="新密码">
          <el-input v-model="form.new_password" type="password" show-password/>
        </el-form-item>
        <el-form-item label="确认密码">
          <el-input v-model="form.confirm_password" type="password" show-password/>
        </el-form-item>
        <el-form-item>
          <el-button type="primary" @click="changePassword">保存修改</el-button>
        </el-form-item>
      </el-form>
    </el-card>
  </div>
</template>

<script setup>
import { ref, computed } from 'vue'
import { ElMessage } from 'element-plus'
import { useAuthStore } from '../../stores/auth'

const authStore = useAuthStore()
const username = computed(() => authStore.username)
const form = ref({ old_password: '', new_password: '', confirm_password: '' })

const changePassword = () => {
  if (!form.value.old_password || !form.value.new_password) return ElMessage.warning('请填写完整')
  if (form.value.new_password !== form.value.confirm_password) return ElMessage.error('两次密码不一致')
  // TODO: 接入修改密码接口
  ElMessage.success('密码修改成功（接口待接入）')
  form.value = { old_password: '', new_password: '', confirm_password: '' }
}
</script>