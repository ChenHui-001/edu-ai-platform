<template>
  <div class="login-page">
    <div class="login-left">
      <div class="brand">
        <el-icon :size="46"><School /></el-icon>
        <h1>新芽学堂</h1>
        <p>九年义务教育 AI 学习平台 · 覆盖教-学-练-考-评-改全教学流程</p>
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
      <!-- 窄屏（<=900px）左侧品牌区被隐藏，这里补一个紧凑品牌头：
           否则小屏/分屏用户看到的是一个没有任何来由的裸表单，
           既看不到产品名也看不到定位（900px 是笔记本分屏的常见宽度）。 -->
      <div class="brand-compact">
        <el-icon :size="28"><School /></el-icon>
        <div class="brand-compact-text">
          <strong>新芽学堂</strong>
          <span>九年义务教育 AI 学习平台</span>
        </div>
      </div>
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
              <!-- 取码失败时不能只留一个空白方块：必须给出可点击的补救入口 -->
              <button v-else type="button" class="captcha-retry" @click="loadCaptcha">
                {{ captchaError ? '重新获取' : '加载中…' }}
              </button>
            </div>
          </el-form-item>
          <!-- 取码失败的可见提示：后端强制化后，静默失败等于登录按钮永久失效 -->
          <el-alert
            v-if="captchaError" type="error" :closable="false" show-icon
            :title="captchaError" class="captcha-alert"
          />

          <el-form-item>
            <el-button type="primary" class="login-btn" :loading="loading" @click="handleLogin">
              登 录
            </el-button>
          </el-form-item>

          <div class="login-footer">
            <div>
              <router-link to="/register" class="link">注册账号</router-link>
              <!-- /auth/forgot-password 与 /auth/reset-password 后端早已实现，
                   但登录页没有任何入口，学生忘记密码只能找管理员。 -->
              <el-link type="primary" :underline="false" class="link"
                       style="margin-left:12px" @click="forgotPassword">忘记密码</el-link>
            </div>
            <!-- 演示账号默认不展示：登录页公网可达，明文列出 admin 口令等于公开
                 默认管理员凭据。仅在显式设置 VITE_SHOW_DEMO_ACCOUNTS=true 时显示
                 （本地体验/演示环境），生产构建保持隐藏。 -->
            <el-dropdown v-if="showDemoAccounts" trigger="click" @command="fillDemo">
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
import { ElMessage, ElMessageBox } from 'element-plus'
import {
  School, MagicStick, Notebook, EditPen, Refresh, DataLine, User, Lock, Key, ArrowDown
} from '@element-plus/icons-vue'
import { authApi } from '@/api'
import { useUserStore } from '@/store/user'

const route = useRoute()
const router = useRouter()
const userStore = useUserStore()

const formRef = ref()
const loading = ref(false)
const captchaImg = ref('')
const captchaKey = ref('')
// 取码失败的原因。非空时页面上必须**看得见**，且禁止提交 —— 这是 S7 强制化
// 的前端对应物：后端不再接受"没带验证码"的登录，前端就不能悄悄降级。
const captchaError = ref('')
const mustChange = ref(false)
// 演示账号下拉默认关闭，避免公网部署时自动暴露 admin 默认口令。
const showDemoAccounts = import.meta.env.VITE_SHOW_DEMO_ACCOUNTS === 'true'

const form = ref({ username: '', password: '', captcha: '' })

const rules = {
  username: [{ required: true, message: '请输入账号', trigger: 'blur' }],
  password: [{ required: true, message: '请输入密码', trigger: 'blur' }],
  captcha: [{ required: true, message: '请输入验证码', trigger: 'blur' }]
}

