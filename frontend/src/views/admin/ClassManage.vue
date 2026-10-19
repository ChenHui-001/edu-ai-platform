<template>
  <div class="page-container">
    <div class="page-header">
      <h2 class="page-title">班级管理</h2>
      <div>
        <el-button :icon="Refresh" @click="load">刷新</el-button>
        <el-button v-if="can('resource:class:write')" type="primary" :icon="Plus" @click="openDialog()">新增班级</el-button>
        <!-- 教师视图：自建班申请（审核制） -->
        <template v-if="!can('resource:class:write')">
          <el-button type="success" :icon="Plus" @click="applyDlg = true">申请建班</el-button>
          <el-button :icon="Tickets" @click="myReqDlg = true; loadMyRequests()">
            我的申请<el-badge v-if="myPending" :value="myPending" class="ml4" />
          </el-button>
        </template>
        <!-- 管理视图：建班审核 -->
        <el-button v-if="can('resource:class:write')" type="warning" :icon="Bell" @click="reviewDlg = true; loadRequests()">
          建班审核<el-badge v-if="pendingCount" :value="pendingCount" class="ml4" />
        </el-button>
      </div>
    </div>

    <el-card shadow="never" class="filter-card">
      <el-form :inline="true" :model="query">
        <el-form-item label="年级">
          <el-select v-model="query.grade_id" placeholder="全部" clearable style="width:140px">
            <el-option v-for="g in grades" :key="g.id" :label="g.name" :value="g.id" />
          </el-select>
        </el-form-item>
        <el-form-item label="班主任">
          <el-select v-model="query.head_teacher_id" placeholder="全部" clearable filterable
                     style="width:160px">
            <el-option v-for="t in teachers" :key="t.id" :label="t.real_name" :value="t.id" />
          </el-select>
        </el-form-item>
        <el-form-item label="关键词">
          <el-input v-model="query.keyword" placeholder="班级名称" clearable style="width:160px"
                    @keyup.enter="load" />
        </el-form-item>
        <el-form-item>
          <el-button type="primary" :icon="Search" @click="load">查询</el-button>
          <el-button :icon="Refresh" @click="reset">重置</el-button>
        </el-form-item>
      </el-form>
    </el-card>

    <el-card shadow="never">
      <el-table v-loading="loading" :data="list" border stripe>
        <el-table-column prop="name" label="班级名称" min-width="160" />
        <el-table-column prop="grade_name" label="所属年级" width="130" />
        <el-table-column prop="head_teacher_name" label="班主任" width="120" />
        <el-table-column prop="student_count" label="学生数" width="90" align="center" />
        <el-table-column prop="description" label="说明" min-width="180" show-overflow-tooltip />
        <el-table-column prop="created_at" label="创建时间" width="160" />
        <el-table-column label="操作" width="200" fixed="right">
          <template #default="{ row }">
            <el-button link type="primary" @click="openStudents(row)">学生</el-button>
            <el-button v-if="can('resource:class:write')" link type="primary" @click="openDialog(row)">编辑</el-button>
            <el-button v-if="can('resource:class:write')" link type="danger" @click="remove(row)">删除</el-button>
          </template>
        </el-table-column>
      </el-table>

      <el-pagination class="mt16" background layout="total, prev, pager, next"
                     :total="total" v-model:current-page="query.page" @current-change="load" />
    </el-card>

    <el-dialog v-model="dlg" :title="form.id ? '编辑班级' : '新增班级'" width="480px">
      <el-form :model="form" label-width="90px">
        <el-form-item label="班级名称">
          <el-input v-model="form.name" placeholder="如：七年级(3)班" />
        </el-form-item>
        <el-form-item label="所属年级">
          <el-select v-model="form.grade_id" style="width:100%">
            <el-option v-for="g in grades" :key="g.id" :label="g.name" :value="g.id" />
          </el-select>
        </el-form-item>
        <el-form-item label="班主任">
          <el-select v-model="form.head_teacher_id" clearable filterable style="width:100%">
            <el-option v-for="t in teachers" :key="t.id" :label="t.real_name" :value="t.id" />
          </el-select>
        </el-form-item>
        <el-form-item label="说明">
          <el-input v-model="form.description" type="textarea" :rows="2" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="dlg = false">取消</el-button>
        <el-button type="primary" :loading="saving" @click="save">确定</el-button>
      </template>
    </el-dialog>

    <!-- 学生管理 -->
    <el-drawer v-model="studentDrawer" :title="`${currentClass?.name || ''} - 学生管理`" size="70%">
      <div class="mb12">
        <el-button v-if="can('resource:class:write')" type="primary" :icon="Upload" @click="importDlg = true">批量导入学生</el-button>
        <el-alert class="mt8" type="info" :closable="false"
                  title="批量导入需填写：username(学号)、real_name(姓名)、password(初始密码，可留空默认123456)" />
      </div>
      <el-table v-loading="studentLoading" :data="students" border stripe>
        <el-table-column prop="username" label="学号" width="130" />
        <el-table-column prop="real_name" label="姓名" width="120" />
        <el-table-column prop="phone" label="手机号" width="140" />
        <el-table-column prop="email" label="邮箱" min-width="180" show-overflow-tooltip />
        <el-table-column label="操作" width="110">
          <template #default="{ row }">
            <el-button link type="danger" @click="removeStudent(row)">移出班级</el-button>
          </template>
        </el-table-column>
      </el-table>
    </el-drawer>

    <el-dialog v-model="importDlg" title="批量导入学生" width="560px">
      <el-form label-width="90px">
        <el-form-item label="导入数据">
          <el-input v-model="importText" type="textarea" :rows="10"
                    placeholder="每行一个学生：username,real_name,password&#10;2026001,张三,123456" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="importDlg = false">取消</el-button>
        <el-button type="primary" :loading="importing" @click="doImport">导入</el-button>
      </template>
    </el-dialog>
  </div>
  <!-- 教师建班申请对话框 -->
  <el-dialog v-model="applyDlg" title="申请建班（提交后由管理员审核）" width="460px">
    <el-form :model="applyForm" label-width="80px">
      <el-form-item label="班级名称" required>
        <el-input v-model="applyForm.name" placeholder="如：七年级(3)班 / 初一兴趣数学班" maxlength="32" />
      </el-form-item>
      <el-form-item label="所属年级" required>
        <el-select v-model="applyForm.grade_id" style="width:100%" placeholder="选择年级">
          <el-option v-for="g in grades" :key="g.id" :label="g.name" :value="g.id" />
        </el-select>
      </el-form-item>
      <el-form-item label="申请说明">
        <el-input v-model="applyForm.description" type="textarea" :rows="2"
                  placeholder="建班用途，便于管理员审核（如走班教学、分层辅导）" />
      </el-form-item>
    </el-form>
    <template #footer>
      <el-button @click="applyDlg = false">取消</el-button>
      <el-button type="primary" :loading="applying" @click="submitApply">提交申请</el-button>
    </template>
  </el-dialog>

  <!-- 我的建班申请抽屉（教师） -->
  <el-drawer v-model="myReqDlg" title="我的建班申请" size="420px">
    <el-table :data="myRequests" size="small" v-loading="myReqLoading">
      <el-table-column label="班级" min-width="110">
        <template #default="{ row }">{{ row.name }}<div class="tip">{{ row.grade_name }}</div></template>
      </el-table-column>
      <el-table-column label="状态" width="90" align="center">
        <template #default="{ row }">
          <el-tag size="small" :type="{ pending: 'warning', approved: 'success', rejected: 'danger' }[row.status]">
            {{ { pending: '待审核', approved: '已通过', rejected: '已拒绝' }[row.status] }}
          </el-tag>
        </template>
      </el-table-column>
      <el-table-column label="审核备注" min-width="120">
        <template #default="{ row }"><span class="tip">{{ row.review_note || '-' }}</span></template>
      </el-table-column>
      <el-table-column label="操作" width="70" align="center">
        <template #default="{ row }">
          <el-button v-if="row.status === 'pending'" link type="danger" size="small"
                     @click="withdraw(row)">撤回</el-button>
        </template>
      </el-table-column>
    </el-table>
  </el-drawer>

  <!-- 建班审核抽屉（管理员） -->
  <el-drawer v-model="reviewDlg" title="建班申请审核" size="560px">
    <el-table :data="requests" size="small" v-loading="reqLoading">
      <el-table-column label="申请人" width="100">
        <template #default="{ row }">{{ row.teacher_name }}<div class="tip">{{ row.username }}</div></template>
      </el-table-column>
      <el-table-column label="班级" min-width="110">
        <template #default="{ row }">{{ row.name }}<div class="tip">{{ row.grade_name }}</div></template>
      </el-table-column>
      <el-table-column label="说明" min-width="120">
        <template #default="{ row }"><span class="tip">{{ row.description || '-' }}</span></template>
      </el-table-column>
      <el-table-column label="操作" width="150" align="center">
        <template #default="{ row }">
          <template v-if="row.status === 'pending'">
            <el-button link type="success" size="small" @click="review(row, 'approve')">通过</el-button>
            <el-button link type="danger" size="small" @click="promptReject(row)">拒绝</el-button>
          </template>
          <el-tag v-else size="small"
                  :type="{ approved: 'success', rejected: 'danger' }[row.status]">
            {{ { approved: '已通过', rejected: '已拒绝' }[row.status] }}
          </el-tag>
        </template>
      </el-table-column>
    </el-table>
    <el-empty v-if="!reqLoading && !requests.length" description="暂无申请" :image-size="70" />
  </el-drawer>
