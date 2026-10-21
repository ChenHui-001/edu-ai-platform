<template>
  <div class="login-page">
    <div class="login-left">
      <div class="brand">
        <el-icon :size="46"><School /></el-icon>
        <h1>九年义务教育学习管理系统</h1>
        <p>AI Agent 版 · 覆盖教-学-练-考-评-改全教学流程</p>
      </div>
      <ul class="feature-list">
        <li><el-icon><MagicStick /></el-icon> 6 大 AI Agent 协作智能引擎</li>
        <li><el-icon><Notebook /></el-icon> 智能组卷与题库管理</li>
        <li><el-icon><EditPen /></el-icon> 客观题自动批改 + AI 辅助批改</li>
        <li><el-icon><Refresh /></el-icon> 艾宾浩斯智能复习计划</li>
        <li><el-icon><DataLine /></el-icon> 全维度学情数据报表</li>
      </ul>
    </div>

    <div class="login-right">
      <el-card class="login-card" shadow="never">
        <h2 class="login-title">欢迎登录</h2>
        <p class="login-sub">请输入账号密码继续</p>

        <el-form ref="formRef" :model="form" :rules="rules" size="large" @keyup.enter="handleLogin">
          <el-form-item prop="username">
            <el-input v-model="form.username" placeholder="请输入账号" clearable>
              <template #prefix><el-icon><User /></el-icon></template>
            </el-input>
          </el-form-item>

          <el-form-item prop="password">
            <el-input v-model="form.password" type="password" placeholder="请输入密码" show-password clearable>
              <template #prefix><el-icon><Lock /></el-icon></template>
            </el-input>
          </el-form-item>

          <el-form-item prop="captcha">
            <div class="captcha-row">
              <el-input v-model="form.captcha" placeholder="验证码" style="flex:1">
                <template #prefix><el-icon><Key /></el-icon></template>
              </el-input>
              <img
                v-if="captchaImg" :src="captchaImg"
                class="captcha-img" title="点击刷新" @click="loadCaptcha"
              />
            </div>
          </el-form-item>

          <el-form-item>
            <el-button type="primary" class="login-btn" :loading="loading" @click="handleLogin">
              登 录
            </el-button>
          </el-form-item>

          <div class="login-footer">
            <router-link to="/register" class="link">注册账号</router-link>
            <el-dropdown trigger="click" @command="fillDemo">
              <el-link type="primary" :underline="false" class="link">
                演示账号<el-icon><ArrowDown /></el-icon>
              </el-link>
              <template #dropdown>
                <el-dropdown-menu>
                  <el-dropdown-item command="admin">系统管理员 admin / Admin@123456</el-dropdown-item>
                  <el-dropdown-item command="teacher">教师 teacher1 / Teacher@123</el-dropdown-item>
                  <el-dropdown-item command="student">学生 stu731 / Student@123</el-dropdown-item>
                </el-dropdown-menu>
              </template>
            </el-dropdown>
          </div>
        </el-form>

        <el-alert v-if="mustChange" type="warning" :closable="false" show-icon
                  title="首次登录请先修改密码" style="margin-top: 12px" />
      </el-card>
    </div>
  </div>
</template>

<script setup>
import { onMounted, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { authApi } from '@/api'
import { useUserStore } from '@/store/user'

const route = useRoute()
const router = useRouter()
const userStore = useUserStore()

const formRef = ref()
const loading = ref(false)
const captchaImg = ref('')
const captchaKey = ref('')
const mustChange = ref(false)

const form = ref({ username: '', password: '', captcha: '' })

const rules = {
  username: [{ required: true, message: '请输入账号', trigger: 'blur' }],
  password: [{ required: true, message: '请输入密码', trigger: 'blur' }],
  captcha: [{ required: true, message: '请输入验证码', trigger: 'blur' }]
}

async function loadCaptcha() {
  try {
    const res = await authApi.captcha()
    captchaImg.value = res.data.image
    captchaKey.value = res.data.key
  } catch (e) { /* 忽略 */ }
}

async function handleLogin() {
  // 同上：校验失败的 rejection 不能被全局错误兜底捕获
  if (!(await formRef.value.validate().catch(() => false))) return
  loading.value = true
  try {
    const res = await userStore.login({
      username: form.value.username,
      password: form.value.password,
      captcha: captchaKey.value ? form.value.captcha : undefined,
      captcha_key: captchaKey.value || undefined
    })
    mustChange.value = res.data.user.must_change_password
    ElMessage.success('登录成功')
    if (res.data.user.must_change_password) {
      router.push('/profile')
    } else {
      router.push(route.query.redirect || '/dashboard')
    }
  } catch (e) {
    loadCaptcha()
    form.value.captcha = ''
  } finally {
    loading.value = false
  }
}

// 演示账号必须与 init_db.py 的播种规则一致：
// 学生为 stu{年级}{班级}{序号}，序号从 1 开始（stu101/stu721/stu731...），
// 不存在 stu710 —— 写错会导致「演示账号一键填充后登录必失败」。
function fillDemo(cmd) {
  const demos = {
    admin: ['admin', 'Admin@123456'],
    teacher: ['teacher1', 'Teacher@123'],
    student: ['stu731', 'Student@123']
  }
  const [u, p] = demos[cmd] || []
  form.value.username = u
  form.value.password = p
}

onMounted(loadCaptcha)
</script>

<style scoped>
.login-page {
  display: flex;
  height: 100vh;
  background: #f0f4f9;
}

.login-left {
  flex: 1;
  background: linear-gradient(135deg, #2f6fd0 0%, #5a8fd6 50%, #764ba2 100%);
  color: #fff;
  display: flex;
  flex-direction: column;
  justify-content: center;
  padding: 0 8%;
  position: relative;
  overflow: hidden;
}

.login-left::after {
  content: '';
  position: absolute;
  width: 400px; height: 400px;
  border-radius: 50%;
  background: rgba(255, 255, 255, 0.08);
  right: -100px; bottom: -100px;
}

.brand h1 {
  font-size: 32px;
  margin: 16px 0 8px;
  font-weight: 700;
}

.brand p {
  font-size: 15px;
  opacity: 0.9;
  margin: 0;
}

.feature-list {
  list-style: none;
  padding: 0;
  margin: 48px 0 0;
}

.feature-list li {
  display: flex;
  align-items: center;
  gap: 10px;
  margin-bottom: 16px;
  font-size: 15px;
  opacity: 0.95;
}

.login-right {
  flex: 1;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 20px;
}

.login-card {
  width: 100%;
  max-width: 400px;
  border-radius: 12px;
}

.login-title {
  margin: 0 0 6px;
  font-size: 24px;
  color: #1f2d3d;
}

.login-sub {
  margin: 0 0 28px;
  color: #909399;
  font-size: 14px;
}

.login-btn {
  width: 100%;
  letter-spacing: 4px;
}

.captcha-row {
  display: flex;
  gap: 10px;
  width: 100%;
  align-items: center;
}

.captcha-img {
  height: 48px;
  width: 170px;
  border-radius: 4px;
  cursor: pointer;
  border: 1px solid #dcdfe6;
  flex-shrink: 0;
}

.login-footer {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.link {
  font-size: 13px;
  text-decoration: none;
}

@media (max-width: 900px) {
  .login-left { display: none; }
}
</style>
