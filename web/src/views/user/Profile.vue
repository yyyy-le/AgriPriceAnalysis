<template>
  <div class="profile-page">

    <!-- 顶部用户信息横幅 -->
    <div class="profile-banner">
      <div class="avatar-circle">{{ username?.charAt(0)?.toUpperCase() }}</div>
      <div class="banner-info">
        <div class="banner-name">{{ username }}</div>
        <div class="banner-role">
          <el-tag :type="isAdmin ? 'danger' : 'success'" size="small" effect="light">
            {{ isAdmin ? '🛡️ 管理员' : '👤 普通用户' }}
          </el-tag>
        </div>
      </div>
      <!-- 退出按钮 -->
      <div style="margin-left:auto">
        <el-button @click="handleLogout" class="logout-btn">
          退出登录
        </el-button>
      </div>
    </div>

    <!-- 主体内容：两列布局 -->
    <el-row :gutter="20" style="margin-top:24px">

      <!-- 左列：个人信息 -->
      <el-col :xs="24" :sm="24" :md="10" :lg="8">
        <el-card class="info-card">
          <template #header>
            <span class="card-title">📋 账号信息</span>
          </template>

          <div class="info-item">
            <span class="info-label">用户名</span>
            <span class="info-value">{{ username }}</span>
          </div>
          <el-divider style="margin:12px 0"/>
          <div class="info-item">
            <span class="info-label">角色</span>
            <el-tag :type="isAdmin ? 'danger' : 'success'" size="small">
              {{ isAdmin ? '管理员' : '普通用户' }}
            </el-tag>
          </div>
          <el-divider style="margin:12px 0"/>
          <div class="info-item">
            <span class="info-label">账号状态</span>
            <el-tag type="success" size="small">✅ 正常</el-tag>
          </div>

          <el-alert
            style="margin-top:20px"
            title="安全建议"
            type="info"
            :closable="false"
            show-icon
          >
            <template #default>
              <div style="font-size:12px;line-height:1.9;color:#606266;margin-top:4px">
                · 定期更换密码，保护账号安全<br/>
                · 密码建议包含字母和数字<br/>
                · 请勿将密码透露给他人
              </div>
            </template>
          </el-alert>
        </el-card>
      </el-col>

      <!-- 右列：修改密码 -->
      <el-col :xs="24" :sm="24" :md="14" :lg="16">
        <el-card class="password-card">
          <template #header>
            <div style="display:flex;align-items:center;justify-content:space-between">
              <span class="card-title">🔒 修改密码</span>
              <span style="font-size:12px;color:#94a3b8">为了账号安全，请定期更换密码</span>
            </div>
          </template>

          <el-form
            ref="formRef"
            :model="form"
            :rules="rules"
            label-width="100px"
            label-position="left"
            status-icon
            style="max-width:480px"
          >
            <el-form-item label="原密码" prop="old_password">
              <el-input
                v-model="form.old_password"
                type="password"
                show-password
                placeholder="请输入当前密码"
                size="large"
                autocomplete="current-password"
              />
            </el-form-item>

            <el-divider style="margin:4px 0 20px">
              <span style="font-size:12px;color:#c0c4cc">设置新密码</span>
            </el-divider>

            <el-form-item label="新密码" prop="new_password">
              <el-input
                v-model="form.new_password"
                type="password"
                show-password
                placeholder="至少6位，建议包含字母和数字"
                size="large"
                autocomplete="new-password"
              />
            </el-form-item>

            <el-form-item label="确认密码" prop="confirm_password">
              <el-input
                v-model="form.confirm_password"
                type="password"
                show-password
                placeholder="请再次输入新密码"
                size="large"
                autocomplete="new-password"
                @keyup.enter="handleSubmit"
              />
            </el-form-item>

            <!-- 密码强度 -->
            <div v-if="form.new_password" class="strength-wrap">
              <span style="font-size:12px;color:#909399;margin-right:8px;white-space:nowrap">密码强度：</span>
              <el-progress
                :percentage="passwordStrength.percent"
                :color="passwordStrength.color"
                :stroke-width="6"
                style="flex:1"
                :show-text="false"
              />
              <span :style="`font-size:12px;margin-left:8px;color:${passwordStrength.color};white-space:nowrap`">
                {{ passwordStrength.label }}
              </span>
            </div>

            <el-form-item style="margin-top:28px">
              <el-button
                type="primary"
                size="large"
                :loading="loading"
                style="width:160px"
                @click="handleSubmit"
              >
                {{ loading ? '保存中...' : '保存修改' }}
              </el-button>
              <el-button size="large" @click="handleReset" style="margin-left:12px">
                重置
              </el-button>
            </el-form-item>
          </el-form>
        </el-card>
      </el-col>

    </el-row>
  </div>
