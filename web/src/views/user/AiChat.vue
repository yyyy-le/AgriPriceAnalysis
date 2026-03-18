<template>
  <div style="height:calc(100vh - 120px);display:flex;flex-direction:column;gap:12px">

    <el-card style="flex:1;overflow:hidden">
      <el-scrollbar ref="scrollbarRef" style="height:100%">
        <div style="padding:8px 4px">

          <div v-if="messages.length === 0" style="text-align:center;padding:50px 20px">
            <div style="font-size:48px;margin-bottom:12px">🤖</div>
            <div style="font-size:17px;font-weight:500;margin-bottom:6px;color:#303133">农产品价格 AI 助手</div>
            <div style="font-size:13px;color:#909399;margin-bottom:24px">
              我可以查询实时价格、历史数据、价格对比，也可以回答农业相关问题
            </div>
            <div style="display:flex;flex-wrap:wrap;gap:8px;justify-content:center;max-width:600px;margin:0 auto">
              <el-tag
                v-for="q in quickQuestions" :key="q"
                style="cursor:pointer;padding:6px 12px;font-size:13px"
                type="info" effect="plain"
                @click="sendQuick(q)"
              >{{ q }}</el-tag>
            </div>
          </div>

          <div v-for="(msg, i) in messages" :key="i" style="margin-bottom:20px">
            <div v-if="msg.role === 'user'" style="display:flex;justify-content:flex-end">
              <div style="
                max-width:72%;background:#409eff;color:#fff;
                padding:10px 16px;border-radius:18px 18px 4px 18px;
                font-size:14px;line-height:1.7;word-break:break-word
              ">{{ msg.content }}</div>
            </div>

            <div v-else style="display:flex;gap:10px;align-items:flex-start">
              <div style="
                width:34px;height:34px;border-radius:50%;
                background:linear-gradient(135deg,#667eea,#764ba2);
                display:flex;align-items:center;justify-content:center;
                font-size:18px;flex-shrink:0;margin-top:2px
              ">🤖</div>
              <div style="max-width:75%">
                <div v-if="msg.querying" style="font-size:12px;color:#909399;margin-bottom:6px;display:flex;align-items:center;gap:4px">
                  <span style="display:inline-block;animation:spin 1s linear infinite">⏳</span>
                  正在查询：{{ toolLabels[msg.querying] || msg.querying }}
                </div>
                <div style="
                  background:#f4f4f5;padding:10px 16px;
                  border-radius:18px 18px 18px 4px;
                  font-size:14px;line-height:1.8;white-space:pre-wrap;word-break:break-word;
                  min-height:40px
                ">
                  <span>{{ msg.content }}</span>
                  <span v-if="msg.loading" style="display:inline-block;animation:blink 1s infinite;color:#409eff">▋</span>
                </div>
              </div>
            </div>
          </div>

        </div>
      </el-scrollbar>
    </el-card>

    <el-card style="flex-shrink:0">
      <el-row :gutter="8" align="middle">
        <el-col :span="20">
          <el-input
            v-model="inputText"
            placeholder="输入问题，如：大白菜今天多少钱？"
            :disabled="loading"
            size="large"
            @keyup.enter="sendMessage"
            clearable
          />
        </el-col>
        <el-col :span="4">
          <el-button type="primary" size="large" style="width:100%" :loading="loading" @click="sendMessage">
            {{ loading ? '回答中' : '发送' }}
          </el-button>
        </el-col>
      </el-row>
      <div style="margin-top:8px;display:flex;gap:6px;flex-wrap:wrap">
        <span style="font-size:12px;color:#c0c4cc;line-height:22px">快捷提问：</span>
        <el-tag
          v-for="q in quickQuestions.slice(0,4)" :key="q"
          size="small" type="info" effect="plain"
          style="cursor:pointer"
          @click="sendQuick(q)"
        >{{ q }}</el-tag>
      </div>
    </el-card>
  </div>
</template>

<script setup>
import { ref, nextTick } from 'vue'
import { ElMessage } from 'element-plus'
import { chatWithAI } from '../../api/ai'

const messages = ref([])
const inputText = ref('')
const loading = ref(false)
const scrollbarRef = ref()

const quickQuestions = [
  '大白菜今天多少钱？',
  '30天前大白菜什么价？',
  '今天最便宜的蔬菜是什么？',
  '最近涨价最厉害的是什么？',
  '大白菜和圆白菜哪个贵？',
  '白菜怎么保存更新鲜？',
]

const toolLabels = {
  get_latest_prices: '最新价格',
  get_price_history: '历史价格',
  get_price_ranking: '价格排行',
  get_price_volatility: '价格波动',
  compare_products: '价格对比',
}

const scrollToBottom = async () => {
  await nextTick()
  scrollbarRef.value?.setScrollTop(999999)
}

const sendQuick = (q) => {
  if (loading.value) return
  inputText.value = q
  sendMessage()
}

const sendMessage = async () => {
  const text = inputText.value.trim()
  if (!text || loading.value) return

  messages.value.push({ role: 'user', content: text })
  inputText.value = ''
  loading.value = true
  await scrollToBottom()

  // 用 index 来更新，确保响应式
  const idx = messages.value.length
  messages.value.push({ role: 'ai', content: '', loading: true, querying: null })
  await scrollToBottom()

  try {
    await chatWithAI(
      text,
      (chunk) => {
        // 直接通过 index 修改，触发响应式
        messages.value[idx].querying = null
        messages.value[idx].content += chunk
        scrollToBottom()
      },
      (toolName) => {
        messages.value[idx].querying = toolName
        scrollToBottom()
      }
    )
  } catch (e) {
    console.error('AI error:', e)
    messages.value[idx].content = '抱歉，请求失败，请稍后重试。'
    ElMessage.error('AI 请求失败')
  } finally {
    messages.value[idx].loading = false
    messages.value[idx].querying = null
    loading.value = false
    await scrollToBottom()
  }
}
</script>

<style scoped>
@keyframes blink {
  0%, 100% { opacity: 1 }
  50% { opacity: 0 }
}
@keyframes spin {
  from { transform: rotate(0deg) }
  to { transform: rotate(360deg) }
}
</style>