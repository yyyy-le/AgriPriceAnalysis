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
        <div class="logo-text">农产品价格分析系统</div>
        <div class="logo-sub">Agricultural Price Analytics Platform</div>
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

            <!-- 昵称 -->
            <el-form-item prop="nickname">
              <div class="input-label">昵称</div>
              <el-input
                v-model="regForm.nickname"
                placeholder="如何称呼您"
                size="large"
                prefix-icon="Avatar"
                class="custom-input"
              />
            </el-form-item>

            <!-- 手机号 + 发送验证码 -->
            <el-form-item prop="cellphone">
              <div class="input-label">手机号</div>
              <div class="phone-row">
                <el-input
                  v-model="regForm.cellphone"
                  placeholder="请输入11位手机号"
                  size="large"
                  prefix-icon="Phone"
                  class="custom-input phone-input"
                  maxlength="11"
                />
                <el-button
                  size="large"
                  class="code-btn"
                  :disabled="codeSending || countdown > 0 || !isPhoneValid"
                  :loading="codeSending"
                  @click="handleSendCode"
                >
                  <span v-if="countdown > 0">{{ countdown }}s 后重发</span>
                  <span v-else-if="codeSending">发送中</span>
                  <span v-else>获取验证码</span>
                </el-button>
              </div>
            </el-form-item>

            <!-- 验证码 -->
            <el-form-item prop="cellphone_verification_code">
              <div class="input-label">验证码</div>
              <el-input
                v-model="regForm.cellphone_verification_code"
                placeholder="请输入6位验证码"
                size="large"
                prefix-icon="Key"
                class="custom-input"
                maxlength="6"
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

            <!-- 性别（可选） -->
            <el-form-item>
              <div class="input-label">性别（可选）</div>
              <div class="gender-group">
                <div
                  v-for="item in genderOptions"
                  :key="item.value"
                  :class="['gender-item', { selected: regForm.gender === item.value }]"
                  @click="regForm.gender = item.value"
                >
                  <span>{{ item.icon }}</span>
                  <span>{{ item.label }}</span>
                </div>
              </div>
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

    <!-- 底部提示：开发模式超级验证码 -->
    <div class="dev-tip" v-if="showDevTip">
      💡 开发模式：验证码为 <code>417938</code>
      <span @click="showDevTip=false" style="cursor:pointer;margin-left:8px">×</span>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onUnmounted } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { useAuthStore } from '../stores/auth'
import { register, sendVerificationCode } from '../api/register'

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
const codeSending = ref(false)
const countdown = ref(0)
let countdownTimer = null

const regForm = ref({
  username: '',
  nickname: '',
  cellphone: '',
  cellphone_verification_code: '',
  password: '',
  confirmPassword: '',
  gender: 'unknown',
})

const genderOptions = [
  { value: 'male', label: '男', icon: '👦' },
  { value: 'female', label: '女', icon: '👧' },
  { value: 'unknown', label: '保密', icon: '🤫' },
]

// 手机号是否合法
const isPhoneValid = computed(() => /^1[3456789]\d{9}$/.test(regForm.value.cellphone))

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
  nickname: [
    { required: true, message: '请输入昵称', trigger: 'blur' },
    { min: 1, max: 20, message: '昵称1~20位', trigger: 'blur' },
  ],
  cellphone: [
    { required: true, message: '请输入手机号', trigger: 'blur' },
    { pattern: /^1[3456789]\d{9}$/, message: '手机号格式不正确', trigger: 'blur' },
  ],
  cellphone_verification_code: [
    { required: true, message: '请输入验证码', trigger: 'blur' },
    { len: 6, message: '验证码为6位数字', trigger: 'blur' },
    { pattern: /^\d{6}$/, message: '验证码为6位数字', trigger: 'blur' },
  ],
  password: [
    { required: true, message: '请输入密码', trigger: 'blur' },
    { min: 6, message: '密码至少6位', trigger: 'blur' },
  ],
  confirmPassword: [
    { required: true, validator: validateConfirm, trigger: 'blur' },
  ],
}

// 发送验证码
const handleSendCode = async () => {
  if (!isPhoneValid.value) {
    ElMessage.warning('请先输入正确的手机号')
    return
  }
  codeSending.value = true
  try {
    await sendVerificationCode(regForm.value.cellphone)
    ElMessage.success('验证码已发送，请注意查收（开发环境：417938）')
    // 倒计时 60 秒
    countdown.value = 60
    countdownTimer = setInterval(() => {
      countdown.value--
      if (countdown.value <= 0) {
        clearInterval(countdownTimer)
        countdown.value = 0
      }
    }, 1000)
  } catch {
    // 错误由 request.js 统一处理
  } finally {
    codeSending.value = false
  }
}

