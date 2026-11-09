<template>
  <div class="page-container">
    <div class="page-header">
      <h2 class="page-title">用户管理</h2>
      <div>
        <el-button :icon="Refresh" @click="load">刷新</el-button>
        <el-button v-if="isSysAdmin" type="primary" :icon="Plus" @click="openDialog()">新增用户</el-button>
      </div>
    </div>

    <el-card shadow="never" class="filter-card">
      <el-form :inline="true" :model="query">
        <el-form-item label="关键词">
          <el-input v-model="query.keyword" placeholder="用户名/姓名/手机号" clearable
                    style="width:180px" @keyup.enter="load" />
        </el-form-item>
        <el-form-item label="身份">
          <el-select v-model="query.identity" placeholder="全部" clearable style="width:120px">
            <el-option label="学生" value="student" />
            <el-option label="教师" value="teacher" />
            <el-option label="管理员" value="admin" />
          </el-select>
        </el-form-item>
        <el-form-item label="状态">
          <el-select v-model="query.status" placeholder="全部" clearable style="width:120px">
            <el-option label="正常" value="active" />
            <el-option label="待审批" value="pending" />
            <el-option label="已禁用" value="disabled" />
            <el-option label="已锁定" value="locked" />
          </el-select>
        </el-form-item>
        <el-form-item label="年级">
          <el-select v-model="query.grade_id" placeholder="全部" clearable style="width:130px">
            <el-option v-for="g in grades" :key="g.id" :label="g.name" :value="g.id" />
          </el-select>
        </el-form-item>
        <el-form-item>
          <el-button type="primary" :icon="Search" @click="load">查询</el-button>
          <el-button :icon="Refresh" @click="reset">重置</el-button>
        </el-form-item>
      </el-form>
    </el-card>

    <el-card shadow="never">
      <el-table v-loading="loading" :data="list" border stripe>
        <template #empty><TableEmpty text="暂无用户" /></template>
        <el-table-column prop="username" label="用户名" width="120" />
        <el-table-column prop="real_name" label="姓名" width="100" />
        <el-table-column label="身份" width="90">
          <template #default="{ row }">
            <el-tag :type="identityTag(row.identity)" size="small">
              {{ IDENTITY[row.identity] || row.identity }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column label="角色" min-width="140">
          <template #default="{ row }">
            <el-tag v-for="r in row.roles" :key="r" size="small" class="mr4"
                    effect="plain">{{ ROLE[r] || r }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="grade_name" label="年级" width="100" />
        <el-table-column prop="class_name" label="班级" width="120" />
        <el-table-column prop="phone" label="手机号" width="130" />
        <el-table-column label="状态" width="110">
          <template #default="{ row }">
            <!-- 锁定不写在 status 上（仍是 active），必须优先判 is_locked，
                 否则被锁账号在列表里显示"正常"，管理员只能猜测原因。 -->
            <el-tag v-if="row.is_locked" type="warning" size="small">
              已锁定{{ row.login_fail_count ? `(${row.login_fail_count})` : '' }}
            </el-tag>
            <el-tag v-else :type="statusTag(row.status)" size="small">{{ STATUS[row.status] || row.status }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="last_login_at" label="最后登录" width="160" />
        <el-table-column label="操作" width="200" fixed="right">
          <template #default="{ row }">
            <el-button v-if="isSysAdmin" link type="primary" @click="openDialog(row)">编辑</el-button>
            <el-button v-if="isSysAdmin && row.is_locked" link type="success"
                       @click="doUnlock(row)">解锁</el-button>
            <el-button v-if="isSysAdmin" link type="warning" @click="openReset(row)">重置密码</el-button>
            <el-button v-if="isSysAdmin" link type="danger" @click="remove(row)">删除</el-button>
          </template>
        </el-table-column>
      </el-table>

      <el-pagination class="mt16" background layout="total, sizes, prev, pager, next"
                     :total="total" v-model:current-page="query.page"
                     v-model:page-size="query.page_size"
                     :page-sizes="[10, 20, 50, 100]"
                     @current-change="load" @size-change="load" />
    </el-card>

    <!-- 新增 / 编辑 -->
    <el-dialog v-model="dlg" :title="form.id ? '编辑用户' : '新增用户'" width="620px">
      <el-form :model="form" :rules="rules" label-width="90px">
        <el-row :gutter="12">
          <el-col :span="12">
            <el-form-item label="用户名" prop="username">
              <el-input v-model="form.username" :disabled="!!form.id" />
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="姓名" prop="real_name">
              <el-input v-model="form.real_name" />
            </el-form-item>
          </el-col>
        </el-row>
        <el-form-item v-if="!form.id" label="初始密码" prop="password">
          <el-input v-model="form.password" show-password placeholder="不填则默认 Edu@2026Init（≥8 位且含字母+数字）" />
        </el-form-item>
        <el-row :gutter="12">
          <el-col :span="12">
            <el-form-item label="身份" prop="identity">
              <el-select v-model="form.identity" style="width:100%">
                <el-option label="学生" value="student" />
                <el-option label="教师" value="teacher" />
                <el-option label="管理员" value="admin" />
              </el-select>
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="状态">
              <el-select v-model="form.status" style="width:100%">
                <el-option label="正常" value="active" />
                <el-option label="待审批" value="pending" />
                <el-option label="已禁用" value="disabled" />
              </el-select>
            </el-form-item>
          </el-col>
        </el-row>
        <el-row :gutter="12">
          <el-col :span="12">
            <el-form-item label="角色">
              <el-select v-model="form.role_codes" multiple style="width:100%">
                <el-option v-for="r in roles" :key="r.code" :label="r.name" :value="r.code" />
              </el-select>
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="手机号">
              <el-input v-model="form.phone" />
            </el-form-item>
          </el-col>
        </el-row>
        <el-row :gutter="12">
          <el-col :span="12">
            <el-form-item label="年级">
              <el-select v-model="form.grade_id" clearable style="width:100%">
                <el-option v-for="g in grades" :key="g.id" :label="g.name" :value="g.id" />
              </el-select>
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="班级">
              <el-select v-model="form.class_id" clearable style="width:100%">
                <el-option v-for="c in classes" :key="c.id" :label="c.name" :value="c.id" />
              </el-select>
            </el-form-item>
          </el-col>
        </el-row>
        <el-form-item label="邮箱">
          <el-input v-model="form.email" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="dlg = false">取消</el-button>
        <el-button type="primary" :loading="saving" @click="save">确定</el-button>
      </template>
    </el-dialog>

    <!-- 重置密码 -->
    <el-dialog v-model="resetDlg" title="重置密码" width="420px">
      <el-alert type="warning" :closable="false" class="mb12"
                title="重置后该用户首次登录需修改密码" />
      <el-form label-width="90px">
        <el-form-item label="用户">
          <span>{{ current?.real_name }}（{{ current?.username }}）</span>
        </el-form-item>
        <el-form-item label="新密码">
          <el-input v-model="newPwd" show-password placeholder="留空自动生成强密码；需 ≥8 位含字母+数字" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="resetDlg = false">取消</el-button>
        <el-button type="primary" @click="doReset">确认重置</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, reactive, computed, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import { Plus, Search, Refresh } from '@element-plus/icons-vue'
import { systemApi, eduApi } from '@/api'
import { confirmAction } from '@/utils/confirm'
import { toastIfUnhandled } from '@/utils/notify'
import { useUserStore } from '@/store/user'

// 路由 admin/users 对 grade_admin 放行，但后端新建/改/删/重置密码四处
// 只认 sys_admin。此前四个写按钮无条件渲染，年级管理员点进去必定 403；
// 与项目其它管理页一致按角色门控，只读列表仍可用。
const userStore = useUserStore()
const isSysAdmin = computed(() => userStore.isAdmin === true)

const IDENTITY = { student: '学生', teacher: '教师', admin: '管理员' }
const ROLE = { sys_admin: '系统管理员', grade_admin: '年级管理员', teacher: '任课教师', student: '学生', guest: '访客' }
const STATUS = { active: '正常', pending: '待审批', disabled: '已禁用', locked: '已锁定' }

const list = ref([])
const roles = ref([])
const grades = ref([])
const classes = ref([])
const total = ref(0)
const loading = ref(false)
const dlg = ref(false)
const resetDlg = ref(false)
const saving = ref(false)
const current = ref(null)
const newPwd = ref('')

const query = reactive({ page: 1, page_size: 20, keyword: '', identity: '', status: '', grade_id: null })
const form = reactive({ id: null, username: '', real_name: '', password: '', identity: 'student',
  role_codes: ['student'], status: 'active', phone: '', email: '', grade_id: null, class_id: null })

const rules = {
  username: [{ required: true, message: '请输入用户名', trigger: 'blur' }],
  real_name: [{ required: true, message: '请输入姓名', trigger: 'blur' }],
  identity: [{ required: true, message: '请选择身份', trigger: 'change' }]
}

function identityTag(v) { return { student: 'info', teacher: 'success', admin: 'danger' }[v] || '' }
function statusTag(v) { return { active: 'success', pending: 'warning', disabled: 'danger', locked: 'info' }[v] || '' }

async function load() {
  loading.value = true
  try {
    const res = await systemApi.users(query)
    const d = res.data || {}
    list.value = d.items || []
    total.value = d.total || 0
  } finally {
    loading.value = false
  }
}

function reset() {
  Object.assign(query, { page: 1, keyword: '', identity: '', status: '', grade_id: null })
  load()
}

function openDialog(row) {
  Object.assign(form, row
    ? { ...row, role_codes: (row.roles || []).slice(), password: '' }
    : { id: null, username: '', real_name: '', password: '', identity: 'student',
        role_codes: ['student'], status: 'active', phone: '', email: '', grade_id: null, class_id: null })
  dlg.value = true
}

async function save() {
  saving.value = true
  try {
    if (form.id) {
      const { id, roles, ...payload } = form
      await systemApi.updateUser(id, payload)
      ElMessage.success('保存成功')
    } else {
      await systemApi.createUser({ ...form })
      ElMessage.success('创建成功')
    }
    dlg.value = false
    load()
  } finally {
    saving.value = false
  }
}

function openReset(row) {
  current.value = row
  newPwd.value = ''
  resetDlg.value = true
}

/** 生成满足强度要求的随机初始密码（字母+数字+特殊字符，12 位） */
function genStrongPassword() {
  const upper = 'ABCDEFGHJKLMNPQRSTUVWXYZ'
  const lower = 'abcdefghijkmnpqrstuvwxyz'
  const digit = '23456789'
  const pick = (s, n) => Array.from({ length: n },
    () => s[Math.floor(Math.random() * s.length)]).join('')
  return pick(upper, 2) + pick(lower, 4) + pick(digit, 4) + '@#'[Math.floor(Math.random() * 2)]
}

async function doReset() {
  // 字段名必须是 new_password：此前传 password，后端 Pydantic 校验失败 → 必然 422
  // 留空时前端生成强密码并明确告知管理员
  const pwd = (newPwd.value || '').trim() || genStrongPassword()
  try {
    await systemApi.resetPassword({ user_id: current.value.id, new_password: pwd })
    ElMessage.success(`密码已重置为：${pwd}（请转告用户，首次登录需修改）`)
    newPwd.value = ''
    resetDlg.value = false
  } catch (e) {
    toastIfUnhandled(e, '重置失败')
  }
}

async function doUnlock(row) {
  // 只用 confirmAction（内部吃掉 'cancel'/'close' 拒绝），避免点取消触发
  // 全局红条「页面运行时错误： cancel」。
  if (!await confirmAction(`解除「${row.real_name || row.username}」的登录锁定？该账号可立即重新登录。`,
    { title: '解除锁定' })) return
  try {
    const res = await systemApi.unlockUser(row.id)
    if (res?.data?.unlocked === false) ElMessage.info(res?.message || '该账号当前未被锁定')
    else ElMessage.success('已解除锁定')
    load()
  } catch (e) {
    toastIfUnhandled(e, '解锁失败')
  }
}

async function remove(row) {
  if (!await confirmAction(
    `确认删除用户「${row.real_name}」？\n` +
    '若该账号已创建题目/试卷/作业/教案，或有作答记录，系统会拒绝删除——请改用「停用」。',
    '提示', { type: 'warning' })) return
  await systemApi.deleteUser(row.id)
  ElMessage.success('已删除')
  load()
}

onMounted(async () => {
  await load()
  const [r, g] = await Promise.all([systemApi.roles(), eduApi.grades()])
  roles.value = r.data || []
  grades.value = g.data || []
  const c = await eduApi.classes({ page_size: 200 })
  // /edu/classes 返回数组（非分页 items），只读 data.items 会让「所属班级」
  // 下拉恒为空 —— 无法把学生/教师绑定到班级。
  const _cd = c.data
  classes.value = Array.isArray(_cd) ? _cd : (_cd?.items || [])
})
</script>

<style scoped>
.mr4 { margin-right: 4px; }
.mt16 { margin-top: 16px; justify-content: flex-end; }
.mb12 { margin-bottom: 12px; }
</style>
