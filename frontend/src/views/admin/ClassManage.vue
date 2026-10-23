<template>
  <div class="page-container">
    <div class="page-header">
      <h2 class="page-title">班级管理</h2>
      <div class="header-actions">
        <el-button :icon="Refresh" @click="refreshAll">刷新</el-button>
        <el-button v-if="canWrite" type="primary" :icon="Plus" @click="openDialog()">新增班级</el-button>
        <template v-if="!canWrite">
          <el-button type="success" :icon="Plus" @click="applyDlg = true">申请建班</el-button>
          <el-button :icon="Tickets" @click="myReqDlg = true; loadMyRequests()">
            我的申请<el-badge v-if="myPending" :value="myPending" class="ml4" />
          </el-button>
        </template>
        <el-button v-if="canWrite" type="warning" :icon="Bell"
                   @click="reviewDlg = true; loadRequests()">
          建班审核<el-badge v-if="pendingCount" :value="pendingCount" class="ml4" />
        </el-button>
      </div>
    </div>

    <!-- 统计卡片 -->
    <el-row :gutter="14" class="stats-row">
      <el-col :xs="12" :md="6">
        <el-card shadow="never" class="stat-card">
          <div class="stat-value">{{ stats.total }}</div><div class="stat-label">班级总数</div>
        </el-card>
      </el-col>
      <el-col :xs="12" :md="6">
        <el-card shadow="never" class="stat-card">
          <div class="stat-value">{{ stats.students }}</div><div class="stat-label">学生总数</div>
        </el-card>
      </el-col>
      <el-col :xs="12" :md="6">
        <el-card shadow="never" class="stat-card">
          <div class="stat-value">{{ stats.active }}</div><div class="stat-label">启用班级</div>
        </el-card>
      </el-col>
      <el-col :xs="12" :md="6">
        <el-card shadow="never" class="stat-card">
          <div class="stat-value">{{ stats.head_teacher_coverage }}%</div>
          <div class="stat-label">班主任覆盖率</div>
        </el-card>
      </el-col>
    </el-row>

    <el-card shadow="never" class="filter-card">
      <el-form :inline="true" :model="query">
        <el-form-item label="年级">
          <el-select v-model="query.grade_id" placeholder="全部" clearable style="width:130px">
            <el-option v-for="g in grades" :key="g.id" :label="g.name" :value="g.id" />
          </el-select>
        </el-form-item>
        <el-form-item label="班主任">
          <el-select v-model="query.head_teacher_id" placeholder="全部" clearable filterable
                     style="width:150px">
            <el-option v-for="t in teachers" :key="t.id" :label="t.real_name" :value="t.id" />
          </el-select>
        </el-form-item>
        <el-form-item label="状态">
          <el-select v-model="query.status" placeholder="全部" clearable style="width:120px">
            <el-option label="启用" value="active" />
            <el-option label="停用" value="inactive" />
          </el-select>
        </el-form-item>
        <el-form-item label="关键词">
          <el-input v-model="query.keyword" placeholder="班级名称" clearable style="width:160px"
                    @keyup.enter="search" />
        </el-form-item>
        <el-form-item>
          <el-button type="primary" :icon="Search" @click="search">查询</el-button>
          <el-button :icon="Refresh" @click="reset">重置</el-button>
        </el-form-item>
      </el-form>
    </el-card>

    <el-card shadow="never">
      <div v-if="canWrite" class="batch-bar">
        <span class="muted">已选 {{ selection.length }} 个班级</span>
        <el-button size="small" :disabled="!selection.length" @click="batchAction('enable')">批量启用</el-button>
        <el-button size="small" :disabled="!selection.length" @click="batchAction('disable')">批量停用</el-button>
        <el-button size="small" type="danger" plain :disabled="!selection.length"
                   @click="batchAction('delete')">批量删除</el-button>
      </div>

      <el-table v-loading="loading" :data="list" border stripe
                @selection-change="onSelectionChange">
        <el-table-column v-if="canWrite" type="selection" width="44" />
        <el-table-column prop="name" label="班级名称" min-width="150" show-overflow-tooltip />
        <el-table-column prop="grade_name" label="所属年级" width="110" />
        <el-table-column label="班主任" width="110">
          <template #default="{ row }">{{ row.head_teacher_name || '-' }}</template>
        </el-table-column>
        <el-table-column label="学生数" width="90" align="center">
          <template #default="{ row }">
            <el-button link type="primary" @click="openStudents(row)">{{ row.student_count }}</el-button>
          </template>
        </el-table-column>
        <el-table-column label="状态" width="80" align="center">
          <template #default="{ row }">
            <el-tag size="small" :type="row.is_active ? 'success' : 'info'">
              {{ row.is_active ? '启用' : '停用' }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="remark" label="说明" min-width="150" show-overflow-tooltip />
        <el-table-column label="创建时间" width="150">
          <template #default="{ row }">{{ formatLocalDate(row.created_at) }}</template>
        </el-table-column>
        <el-table-column label="操作" width="230" fixed="right">
          <template #default="{ row }">
            <el-button link type="primary" @click="openStudents(row)">学生</el-button>
            <template v-if="canWrite">
              <el-button link type="primary" @click="openDialog(row)">编辑</el-button>
              <el-button link :type="row.is_active ? 'warning' : 'success'"
                         @click="toggleActive(row)">{{ row.is_active ? '停用' : '启用' }}</el-button>
              <el-button link type="danger" @click="remove(row)">删除</el-button>
            </template>
          </template>
        </el-table-column>
      </el-table>

      <el-pagination class="mt16" background layout="total, sizes, prev, pager, next"
                     :total="total" :page-sizes="[10, 20, 50, 100]"
                     v-model:current-page="query.page" v-model:page-size="query.page_size"
                     @current-change="load" @size-change="onPageSizeChange" />
    </el-card>

    <!-- 新增/编辑班级 -->
    <el-dialog v-model="dlg" :title="form.id ? '编辑班级' : '新增班级'" width="540px">
      <el-form :model="form" label-width="100px">
        <el-form-item label="所属年级" required>
          <el-select v-model="form.grade_id" style="width:100%" @change="onClassGradeChange">
            <el-option v-for="g in grades" :key="g.id" :label="g.name" :value="g.id" />
          </el-select>
          <div v-if="form.id" class="tip">修改年级会同步迁移班内学生的年级</div>
        </el-form-item>
        <el-form-item label="班级名称" required>
          <div class="class-name-row">
            <el-input v-if="form.custom_name" v-model="form.name" maxlength="32" show-word-limit
                      placeholder="如：七年级(3)班 / 数学兴趣班" />
            <el-input v-else :model-value="autoClassName" disabled />
            <el-switch v-model="form.custom_name" active-text="自定义名称"
                       @change="onCustomNameChange" />
          </div>
          <div v-if="!form.custom_name" class="tip">
            名称按「年级 + 班级序号」自动生成，避免手输格式不一致
          </div>
          <div v-else class="tip">
            仅支持中文、字母、数字、括号、间隔号、短横线，长度 2-32
          </div>
        </el-form-item>
        <el-form-item v-if="!form.custom_name" label="班级序号" required>
          <el-input-number v-model="form.class_no" :min="1" :max="99" style="width:100%" />
        </el-form-item>
        <el-form-item label="班主任">
          <el-select v-model="form.head_teacher_id" clearable filterable style="width:100%">
            <el-option v-for="t in teachers" :key="t.id" :label="t.real_name" :value="t.id" />
          </el-select>
        </el-form-item>
        <el-form-item label="状态">
          <el-switch v-model="form.is_active" active-text="启用" inactive-text="停用" />
        </el-form-item>
        <el-form-item label="说明">
          <el-input v-model="form.remark" type="textarea" :rows="2" maxlength="255" show-word-limit />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="dlg = false">取消</el-button>
        <el-button type="primary" :loading="saving" @click="save">保存</el-button>
      </template>
    </el-dialog>

    <!-- 学生管理 -->
    <el-drawer v-model="studentDrawer" :title="`${currentClass?.name || ''} - 学生管理`" size="72%">
      <div class="student-toolbar">
        <div class="student-tools">
          <el-input v-model="studentQuery.keyword" placeholder="搜索学号/姓名" clearable
                    style="width:200px" @keyup.enter="loadStudents" @clear="loadStudents" />
          <el-button :icon="Search" @click="loadStudents">查询</el-button>
          <el-button v-if="canWrite" type="primary" :icon="Upload"
                     @click="openImport">批量导入</el-button>
          <el-button :icon="Download" @click="exportStudents">导出名单</el-button>
          <el-button v-if="canWrite" type="danger" plain :disabled="!studentSelection.length"
                     @click="batchRemoveStudents">移出选中（{{ studentSelection.length }}）</el-button>
        </div>
        <span class="muted">共 {{ studentTotal }} 名学生 · {{ currentClass?.grade_name || '' }}</span>
      </div>

      <el-table v-loading="studentLoading" :data="students" border stripe
                @selection-change="onStudentSelection">
        <el-table-column v-if="canWrite" type="selection" width="44" />
        <el-table-column prop="username" label="学号" width="140" />
        <el-table-column prop="real_name" label="姓名" width="120" />
        <el-table-column prop="phone" label="手机号" width="140" />
        <el-table-column prop="email" label="邮箱" min-width="180" show-overflow-tooltip />
        <el-table-column label="状态" width="90" align="center">
          <template #default="{ row }">
            <el-tag size="small" :type="row.status === 'active' ? 'success' : 'info'">
              {{ row.status === 'active' ? '正常' : row.status }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column label="操作" width="100" align="center">
          <template #default="{ row }">
            <el-button v-if="canWrite" link type="danger" @click="removeStudent(row)">移出</el-button>
          </template>
        </el-table-column>
      </el-table>
      <el-pagination class="mt16" background layout="total, prev, pager, next"
                     :total="studentTotal" v-model:current-page="studentQuery.page"
                     @current-change="loadStudents" />
      <el-empty v-if="!studentLoading && !students.length" description="该班级暂无学生"
                :image-size="60" />
    </el-drawer>

    <el-dialog v-model="importDlg" title="批量导入学生" width="580px">
      <el-form label-width="90px">
        <el-form-item label="导入数据">
          <el-input v-model="importText" type="textarea" :rows="10"
                    placeholder="每行一个学生：学号,姓名,初始密码（可留空）&#10;2026001,张三,Student@123" />
        </el-form-item>
      </el-form>
      <div class="muted">
        导入规则：学号必填且不可重复；初始密码留空默认 Student@123；导入后首次登录需改密。
        <el-button link type="primary" @click="downloadTemplate">下载 CSV 模板</el-button>
      </div>
      <template #footer>
        <el-button @click="importDlg = false">取消</el-button>
        <el-button type="primary" :loading="importing" @click="doImport">导入</el-button>
      </template>
    </el-dialog>

    <!-- 教师建班申请 -->
    <el-dialog v-model="applyDlg" title="申请建班（提交后由管理员审核）" width="460px">
      <el-form :model="applyForm" label-width="80px">
        <el-form-item label="班级名称" required>
          <el-input v-model="applyForm.name" placeholder="如：七年级(3)班" maxlength="32" />
        </el-form-item>
        <el-form-item label="所属年级" required>
          <el-select v-model="applyForm.grade_id" style="width:100%" placeholder="选择年级">
            <el-option v-for="g in grades" :key="g.id" :label="g.name" :value="g.id" />
          </el-select>
        </el-form-item>
        <el-form-item label="申请说明">
          <el-input v-model="applyForm.description" type="textarea" :rows="2"
                    placeholder="建班用途，便于管理员审核" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="applyDlg = false">取消</el-button>
        <el-button type="primary" :loading="applying" @click="submitApply">提交申请</el-button>
      </template>
    </el-dialog>

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
  </div>
</template>

<script setup>
import { computed, onMounted, reactive, ref } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import {
  Bell, Download, Plus, Refresh, Search, Tickets, Upload,
} from '@element-plus/icons-vue'
import { useUserStore } from '@/store/user'
import { eduApi } from '@/api'
import { downloadBlob } from '@/utils/download'
import { formatLocalDate } from '@/utils/date'

const { can } = useUserStore()
const canWrite = computed(() => can('resource:class:write'))

const list = ref([])
const grades = ref([])
const teachers = ref([])
const total = ref(0)
const loading = ref(false)
const stats = ref({ total: 0, students: 0, active: 0, inactive: 0, head_teacher_coverage: 0 })
const selection = ref([])

const query = reactive({
  page: 1, page_size: 20, grade_id: null, head_teacher_id: null, status: null, keyword: '',
})

const dlg = ref(false)
const saving = ref(false)
const form = reactive({
  id: null, name: '', grade_id: null, head_teacher_id: null, is_active: true, remark: '',
  class_no: 1, custom_name: false,
})

// 学生抽屉
const studentDrawer = ref(false)
const currentClass = ref(null)
const students = ref([])
const studentTotal = ref(0)
const studentLoading = ref(false)
const studentSelection = ref([])
const studentQuery = reactive({ page: 1, page_size: 20, keyword: '' })

// 导入
const importDlg = ref(false)
const importing = ref(false)
const importText = ref('')

// 教师建班申请/审核
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

async function loadStats() {
  const res = await eduApi.classStats({ grade_id: query.grade_id || undefined })
  stats.value = res.data || stats.value
}

async function load() {
  loading.value = true
  try {
    const res = await eduApi.classes(query)
    const d = res.data
    if (Array.isArray(d)) {
      list.value = d
      total.value = d.length
    } else {
      list.value = d?.items || []
      total.value = d?.total || 0
    }
  } finally {
    loading.value = false
  }
  loadStats()
}

async function refreshAll() {
  await Promise.all([load(), loadOptions()])
}

function search() {
  query.page = 1
  load()
}

function reset() {
  Object.assign(query, {
    page: 1, page_size: 20, grade_id: null, head_teacher_id: null, status: null, keyword: '',
  })
  load()
}

function onPageSizeChange() {
  query.page = 1
  load()
}

function onSelectionChange(val) {
  selection.value = val || []
}

function gradeNameOf(gid) {
  return grades.value.find(g => g.id === gid)?.name || ''
}

const autoClassName = computed(() => {
  const g = gradeNameOf(form.grade_id)
  return g ? `${g}(${form.class_no || 1})班` : ''
})

function nextClassNo(gradeId) {
  const nos = list.value
    .filter(c => c.grade_id === gradeId)
    .map(c => c.class_no || 0)
    .filter(n => n > 0)
  return (nos.length ? Math.max(...nos) : 0) + 1
}

function onClassGradeChange(gid) {
  if (!form.custom_name) form.class_no = nextClassNo(gid)
}

function onCustomNameChange(val) {
  if (!val) {
    form.class_no = nextClassNo(form.grade_id)
  } else if (!form.name) {
    form.name = autoClassName.value
  }
}

function openDialog(row) {
  if (row) {
    const classNo = row.class_no || 0
    Object.assign(form, {
      id: row.id,
      name: row.name,
      grade_id: row.grade_id,
      head_teacher_id: row.head_teacher_id || null,
      is_active: row.is_active !== false,
      remark: row.remark || '',
      class_no: classNo || 1,
      custom_name: !classNo,
    })
  } else {
    const gid = query.grade_id || grades.value[0]?.id || null
    Object.assign(form, {
      id: null, name: '', grade_id: gid, head_teacher_id: null,
      is_active: true, remark: '', class_no: nextClassNo(gid), custom_name: false,
    })
  }
  dlg.value = true
}

async function save() {
  if (!form.grade_id) return ElMessage.warning('请选择年级')
  if (form.custom_name) {
    const name = (form.name || '').trim()
    if (!name) return ElMessage.warning('请输入班级名称')
    if (!/^[\u4e00-\u9fa5A-Za-z0-9()（）·\-_\s]{2,32}$/.test(name)) {
      return ElMessage.warning('名称仅支持中文、字母、数字、括号、间隔号、短横线，长度 2-32')
    }
    form.name = name
  } else if (!form.class_no) {
    return ElMessage.warning('请填写班级序号')
  }
  saving.value = true
  try {
    const payload = {
      grade_id: form.grade_id,
      head_teacher_id: form.head_teacher_id || null,
      is_active: form.is_active,
      remark: form.remark,
      auto_name: !form.custom_name,
      strict_name: form.custom_name,
      class_no: form.class_no,
      name: form.custom_name ? form.name : autoClassName.value,
    }
    if (form.id) await eduApi.updateClass(form.id, payload)
    else await eduApi.createClass(payload)
    ElMessage.success('保存成功')
    dlg.value = false
    await load()
  } finally {
    saving.value = false
  }
}

async function remove(row) {
  await ElMessageBox.confirm(
    `确认删除班级「${row.name}」？有学生的班级不能删除。`, '删除确认', { type: 'warning' })
  await eduApi.deleteClass(row.id)
  ElMessage.success('已删除')
  await load()
}

async function toggleActive(row) {
  await eduApi.updateClass(row.id, { is_active: !row.is_active })
  ElMessage.success(row.is_active ? '班级已停用' : '班级已启用')
  await load()
}

async function batchAction(action) {
  const labels = { enable: '启用', disable: '停用', delete: '删除' }
  await ElMessageBox.confirm(
    `确认批量${labels[action]}选中的 ${selection.value.length} 个班级？`,
    '批量操作', { type: action === 'delete' ? 'warning' : 'info' })
  const res = await eduApi.batchClasses({
    action, ids: selection.value.map(x => x.id),
  })
  const d = res.data || {}
  ElMessage.success(`完成 ${(d.done || []).length} 个，跳过 ${(d.skipped || []).length} 个`)
  await load()
}

async function loadOptions() {
  const g = await eduApi.grades()
  grades.value = Array.isArray(g.data) ? g.data : (g.data?.data || [])
  const t = await eduApi.peopleBrief({ identity: 'teacher' })
  teachers.value = Array.isArray(t.data) ? t.data : (t.data?.items || [])
}

async function openStudents(row) {
  currentClass.value = row
  studentDrawer.value = true
  studentQuery.page = 1
  studentQuery.keyword = ''
  await loadStudents()
}

async function loadStudents() {
  if (!currentClass.value) return
  studentLoading.value = true
  try {
    const res = await eduApi.classStudents(currentClass.value.id, studentQuery)
    const d = res.data || {}
    students.value = d.items || []
    studentTotal.value = d.total || 0
  } finally {
    studentLoading.value = false
  }
}

function onStudentSelection(val) {
  studentSelection.value = val || []
}

async function removeStudent(row) {
  await ElMessageBox.confirm(`确认将「${row.real_name}」移出本班？`, '提示', { type: 'warning' })
  await eduApi.removeStudent(currentClass.value.id, row.id)
  ElMessage.success('已移出')
  await loadStudents()
  await load()
}

async function batchRemoveStudents() {
  await ElMessageBox.confirm(
    `确认将选中的 ${studentSelection.value.length} 名学生移出本班？`, '提示', { type: 'warning' })
  await eduApi.batchRemoveStudents(currentClass.value.id, {
    ids: studentSelection.value.map(x => x.id),
  })
  ElMessage.success('已移出')
  await loadStudents()
  await load()
}

async function exportStudents() {
  if (!currentClass.value) return
  await downloadBlob(eduApi.exportClassStudents(currentClass.value.id),
    `${currentClass.value.name}-学生名单.csv`)
}

function openImport() {
  importText.value = ''
  importDlg.value = true
}

function downloadTemplate() {
  const blob = new Blob([`\ufeff学号,姓名,初始密码\n2026001,张三,Student@123\n`],
    { type: 'text/csv;charset=utf-8' })
  downloadBlob(Promise.resolve({ data: blob }), '学生导入模板.csv')
}

async function doImport() {
  const rows = importText.value.split('\n').map(l => l.trim()).filter(Boolean).map(line => {
    const [username, real_name, password] = line.split(/[,，\t]/).map(s => s?.trim())
    return { username, real_name, password: password || 'Student@123' }
  }).filter(r => r.username && r.real_name)
  if (!rows.length) return ElMessage.warning('没有解析到有效数据')
  importing.value = true
  try {
    const res = await eduApi.importStudents(currentClass.value.id, rows)
    const d = res.data || {}
    const skipped = d.skipped || []
    if (skipped.length) {
      ElMessage.warning(`成功 ${d.created || 0} 名，跳过 ${skipped.length} 名：` +
        skipped.map(s => `${s.username}(${s.reason})`).join('；'))
    } else {
      ElMessage.success(`成功导入 ${d.created || 0} 名学生`)
    }
    importDlg.value = false
    await loadStudents()
    await load()
  } finally {
    importing.value = false
  }
}

// ---------- 教师建班申请（审核制） ----------
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
  } finally {
    applying.value = false
  }
}