</template>

<script setup>
const { can } = useUserStore()

// ---------- 教师建班申请（审核制） ----------
const applyDlg = ref(false)
const applying = ref(false)
const applyForm = reactive({ name: '', grade_id: null, description: '' })
const myReqDlg = ref(false)
const myRequests = ref([])
const myReqLoading = ref(false)
const myPending = computed(() => myRequests.value.filter(r => r.status === 'pending').length)

const reviewDlg = ref(false)
const requests = ref([])
const reqLoading = ref(false)
const pendingCount = ref(0)

async function submitApply() {
  if (!applyForm.name) return ElMessage.warning('请填写班级名称')
  if (!applyForm.grade_id) return ElMessage.warning('请选择年级')
  applying.value = true
  try {
    await eduApi.createClassRequest({ ...applyForm })
    ElMessage.success('申请已提交，等待管理员审核')
    applyDlg.value = false
    Object.assign(applyForm, { name: '', grade_id: null, description: '' })
    loadMyRequests()
  } finally { applying.value = false }
}

async function loadMyRequests() {
  myReqLoading.value = true
  try {
    const res = await eduApi.myClassRequests()
    myRequests.value = res.data?.items || []
  } finally { myReqLoading.value = false }
}

async function withdraw(row) {
  await ElMessageBox.confirm('撤回「' + row.name + '」的申请？', '提示', { type: 'warning' })
  await eduApi.withdrawClassRequest(row.id)
  ElMessage.success('已撤回')
  loadMyRequests()
}