// 注册
const handleRegister = async () => {
  await regRef.value.validate(async (valid) => {
    if (!valid) return
    regLoading.value = true
    try {
      await register({
        username: regForm.value.username,
        nickname: regForm.value.nickname,
        cellphone: regForm.value.cellphone,
        cellphone_verification_code: regForm.value.cellphone_verification_code,
        password: regForm.value.password,
        gender: regForm.value.gender,
      })
      ElMessage.success('注册成功，请登录')
      // 切换到登录 Tab 并预填用户名
      loginForm.value.username = regForm.value.username
      switchTab('login')
      // 重置注册表单
      regForm.value = {
        username: '', nickname: '', cellphone: '',
        cellphone_verification_code: '', password: '',
        confirmPassword: '', gender: 'unknown',
      }
    } catch {
      // 错误由 request.js 统一处理
    } finally {
      regLoading.value = false
    }
  })
}

onUnmounted(() => {
  if (countdownTimer) clearInterval(countdownTimer)
})
</script>

<style scoped>
/* ===== 容器 ===== */
.auth-container {
  min-height: 100vh;
  display: flex;
  align-items: center;
  justify-content: center;
  background: #0a0f1e;
  position: relative;
  overflow: hidden;
}

/* 背景网格 */
.bg-grid {
  position: absolute;
  inset: 0;
  background-image:
    linear-gradient(rgba(99,102,241,0.08) 1px, transparent 1px),
    linear-gradient(90deg, rgba(99,102,241,0.08) 1px, transparent 1px);
  background-size: 48px 48px;
}

