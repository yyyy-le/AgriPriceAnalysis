<template>
  <div class="auth-container">
    <!-- 背景装饰 -->
    <div class="bg-grid"/>
    <div class="bg-blob blob-1"/>
    <div class="bg-blob blob-2"/>

    <div class="auth-card">
      <!-- Logo 区域 -->
      <div class="logo-area">
        <div class="logo-icon">🌾</div>
        <div class="logo-text">农产品物价数据分析系统</div>
      </div>

      <!-- Tab 切换 -->
      <div class="tab-switcher">
        <button
          :class="['tab-btn', { active: activeTab === 'login' }]"
          @click="switchTab('login')"
        >登录</button>
        <button
          :class="['tab-btn', { active: activeTab === 'register' }]"
          @click="switchTab('register')"
        >注册</button>
        <div class="tab-indicator" :style="activeTab === 'login' ? 'left:4px' : 'left:calc(50% + 4px)'"/>
      </div>

      <!-- 登录表单 -->
      <transition name="slide-fade" mode="out-in">
        <div v-if="activeTab === 'login'" key="login" class="form-wrap">
          <el-form :model="loginForm" :rules="loginRules" ref="loginRef">
            <el-form-item prop="username">
              <div class="input-label">用户名 / 手机号</div>
              <el-input
                v-model="loginForm.username"
                placeholder="请输入用户名或手机号"
                size="large"
                prefix-icon="User"
                class="custom-input"
              />
            </el-form-item>

            <el-form-item prop="password">
              <div class="input-label">密码</div>
              <el-input
                v-model="loginForm.password"
                type="password"
                placeholder="请输入密码"
                size="large"
                prefix-icon="Lock"
                show-password
                class="custom-input"
                @keyup.enter="handleLogin"
              />
            </el-form-item>

            <el-button
              type="primary"
              size="large"
              class="submit-btn"
              :loading="loginLoading"
              @click="handleLogin"
            >
              <span v-if="!loginLoading">登 录</span>
              <span v-else>登录中...</span>
            </el-button>

            <div class="form-footer">
              <span>还没有账号？</span>
              <a @click="switchTab('register')">立即注册 →</a>
            </div>
          </el-form>
        </div>

        <!-- 注册表单 -->
        <div v-else key="register" class="form-wrap">
          <el-form :model="regForm" :rules="regRules" ref="regRef">
            <!-- 用户名 -->
            <el-form-item prop="username">
              <div class="input-label">用户名</div>
              <el-input
                v-model="regForm.username"
                placeholder="字母、数字，3~20位"
                size="large"
                prefix-icon="User"
                class="custom-input"
              />
            </el-form-item>

            <!-- 手机号 -->
            <el-form-item prop="cellphone">
              <div class="input-label">手机号</div>
              <el-input
                v-model="regForm.cellphone"
                placeholder="请输入11位手机号"
                size="large"
                prefix-icon="Phone"
                class="custom-input"
                maxlength="11"
              />
            </el-form-item>

            <!-- 密码 -->
            <el-form-item prop="password">
              <div class="input-label">密码</div>
              <el-input
                v-model="regForm.password"
                type="password"
                placeholder="至少6位，建议包含字母和数字"
                size="large"
                prefix-icon="Lock"
                show-password
                class="custom-input"
              />
              <!-- 密码强度条 -->
              <div v-if="regForm.password" class="pwd-strength">
                <div
                  v-for="i in 4" :key="i"
                  class="strength-bar"
                  :class="{ active: pwdStrength >= i, [`level-${pwdStrength}`]: pwdStrength >= i }"
                />
                <span class="strength-label" :class="`level-${pwdStrength}`">
                  {{ ['', '弱', '中', '强', '极强'][pwdStrength] }}
                </span>
              </div>
            </el-form-item>

            <!-- 确认密码 -->
            <el-form-item prop="confirmPassword">
              <div class="input-label">确认密码</div>
              <el-input
                v-model="regForm.confirmPassword"
                type="password"
                placeholder="再次输入密码"
                size="large"
                prefix-icon="Lock"
                show-password
                class="custom-input"
                @keyup.enter="handleRegister"
              />
            </el-form-item>

            <el-button
              type="primary"
              size="large"
              class="submit-btn"
              :loading="regLoading"
              @click="handleRegister"
            >
              <span v-if="!regLoading">注 册</span>
              <span v-else>注册中...</span>
            </el-button>

            <div class="form-footer">
              <span>已有账号？</span>
              <a @click="switchTab('login')">立即登录 →</a>
            </div>
          </el-form>
        </div>
      </transition>
    </div>

  </div>
