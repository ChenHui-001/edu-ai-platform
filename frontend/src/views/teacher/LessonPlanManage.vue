<template>
  <div class="page-container">
    <div class="page-header">
      <h2 class="page-title">教案管理</h2>
      <div>
        <el-button :icon="Refresh" @click="load">刷新</el-button>
        <el-button :icon="CopyDocument" @click="onlyMine = !onlyMine; load()">
          {{ onlyMine ? '看共享' : '只看我的' }}
        </el-button>
        <el-button v-if="can('lesson:plan:write')" type="primary" :icon="Plus"
                   @click="openDialog()">新建教案</el-button>
      </div>
    </div>

    <!-- 筛选 -->
    <el-card shadow="never" class="filter-card">
      <el-form :inline="true" :model="query">
        <el-form-item label="学科">
          <el-select v-model="query.subject_id" placeholder="全部" clearable style="width:160px">
            <el-option v-for="s in subjects" :key="s.id" :label="s.name" :value="s.id" />
          </el-select>
        </el-form-item>
        <el-form-item label="年级">
          <el-select v-model="query.grade_id" placeholder="全部" clearable style="width:130px">
            <el-option v-for="g in grades" :key="g.id" :label="g.name" :value="g.id" />
          </el-select>
        </el-form-item>
        <el-form-item label="关键词">
          <el-input v-model="query.keyword" placeholder="标题/课题" clearable
                    style="width:200px" @keyup.enter="load" />
        </el-form-item>
        <el-form-item>
          <el-button type="primary" :icon="Search" @click="load">查询</el-button>
          <el-button :icon="RefreshLeft" @click="reset">重置</el-button>
        </el-form-item>
      </el-form>
    </el-card>

    <!-- 列表 -->
    <el-card shadow="never">
      <el-table v-loading="loading" :data="list" border stripe>
        <el-table-column prop="title" label="教案标题" min-width="220" show-overflow-tooltip />
        <el-table-column prop="topic" label="课题" min-width="160" show-overflow-tooltip />
        <el-table-column label="学科/年级" width="160">
          <template #default="{ row }">
            <el-tag size="small" class="mr4">{{ row.subject_name || '-' }}</el-tag>
            <el-tag size="small" type="info">{{ row.grade_name || '-' }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column label="课时" width="80" align="center">
          <template #default="{ row }">
            {{ row.duration_minutes || 45 }} 分钟
          </template>
        </el-table-column>
        <el-table-column prop="period" label="第几课时" width="100" show-overflow-tooltip />
        <el-table-column label="使用次数" width="90" align="center" prop="use_count" />
        <el-table-column label="共享" width="80" align="center">
          <template #default="{ row }">
            <el-tag v-if="row.is_shared" type="success" size="small">已共享</el-tag>
            <el-tag v-else type="info" size="small">私有</el-tag>
          </template>
        </el-table-column>
        <el-table-column label="更新时间" width="160" prop="updated_at" />
        <el-table-column label="操作" width="240" fixed="right">
          <template #default="{ row }">
            <el-button link type="primary" @click="openDialog(row)">查看/编辑</el-button>
            <el-button link type="primary" v-if="can('lesson:plan:copy')"
                       @click="copyPlan(row)">复制</el-button>
            <el-button link type="warning" v-if="can('lesson:plan:share') && row.creator_id === meId"
                       @click="toggleShare(row)">
              {{ row.is_shared ? '取消共享' : '共享' }}
            </el-button>
            <el-button link type="danger" v-if="can('lesson:plan:write') && row.creator_id === meId"
                       @click="remove(row)">删除</el-button>
          </template>
        </el-table-column>
      </el-table>
      <el-pagination class="mt16" background layout="total, prev, pager, next, jumper"
                     :total="total" v-model:current-page="query.page"
                     :page-size="query.page_size" @current-change="load" />
    </el-card>

    <!-- 编辑/新建 弹窗 -->
    <el-dialog v-model="dialogVisible" :title="form.id ? '编辑教案' : '新建教案'" width="920px"
               destroy-on-close>
      <el-form :model="form" :rules="rules" ref="formRef" label-width="100px">
        <el-row :gutter="10">
          <el-col :span="12">
            <el-form-item label="标题" prop="title">
              <el-input v-model="form.title" placeholder="如：解一元一次方程——移项" />
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="课题" prop="topic">
              <el-input v-model="form.topic" placeholder="如：解一元一次方程" />
            </el-form-item>
          </el-col>
        </el-row>
        <el-row :gutter="10">
          <el-col :span="8">
            <el-form-item label="学科" prop="subject_id">
              <el-select v-model="form.subject_id" style="width:100%" @change="onFormSubjectChange">
                <el-option v-for="s in subjects" :key="s.id" :label="s.name" :value="s.id" />
              </el-select>
            </el-form-item>
          </el-col>
          <el-col :span="8">
            <el-form-item label="年级" prop="grade_id">
              <el-select v-model="form.grade_id" style="width:100%" @change="onFormGradeChange">
                <el-option v-for="g in grades" :key="g.id" :label="g.name" :value="g.id" />
              </el-select>
            </el-form-item>
          </el-col>
          <el-col :span="4">
            <el-form-item label="课时（分）">
              <el-input-number v-model="form.duration_minutes" :min="5" :max="180" :step="5" style="width:100%" />
            </el-form-item>
          </el-col>
          <el-col :span="4">
            <el-form-item label="第几课时">
              <el-input v-model="form.period" placeholder="如：第 1 课时" />
            </el-form-item>
          </el-col>
        </el-row>
        <el-form-item label="关联知识点">
          <el-select v-model="form.knowledge_point_id" clearable filterable
                     style="width:100%" :disabled="!formKnowledge.length">
            <el-option v-for="k in formKnowledge" :key="k.id" :label="k.name" :value="k.id" />
          </el-select>
        </el-form-item>
        <el-row :gutter="10">
          <el-col :span="12">
            <el-form-item label="教学目标">
              <el-input v-model="form.objectives" type="textarea" :rows="4"
                        placeholder="知识与技能 / 过程与方法 / 情感态度价值观" />
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="教学重点">
              <el-input v-model="form.key_points" type="textarea" :rows="4" />
            </el-form-item>
          </el-col>
        </el-row>
        <el-row :gutter="10">
          <el-col :span="12">
            <el-form-item label="教学难点">
              <el-input v-model="form.difficulties" type="textarea" :rows="4" />
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="板书设计">
              <el-input v-model="form.board_design" type="textarea" :rows="4" />
            </el-form-item>
          </el-col>
        </el-row>
        <el-divider content-position="left">教学过程</el-divider>
        <div v-for="(stage, i) in form.stages" :key="i" class="stage-row">
          <el-input v-model="stage.name" placeholder="阶段名（导入/新授/练习/小结/作业）"
                    style="width:200px" class="mr8" />
          <el-input-number v-model="stage.duration_minutes" :min="1" :max="60" :step="1"
                           style="width:100px" class="mr8" />
          <el-input v-model="stage.content" type="textarea" :rows="2"
                    placeholder="教师活动 / 学生活动" />
          <el-button :icon="Delete" link type="danger" @click="form.stages.splice(i, 1)" />
        </div>
        <el-button :icon="Plus" plain size="small" @click="addStage" class="mt8">添加阶段</el-button>

        <el-form-item label="作业布置" class="mt12">
          <el-input v-model="form.homework" type="textarea" :rows="2" />
        </el-form-item>
        <el-form-item label="教学反思">
          <el-input v-model="form.reflection" type="textarea" :rows="2" placeholder="课后可填写" />
        </el-form-item>
        <el-form-item label="共享给同科">
          <el-switch v-model="form.is_shared" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="dialogVisible = false">关闭</el-button>
        <el-button type="primary" :loading="saving" @click="save">保存教案</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import {
  Plus, Refresh, RefreshLeft, Search, Delete, CopyDocument
} from '@element-plus/icons-vue'
import { lessonApi, eduApi } from '@/api'
import { useUserStore } from '@/store/user'

const { can } = useUserStore()
const meId = (window.localStorage.getItem('user') &&
  JSON.parse(window.localStorage.getItem('user')) || {}).id

const list = ref([])
const total = ref(0)
const loading = ref(false)
const onlyMine = ref(false)
const subjects = ref([])
const grades = ref([])
const formKnowledge = ref([])

const query = reactive({ page: 1, page_size: 20, subject_id: null,
  grade_id: null, keyword: '' })

async function load() {
  loading.value = true
  try {
    const params = Object.fromEntries(
      Object.entries({ ...query, only_mine: onlyMine.value })
        .filter(([, v]) => v !== null && v !== ''))
    const res = await lessonApi.list(params)
    list.value = res.data?.items || []
    total.value = res.data?.total || 0
  } finally { loading.value = false }
}

function reset() {
  Object.assign(query, { page: 1, subject_id: null, grade_id: null, keyword: '' })
  load()
}

const dialogVisible = ref(false)
const saving = ref(false)
const formRef = ref()
const form = reactive({
  id: null, title: '', topic: '', subject_id: null, grade_id: null,
  knowledge_point_id: null, duration_minutes: 45, period: '',
  objectives: '', key_points: '', difficulties: '',
  board_design: '', homework: '', reflection: '',
  is_shared: false, stages: []
})

const rules = {
  title: [{ required: true, message: '请输入标题', trigger: 'blur' }],
  topic: [{ required: true, message: '请输入课题', trigger: 'blur' }],
  subject_id: [{ required: true, message: '请选择学科', trigger: 'change' }],
  grade_id: [{ required: true, message: '请选择年级', trigger: 'change' }]
}

function addStage() {
  form.stages.push({ name: '', duration_minutes: 5, content: '' })
}

async function openDialog(row) {
  form.id = row?.id ?? null
  if (form.id) {
    const r = await lessonApi.detail(form.id)
    const d = r.data || {}
    Object.assign(form, {
      title: d.title, topic: d.topic,
      subject_id: d.subject_id, grade_id: d.grade_id,
      knowledge_point_id: d.knowledge_point_id,
      duration_minutes: d.duration_minutes || 45,
      period: d.period || '',
      objectives: d.objectives || '',
      key_points: d.key_points || '',
      difficulties: d.difficulties || '',
      board_design: d.board_design || '',
      homework: d.homework || '',
      reflection: d.reflection || '',
      is_shared: !!d.is_shared,
      stages: (d.stages || []).map(s => ({ ...s }))
    })
    if (form.subject_id && form.grade_id) {
      await loadFormKnowledge(form.grade_id, form.subject_id)
    }
  } else {
    Object.assign(form, {
      id: null, title: '', topic: '', subject_id: query.subject_id,
      grade_id: query.grade_id, knowledge_point_id: null,
      duration_minutes: 45, period: '',
      objectives: '', key_points: '', difficulties: '',
      board_design: '', homework: '', reflection: '',
      is_shared: false, stages: []
    })
    form.stages.push({ name: '导入', duration_minutes: 3, content: '' })
    form.stages.push({ name: '新课讲授', duration_minutes: 25, content: '' })
    form.stages.push({ name: '课堂练习', duration_minutes: 10, content: '' })
    form.stages.push({ name: '课堂小结', duration_minutes: 5, content: '' })
    form.stages.push({ name: '布置作业', duration_minutes: 2, content: '' })
  }
  dialogVisible.value = true
}

async function onFormSubjectChange() {
  form.knowledge_point_id = null
  if (form.subject_id && form.grade_id) await loadFormKnowledge(form.grade_id, form.subject_id)
}
async function onFormGradeChange() {
  form.knowledge_point_id = null
  if (form.subject_id && form.grade_id) await loadFormKnowledge(form.grade_id, form.subject_id)
}
async function loadFormKnowledge(gid, sid) {
  if (!gid || !sid) { formKnowledge.value = []; return }
  const r = await eduApi.knowledgeList({ grade_id: gid, subject_id: sid, params_limit: 200 })
  formKnowledge.value = r.data || []
}

async function save() {
  await formRef.value.validate()
  saving.value = true
  try {
    const payload = {
      ...form,
      is_shared: form.is_shared ? 1 : 0,
      stages: form.stages
        .filter(s => s.name)
        .map((s, i) => ({ ...s, sort_order: i }))
    }
    if (form.id) await lessonApi.update(form.id, payload)
    else await lessonApi.create(payload)
    ElMessage.success('保存成功')
    dialogVisible.value = false
    load()
  } finally { saving.value = false }
}

async function copyPlan(row) {
  const res = await lessonApi.copy(row.id, {})
  ElMessage.success(`已复制：${(res.data || {}).title || '教案'}`)
  load()
}

async function toggleShare(row) {
  const next = !row.is_shared
  await lessonApi.share(row.id, { is_shared: next })
  ElMessage.success(next ? '已共享给同科教师' : '已取消共享')
  load()
}

async function remove(row) {
  await ElMessageBox.confirm(`确定删除教案「${row.title}」吗？此操作不可恢复。`,
    '提示', { type: 'warning' })
  await lessonApi.remove(row.id)
  ElMessage.success('已删除')
  load()
}

onMounted(async () => {
  const [g, s] = await Promise.all([
    eduApi.grades(),
    eduApi.subjects({ distinct: true })
  ])
  grades.value = g.data || []
  subjects.value = s.data || []
  load()
})
</script>

<style scoped>
.filter-card { margin-bottom: 12px; }
.stage-row { display: flex; align-items: center; gap: 8px; margin-bottom: 8px; }
</style>