/* 背景光晕 */
.bg-blob {
  position: absolute;
  border-radius: 50%;
  filter: blur(80px);
  opacity: 0.35;
}
.blob-1 {
  width: 500px; height: 500px;
  background: radial-gradient(circle, #6366f1, transparent 70%);
  top: -150px; left: -150px;
}
.blob-2 {
  width: 400px; height: 400px;
  background: radial-gradient(circle, #10b981, transparent 70%);
  bottom: -100px; right: -100px;
}

/* ===== 卡片 ===== */
.auth-card {
  position: relative;
  z-index: 10;
  width: 460px;
  background: rgba(15, 23, 42, 0.85);
  backdrop-filter: blur(20px);
  border: 1px solid rgba(99, 102, 241, 0.25);
  border-radius: 20px;
  padding: 36px 40px 32px;
  box-shadow:
    0 0 0 1px rgba(99,102,241,0.1),
    0 25px 50px rgba(0,0,0,0.5),
    inset 0 1px 0 rgba(255,255,255,0.05);
}

/* ===== Logo ===== */
.logo-area {
  text-align: center;
  margin-bottom: 28px;
}
.logo-icon {
  font-size: 42px;
  line-height: 1;
  filter: drop-shadow(0 0 12px rgba(99,102,241,0.6));
}
.logo-text {
  margin-top: 10px;
  font-size: 18px;
  font-weight: 700;
  color: #f1f5f9;
  letter-spacing: 1px;
}
.logo-sub {
  margin-top: 4px;
  font-size: 11px;
  color: #475569;
  letter-spacing: 1.5px;
  text-transform: uppercase;
}

/* ===== Tab 切换 ===== */
.tab-switcher {
  position: relative;
  display: flex;
  background: rgba(255,255,255,0.04);
  border: 1px solid rgba(255,255,255,0.08);
  border-radius: 10px;
  padding: 4px;
  margin-bottom: 28px;
}
.tab-btn {
  flex: 1;
  padding: 9px 0;
  background: none;
  border: none;
  color: #64748b;
  font-size: 14px;
  font-weight: 500;
  cursor: pointer;
  position: relative;
  z-index: 1;
  transition: color 0.3s;
  font-family: 'Microsoft YaHei', sans-serif;
}
.tab-btn.active {
  color: #f1f5f9;
}
.tab-indicator {
  position: absolute;
  top: 4px;
  width: calc(50% - 4px);
  height: calc(100% - 8px);
  background: linear-gradient(135deg, #6366f1, #8b5cf6);
  border-radius: 7px;
  transition: left 0.3s cubic-bezier(0.4, 0, 0.2, 1);
  box-shadow: 0 2px 12px rgba(99,102,241,0.4);
}

/* ===== 表单 ===== */
.form-wrap {
  /* 注册表单需要可滚动 */
}
.input-label {
  font-size: 12px;
  color: #64748b;
  margin-bottom: 6px;
  letter-spacing: 0.5px;
}

/* 覆盖 Element Plus 样式 */
:deep(.custom-input .el-input__wrapper) {
  background: rgba(255,255,255,0.04) !important;
  border: 1px solid rgba(255,255,255,0.1) !important;
  border-radius: 8px !important;
  box-shadow: none !important;
  transition: border-color 0.2s, background 0.2s;
}
:deep(.custom-input .el-input__wrapper:hover) {
  border-color: rgba(99,102,241,0.5) !important;
  background: rgba(255,255,255,0.06) !important;
}
:deep(.custom-input .el-input__wrapper.is-focus) {
  border-color: #6366f1 !important;
  background: rgba(99,102,241,0.08) !important;
  box-shadow: 0 0 0 3px rgba(99,102,241,0.15) !important;
}
:deep(.custom-input .el-input__inner) {
  color: #f1f5f9 !important;
  font-size: 14px;
}
:deep(.custom-input .el-input__inner::placeholder) {
  color: #334155 !important;
}
:deep(.custom-input .el-input__prefix-inner .el-icon) {
  color: #475569 !important;
}
:deep(.el-form-item) {
  margin-bottom: 16px;
}
:deep(.el-form-item__error) {
  color: #f87171 !important;
  font-size: 11px;
}

/* 手机号行 */
.phone-row {
  display: flex;
  gap: 8px;
  align-items: flex-start;
}
.phone-input {
  flex: 1;
}
.code-btn {
  flex-shrink: 0;
  min-width: 110px;
  background: rgba(99,102,241,0.15) !important;
  border: 1px solid rgba(99,102,241,0.4) !important;
  color: #818cf8 !important;
  border-radius: 8px !important;
  font-size: 13px !important;
  height: 40px !important;
  transition: all 0.2s !important;
}
.code-btn:hover:not(:disabled) {
  background: rgba(99,102,241,0.3) !important;
  border-color: #6366f1 !important;
  color: #c7d2fe !important;
}
.code-btn:disabled {
  opacity: 0.5 !important;
  cursor: not-allowed !important;
}

/* 密码强度 */
.pwd-strength {
  display: flex;
  align-items: center;
  gap: 4px;
  margin-top: 6px;
}
.strength-bar {
  flex: 1;
  height: 3px;
  border-radius: 2px;
  background: rgba(255,255,255,0.08);
  transition: background 0.3s;
}
.strength-bar.active.level-1 { background: #ef4444; }
.strength-bar.active.level-2 { background: #f59e0b; }
.strength-bar.active.level-3 { background: #3b82f6; }
.strength-bar.active.level-4 { background: #10b981; }
.strength-label {
  font-size: 11px;
  margin-left: 4px;
  white-space: nowrap;
}
.strength-label.level-1 { color: #ef4444; }
.strength-label.level-2 { color: #f59e0b; }
.strength-label.level-3 { color: #3b82f6; }
.strength-label.level-4 { color: #10b981; }

/* 性别选择 */
.gender-group {
  display: flex;
  gap: 8px;
}
.gender-item {
  flex: 1;
  padding: 8px 0;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 4px;
  background: rgba(255,255,255,0.04);
  border: 1px solid rgba(255,255,255,0.08);
  border-radius: 8px;
  cursor: pointer;
  font-size: 13px;
  color: #64748b;
  transition: all 0.2s;
  user-select: none;
}
.gender-item:hover {
  border-color: rgba(99,102,241,0.4);
  color: #94a3b8;
}
.gender-item.selected {
  border-color: #6366f1;
  background: rgba(99,102,241,0.15);
  color: #c7d2fe;
}

/* 提交按钮 */
.submit-btn {
  width: 100%;
  height: 46px !important;
  background: linear-gradient(135deg, #6366f1, #8b5cf6) !important;
  border: none !important;
  border-radius: 10px !important;
  font-size: 16px !important;
  font-weight: 600 !important;
  letter-spacing: 2px !important;
  margin-top: 8px !important;
  box-shadow: 0 4px 20px rgba(99,102,241,0.4) !important;
  transition: all 0.2s !important;
}
.submit-btn:hover {
  transform: translateY(-1px) !important;
  box-shadow: 0 6px 24px rgba(99,102,241,0.55) !important;
}
.submit-btn:active {
  transform: translateY(0) !important;
}

/* 底部链接 */
.form-footer {
  margin-top: 16px;
  text-align: center;
  font-size: 13px;
  color: #475569;
}
.form-footer a {
  color: #818cf8;
  cursor: pointer;
  margin-left: 4px;
  transition: color 0.2s;
}
.form-footer a:hover {
  color: #c7d2fe;
}

/* 过渡动画 */
.slide-fade-enter-active,
.slide-fade-leave-active {
  transition: all 0.25s ease;
}
.slide-fade-enter-from {
  opacity: 0;
  transform: translateX(20px);
}
.slide-fade-leave-to {
  opacity: 0;
  transform: translateX(-20px);
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
</style>