async function loadRequests() {
  reqLoading.value = true
  try {
    const res = await eduApi.classRequests({})
    requests.value = res.data?.items || []
    pendingCount.value = requests.value.filter(r => r.status === 'pending').length
  } finally { reqLoading.value = false }
}

async function review(row, action) {
  let note = ''
  if (action === 'reject') {
    const { value } = await ElMessageBox.prompt('请填写拒绝理由', '拒绝申请', {
      inputValidator: v => (v && v.trim() ? true : '理由不能为空')
    })
    note = value
  }
  await eduApi.reviewClassRequest(row.id, { action, note })
  ElMessage.success(action === 'approve' ? '已通过，班级已创建' : '已拒绝')
  loadRequests()
  load()
}

import { ref, reactive, onMounted, computed } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Plus, Search, Refresh, Upload, Tickets, Bell } from '@element-plus/icons-vue'
import { useUserStore } from '@/store/user'
import { eduApi } from '@/api'

const list = ref([])
const grades = ref([])
const teachers = ref([])
const students = ref([])
const total = ref(0)
const loading = ref(false)
const saving = ref(false)
const dlg = ref(false)
const studentDrawer = ref(false)
const studentLoading = ref(false)
const importDlg = ref(false)
const importing = ref(false)
const importText = ref('')
const currentClass = ref(null)