</template>

<script setup>
import { ref, computed } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { useAuthStore } from '../stores/auth'
import { register } from '../api/register'

const router = useRouter()
const authStore = useAuthStore()

// Tab
const activeTab = ref('login')
const showDevTip = ref(true)

const switchTab = (tab) => {
  activeTab.value = tab
}

// ================== 登录 ==================
const loginRef = ref()
const loginLoading = ref(false)
const loginForm = ref({ username: '', password: '' })

const loginRules = {
  username: [{ required: true, message: '请输入用户名或手机号', trigger: 'blur' }],
  password: [{ required: true, message: '请输入密码', trigger: 'blur' }],
}

const handleLogin = async () => {
  await loginRef.value.validate(async (valid) => {
    if (!valid) return
    loginLoading.value = true
    try {
      await authStore.login(loginForm.value.username, loginForm.value.password)
      ElMessage.success('登录成功')
      router.push(authStore.role === 'admin' ? '/admin/users' : '/dashboard')
    } catch {
      // 错误由 request.js 统一处理
    } finally {
      loginLoading.value = false
    }
  })
}

// ================== 注册 ==================
const regRef = ref()
const regLoading = ref(false)

const regForm = ref({
  username: '',
  cellphone: '',
  password: '',
  confirmPassword: '',
})

// 密码强度
const pwdStrength = computed(() => {
  const pwd = regForm.value.password
  if (!pwd) return 0
  let score = 0
  if (pwd.length >= 6) score++
  if (pwd.length >= 10) score++
  if (/[A-Z]/.test(pwd) || /[0-9]/.test(pwd)) score++
  if (/[^A-Za-z0-9]/.test(pwd)) score++
  return Math.max(1, score)
})

const validateConfirm = (rule, value, callback) => {
  if (!value) return callback(new Error('请确认密码'))
  if (value !== regForm.value.password) return callback(new Error('两次密码不一致'))
  callback()
}

const regRules = {
  username: [
    { required: true, message: '请输入用户名', trigger: 'blur' },
    { min: 3, max: 20, message: '用户名3~20位', trigger: 'blur' },
    { pattern: /^[a-zA-Z0-9_]+$/, message: '只能包含字母、数字、下划线', trigger: 'blur' },
  ],
  cellphone: [
    { required: true, message: '请输入手机号', trigger: 'blur' },
    { pattern: /^1[3456789]\d{9}$/, message: '手机号格式不正确', trigger: 'blur' },
  ],
  password: [
    { required: true, message: '请输入密码', trigger: 'blur' },
    { min: 6, message: '密码至少6位', trigger: 'blur' },
  ],
  confirmPassword: [
    { required: true, validator: validateConfirm, trigger: 'blur' },
  ],
}

// 注册
const handleRegister = async () => {
  await regRef.value.validate(async (valid) => {
    if (!valid) return
    regLoading.value = true
    try {
      await register({
        username: regForm.value.username,
        cellphone: regForm.value.cellphone,
        password: regForm.value.password,
      })
      ElMessage.success('注册成功，请登录')
      // 切换到登录 Tab 并预填用户名
      loginForm.value.username = regForm.value.username
      switchTab('login')
      // 重置注册表单
      regForm.value = {
        username: '',
        cellphone: '',
        password: '',
        confirmPassword: '',
      }
    } catch {
      // 错误由 request.js 统一处理
    } finally {
      regLoading.value = false
    }
  })
}

</script>

<style scoped>
@import url('https://fonts.googleapis.com/css2?family=Poppins:wght@400;500;600;700&family=Playfair+Display:wght@700&display=swap');

:root {
  --primary: #3b82f6;
  --primary-dark: #2563eb;
  --accent-green: #60a5fa;
  --accent-orange: #f97316;
  --bg-dark: #f3f4f6;
  --bg-card: #ffffff;
  --text-primary: #1f2937;
  --text-secondary: #6b7280;
  --border-light: rgba(0, 0, 0, 0.08);
}