</template>

<script setup>
import { ref, computed } from 'vue'
import { ElMessage } from 'element-plus'
import { useAuthStore } from '../../stores/auth'
import request from '../../utils/request'

const authStore = useAuthStore()
const username = computed(() => authStore.username)
const isAdmin = computed(() => authStore.role === 'admin')

const formRef = ref()
const loading = ref(false)

const form = ref({
  old_password: '',
  new_password: '',
  confirm_password: '',
})

// 密码强度计算
const passwordStrength = computed(() => {
  const pwd = form.value.new_password
  if (!pwd) return { percent: 0, color: '#dcdfe6', label: '' }
  let score = 0
  if (pwd.length >= 6) score++
  if (pwd.length >= 10) score++
  if (/[A-Z]/.test(pwd)) score++
  if (/[0-9]/.test(pwd)) score++
  if (/[^A-Za-z0-9]/.test(pwd)) score++
  if (score <= 1) return { percent: 20, color: '#f56c6c', label: '弱' }
  if (score <= 2) return { percent: 50, color: '#e6a23c', label: '中' }
  if (score <= 3) return { percent: 75, color: '#409eff', label: '强' }
  return { percent: 100, color: '#67c23a', label: '非常强' }
})

// 校验规则
const validateConfirm = (rule, value, callback) => {
  if (!value) {
    callback(new Error('请再次输入新密码'))
  } else if (value !== form.value.new_password) {
    callback(new Error('两次输入的密码不一致'))
  } else {
    callback()
  }
}

const validateNewPassword = (rule, value, callback) => {
  if (!value) {
    callback(new Error('请输入新密码'))
  } else if (value.length < 6) {
    callback(new Error('新密码至少6位'))
  } else if (value === form.value.old_password) {
    callback(new Error('新密码不能与原密码相同'))
  } else {
    callback()
  }
}

const rules = {
  old_password: [{ required: true, message: '请输入原密码', trigger: 'blur' }],
  new_password: [{ required: true, validator: validateNewPassword, trigger: 'blur' }],
  confirm_password: [{ required: true, validator: validateConfirm, trigger: 'blur' }],
}

const handleSubmit = async () => {
  const valid = await formRef.value.validate().catch(() => false)
  if (!valid) return
  loading.value = true
  try {
    await request.put('/api/users/password', {
      old_password: form.value.old_password,
      new_password: form.value.new_password,
    })
    ElMessage.success('密码修改成功，即将重新登录...')
    formRef.value.resetFields()
    setTimeout(() => {
      authStore.logout()
      window.location.href = '/login'
    }, 1500)
  } catch (e) {
    // 错误由 request.js 拦截器统一处理
  } finally {
    loading.value = false
  }
}

const handleReset = () => {
  formRef.value.resetFields()
}

const handleLogout = async () => {
  await authStore.logout()
  window.location.href = '/login'
}
</script>

<style scoped>
.profile-page {
  width: 100%;
  box-sizing: border-box;
}

/* 顶部横幅 */
.profile-banner {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  border-radius: 12px;
  padding: 28px 32px;
  display: flex;
  align-items: center;
  gap: 20px;
  color: #fff;
}

.avatar-circle {
  width: 68px;
  height: 68px;
  border-radius: 50%;
  background: rgba(255, 255, 255, 0.25);
  border: 3px solid rgba(255, 255, 255, 0.6);
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 28px;
  font-weight: 700;
  color: #fff;
  flex-shrink: 0;
}

.banner-info {
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.banner-name {
  font-size: 22px;
  font-weight: 700;
  letter-spacing: 0.5px;
}

/* 卡片 */
.info-card,
.password-card {
  border-radius: 10px;
  border: 1px solid #e8eaf0;
  box-shadow: 0 2px 12px rgba(0, 0, 0, 0.04);
  height: 100%;
}

.card-title {
  font-size: 15px;
  font-weight: 600;
  color: #1e293b;
}

/* 信息行 */
.info-item {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 6px 0;
}

.info-label {
  font-size: 13px;
  color: #64748b;
  font-weight: 500;
}

.info-value {
  font-size: 14px;
  color: #1e293b;
  font-weight: 500;
}

/* 退出按钮 */
.logout-btn {
  background: rgba(255, 255, 255, 0.15) !important;
  border: 1px solid rgba(255, 255, 255, 0.55) !important;
  color: #fff !important;
  border-radius: 8px !important;
  font-weight: 500 !important;
  transition: background 0.2s;
}
.logout-btn:hover {
  background: rgba(255, 255, 255, 0.28) !important;
}

/* 密码强度条 */
.strength-wrap {
  display: flex;
  align-items: center;
  margin: -8px 0 16px;
  padding-left: 100px;
}
</style>