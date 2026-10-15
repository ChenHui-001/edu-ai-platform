<template>
  <div class="page-container">
    <div class="page-header">
      <h2 class="page-title">作业与考试</h2>
      <div>
        <el-button :icon="Refresh" @click="load">刷新</el-button>
        <el-button v-if="can('task:write')" type="primary" :icon="Plus" @click="openDialog()">发布作业 / 考试</el-button>
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
        <el-form-item label="关键词">
          <el-input v-model="query.keyword" placeholder="任务标题" clearable style="width:170px"
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
        <el-table-column prop="title" label="任务标题" min-width="200" show-overflow-tooltip />
        <el-table-column label="类型" width="90">
          <template #default="{ row }">
            <el-tag :type="row.type === 'exam' ? 'danger' : 'primary'" size="small">
              {{ row.type_label }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="subject_name" label="学科" width="90" />
        <el-table-column label="提交进度" width="200">
          <template #default="{ row }">
            <el-progress :percentage="Math.min(row.completion_rate || 0, 100)"
                         :status="(row.completion_rate || 0) >= 60 ? 'success' : ''" />
            <span class="tip">{{ row.submission_count }}/{{ row.assignment_count }} 人已交</span>
          </template>
        </el-table-column>
        <el-table-column prop="start_at" label="开始时间" width="160" />
        <el-table-column prop="end_at" label="截止时间" width="160" />
        <el-table-column label="状态" width="100">
          <template #default="{ row }">
            <el-tag :type="statusTag(row)" size="small">{{ statusLabel(row) }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column label="操作" width="220" fixed="right">
          <template #default="{ row }">
            <el-button link type="primary" @click="openSubs(row)">提交情况</el-button>
            <el-button link type="success" @click="openReport(row)">学情报告</el-button>
            <el-button link type="primary" @click="openDialog(row)">编辑</el-button>
            <el-button link type="danger" @click="remove(row)">删除</el-button>
          </template>
        </el-table-column>
      </el-table>

      <el-pagination class="mt16" background layout="total, prev, pager, next"
                     :total="total" v-model:current-page="query.page" @current-change="load" />
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
              <el-select v-model="form.paper_id" filterable placeholder="选择试卷" style="width:100%">
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
              <el-input-number v-model="form.pass_score" :min="0" :max="100" style="width:100%" />
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
        <el-table-column prop="duration_seconds" label="用时(分)" width="100" />
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
const can = (p) => userStore.hasPerm(p)

const list = ref([])
const papers = ref([])
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

const query = reactive({ page: 1, page_size: 20, task_type: '', status: '', keyword: '' })
const form = reactive({
  id: null, title: '', type: 'homework', paper_id: null, class_ids: [],
  start_at: '', end_at: '', duration: 60, pass_score: 60,
  allow_retake: true, show_answer: true, anti_cheat: false, description: ''
})

const subStats = ref(null)
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
    const res = await taskApi.list(query)
    const d = res.data.data || {}
    list.value = d.items || []
    total.value = d.total || 0
  } finally {
    loading.value = false
  }
}

function reset() {
  Object.assign(query, { page: 1, task_type: '', status: '', keyword: '' })
  load()
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
    load()
  } finally {
    saving.value = false
  }
}

async function remove(row) {
  await ElMessageBox.confirm(`确认删除任务「${row.title}」？相关提交记录将一并删除。`, '提示', { type: 'warning' })
  await taskApi.remove(row.id)
  ElMessage.success('已删除')
  load()
}

async function openSubs(row) {
  currentTask.value = row
  subDrawer.value = true
  subLoading.value = true
  subStats.value = null
  try {
    const res = await taskApi.submissions(row.id, { page: 1, page_size: 200 })
    const d = res.data.data || {}
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
    report.value = res.data.data
    ElMessage.success('学情报告已生成')
  } finally {
    reportLoading.value = false
  }
}

async function genAdvice() {
  reportLoading.value = true
  try {
    const res = await gradingApi.aiComment(currentTask.value.id)
    const d = res.data.data
    advice.value = typeof d === 'string' ? d : (d.advice || d.raw || '')
    if (!report.value) await genReport()
    ElMessage.success(d.is_fallback ? '已生成（规则引擎降级）' : 'AI 建议已生成')
  } finally {
    reportLoading.value = false
  }
}

async function viewAnswer(row) {
  answerDlg.value = true
  answerLoading.value = true
  answerItems.value = []
  try {
    const res = await gradingApi.detail(row.id)
    answerItems.value = res.data.data?.items || []
    Object.assign(answerItems.value, { length: answerItems.value.length })
    answerDetail.value = res.data.data
  } finally {
    answerLoading.value = false
  }
}

const answerDetail = ref(null)
const answer = computed(() => answerDetail.value)

onMounted(async () => {
  await load()
  const p = await questionApi.papers({ page: 1, page_size: 100 })
  papers.value = p.data.data?.items || []
  const c = await eduApi.classes({ page_size: 100 })
  classes.value = c.data.data?.items || []
})
</script>

<style scoped>
.mt16 { margin-top: 16px; justify-content: flex-end; }
.mt12 { margin-top: 12px; }
.mb12 { margin-bottom: 12px; }
.tip { font-size: 12px; color: #909399; }
.filter-card :deep(.el-form-item) { margin-bottom: 12px; }
.q-item { padding: 10px 0; border-bottom: 1px dashed #ebeef5; }
.correct { color: #67c23a; margin: 4px 0; }
.analysis { color: #909399; font-size: 13px; margin: 4px 0; }
.advice-box { background: #f7f9fc; padding: 12px; border-radius: 8px; }
.advice { white-space: pre-wrap; margin: 0; font-family: inherit; font-size: 13px; line-height: 1.8; }
</style>
