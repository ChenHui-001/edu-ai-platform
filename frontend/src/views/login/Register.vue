<template>
  <div class="register-page">
    <el-card class="register-card">
      <div class="header">
        <h2>用户注册</h2>
        <p>注册后需管理员审批，审批通过后方可登录</p>
      </div>

      <el-form ref="formRef" :model="form" :rules="rules" label-width="100px">
        <el-tabs v-model="form.identity" @change="onIdentityChange">
          <el-tab-pane label="学生注册" name="student" />
          <el-tab-pane label="教师注册" name="teacher" />
        </el-tabs>

        <el-form-item label="登录账号" prop="username">
          <el-input v-model="form.username" placeholder="3-32 位字母或数字" />
        </el-form-item>

        <el-form-item label="密码" prop="password">
          <el-input v-model="form.password" type="password" show-password placeholder="至少 6 位" />
        </el-form-item>

        <el-form-item label="确认密码" prop="confirmPassword">
          <el-input v-model="form.confirmPassword" type="password" show-password />
        </el-form-item>

        <el-form-item label="真实姓名" prop="real_name">
          <el-input v-model="form.real_name" placeholder="请输入真实姓名" />
        </el-form-item>

        <el-form-item label="学校名称">
          <el-input v-model="form.school_name" placeholder="选填" />
        </el-form-item>

        <el-form-item v-if="form.identity === 'student'" label="所属班级" prop="class_id">
          <el-select v-model="form.class_id" placeholder="请选择班级" style="width:100%">
            <el-option
              v-for="c in classes" :key="c.id"
              :label="`${c.grade_name || ''} ${c.name}`" :value="c.id"
            />
          </el-select>
        </el-form-item>

        <el-form-item label="手机号">
          <el-input v-model="form.phone" placeholder="选填，用于找回密码" />
        </el-form-item>

        <el-form-item label="邮箱">
          <el-input v-model="form.email" placeholder="选填" />
        </el-form-item>

        <el-form-item label="证明材料">
          <el-upload
            :http-request="uploadFile" :limit="3"
            :on-remove="removeFile" :file-list="fileList"
            list-type="picture-card"
          >
            <el-icon><Plus /></el-icon>
          </el-upload>
          <div class="tip">{{ form.identity === 'teacher' ? '教师资格证' : '学生证 / 班级证明' }}</div>
        </el-form-item>

        <el-form-item>
          <el-button type="primary" :loading="loading" @click="handleRegister">
            提交注册申请
          </el-button>
          <el-button @click="$router.push('/login')">返回登录</el-button>
        </el-form-item>
      </el-form>
    </el-card>
  </div>
</template>

<script setup>
import { onMounted, ref } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { authApi, attachmentApi, eduApi } from '@/api'

const router = useRouter()
const formRef = ref()
const loading = ref(false)
const classes = ref([])
const fileList = ref([])
const attachmentIds = ref([])

const form = ref({
  username: '', password: '', confirmPassword: '', real_name: '',
  identity: 'student', school_name: '', class_id: null,
  phone: '', email: ''
})

const rules = {
  username: [
    { required: true, message: '请输入登录账号', trigger: 'blur' },
    { min: 3, max: 32, message: '账号长度 3-32 位', trigger: 'blur' }
  ],
  password: [
    { required: true, message: '请输入密码', trigger: 'blur' },
    { min: 6, message: '密码至少 6 位', trigger: 'blur' }
  ],
  confirmPassword: [
    { required: true, message: '请再次输入密码', trigger: 'blur' },
    { validator: (r, v, cb) => v === form.value.password ? cb() : cb(new Error('两次密码不一致')), trigger: 'blur' }
  ],
  real_name: [{ required: true, message: '请输入真实姓名', trigger: 'blur' }],
  class_id: [{
    validator: (r, v, cb) => {
      if (form.value.identity === 'student' && !v) return cb(new Error('学生注册需选择班级'))
      cb()
    },
    trigger: 'change'
  }]
}

function onIdentityChange() {
  form.value.class_id = null
}

async function uploadFile({ file }) {
  const fd = new FormData()
  fd.append('file', file)
  fd.append('category', 'registration')
  try {
    const res = await attachmentApi.upload(fd)
    attachmentIds.value.push(res.data.id)
    fileList.value.push({ name: file.name, url: res.data.url, id: res.data.id })
    ElMessage.success('上传成功')
  } catch (e) { /* 错误已提示 */ }
}

function removeFile(file) {
  attachmentIds.value = attachmentIds.value.filter(id => id !== file.id)
}

async function handleRegister() {
  await formRef.value.validate()
  loading.value = true
  try {
    await authApi.register({
      ...form.value,
      attachments: attachmentIds.value.join(',')
    })
    ElMessage.success('注册申请已提交，请等待管理员审批')
    router.push('/login')
  } finally {
    loading.value = false
  }
}

onMounted(async () => {
  const res = await eduApi.classes()
  classes.value = res.data
})
</script>

<style scoped>
.register-page {
  min-height: 100vh;
  background: linear-gradient(135deg, #eef3fa 0%, #e8eef7 100%);
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 30px 16px;
}

.register-card { width: 100%; max-width: 640px; }

.header { margin-bottom: 20px; }
.header h2 { margin: 0 0 6px; }
.header p { margin: 0; color: #909399; font-size: 13px; }

.tip { font-size: 12px; color: #909399; margin-top: 6px; }
</style>
