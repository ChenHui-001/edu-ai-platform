<template>
  <div class="page-container">
    <div class="page-header">
      <h2 class="page-title">班级管理</h2>
      <div>
        <el-button :icon="Refresh" @click="load">刷新</el-button>
        <el-button v-if="can('resource:class:write')" type="primary" :icon="Plus" @click="openDialog()">新增班级</el-button>
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
</template>

<script setup>
const { can } = useUserStore()
import { ref, reactive, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Plus, Search, Refresh, Upload } from '@element-plus/icons-vue'
import { useUserStore } from '@/store/user'
import { eduApi, systemApi } from '@/api'

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
    const d = res.data.data || {}
    list.value = d.items || []
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
    const res = await systemApi.users({ class_id: row.id, page_size: 200 })
    students.value = res.data.data?.items || []
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
  grades.value = g.data.data || []
  const t = await systemApi.users({ identity: 'teacher', page_size: 200 })
  teachers.value = t.data.data?.items || []
})
</script>

<style scoped>
.mt16 { margin-top: 16px; justify-content: flex-end; }
.mb12 { margin-bottom: 12px; }
.mt8 { margin-top: 8px; }
.filter-card :deep(.el-form-item) { margin-bottom: 12px; }
</style>