// 找回密码：后端 /auth/forgot-password + /auth/reset-password 早已实现，
// 但页面上没有入口。用三步 prompt 走完「发码 → 验码 → 设新密码」，
// 不新增路由/弹窗组件，避免为了一个低频入口扩大改动面。
async function forgotPassword() {
  try {
    const { value: target } = await ElMessageBox.prompt(
      '请输入注册时使用的邮箱或手机号', '找回密码', {
        confirmButtonText: '发送验证码', cancelButtonText: '取消',
        inputPattern: /\S+/, inputErrorMessage: '请输入邮箱或手机号'
      })
    const field = String(target).includes('@') ? 'email' : 'phone'
    const res = await authApi.forgotPassword({ [field]: target })
    // 后端有两个分支：sent=true（已发 / 账号不存在但按安全惯例不泄露）
    // 与 sent=false（账号存在但系统没配邮件通道）。此前硬编码绿色「已发送」，
    // 未配置邮件时用户会白等 5 分钟、第 3 步必然报「验证码错误」。
    if (res?.data?.sent === false) {
      ElMessage.warning(res?.message || '邮件服务未配置，请联系管理员重置密码')
      return
    }
    ElMessage.success('若该账号存在，验证码已发送')
    const { value: code } = await ElMessageBox.prompt(
      '请输入收到的 6 位验证码', '找回密码', {
        confirmButtonText: '下一步', cancelButtonText: '取消',
        inputPattern: /^\d{6}$/, inputErrorMessage: '验证码为 6 位数字'
      })
    const { value: newPwd } = await ElMessageBox.prompt(
      '请设置新密码（至少 8 位，含字母和数字）', '找回密码', {
        confirmButtonText: '提交', cancelButtonText: '取消',
        inputType: 'password', inputPattern: /^.{8,}$/,
        inputErrorMessage: '密码至少 8 位'
      })
    await authApi.resetPasswordByCode({ [field]: target, code, new_password: newPwd })
    ElMessage.success('密码已重置，请用新密码登录')
    loadCaptcha()
  } catch {
    // 用户点「取消」或接口失败：拦截器已统一提示，这里不重复弹窗
  }
}

async function loadCaptcha() {
  // S7：后端已强制校验验证码（不携带 captcha_key 直接 400），所以这里
  // **绝不能再静默吞异常**。原先的 `catch (e) { /* 忽略 */ }` 会让
  // captchaKey 保持空字符串，handleLogin 就发出 captcha_key: undefined，
  // 强制化之后必然 400 —— 而页面上一个字的提示都没有，用户只会看到
  // "登录失败" 反复重试，永远不可能成功。
  //
  // 现在的契约：取码失败 → captchaError 置位 → 提交按钮禁用并提示重试。
  // 宁可让用户明确知道"验证码没加载出来，点一下刷新"，也不要让他对着
  // 一个永远失败的登录按钮重输密码。
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

async function handleLogin() {
  // 同上：校验失败的 rejection 不能被全局错误兜底捕获
  if (!(await formRef.value.validate().catch(() => false))) return
  // 兜底：本地没有 captcha_key 一定过不了后端（强制化后返回 400「请输入
  // 图形验证码」）。与其把请求发出去换一个服务端错误，不如在这里先补一次
  // 取码并提示 —— 常见触发场景是页面开着很久，验证码 3 分钟就过期了。
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
    const res = await userStore.login({
      username: form.value.username,
      password: form.value.password,
      captcha: form.value.captcha,
      captcha_key: captchaKey.value
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

/* 取码失败时的替补按钮：与验证码图同尺寸，位置不跳动，
   让"点不到图"的用户一眼看到下一步该点哪里 */
.captcha-retry {
  height: 48px;
  width: 170px;
  border: 1px dashed var(--el-border-color);
  border-radius: 4px;
  background: var(--el-fill-color-lighter);
  color: var(--el-color-primary);
  font-size: 13px;
  cursor: pointer;
}

.captcha-retry:hover {
  border-color: var(--el-color-primary);
}

.captcha-alert {
  margin-bottom: 16px;
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

.brand-compact { display: none; }

@media (max-width: 900px) {
  .login-left { display: none; }
  .login-right { flex-direction: column; justify-content: center; }
  .brand-compact {
    display: flex;
    align-items: center;
    gap: 10px;
    margin-bottom: 14px;
    color: var(--el-color-primary);
  }
  .brand-compact-text strong { display: block; font-size: 20px; line-height: 1.25; }
  .brand-compact-text span { font-size: 12px; color: #8a94a6; }
}
</style>
