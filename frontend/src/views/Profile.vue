<template>
  <div class="page-container">
    <el-row :gutter="16">
      <el-col :xs="24" :md="10">
        <el-card shadow="never">
          <template #header><span>个人信息</span></template>
          <div class="profile-header">
            <el-avatar :size="72" style="background:#2f6fd0;font-size:28px">
              {{ userStore.realName.charAt(0) }}
            </el-avatar>
            <div>
              <h3>{{ user.real_name }}</h3>
              <el-tag size="small">{{ userStore.roleLabel }}</el-tag>
              <p class="muted">@{{ user.username }}</p>
            </div>
          </div>

          <el-descriptions :column="1" border size="small" style="margin-top:20px">
            <el-descriptions-item label="账号">{{ user.username }}</el-descriptions-item>
            <el-descriptions-item label="身份">{{ identityLabel }}</el-descriptions-item>
            <el-descriptions-item label="学校">{{ user.school_name || '-' }}</el-descriptions-item>
            <el-descriptions-item label="手机号">{{ user.phone || '-' }}</el-descriptions-item>
            <el-descriptions-item label="邮箱">{{ user.email || '-' }}</el-descriptions-item>
            <el-descriptions-item label="上次登录">{{ user.last_login_at || '-' }}</el-descriptions-item>
          </el-descriptions>
        </el-card>
      </el-col>

      <el-col :xs="24" :md="14">
        <el-card shadow="never" style="margin-bottom:16px">
          <template #header><span>编辑资料</span></template>
          <el-form :model="editForm" label-width="90px" style="max-width:480px">
            <el-form-item label="姓名">
              <el-input v-model="editForm.real_name" />
            </el-form-item>
            <el-form-item label="手机号">
              <el-input v-model="editForm.phone" />
            </el-form-item>
            <el-form-item label="邮箱">
              <el-input v-model="editForm.email" />
            </el-form-item>
            <el-form-item>
              <el-button type="primary" :loading="saving" @click="saveProfile">保存</el-button>
            </el-form-item>
          </el-form>
        </el-card>

        <el-card shadow="never">
          <template #header><span>修改密码</span></template>
          <el-alert v-if="user.must_change_password" type="warning" show-icon :closable="false"
                    title="你正在使用初始密码，为保障账号安全请立即修改" style="margin-bottom:16px" />
          <el-form :model="pwdForm" :rules="pwdRules" ref="pwdRef" label-width="90px" style="max-width:480px">
            <el-form-item label="原密码" prop="old_password">
              <el-input v-model="pwdForm.old_password" type="password" show-password />
            </el-form-item>
            <el-form-item label="新密码" prop="new_password">
              <el-input v-model="pwdForm.new_password" type="password" show-password />
            </el-form-item>
            <el-form-item label="确认密码" prop="confirm_password">
              <el-input v-model="pwdForm.confirm_password" type="password" show-password />
            </el-form-item>
            <el-form-item>
              <el-button type="primary" :loading="changing" @click="changePassword">修改密码</el-button>
            </el-form-item>
          </el-form>
        </el-card>
      </el-col>
    </el-row>
  </div>
</template>

<script setup>
import { computed, onMounted, ref } from 'vue'
import { ElMessage } from 'element-plus'
import { authApi } from '@/api'
import { useUserStore } from '@/store/user'
import { validatePassword } from '@/utils/password'

const userStore = useUserStore()
const user = ref({})

const pwdRef = ref()
const saving = ref(false)
const changing = ref(false)

const editForm = ref({ real_name: '', phone: '', email: '' })
const pwdForm = ref({ old_password: '', new_password: '', confirm_password: '' })

const identityLabel = computed(() => ({
  student: '学生', teacher: '教师', grade_admin: '年级管理员', sys_admin: '系统管理员'
}[user.value.identity] || user.value.identity))

const pwdRules = {
  old_password: [{ required: true, message: '请输入原密码', trigger: 'blur' }],
  new_password: [
    { required: true, message: '请输入新密码', trigger: 'blur' },
    { validator: validatePassword, trigger: 'blur' }
  ],
  confirm_password: [
    { required: true, message: '请再次输入新密码', trigger: 'blur' },
    { validator: (r, v, cb) => v === pwdForm.value.new_password ? cb() : cb(new Error('两次密码不一致')), trigger: 'blur' }
  ]
}

async function loadProfile() {
  const data = await userStore.fetchProfile()
  user.value = data
  editForm.value = {
    real_name: data.real_name || '', phone: data.phone || '', email: data.email || ''
  }
}

async function saveProfile() {
  saving.value = true
  try {
    await authApi.updateProfile(editForm.value)
    ElMessage.success('资料已保存')
    await loadProfile()
  } finally {
    saving.value = false
  }
}

async function changePassword() {
  // 校验失败会 reject；未 catch 时冒泡到 app.config.errorHandler，
  // 用户看到的是「页面出错」而不是表单红字提示
  if (!(await pwdRef.value.validate().catch(() => false))) return
  changing.value = true
  try {
    await authApi.changePassword({
      old_password: pwdForm.value.old_password,
      new_password: pwdForm.value.new_password
    })
    ElMessage.success('密码修改成功')
    pwdForm.value = { old_password: '', new_password: '', confirm_password: '' }
    await loadProfile()
  } finally {
    changing.value = false
  }
}

onMounted(loadProfile)
</script>

<style scoped>
.profile-header {
  display: flex;
  align-items: center;
  gap: 20px;
}

.profile-header h3 {
  margin: 0 0 8px;
  font-size: 18px;
}

.muted {
  color: #909399;
  font-size: 13px;
  margin: 8px 0 0;
}
</style>
