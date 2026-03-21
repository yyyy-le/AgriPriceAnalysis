<template>
  <div>
      <el-card style="margin-bottom:16px">
      <el-row :gutter="12" align="middle">
        <el-col :span="10">
          <el-input v-model="keyword" placeholder="搜索用户名/手机号/昵称" clearable @change="fetchData"/>
        </el-col>
        <el-col :span="4">
          <el-button type="primary" @click="fetchData">搜索</el-button>
        </el-col>
        <!-- 新增用户按钮移到同一行最右侧 -->
        <el-col :span="10" style="text-align:right">
          <el-button type="success" @click="openAdd">+ 新增用户</el-button>
        </el-col>
      </el-row>
    </el-card>

    <el-card>
      <el-table :data="list" stripe v-loading="loading" style="width:100%">
        <el-table-column prop="username" label="用户名" width="120"/>
        <el-table-column prop="nickname" label="昵称" width="120"/>
        <el-table-column prop="cellphone" label="手机号" width="140"/>
        <el-table-column prop="gender" label="性别" width="70">
          <template #default="{ row }">
            {{ row.gender === 'male' ? '男' : row.gender === 'female' ? '女' : '未知' }}
          </template>
        </el-table-column>
        <el-table-column prop="state" label="状态" width="80">
          <template #default="{ row }">
            <el-tag :type="row.state === 'enabled' ? 'success' : 'danger'" size="small">
              {{ row.state === 'enabled' ? '正常' : '禁用' }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="is_admin" label="角色" width="90">
          <template #default="{ row }">
            <el-tag :type="row.is_admin ? 'danger' : 'info'" size="small">
              {{ row.is_admin ? '管理员' : '普通用户' }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="created_at" label="注册时间" width="180">
          <template #default="{ row }">{{ formatDate(row.created_at) }}</template>
        </el-table-column>
        <el-table-column label="操作" min-width="240" fixed="right">
          <template #default="{ row }">
            <el-space>
              <el-button size="small" type="primary" @click="openEdit(row)">编辑</el-button>
              <el-button size="small" :type="row.state === 'enabled' ? 'warning' : 'success'" @click="toggleState(row)">
                {{ row.state === 'enabled' ? '禁用' : '启用' }}
              </el-button>
              <el-button size="small" :type="row.is_admin ? 'info' : 'primary'" @click="toggleAdmin(row)">
                {{ row.is_admin ? '取消管理员' : '设为管理员' }}
              </el-button>
              <el-button size="small" type="danger" @click="handleDelete(row)">删除</el-button>
            </el-space>
          </template>
        </el-table-column>
      </el-table>

      <el-pagination
        style="margin-top:16px;justify-content:flex-end;display:flex"
        :current-page="page"
        :page-size="pageSize"
        :total="total"
        layout="total, prev, pager, next"
        @current-change="(p) => { page = p; fetchData() }"
      />
    </el-card>

    <!-- 新增/编辑弹窗 -->
    <el-dialog v-model="dialogVisible" :title="isEdit ? '编辑用户' : '新增用户'" width="480px" @close="resetForm">
      <el-form :model="form" :rules="rules" ref="formRef" label-width="90px">
        <el-form-item label="用户名" prop="username">
          <el-input v-model="form.username" :disabled="isEdit" placeholder="登录用户名"/>
        </el-form-item>
        <el-form-item label="昵称" prop="nickname">
          <el-input v-model="form.nickname" placeholder="显示昵称"/>
        </el-form-item>
        <el-form-item label="手机号" prop="cellphone">
          <el-input v-model="form.cellphone" placeholder="11位手机号"/>
        </el-form-item>
        <el-form-item label="密码" :prop="isEdit ? '' : 'password'">
          <el-input v-model="form.password" type="password" show-password
            :placeholder="isEdit ? '不填则不修改密码' : '请输入密码'"/>
        </el-form-item>
        <el-form-item label="性别">
          <el-radio-group v-model="form.gender">
            <el-radio value="male">男</el-radio>
            <el-radio value="female">女</el-radio>
            <el-radio value="unknown">未知</el-radio>
          </el-radio-group>
        </el-form-item>
        <el-form-item label="角色">
          <el-switch v-model="form.is_admin" active-text="管理员" inactive-text="普通用户"/>
        </el-form-item>
        <el-form-item label="状态">
          <el-switch v-model="form.enabled" active-text="正常" inactive-text="禁用"/>
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="dialogVisible = false">取消</el-button>
        <el-button type="primary" :loading="submitLoading" @click="handleSubmit">确定</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { getUsers, updateUserState, updateUserAdmin, deleteUser, createUser, updateUser } from '../../api/admin'

const list = ref([])
const total = ref(0)
const loading = ref(false)
const submitLoading = ref(false)
const keyword = ref('')
const page = ref(1)
const pageSize = ref(20)
const dialogVisible = ref(false)
const isEdit = ref(false)
const formRef = ref()

const defaultForm = () => ({
  id: null,
  username: '',
  nickname: '',
  cellphone: '',
  password: '',
  gender: 'unknown',
  is_admin: false,
  enabled: true,
})

const form = ref(defaultForm())

const rules = {
  username: [{ required: true, message: '请输入用户名', trigger: 'blur' }],
  nickname: [{ required: true, message: '请输入昵称', trigger: 'blur' }],
  cellphone: [
    { required: true, message: '请输入手机号', trigger: 'blur' },
    { pattern: /^1[3456789]\d{9}$/, message: '手机号格式不正确', trigger: 'blur' }
  ],
  password: [{ required: true, message: '请输入密码', trigger: 'blur' }],
}

const formatDate = (d) => d ? new Date(d).toLocaleString('zh-CN') : '-'

const fetchData = async () => {
  loading.value = true
  try {
    const res = await getUsers({ page: page.value, page_size: pageSize.value, keyword: keyword.value || undefined })
    list.value = res.list
    total.value = res.total
  } finally {
    loading.value = false
  }
}

const openAdd = () => {
  isEdit.value = false
  form.value = defaultForm()
  dialogVisible.value = true
}

const openEdit = (row) => {
  isEdit.value = true
  form.value = {
    id: row.id,
    username: row.username,
    nickname: row.nickname,
    cellphone: row.cellphone,
    password: '',
    gender: row.gender,
    is_admin: row.is_admin,
    enabled: row.state === 'enabled',
  }
  dialogVisible.value = true
}

const resetForm = () => {
  formRef.value?.resetFields()
}

const handleSubmit = async () => {
  await formRef.value.validate(async (valid) => {
    if (!valid) return
    submitLoading.value = true
    try {
      if (isEdit.value) {
        await updateUser(form.value)
        ElMessage.success('修改成功')
      } else {
        await createUser(form.value)
        ElMessage.success('新增成功')
      }
      dialogVisible.value = false
      fetchData()
    } catch (e) {
      // request.js 已统一弹出错误，这里不需要额外处理
    } finally {
      submitLoading.value = false
    }
  })
}

const toggleState = async (row) => {
  const newState = row.state === 'enabled' ? 'disabled' : 'enabled'
  await updateUserState(row.id, newState)
  row.state = newState
  ElMessage.success(newState === 'enabled' ? '已启用' : '已禁用')
}

const toggleAdmin = async (row) => {
  const newVal = !row.is_admin
  await updateUserAdmin(row.id, newVal)
  row.is_admin = newVal
  ElMessage.success(newVal ? '已设为管理员' : '已取消管理员')
}

const handleDelete = async (row) => {
  await ElMessageBox.confirm(`确认删除用户「${row.username}」？此操作不可恢复`, '警告', {
    type: 'warning', confirmButtonText: '确认删除', cancelButtonText: '取消'
  })
  await deleteUser(row.id)
  ElMessage.success('删除成功')
  fetchData()
}

onMounted(fetchData)
</script>