async function loadMyRequests() {
  myReqLoading.value = true
  try {
    const res = await eduApi.myClassRequests()
    myRequests.value = res.data?.items || []
  } finally {
    myReqLoading.value = false
  }
}

async function withdraw(row) {
  await ElMessageBox.confirm(`撤回「${row.name}」的申请？`, '提示', { type: 'warning' })
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
  } finally {
    reqLoading.value = false
  }
}

async function review(row, action) {
  let note = ''
  if (action === 'reject') {
    const { value } = await ElMessageBox.prompt('请填写拒绝理由', '拒绝申请', {
      inputValidator: v => (v && v.trim() ? true : '理由不能为空'),
    })
    note = value
  }
  await eduApi.reviewClassRequest(row.id, { action, note })
  ElMessage.success(action === 'approve' ? '已通过，班级已创建' : '已拒绝')
  loadRequests()
  load()
}

async function promptReject(row) {
  return review(row, 'reject')
}

onMounted(async () => {
  await Promise.all([load(), loadOptions()])
})
</script>

<style scoped>
.header-actions { display: flex; flex-wrap: wrap; gap: 8px; }
.stats-row { margin-bottom: 14px; }
.stat-card { border-radius: 10px; }
.stat-value { font-size: 24px; font-weight: 600; color: #1f2d3d; line-height: 1.3; }
.stat-label { color: #8a94a6; font-size: 13px; margin-top: 2px; }
.filter-card :deep(.el-form-item) { margin-bottom: 10px; }
.mt16 { margin-top: 16px; justify-content: flex-end; }
.ml4 { margin-left: 4px; }
.mb12 { margin-bottom: 12px; }
.tip { color: #8a94a6; font-size: 12px; }
.muted { color: #8a94a6; font-size: 13px; }
.batch-bar {
  display: flex; align-items: center; gap: 8px;
  padding: 10px 12px; margin-bottom: 10px;
  background: #f5f8ff; border: 1px solid #dbe7ff; border-radius: 8px;
}
.student-toolbar {
  display: flex; justify-content: space-between; align-items: center;
  gap: 12px; margin-bottom: 12px; flex-wrap: wrap;
}
.student-tools { display: flex; align-items: center; gap: 8px; flex-wrap: wrap; }
.class-name-row { display: flex; align-items: center; gap: 12px; width: 100%; }
.class-name-row .el-input { flex: 1; }
.class-name-row .el-switch { flex-shrink: 0; }
@media (max-width: 768px) {
  .header-actions { width: 100%; }
  .student-toolbar { align-items: flex-start; }
}
</style>