/* ===== 容器 ===== */
.auth-container {
  min-height: 100vh;
  display: flex;
  align-items: center;
  justify-content: center;
  background: linear-gradient(135deg, #f8fafc 0%, #f0f4f8 50%, #f8fafc 100%);
  position: relative;
  overflow: hidden;
  font-family: 'Poppins', sans-serif;
}

/* 背景网格 - 增强 */
.bg-grid {
  position: absolute;
  inset: 0;
  background-image:
    radial-gradient(circle at 20% 30%, rgba(59,130,246,0.1) 0%, transparent 50%),
    radial-gradient(circle at 80% 70%, rgba(96,165,250,0.08) 0%, transparent 50%);
  background-size: 100% 100%;
  animation: drift 20s ease-in-out infinite;
}

@keyframes drift {
  0%, 100% { opacity: 1; }
  50% { opacity: 0.8; }
}

/* 背景光晕 - 优化 */
.bg-blob {
  position: absolute;
  border-radius: 50%;
  filter: blur(100px);
  opacity: 0.4;
}
.blob-1 {
  width: 600px; height: 600px;
  background: radial-gradient(circle, rgba(59,130,246,0.3), transparent 70%);
  top: -200px; left: -200px;
  animation: float 15s ease-in-out infinite;
}
.blob-2 {
  width: 500px; height: 500px;
  background: radial-gradient(circle, rgba(96,165,250,0.2), transparent 70%);
  bottom: -150px; right: -150px;
  animation: float 18s ease-in-out infinite reverse;
}

@keyframes float {
  0%, 100% { transform: translate(0, 0); }
  50% { transform: translate(40px, -40px); }
}

/* ===== 卡片 - 现代玻璃态 ===== */
.auth-card {
  position: relative;
  z-index: 10;
  width: 480px;
  background: var(--bg-card);
  backdrop-filter: blur(10px);
  border: 1px solid #e5e7eb;
  border-radius: 24px;
  padding: 48px 44px 40px;
  box-shadow:
    0 0 0 1px rgba(0,0,0,0.05),
    0 10px 30px rgba(0,0,0,0.08);
  animation: slideUp 0.6s ease-out;
}

@keyframes slideUp {
  from {
    opacity: 0;
    transform: translateY(40px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

/* ===== Logo ===== */
.logo-area {
  text-align: center;
  margin-bottom: 36px;
  animation: logoFade 0.8s ease-out 0.1s both;
}

@keyframes logoFade {
  from {
    opacity: 0;
    transform: scale(0.8);
  }
  to {
    opacity: 1;
    transform: scale(1);
  }
}

.logo-icon {
  font-size: 56px;
  line-height: 1;
  filter: drop-shadow(0 0 10px rgba(59,130,246,0.3));
}

@keyframes spin {
  from { transform: rotate(0deg); }
  to { transform: rotate(360deg); }
}

.logo-text {
  margin-top: 14px;
  font-size: 22px;
  font-weight: 700;
  color: var(--text-primary);
  letter-spacing: 0.5px;
  font-family: 'Playfair Display', serif;
  background: linear-gradient(135deg, #1f2937, #374151);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
}

.logo-sub {
  margin-top: 6px;
  font-size: 12px;
  color: #64748b;
  letter-spacing: 1.2px;
  text-transform: uppercase;
  font-weight: 500;
}

/* ===== Tab 切换 - 增强 ===== */
.tab-switcher {
  position: relative;
  display: flex;
  background: #f3f4f6;
  border: 1px solid #e5e7eb;
  border-radius: 12px;
  padding: 5px;
  margin-bottom: 32px;
  gap: 0;
}

.tab-btn {
  flex: 1;
  padding: 11px 0;
  background: none;
  border: none;
  color: #64748b;
  font-size: 15px;
  font-weight: 600;
  cursor: pointer;
  position: relative;
  z-index: 1;
  transition: color 0.3s ease;
  font-family: 'Poppins', sans-serif;
}

.tab-btn.active {
  color: #ffffff;
}

.tab-indicator {
  position: absolute;
  top: 5px;
  width: calc(50% - 5px);
  height: calc(100% - 10px);
  background: linear-gradient(135deg, #3b82f6 0%, #60a5fa 100%);
  border-radius: 10px;
  transition: left 0.35s cubic-bezier(0.34, 1.56, 0.64, 1);
  box-shadow:
    0 2px 8px rgba(59,130,246,0.3);
}

/* ===== 表单容器 ===== */
.form-wrap {
  max-height: 600px;
  overflow-y: auto;
  animation: fadeIn 0.3s ease-out;
}

.form-wrap::-webkit-scrollbar {
  width: 6px;
}

.form-wrap::-webkit-scrollbar-track {
  background: transparent;
}

.form-wrap::-webkit-scrollbar-thumb {
  background: rgba(59,130,246,0.3);
  border-radius: 3px;
}

.form-wrap::-webkit-scrollbar-thumb:hover {
  background: rgba(59,130,246,0.5);
}

@keyframes fadeIn {
  from { opacity: 0; }
  to { opacity: 1; }
}

.input-label {
  font-size: 13px;
  color: #6b7280;
  margin-bottom: 8px;
  letter-spacing: 0.3px;
  font-weight: 600;
  text-transform: uppercase;
}

/* 覆盖 Element Plus 样式 */
:deep(.custom-input .el-input__wrapper) {
  background: #f9fafb !important;
  border: 1.5px solid #d1d5db !important;
  border-radius: 10px !important;
  box-shadow: none !important;
  transition: all 0.3s ease !important;
  padding: 12px 16px !important;
}

:deep(.custom-input .el-input__wrapper:hover) {
  border-color: #bfdbfe !important;
  background: #ffffff !important;
  box-shadow: 0 0 0 3px rgba(59,130,246,0.1) !important;
}

:deep(.custom-input .el-input__wrapper.is-focus) {
  border-color: #3b82f6 !important;
  background: #ffffff !important;
  box-shadow: 0 0 0 4px rgba(59,130,246,0.15) !important;
}

:deep(.custom-input .el-input__inner) {
  color: #1f2937 !important;
  font-size: 15px !important;
  font-weight: 500 !important;
}

:deep(.custom-input .el-input__inner::placeholder) {
  color: #9ca3af !important;
  font-weight: 400 !important;
}

:deep(.custom-input .el-input__prefix-inner .el-icon) {
  color: #9ca3af !important;
  transition: color 0.3s ease !important;
}

:deep(.custom-input .el-input__wrapper.is-focus .el-input__prefix-inner .el-icon) {
  color: #3b82f6 !important;
}

:deep(.el-form-item) {
  margin-bottom: 18px;
}

:deep(.el-form-item__error) {
  color: #ff6b6b !important;
  font-size: 12px !important;
  margin-top: 6px !important;
}

/* 手机号行 */
.phone-row {
  display: flex;
  gap: 10px;
  align-items: flex-start;
}

.phone-input {
  flex: 1;
}

.code-btn {
  flex-shrink: 0;
  min-width: 120px;
  background: linear-gradient(135deg, rgba(59,130,246,0.1), rgba(96,165,250,0.05)) !important;
  border: 1.5px solid #bfdbfe !important;
  color: #3b82f6 !important;
  border-radius: 10px !important;
  font-size: 14px !important;
  height: 42px !important;
  transition: all 0.3s ease !important;
  font-weight: 600 !important;
}

.code-btn:hover:not(:disabled) {
  background: linear-gradient(135deg, rgba(59,130,246,0.15), rgba(96,165,250,0.1)) !important;
  border-color: #3b82f6 !important;
  color: #2563eb !important;
  transform: translateY(-2px);
  box-shadow: 0 4px 12px rgba(59,130,246,0.2) !important;
}

.code-btn:disabled {
  opacity: 0.5 !important;
  cursor: not-allowed !important;
}

/* 密码强度 */
.pwd-strength {
  display: flex;
  align-items: center;
  gap: 6px;
  margin-top: 10px;
  padding: 0 4px;
}

.strength-bar {
  flex: 1;
  height: 4px;
  border-radius: 2px;
  background: rgba(255,255,255,0.1);
  transition: all 0.3s ease;
  overflow: hidden;
}

.strength-bar.active {
  box-shadow: 0 0 8px currentColor;
}

.strength-bar.active.level-1 {
  background: linear-gradient(90deg, #ef4444, #f87171);
}

.strength-bar.active.level-2 {
  background: linear-gradient(90deg, #f59e0b, #fbbf24);
}

.strength-bar.active.level-3 {
  background: linear-gradient(90deg, #3b82f6, #60a5fa);
}

.strength-bar.active.level-4 {
  background: linear-gradient(90deg, #10b981, #34d399);
}

.strength-label {
  font-size: 12px;
  margin-left: 6px;
  white-space: nowrap;
  font-weight: 600;
  min-width: 36px;
}

.strength-label.level-1 { color: #ef4444; }
.strength-label.level-2 { color: #f59e0b; }
.strength-label.level-3 { color: #3b82f6; }
.strength-label.level-4 { color: #10b981; }

/* 提交按钮 - 增强 */
.submit-btn {
  width: 100%;
  height: 48px !important;
  background: linear-gradient(135deg, #3b82f6 0%, #2563eb 100%) !important;
  border: none !important;
  border-radius: 12px !important;
  font-size: 16px !important;
  font-weight: 700 !important;
  letter-spacing: 1px !important;
  margin-top: 12px !important;
  color: #ffffff !important;
  box-shadow:
    0 4px 12px rgba(59,130,246,0.3),
    inset 0 1px 0 rgba(255,255,255,0.2) !important;
  transition: all 0.3s cubic-bezier(0.34, 1.56, 0.64, 1) !important;
  position: relative;
  overflow: hidden;
}

.submit-btn::before {
  content: '';
  position: absolute;
  inset: 0;
  background: linear-gradient(135deg, transparent, rgba(255,255,255,0.15), transparent);
  opacity: 0;
  transition: opacity 0.3s ease;
}

.submit-btn:hover {
  transform: translateY(-3px) !important;
  box-shadow:
    0 6px 20px rgba(59,130,246,0.4),
    inset 0 1px 0 rgba(255,255,255,0.25) !important;
}

.submit-btn:hover::before {
  opacity: 1;
}

.submit-btn:active {
  transform: translateY(-1px) !important;
}

/* 底部链接 - 优化 */
.form-footer {
  margin-top: 20px;
  text-align: center;
  font-size: 14px;
  color: #6b7280;
  font-weight: 500;
}

.form-footer a {
  color: #3b82f6;
  cursor: pointer;
  margin-left: 2px;
  transition: all 0.3s ease;
  font-weight: 600;
  position: relative;
}

.form-footer a::after {
  content: '';
  position: absolute;
  bottom: -2px;
  left: 0;
  width: 0;
  height: 2px;
  background: linear-gradient(90deg, #3b82f6, #2563eb);
  transition: width 0.3s ease;
}

.form-footer a:hover {
  color: #2563eb;
}

.form-footer a:hover::after {
  width: 100%;
}

/* 过渡动画 - 增强 */
.slide-fade-enter-active,
.slide-fade-leave-active {
  transition: all 0.35s cubic-bezier(0.4, 0, 0.2, 1);
}

.slide-fade-enter-from {
  opacity: 0;
  transform: translateX(30px);
}

.slide-fade-leave-to {
  opacity: 0;
  transform: translateX(-30px);
}

/* 开发提示 */
.dev-tip {
  position: fixed;
  bottom: 20px;
  left: 50%;
  transform: translateX(-50%);
  background: rgba(245, 158, 11, 0.15);
  border: 1px solid rgba(245, 158, 11, 0.3);
  color: #fbbf24;
  padding: 8px 16px;
  border-radius: 8px;
  font-size: 12px;
  z-index: 100;
  white-space: nowrap;
}

.dev-tip code {
  background: rgba(245,158,11,0.2);
  padding: 1px 6px;
  border-radius: 4px;
  font-family: monospace;
  font-weight: bold;
}

/* 响应式设计 */
@media (max-width: 520px) {
  .auth-card {
    width: calc(100% - 32px);
    padding: 36px 24px 28px;
  }

  .logo-text {
    font-size: 20px;
  }

  .logo-icon {
    font-size: 48px;
  }

  .submit-btn {
    height: 44px !important;
    font-size: 15px !important;
  }

  .form-wrap {
    max-height: 70vh;
  }
}
</style>