const query = reactive({ page: 1, page_size: 50, grade_id: null, head_teacher_id: null, keyword: '' })
const form = reactive({ id: null, name: '', grade_id: null, head_teacher_id: null, description: '' })

async function load() {
  loading.value = true
  try {
    const res = await eduApi.classes(query)
    // /edu/classes 返回数组
    const d = res.data
    list.value = Array.isArray(d) ? d : (d?.items || [])
    total.value = d.total || 0
  } finally {
    loading.value = false
  }
}

function reset() {
  Object.assign(query, { page: 1, grade_id: null, head_teacher_id: null, keyword: '' })
  load()
}

function openDialog(row) {
  Object.assign(form, row || { id: null, name: '', grade_id: null, head_teacher_id: null, description: '' })
  dlg.value = true
}

async function save() {
  if (!form.name) return ElMessage.warning('请输入班级名称')
  saving.value = true
  try {
    if (form.id) await eduApi.updateClass(form.id, form)
    else await eduApi.createClass(form)
    ElMessage.success('保存成功')
    dlg.value = false
    load()
  } finally {
    saving.value = false
  }
}

async function remove(row) {
  await ElMessageBox.confirm(`确认删除班级「${row.name}」？`, '提示', { type: 'warning' })
  await eduApi.deleteClass(row.id)
  ElMessage.success('已删除')
  load()
}

async function openStudents(row) {
  currentClass.value = row
  studentDrawer.value = true
  studentLoading.value = true
  try {
    // 人员简表：教师可进本页（resource:class:list），/system/users 会 403；
    // 非任教班级由后端 DataScope 拒绝，抽屉展示空态
    const res = await eduApi.peopleBrief({ identity: 'student', class_id: row.id })
    // /edu/classes/{id}/students 也走 people/brief 返数组
    const sd = res.data
    students.value = Array.isArray(sd) ? sd : (sd?.items || [])
  } finally {
    studentLoading.value = false
  }
}

async function removeStudent(row) {
  await ElMessageBox.confirm(`确认将「${row.real_name}」移出本班？`, '提示', { type: 'warning' })
  await eduApi.removeStudent(currentClass.value.id, row.id)
  ElMessage.success('已移出')
  openStudents(currentClass.value)
}

function openImport() { importText.value = '' }

async function doImport() {
  const rows = importText.value.split('\n').map(l => l.trim()).filter(Boolean).map(line => {
    const [username, real_name, password] = line.split(/[,，\t]/).map(s => s?.trim())
    return { username, real_name, password: password || '123456', class_id: currentClass.value.id,
      grade_id: currentClass.value.grade_id, identity: 'student', role_codes: ['student'] }
  }).filter(r => r.username && r.real_name)

  if (!rows.length) return ElMessage.warning('没有解析到有效数据')

  importing.value = true
  try {
    await eduApi.importStudents(currentClass.value.id, rows)
    ElMessage.success(`成功导入 ${rows.length} 名学生`)
    importDlg.value = false
    openStudents(currentClass.value)
  } finally {
    importing.value = false
  }
}

onMounted(async () => {
  await load()
  const g = await eduApi.grades()
  grades.value = Array.isArray(g.data) ? g.data : (g.data?.data || [])
  const t = await eduApi.peopleBrief({ identity: 'teacher' })
  // people/brief?identity=teacher 返数组
    teachers.value = Array.isArray(t.data) ? t.data : (t.data?.items || [])
})
</script>

<style scoped>
.mt16 { margin-top: 16px; justify-content: flex-end; }
.mb12 { margin-bottom: 12px; }
.mt8 { margin-top: 8px; }
.filter-card :deep(.el-form-item) { margin-bottom: 12px; }
</style>
