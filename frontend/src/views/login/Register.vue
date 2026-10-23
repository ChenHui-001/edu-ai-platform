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
          <el-input v-model="form.password" type="password" show-password placeholder="至少 8 位，需含字母和数字" />
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
              :label="classLabel(c)" :value="c.id"
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
import { Plus } from '@element-plus/icons-vue'
import { authApi, attachmentApi, eduApi } from '@/api'
import { validatePassword } from '@/utils/password'

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
    { validator: validatePassword, trigger: 'blur' }
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

// 班级名多已自带年级前缀（如「一年级(1)班」），直接拼 grade_name 会重复成
// 「一年级 一年级(1)班」。同名判断后按需补前缀。
function classLabel(c) {
  const name = c.name || ''
  const grade = c.grade_name || ''
  if (!grade || name.startsWith(grade)) return name
  return `${grade} ${name}`
}

function onIdentityChange() {
  form.value.class_id = null
}

async function uploadFile({ file }) {
  const fd = new FormData()
  fd.append('file', file)
  fd.append('category', 'registration')
  try {
    // 注册页未登录，必须用匿名上传接口（/attachments/upload 需登录会 401）
    const res = await attachmentApi.publicUpload(fd)
    attachmentIds.value.push(res.data.id)
    fileList.value.push({ name: file.name, url: res.data.url, id: res.data.id })
    ElMessage.success('上传成功')
  } catch (e) { /* 错误已由拦截器提示 */ }
}

function removeFile(file) {
  attachmentIds.value = attachmentIds.value.filter(id => id !== file.id)
}

async function handleRegister() {
  // validate() 校验失败时 reject，未 catch 会冒泡到 app.config.errorHandler
  const valid = await formRef.value.validate().catch(() => false)
  if (!valid) return
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
  // 注册页必须能在**未登录**状态完整渲染：这里只用匿名接口，且失败也要降级，
  // 绝不能因为班级列表拉取失败把整页打回登录页。
  try {
    const res = await eduApi.classesPublic()
    classes.value = res.data || []
  } catch (e) {
    classes.value = []
    ElMessage.warning('班级列表暂时无法加载，可稍后重试或先不选班级')
  }
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
