<template>
  <div class="page-container">
    <div class="page-header tm-header">
      <div class="tm-title-wrap">
        <h2 class="page-title">作业与考试</h2>
        <div class="tm-stats" v-loading="statsLoading">
          <div v-for="c in statCards" :key="c.label" class="stat-card tm-stat">
            <div class="stat-value">{{ c.value }}</div>
            <div class="stat-label">{{ c.label }}</div>
          </div>
        </div>
      </div>
      <div class="tm-actions">
        <el-button :icon="Refresh" :loading="loading" @click="refreshAll">刷新</el-button>
        <el-button v-if="can('task:write')" type="primary" :icon="Plus" @click="openDialog()">
          发布作业 / 考试
        </el-button>
      </div>
    </div>

    <el-card shadow="never" class="filter-card">
      <el-form :inline="true" :model="query">
        <el-form-item label="类型">
          <el-select v-model="query.task_type" placeholder="全部" clearable style="width:120px">
            <el-option label="作业" value="homework" />
            <el-option label="考试" value="exam" />
          </el-select>
        </el-form-item>
        <el-form-item label="状态">
          <el-select v-model="query.status" placeholder="全部" clearable style="width:120px">
            <el-option label="已发布" value="published" />
            <el-option label="进行中" value="ongoing" />
            <el-option label="已结束" value="finished" />
            <el-option label="草稿" value="draft" />
          </el-select>
        </el-form-item>
        <el-form-item label="学科">
          <el-select v-model="query.subject_id" placeholder="全部" clearable style="width:190px">
            <el-option v-for="s in subjects" :key="s.id"
                       :label="`${subjectGradeName(s.grade_id)} ${s.name}`" :value="s.id" />
          </el-select>
        </el-form-item>
        <el-form-item label="班级">
          <el-select v-model="query.class_id" placeholder="全部" clearable style="width:180px">
            <el-option v-for="c in classes" :key="c.id"
                       :label="`${c.grade_name || ''} ${c.name}`" :value="c.id" />
          </el-select>
        </el-form-item>
        <el-form-item label="关键词">
          <el-input v-model="query.keyword" placeholder="任务标题" clearable style="width:170px"
                    @keyup.enter="search" />
        </el-form-item>
        <el-form-item>
          <el-button type="primary" :icon="Search" @click="search">查询</el-button>
          <el-button :icon="Refresh" @click="reset">重置</el-button>
        </el-form-item>
      </el-form>
    </el-card>

    <el-card shadow="never">
      <div v-if="can('task:write')" class="batch-bar">
        <span class="muted">已选 {{ selection.length }} 个任务</span>
        <el-button size="small" :disabled="!selection.length" :loading="batchLoading"
                   @click="batchAction('close')">批量结束</el-button>
        <el-button size="small" type="danger" plain :disabled="!selection.length"
                   :loading="batchLoading" @click="batchAction('delete')">批量删除</el-button>
      </div>

      <el-table v-loading="loading" :data="list" border stripe
                @selection-change="onSelectionChange">
        <el-table-column type="selection" width="44" />
        <el-table-column prop="title" label="任务标题" min-width="200" show-overflow-tooltip />
        <el-table-column label="类型" width="90">
          <template #default="{ row }">
            <el-tag :type="row.type === 'exam' ? 'danger' : 'primary'" size="small">
              {{ row.type_label }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="subject_name" label="学科" width="90" />
        <el-table-column label="班级" width="170" show-overflow-tooltip>
          <template #default="{ row }">
            {{ Array.isArray(row.class_names) ? row.class_names.join('、') : (row.class_names || '-') }}
          </template>
        </el-table-column>
        <el-table-column label="提交进度" width="190">
          <template #default="{ row }">
            <el-progress :percentage="Math.min(row.completion_rate || 0, 100)"
                         :status="(row.completion_rate || 0) >= 60 ? 'success' : ''" />
            <span class="tip">{{ row.submission_count }}/{{ row.assigned_count || row.assignment_count }} 人已交</span>
          </template>
        </el-table-column>
        <el-table-column prop="start_at" label="开始时间" width="160" />
        <el-table-column prop="end_at" label="截止时间" width="160" />
        <el-table-column label="状态" width="100">
          <template #default="{ row }">
            <el-tag :type="statusTag(row)" size="small">{{ statusLabel(row) }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column label="操作" width="230" fixed="right">
          <template #default="{ row }">
            <el-button link type="primary" @click="openSubs(row)">提交情况</el-button>
            <el-button link type="success" @click="openReport(row)">学情报告</el-button>
            <el-button v-if="canEditTask(row)" link type="primary" @click="openDialog(row)">编辑</el-button>
            <el-button v-if="canEditTask(row)" link type="danger" @click="remove(row)">删除</el-button>
          </template>
        </el-table-column>
        <template #empty>
          <el-empty description="暂无任务，点击右上角发布作业 / 考试" :image-size="70" />
        </template>
      </el-table>

      <el-pagination class="mt16" background layout="total, sizes, prev, pager, next, jumper"
                     :total="total" v-model:current-page="query.page"
                     v-model:page-size="query.page_size" :page-sizes="[20, 50, 100]"
                     @current-change="load" @size-change="search" />
    </el-card>

    <!-- 发布 / 编辑 -->
    <el-dialog v-model="dlg" :title="form.id ? '编辑任务' : '发布作业 / 考试'" width="680px">
      <el-form :model="form" label-width="100px">
        <el-form-item label="任务标题">
          <el-input v-model="form.title" placeholder="如：七年级数学第三章练习" />
        </el-form-item>
        <el-row :gutter="12">
          <el-col :span="12">
            <el-form-item label="类型">
              <el-radio-group v-model="form.type">
                <el-radio-button value="homework">作业</el-radio-button>
                <el-radio-button value="exam">考试</el-radio-button>
              </el-radio-group>
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="试卷">
              <el-select v-model="form.paper_id" filterable placeholder="选择试卷" style="width:100%"
                         @change="onPaperChange">
                <el-option v-for="p in papers" :key="p.id"
                           :label="`${p.name}（${p.item_count}题/ ${p.total_score}分）`" :value="p.id" />
              </el-select>
            </el-form-item>
          </el-col>
        </el-row>
        <el-row :gutter="12">
          <el-col :span="12">
            <el-form-item label="开始时间">
              <el-date-picker v-model="form.start_at" type="datetime" value-format="YYYY-MM-DD HH:mm:ss"
                              style="width:100%" />
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="截止时间">
              <el-date-picker v-model="form.end_at" type="datetime" value-format="YYYY-MM-DD HH:mm:ss"
                              style="width:100%" />
            </el-form-item>
          </el-col>
        </el-row>
        <el-row :gutter="12">
          <el-col :span="12">
            <el-form-item label="时长(分钟)">
              <el-input-number v-model="form.duration" :min="0" :max="300" style="width:100%" />
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="及格分">
              <el-input-number v-model="form.pass_score" :min="0" :max="paperTotal" style="width:100%" />
            </el-form-item>
          </el-col>
        </el-row>
        <el-form-item label="下发班级">
          <el-select v-model="form.class_ids" multiple style="width:100%">
            <el-option v-for="c in classes" :key="c.id" :label="`${c.grade_name} ${c.name}`" :value="c.id" />
          </el-select>
        </el-form-item>
        <el-form-item label="考试设置">
          <el-checkbox v-model="form.allow_retake">允许重考</el-checkbox>
          <el-checkbox v-model="form.show_answer">交卷后显示答案解析</el-checkbox>
          <el-checkbox v-model="form.anti_cheat">开启防切屏监控</el-checkbox>
        </el-form-item>
        <el-form-item label="任务说明">
          <el-input v-model="form.description" type="textarea" :rows="2" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="dlg = false">取消</el-button>
        <el-button type="primary" :loading="saving" @click="save">确定</el-button>
      </template>
    </el-dialog>

    <!-- 提交情况 -->
    <el-drawer v-model="subDrawer" :title="`${currentTask?.title} - 提交情况`" size="60%">
      <el-row :gutter="12" class="mb12" v-if="subStats">
        <el-col :span="6" v-for="c in subCards" :key="c.label">
          <div class="stat-card">
            <div class="stat-value">{{ c.value }}</div>
            <div class="stat-label">{{ c.label }}</div>
          </div>
        </el-col>
      </el-row>
      <el-table v-loading="subLoading" :data="submissions" border stripe>
        <el-table-column prop="student_name" label="学生" width="120" />
        <el-table-column label="状态" width="110">
          <template #default="{ row }">
            <el-tag :type="{ submitted: 'success', grading: 'warning', graded: 'primary', rejected: 'danger' }[row.status] || 'info'"
                    size="small">
              {{ { submitted: '已提交', grading: '批改中', graded: '已批改', rejected: '已打回' }[row.status] || row.status }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="score" label="得分" width="90" />
        <el-table-column prop="total_score" label="满分" width="90" />
        <el-table-column prop="class_rank" label="排名" width="80" />
        <el-table-column prop="submit_time" label="提交时间" width="170" />
        <el-table-column label="用时" width="100">
          <template #default="{ row }">
            {{ row.duration_seconds != null ? Math.round(row.duration_seconds / 60) + ' 分' : '-' }}
          </template>
        </el-table-column>
        <el-table-column prop="switch_count" label="切屏次数" width="100" />
        <el-table-column label="操作" width="110">
          <template #default="{ row }">
            <el-button link type="primary" @click="viewAnswer(row)">查看答卷</el-button>
          </template>
        </el-table-column>
      </el-table>
    </el-drawer>

    <!-- 学情报告 -->
    <el-drawer v-model="reportDrawer" title="班级学情报告" size="65%">
      <div v-loading="reportLoading">
        <template v-if="report">
          <el-row :gutter="12" class="mb12">
            <el-col :span="6" v-for="c in reportCards" :key="c.label">
              <div class="stat-card">
                <div class="stat-value">{{ c.value }}</div>
                <div class="stat-label">{{ c.label }}</div>
              </div>
            </el-col>
          </el-row>

          <el-descriptions title="成绩分布" :column="3" border class="mb12">
            <el-descriptions-item v-for="(v, k) in report.score_bands || {}" :key="k" :label="k">
              {{ v }} 人
            </el-descriptions-item>
          </el-descriptions>

          <el-divider content-position="left">AI 教学建议</el-divider>
          <div class="advice-box" v-if="advice">
            <pre class="advice">{{ advice }}</pre>
          </div>
          <el-empty v-else description="点击下方按钮生成 AI 教学建议" :image-size="60" />

          <el-table :data="report.detail || []" border size="small" class="mt12">
            <el-table-column prop="student_name" label="学生" width="110" />
            <el-table-column prop="score" label="得分" width="80" />
            <el-table-column prop="correct_count" label="正确题数" width="100" />
            <el-table-column prop="wrong_count" label="错误题数" width="100" />
            <el-table-column prop="accuracy" label="正确率" width="100" />
            <el-table-column prop="class_rank" label="排名" width="80" />
          </el-table>
        </template>
      </div>
      <template #footer>
        <el-button @click="genReport">生成班级学情报告</el-button>
        <el-button type="primary" @click="genAdvice">AI 生成教学建议</el-button>
      </template>
    </el-drawer>

    <!-- 答卷详情 -->
    <el-dialog v-model="answerDlg" title="答卷详情" width="720px" top="5vh">
      <div v-loading="answerLoading">
        <el-descriptions :column="3" border class="mb12">
          <el-descriptions-item label="得分">{{ answer?.score ?? '-' }}</el-descriptions-item>
          <el-descriptions-item label="排名">{{ answer?.class_rank ?? '-' }}</el-descriptions-item>
          <el-descriptions-item label="用时">{{ answer?.duration_seconds ?? 0 }} 秒</el-descriptions-item>
        </el-descriptions>
        <div v-for="(it, idx) in answerItems" :key="idx" class="q-item">
          <p><b>{{ idx + 1 }}. {{ it.student_answer }}</b></p>
          <p class="correct">正确答案：{{ it.correct_answer }}</p>
          <p class="analysis">解析：{{ it.analysis || it.ai_comment || '-' }}</p>
          <p>得分：{{ it.score }} / {{ it.full_score }}</p>
        </div>
      </div>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, reactive, computed, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Plus, Search, Refresh } from '@element-plus/icons-vue'
import { taskApi, questionApi, eduApi, gradingApi } from '@/api'
import { useUserStore } from '@/store/user'

const userStore = useUserStore()
// 按钮级权限统一取 store 的 can getter
const { can } = userStore
const isSysAdmin = computed(() => userStore.isAdmin === true)
const meId = (() => {
  try { return JSON.parse(localStorage.getItem('user') || '{}').id } catch { return null }
})()

const list = ref([])
const papers = ref([])
const subjects = ref([])
const grades = ref([])
const classes = ref([])
const submissions = ref([])
const report = ref(null)
const advice = ref('')
const answerItems = ref([])
const total = ref(0)
const loading = ref(false)
const saving = ref(false)
const dlg = ref(false)
const subDrawer = ref(false)
const reportDrawer = ref(false)
const answerDlg = ref(false)
const subLoading = ref(false)
const reportLoading = ref(false)
const answerLoading = ref(false)
const currentTask = ref(null)
const stats = ref({})
const statsLoading = ref(false)
const selection = ref([])
const batchLoading = ref(false)

const query = reactive({
  page: 1, page_size: 20, task_type: '', status: '',
  subject_id: null, class_id: null, keyword: ''
})

function subjectGradeName(gradeId) {
  return grades.value.find(g => g.id === gradeId)?.name || ''
}

const statCards = computed(() => {
  const d = stats.value || {}
  const avg = d.avg_completion
  return [
    { label: '任务总数', value: d.total ?? '-' },
    { label: '进行中', value: d.ongoing ?? '-' },
    { label: '已结束', value: d.finished ?? '-' },
    { label: '平均提交率', value: avg === undefined || avg === null ? '-' : `${avg}%` }
  ]
})

function buildParams() {
  const params = {}
  if (query.task_type) params.task_type = query.task_type
  if (query.status) params.status = query.status
  if (query.subject_id) params.subject_id = query.subject_id
  if (query.class_id) params.class_id = query.class_id
  const keyword = query.keyword.trim()
  if (keyword) params.keyword = keyword
  return params
}

async function loadStats() {
  statsLoading.value = true
  try {
    const res = await taskApi.stats(buildParams())
    stats.value = res.data || {}
  } catch {
    // 统计接口未就绪时保持占位，不阻断列表
  } finally {
    statsLoading.value = false
  }
}

function isOwner(row) {
  return row && (isSysAdmin.value || row.creator_id === meId)
}

function canEditTask(row) {
  return can('task:write') && isOwner(row)
}

function onSelectionChange(rows) { selection.value = rows || [] }

async function batchAction(action) {
  const ids = selection.value.map(t => t.id)
  if (!ids.length) return ElMessage.warning('请先勾选任务')
  const isDelete = action === 'delete'
  try {
    await ElMessageBox.confirm(
      isDelete
        ? `确认删除 ${ids.length} 个任务？已有提交记录的任务会被跳过（不级联删除成绩），删除不可恢复。`
        : `确认将 ${ids.length} 个任务批量结束？结束后学生不能继续作答。`,
      isDelete ? '批量删除确认' : '批量结束确认', { type: 'warning' })
  } catch { return }
  batchLoading.value = true
  try {
    const res = await taskApi.batch({ action, ids })
    const d = res.data || {}
    const done = (d.done || []).length
    const skipped = d.skipped || []
    if (skipped.length) {
      const reasons = skipped.slice(0, 3)
        .map(s => `#${s.id} ${s.reason || '失败'}`).join('；')
      ElMessage.warning(`已处理 ${done} 个，跳过 ${skipped.length} 个：${reasons}`)
    } else {
      ElMessage.success(`已${isDelete ? '删除' : '结束'} ${done} 个任务`)
    }
    selection.value = []
    await refreshAll()
  } finally {
    batchLoading.value = false
  }
}
const form = reactive({
  id: null, title: '', type: 'homework', paper_id: null, class_ids: [],
  start_at: '', end_at: '', duration: 60, pass_score: 60,
  allow_retake: true, show_answer: true, anti_cheat: false, description: ''
})

const subStats = ref(null)
const paperTotal = computed(() => {
  const p = papers.value.find((x) => x.id === form.paper_id)
  return Number(p?.total_score ?? 100)
})

// 及格分默认 60 是百分制假设。选中 5 分的随堂练习时后端会直接 400
// 「及格分应在 0~5.0 之间，当前 60.0」，表现为「换张小卷就发不出去」。
// 后端仅在**未传** pass_score 时才按总分折算，所以前端必须在选卷时主动收敛。
function onPaperChange() {
  const total = paperTotal.value
  if (!(Number(form.pass_score) > 0) || Number(form.pass_score) > total) {
    form.pass_score = Math.round(total * 0.6 * 100) / 100
  }
}

const subCards = computed(() => subStats.value ? [
  { label: '应交人数', value: subStats.value.total ?? 0 },
  { label: '已提交', value: subStats.value.submitted ?? 0 },
  { label: '待批改', value: subStats.value.pending ?? 0 },
  { label: '完成率', value: `${subStats.value.rate ?? 0}%` }
] : [])

const reportCards = computed(() => report.value ? [
  { label: '平均分', value: report.value.avg_score },
  { label: '最高分', value: report.value.max_score },
  { label: '最低分', value: report.value.min_score },
  { label: '及格率', value: `${report.value.pass_rate}%` }
] : [])

function statusLabel(row) {
  if (row.status === 'draft') return '草稿'
  if (row.end_at && new Date(row.end_at.replace(/-/g, '/')) < new Date()) return '已结束'
  if (row.start_at && new Date(row.start_at.replace(/-/g, '/')) > new Date()) return '未开始'
  return '进行中'
}
function statusTag(row) {
  const l = statusLabel(row)
  return { '草稿': 'info', '未开始': 'info', '进行中': 'primary', '已结束': 'success' }[l]
}

async function load() {
  loading.value = true
  try {
    const res = await taskApi.list({ ...buildParams(), page: query.page, page_size: query.page_size })
    const d = res.data || {}
    list.value = d.items || []
    total.value = d.total || 0
    selection.value = []
  } finally {
    loading.value = false
  }
}

async function refreshAll() {
  await Promise.all([load(), loadStats()])
}

function search() { query.page = 1; refreshAll() }

function reset() {
  Object.assign(query, {
    page: 1, task_type: '', status: '', subject_id: null, class_id: null, keyword: ''
  })
  refreshAll()
}

function openDialog(row) {
  Object.assign(form, row
    ? { ...row, class_ids: (row.classes || row.class_ids || []) }
    : { id: null, title: '', type: 'homework', paper_id: null, class_ids: [],
        start_at: '', end_at: '', duration: 60, pass_score: 60,
        allow_retake: true, show_answer: true, anti_cheat: false, description: '' })
  dlg.value = true
}

async function save() {
  if (!form.title) return ElMessage.warning('请输入任务标题')
  if (!form.paper_id) return ElMessage.warning('请选择试卷')
  if (!form.class_ids.length) return ElMessage.warning('请选择下发班级')
  saving.value = true
  try {
    if (form.id) await taskApi.update(form.id, form)
    else await taskApi.create(form)
    ElMessage.success('保存成功')
    dlg.value = false
    await refreshAll()
  } finally {
    saving.value = false
  }
}

async function remove(row) {
  if (!canEditTask(row)) return ElMessage.warning('只能删除自己创建的任务')
  await ElMessageBox.confirm(`确认删除任务「${row.title}」？相关提交记录将一并删除。`, '提示', { type: 'warning' })
  await taskApi.remove(row.id)
  ElMessage.success('已删除')
  await refreshAll()
}

async function openSubs(row) {
  currentTask.value = row
  subDrawer.value = true
  subLoading.value = true
  subStats.value = null
  try {
    const res = await taskApi.submissions(row.id, { page: 1, page_size: 200 })
    const d = res.data || {}
    submissions.value = d.items || []
    subStats.value = d.stats || {
      total: d.total, submitted: (d.items || []).length,
      rate: row.completion_rate || 0
    }
  } finally {
    subLoading.value = false
  }
}

function openReport(row) {
  currentTask.value = row
  report.value = null
  advice.value = ''
  reportDrawer.value = true
}

async function genReport() {
  reportLoading.value = true
  try {
    const res = await gradingApi.report(currentTask.value.id)
    report.value = res.data
    ElMessage.success('学情报告已生成')
  } finally {
    reportLoading.value = false
  }
}

async function genAdvice() {
  reportLoading.value = true
  try {
    const res = await gradingApi.aiComment(currentTask.value.id)
    const d = res.data
    advice.value = typeof d === 'string' ? d : (d.advice || d.raw || '')
    if (!report.value) await genReport()
    ElMessage.success(d.is_fallback ? '已生成（规则引擎降级）' : 'AI 建议已生成')
  } finally {
    reportLoading.value = false
  }
}

async function viewAnswer(row) {
  // 提交行只有 submission_id（无 id）。此前读 row.id 得到 undefined，
  // 请求 /grading/submissions/undefined -> FastAPI int 校验失败 -> 422。
  const sid = row.submission_id ?? row.id
  if (!sid) {
    ElMessage.error('该记录缺少提交 ID，请刷新提交列表')
    return
  }
  answerDlg.value = true
  answerLoading.value = true
  answerItems.value = []
  try {
    const res = await gradingApi.detail(sid)
    answerItems.value = res.data?.items || []
    answerDetail.value = res.data
  } finally {
    answerLoading.value = false
  }
}

const answerDetail = ref(null)
const answer = computed(() => answerDetail.value)

onMounted(async () => {
  await refreshAll()
  const [p, c, s, g] = await Promise.all([
    questionApi.papers({ page: 1, page_size: 100 }),
    eduApi.classes({ page_size: 100, mine: true }),
    eduApi.subjects(),
    eduApi.grades()
  ])
  papers.value = p.data?.items || []
  // mine=true 只返回本人任教的班级：后端发布时会校验「只能给自己任教的
  // 班级下发」，全量列出只会让教师选中后收到 400。
  // /edu/classes 返回数组（非分页 items）—— 只读 data.items 会得到 undefined，
  // 班级下拉恒为空且没有任何报错，教师因此完全无法发布作业/考试。
  const _cd = c.data
  classes.value = Array.isArray(_cd) ? _cd : (_cd?.items || [])
  subjects.value = s.data || []
  grades.value = g.data || []
})
</script>

<style scoped>
.mt16 { margin-top: 16px; justify-content: flex-end; }
.mt12 { margin-top: 12px; }
.mb12 { margin-bottom: 12px; }
.tip { font-size: 12px; color: #909399; }
.muted { color: var(--el-text-color-secondary); font-size: 12px; }
.filter-card :deep(.el-form-item) { margin-bottom: 12px; }
.q-item { padding: 10px 0; border-bottom: 1px dashed #ebeef5; }
.correct { color: #67c23a; margin: 4px 0; }
.analysis { color: #909399; font-size: 13px; margin: 4px 0; }
.advice-box { background: #f7f9fc; padding: 12px; border-radius: 8px; }
.advice { white-space: pre-wrap; margin: 0; font-family: inherit; font-size: 13px; line-height: 1.8; }

.tm-header {
  display: flex; align-items: flex-start; justify-content: space-between;
  gap: 16px; flex-wrap: wrap;
}
.tm-title-wrap { display: flex; flex-direction: column; gap: 10px; }
.tm-stats { display: flex; gap: 12px; flex-wrap: wrap; }
.tm-stat { min-width: 110px; padding: 10px 14px; }
.tm-stat .stat-label { font-size: 12px; margin-top: 2px; }
.tm-actions { display: flex; align-items: center; gap: 8px; flex-wrap: wrap; }
.tm-actions :deep(.el-button + .el-button) { margin-left: 0; }
.batch-bar {
  display: flex; align-items: center; gap: 8px; flex-wrap: wrap;
  padding: 8px 0 12px;
}
.batch-bar :deep(.el-button + .el-button) { margin-left: 0; }
</style>
