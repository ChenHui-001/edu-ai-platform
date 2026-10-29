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

        <el-form-item label="图形验证码" prop="captcha">
          <div class="captcha-row">
            <el-input v-model="form.captcha" placeholder="请输入图中字符" style="flex:1" />
            <img
              v-if="captchaImg" :src="captchaImg"
              class="captcha-img" title="点击刷新" @click="loadCaptcha"
            />
            <button v-else type="button" class="captcha-retry" @click="loadCaptcha">
              {{ captchaError ? '重新获取' : '加载中…' }}
            </button>
          </div>
          <!-- 取码失败必须可见：后端强制化后，静默失败会让注册按钮永久无效 -->
          <div v-if="captchaError" class="captcha-alert">{{ captchaError }}</div>
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
  phone: '', email: '', captcha: ''
})

// S7：注册接口同样强制校验图形验证码（后端 `_verify_captcha_or_raise`）。
// 修复前这里连输入框都没有 —— 因为后端是短路绕过，不传 key 就整段跳过。
const captchaImg = ref('')
const captchaKey = ref('')
const captchaError = ref('')

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
  captcha: [{ required: true, message: '请输入图形验证码', trigger: 'blur' }],
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

async function loadCaptcha() {
  // 与 Login.vue 同契约：失败**不静默**。注册页的失败代价更高 ——
  // 用户已经填完账号/密码/姓名/班级，还要上传证明材料；如果取码失败被吞掉，
  // 提交时才报一个含糊的 400，用户不会认为是验证码问题，只会反复重填。
  try {
    const res = await authApi.captcha()
    captchaImg.value = res.data.image
    captchaKey.value = res.data.key
    captchaError.value = ''
    return true
  } catch (e) {
    captchaImg.value = ''
    captchaKey.value = ''
    captchaError.value = '验证码加载失败，请点击「重新获取」后重试'
    return false
  }
}

async function handleRegister() {
  // validate() 校验失败时 reject，未 catch 会冒泡到 app.config.errorHandler
  const valid = await formRef.value.validate().catch(() => false)
  if (!valid) return
  // 本地没有 captcha_key 必然被后端拒绝，先补一次取码并明确告知
  if (!captchaKey.value) {
    const ok = await loadCaptcha()
    if (!ok) {
      ElMessage.warning(captchaError.value)
      return
    }
    ElMessage.warning('验证码已刷新，请重新输入验证码')
    form.value.captcha = ''
    return
  }
  loading.value = true
  try {
    await authApi.register({
      ...form.value,
      // confirmPassword 只用于前端一致性校验，后端 schema 没有该字段
      confirmPassword: undefined,
      captcha: form.value.captcha,
      captcha_key: captchaKey.value,
      attachments: attachmentIds.value.join(',')
    })
    ElMessage.success('注册申请已提交，请等待管理员审批')
    router.push('/login')
  } catch (e) {
    // 验证码一次性：失败后必须换一张，否则同一 key 重试永远失败
    loadCaptcha()
    form.value.captcha = ''
  } finally {
    loading.value = false
  }
}

onMounted(async () => {
  // 验证码与班级列表互不依赖，并行取；任一失败都不阻断整页渲染
  loadCaptcha()
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

.captcha-row { display: flex; gap: 10px; width: 100%; align-items: center; }

.captcha-img {
  height: 40px;
  width: 140px;
  border-radius: 4px;
  cursor: pointer;
  border: 1px solid var(--el-border-color-lighter);
}

.captcha-retry {
  height: 40px;
  width: 140px;
  border: 1px dashed var(--el-border-color);
  border-radius: 4px;
  background: var(--el-fill-color-lighter);
  color: var(--el-color-primary);
  font-size: 13px;
  cursor: pointer;
}

.captcha-retry:hover { border-color: var(--el-color-primary); }

.captcha-alert {
  font-size: 12px;
  line-height: 1.6;
  color: var(--el-color-danger);
  margin-top: 6px;
}
</style>
