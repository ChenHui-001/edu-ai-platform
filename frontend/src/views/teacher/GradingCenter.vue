<template>
  <div class="page-container">
    <div class="page-header">
      <h2 class="page-title">批改中心</h2>
      <div class="header-actions">
        <span class="queue-summary" v-if="list.length">
          共 <b>{{ list.length }}</b> 份待批 ·
          需人工 <b class="warn">{{ needManualCount }}</b> 份
        </span>
        <el-tooltip placement="bottom" :show-after="200">
          <template #content>
            <div class="kb-tip">Ctrl+Enter 保存并批下一份<br>Ctrl+S 保存<br>Alt+F 满分（当前题）<br>Alt+Z 零分（当前题）</div>
          </template>
          <el-button :icon="QuestionFilled" circle />
        </el-tooltip>
        <el-button :icon="Refresh" :loading="loading" @click="refreshAll">刷新队列</el-button>
      </div>
    </div>

    <!-- 统计卡 -->
    <div class="gc-stats" v-loading="statsLoading">
      <div v-for="c in statCards" :key="c.label" class="stat-card gc-stat">
        <div class="stat-value">{{ c.value }}</div>
        <div class="stat-label">{{ c.label }}</div>
      </div>
    </div>

    <!-- 筛选：班级 / 任务 / 关键词 -->
    <el-card shadow="never" class="filter-card">
      <el-form :inline="true" :model="query">
        <el-form-item label="班级">
          <el-select v-model="query.class_id" placeholder="全部" clearable style="width:170px">
            <el-option v-for="c in classes" :key="c.id"
                       :label="`${c.grade_name || ''} ${c.name}`" :value="c.id" />
          </el-select>
        </el-form-item>
        <el-form-item label="任务">
          <el-select v-model="query.task_id" placeholder="全部" clearable filterable style="width:220px">
            <el-option v-for="t in tasks" :key="t.id" :label="t.title" :value="t.id" />
          </el-select>
        </el-form-item>
        <el-form-item label="关键词">
          <el-input v-model="query.keyword" placeholder="学生 / 任务" clearable style="width:170px"
                    @keyup.enter="refreshAll" />
        </el-form-item>
        <el-form-item>
          <el-button type="primary" :icon="Search" @click="refreshAll">查询</el-button>
          <el-button :icon="Refresh" @click="resetFilters">重置</el-button>
        </el-form-item>
      </el-form>
    </el-card>

    <el-row :gutter="16">
      <!-- ============ 左：待批队列 ============ -->
      <el-col :xs="24" :md="8">
        <el-card shadow="never" class="queue-card">
          <template #header>
            <div class="flex-between">
              <b>待批改队列</b>
              <div class="queue-head-actions">
                <el-tag type="warning" size="small">{{ filtered.length }} 份</el-tag>
                <el-button size="small" :disabled="!nextItem" @click="select(nextItem)">
                  下一份
                </el-button>
              </div>
            </div>
          </template>
          <div class="queue-filters mb10">
            <el-radio-group v-model="queueFilter" size="small">
              <el-radio-button label="all">全部</el-radio-button>
              <el-radio-button label="manual">需人工</el-radio-button>
            </el-radio-group>
          </div>
          <!-- 批量操作条 -->
          <div class="batch-bar" v-if="checkedIds.length && (can('grading:do') || can('grading:publish'))">
            <span class="tip">已选 <b>{{ checkedIds.length }}</b> 份</span>
            <div class="batch-actions">
              <el-button v-if="can('grading:do')" size="small" @click="batchGrade" :loading="batching">
                批量采纳
              </el-button>
              <el-button v-if="can('grading:publish')" size="small" type="warning"
                         @click="batchPublish" :loading="batching">
                批量发布
              </el-button>
              <el-button size="small" text @click="checkedIds = []">清空</el-button>
            </div>
          </div>
          <div v-loading="loading" class="sub-list">
            <div v-for="item in filtered" :key="item.submission_id"
                 class="sub-item"
                 :class="{ active: item.submission_id === current?.id }"
                 @click="select(item)">
              <div class="row-between">
                <div class="name-line">
                  <el-checkbox
                    :model-value="checkedIds.includes(item.submission_id)"
                    @click.stop
                    @change="(v) => toggleCheck(item.submission_id, v)" />
                  <span class="name">{{ item.student_name }}</span>
                </div>
                <el-tag size="small" :type="item.needs_manual ? 'warning' : 'info'">
                  {{ item.needs_manual ? '需人工' : 'AI 已批' }}
                </el-tag>
              </div>
              <p class="task">{{ item.task_title }}</p>
              <div class="row-between">
                <span class="tip">{{ fmtTime(item.submit_time) }}</span>
                <span class="score">
                  {{ item.score ?? '未批' }}<template v-if="item.score != null"> / {{ item.total_score }}</template>
                </span>
              </div>
            </div>
            <el-empty v-if="!loading && !filtered.length" description="暂无待批改作业" :image-size="70" />
            <div v-if="hasMore" class="load-more">
              <el-button size="small" text :loading="loadingMore" @click="loadMore">
                加载更多（{{ list.length }} / {{ total }}）
              </el-button>
            </div>
            <div v-else-if="list.length" class="load-more tip">
              已全部加载（{{ list.length }} 份）
            </div>
          </div>
        </el-card>
      </el-col>

      <!-- ============ 右：批改工作区 ============ -->
      <el-col :xs="24" :md="16">
        <el-card shadow="never" v-loading="detailLoading" class="grading-card">
          <template #header>
            <div class="flex-between grading-head" v-if="detail">
              <div class="student-info">
                <b class="student-name">{{ detail.student?.name }}</b>
                <span class="task-name">{{ detail.task_title }}</span>
              </div>
              <div class="head-tags">
                <el-tag size="small">客观 {{ detail.objective_score ?? 0 }}</el-tag>
                <el-tag size="small" type="warning">主观 {{ detail.subjective_score ?? 0 }}</el-tag>
                <el-tag size="small" :type="statusType(detail.status)">
                  {{ statusText(detail.status) }}
                </el-tag>
              </div>
            </div>
          </template>

          <el-empty v-if="!detail" description="请从左侧队列选择一份答卷开始批改" />

          <template v-else>
            <!-- 批改进度条 -->
            <div class="progress-bar">
              <div class="progress-info">
                <span>批改进度 <b>{{ scoredCount }}</b> / {{ detail.items?.length || 0 }} 题</span>
                <span class="tip">总分 <b class="total">{{ totalScore }}</b> / {{ detail.total_score }}</span>
              </div>
              <el-progress :percentage="gradeProgress" :stroke-width="8"
                           :status="gradeProgress === 100 ? 'success' : undefined" />
            </div>

            <!-- 逐题批改：左信息 / 右评分 -->
            <div v-for="(it, idx) in detail.items" :key="it.answer_id"
                 class="q-item" :class="{ scored: isScored(it) }">
              <div class="q-head">
                <span class="q-no">{{ idx + 1 }}</span>
                <el-tag size="small" effect="plain">{{ TYPE_LABEL[it.type] || it.type }}</el-tag>
                <el-tag size="small" :type="it.is_correct ? 'success' : it.is_correct === false ? 'danger' : 'info'">
                  {{ it.is_correct === true ? '正确' : it.is_correct === false ? '错误' : '待判' }}
                </el-tag>
                <el-tag v-if="it.grader_type" size="small" effect="plain" type="info">
                  {{ it.grader_type === 'ai' ? 'AI 批改' : it.grader_type === 'auto' ? '自动判分' : '人工批改' }}
                </el-tag>
                <div class="q-score-panel">
                  <el-button-group size="small">
                    <el-button size="small" @click="setScore(it, it.full_score)">满分</el-button>
                    <el-button size="small" @click="setScore(it, 0)">零分</el-button>
                  </el-button-group>
                  <el-input-number v-model="scores[it.answer_id]" :min="0" :max="it.full_score || 0"
                                   :step="0.5" size="small" style="width:110px" />
                  <span class="full-score">/ {{ it.full_score }}</span>
                </div>
              </div>

              <div class="q-body">
                <div class="q-col q-detail">
                  <p class="content"><b>学生答案：</b><span class="ans">{{ it.content || '（未作答）' }}</span></p>
                  <p class="correct">
                    <b>正确答案：</b>
                    <span class="std">{{ fmtAnswer(it.standard_answer) || '—' }}</span>
                  </p>
                  <p v-if="it.knowledge_point_name" class="kp">
                    <el-tag size="small" effect="plain" type="info">{{ it.knowledge_point_name }}</el-tag>
                  </p>
                  <p v-if="it.ai_comment" class="ai-comment">
                    <b>AI 评语：</b>{{ it.ai_comment }}
                  </p>
                  <p v-if="it.ai_error_points?.length" class="err-points">
                    <b>失分点：</b>
                    <el-tag v-for="(p, i) in it.ai_error_points" :key="i" size="small" type="danger"
                            effect="plain" class="ml4">{{ p }}</el-tag>
                  </p>
                </div>
                <div class="q-col q-grade">
                  <el-input v-model="comments[it.answer_id]" placeholder="教师评语（可选，会展示给学生）"
                            type="textarea" :rows="3" />
                </div>
              </div>
            </div>

            <!-- 底部操作栏 -->
            <div class="footer-bar">
              <div class="footer-total">
                总分 <b class="total">{{ totalScore }}</b> / {{ detail.total_score }}
              </div>
              <div class="footer-actions">
                <el-button v-if="can('grading:do')" type="danger" plain size="default" @click="reject">
                  打回重做
                </el-button>
                <el-button v-if="can('grading:do')" type="primary" :loading="saving" @click="saveGrade()">
                  保存批改结果
                </el-button>
                <el-button v-if="can('grading:do')" type="success" :loading="saving"
                           :disabled="!nextItem" @click="saveAndNext">
                  保存并批下一份
                </el-button>
                <el-button v-if="can('grading:publish')" type="warning" :disabled="!canPublish" @click="publish">
                  发布成绩
                </el-button>
              </div>
            </div>
          </template>
        </el-card>
      </el-col>
    </el-row>
  </div>
</template>

<script setup>
import { ref, reactive, computed, onMounted, onBeforeUnmount } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Search, Refresh, QuestionFilled } from '@element-plus/icons-vue'
import { gradingApi, taskApi, eduApi } from '@/api'
import { useUserStore } from '@/store/user'

const { can } = useUserStore()
const route = useRoute()
const router = useRouter()

const TYPE_LABEL = {
  single: '单选题', multiple: '多选题', judge: '判断题', blank: '填空题',
  short: '简答题', calc: '计算题', material: '材料分析题', composition: '作文题',
}
// 可发布成绩的状态。
// 枚举真实取值见 backend/app/models/task.py::GradeStatus：
//   not_graded / auto_graded / fully_graded / published
// 此前这里写的是 'graded' —— 该值**在枚举里并不存在**，纯客观题自动判分后
// 状态停在 auto_graded（页面标「待人工确认」），于是「发布成绩」按钮永远
// disabled：教师把题改完、保存成功，按钮仍是灰的，成绩永远发不出去。
// 保留 'graded' 只为兼容历史脏数据。
const PUBLISHABLE = new Set(['auto_graded', 'graded', 'fully_graded'])

const list = ref([])
const detail = ref(null)
const current = ref(null)
const scores = reactive({})
const comments = reactive({})
const queueFilter = ref('all')
const loading = ref(false)
const detailLoading = ref(false)
const saving = ref(false)
// 筛选 + 统计
const query = reactive({ class_id: null, task_id: null, keyword: '' })
const classes = ref([])
const tasks = ref([])
const stats = ref({})
const statsLoading = ref(false)
const statCards = computed(() => {
  const d = stats.value || {}
  return [
    { label: '待批改', value: d.pending ?? '-' },
    { label: '批改中', value: d.grading ?? '-' },
    { label: '已批改', value: d.graded ?? '-' },
    { label: '已发布', value: d.published ?? '-' },
    { label: '平均分', value: d.avg_score ?? '-' }
  ]
})
// 批量 / 分页 / 快捷键
const checkedIds = ref([])
const batching = ref(false)
const total = ref(0)
const PAGE_SIZE = 30
const page = ref(1)
const loadingMore = ref(false)
const focusedIdx = ref(0)   // Alt+F/Alt+Z 作用的题目索引

const needManualCount = computed(() => list.value.filter(i => i.needs_manual).length)
const hasMore = computed(() => list.value.length < total.value)

const filtered = computed(() => {
  const k = query.keyword.trim().toLowerCase()
  let out = list.value
  if (queueFilter.value === 'manual') out = out.filter(i => i.needs_manual)
  if (!k) return out
  return out.filter(i =>
    (i.student_name || '').toLowerCase().includes(k) ||
    (i.task_title || '').toLowerCase().includes(k))
})

/** 当前提交的下一份（用于「保存并批下一份」） */
const nextItem = computed(() => {
  const sid = current.value?.id
  const idx = filtered.value.findIndex(i => i.submission_id === sid)
  if (idx < 0) return filtered.value[0] || null
  return filtered.value[idx + 1] || filtered.value[0] || null
})

const scoredCount = computed(() =>
  (detail.value?.items || []).filter(it => scores[it.answer_id] !== undefined
    && scores[it.answer_id] !== null).length)

const gradeProgress = computed(() => {
  const total = detail.value?.items?.length || 0
  return total ? Math.round((scoredCount.value / total) * 100) : 0
})

const totalScore = computed(() => {
  if (!detail.value) return 0
  const s = (detail.value.items || []).reduce(
    (sum, it) => sum + (Number(scores[it.answer_id]) || 0), 0)
  return Number(s.toFixed(1))
})

// 详情接口返回的 item 里没有 needs_manual 字段（那是队列接口才有的），
// 这里按题型 + 是否已给分判断，与后端 publish 的复核逻辑保持一致。
const SUBJECTIVE = new Set(['short', 'calc', 'material', 'composition'])
const canPublish = computed(() => {
  const d = detail.value
  if (!d || d.score == null || !PUBLISHABLE.has(d.status)) return false
  if (d.status === 'published') return false
  return !(d.items || []).some(it => SUBJECTIVE.has(it.type) && it.score == null)
})

function statusText(s) {
  return {
    not_graded: '未批改', auto_graded: '待人工确认', fully_graded: '已批改',
    graded: '已批改', published: '已发布', rejected: '已打回',
  }[s] || s || '-'
}
function statusType(s) {
  return {
    not_graded: 'info', auto_graded: 'warning', fully_graded: 'success',
    graded: 'success', published: 'primary', rejected: 'danger',
  }[s] || 'info'
}

function isScored(it) {
  return scores[it.answer_id] !== undefined && scores[it.answer_id] !== null
}

function setScore(it, v) {
  scores[it.answer_id] = v
}

function fmtTime(t) {
  if (!t) return '-'
  const s = String(t).replace('T', ' ')
  return s.slice(0, 16)
}

function fmtAnswer(a) {
  if (a === null || a === undefined) return ''
  if (Array.isArray(a)) return a.join('')
  if (typeof a === 'object') return JSON.stringify(a)
  return String(a)
}

function buildPendingParams(pageNo) {
  const params = { page: pageNo, page_size: PAGE_SIZE }
  if (query.class_id) params.class_id = query.class_id
  if (query.task_id) params.task_id = query.task_id
  const keyword = query.keyword.trim()
  if (keyword) params.keyword = keyword
  return params
}

async function loadStats() {
  statsLoading.value = true
  try {
    const params = {}
    if (query.class_id) params.class_id = query.class_id
    if (query.task_id) params.task_id = query.task_id
    const keyword = query.keyword.trim()
    if (keyword) params.keyword = keyword
    const res = await gradingApi.stats(params)
    stats.value = res.data || {}
  } catch {
    // 统计接口未就绪时保持占位，不阻断批改
  } finally {
    statsLoading.value = false
  }
}

async function load() {
  loading.value = true
  page.value = 1
  try {
    const res = await gradingApi.pending(buildPendingParams(1))
    list.value = res.data?.items || []
    total.value = res.data?.total ?? list.value.length
    checkedIds.value = []
  } finally {
    loading.value = false
  }
}

async function refreshAll() {
  await Promise.all([load(), loadStats()])
}

function resetFilters() {
  Object.assign(query, { class_id: null, task_id: null, keyword: '' })
  refreshAll()
}

async function loadOptions() {
  try {
    const [c, t] = await Promise.all([
      eduApi.classes({ page_size: 100, mine: true }),
      taskApi.list({ page: 1, page_size: 100 })
    ])
    const _cd = c.data
    classes.value = Array.isArray(_cd) ? _cd : (_cd?.items || [])
    tasks.value = t.data?.items || []
  } catch {
    classes.value = []
    tasks.value = []
  }
}

/** 分页追加：待批量大时不必一次全拉（此前固定 100 条，超出看不到） */
async function loadMore() {
  loadingMore.value = true
  try {
    page.value += 1
    const res = await gradingApi.pending(buildPendingParams(page.value))
    const more = res.data?.items || []
    const seen = new Set(list.value.map(x => x.submission_id))
    list.value = [...list.value, ...more.filter(x => !seen.has(x.submission_id))]
    total.value = res.data?.total ?? list.value.length
  } finally {
    loadingMore.value = false
  }
}

function toggleCheck(sid, v) {
  if (v) {
    if (!checkedIds.value.includes(sid)) checkedIds.value.push(sid)
  } else {
    checkedIds.value = checkedIds.value.filter(x => x !== sid)
  }
}

/** 批量采纳：把选中提交的当前分数直接落库（AI 已批的抽检确认场景） */
async function batchGrade() {
  batching.value = true
  try {
    const res = await gradingApi.batchGrade({ submission_ids: checkedIds.value })
    const d = res.data || {}
    ElMessage.success(
      `批量批改 ${d.graded?.length || 0} 份` +
      (d.skipped?.length ? `，跳过 ${d.skipped.length} 份` : ''))
    await refreshAll()
  } catch (e) {
    ElMessage.error(`批量批改失败：${e?.message || e}`)
  } finally {
    batching.value = false
  }
}

/** 批量发布：仅对已批改且未发布的记录生效（未批改的自动跳过） */
async function batchPublish() {
  try {
    await ElMessageBox.confirm(
      `将发布 ${checkedIds.value.length} 份成绩，学生立即可见。确认？`, '批量发布', { type: 'warning' })
  } catch { return }
  batching.value = true
  try {
    const res = await gradingApi.batchPublish({ submission_ids: checkedIds.value })
    const d = res.data || {}
    ElMessage.success(
      `已发布 ${d.published?.length || 0} 份` +
      (d.skipped?.length ? `，跳过 ${d.skipped.length} 份（未批改/已发布）` : ''))
    await refreshAll()
  } catch (e) {
    ElMessage.error(`批量发布失败：${e?.message || e}`)
  } finally {
    batching.value = false
  }
}

/** 键盘快捷键：Ctrl+Enter 保存并下一份 / Ctrl+S 保存 / Alt+F 满分 / Alt+Z 零分 */
function onKeydown(e) {
  if (!detail.value) return
  const tag = (e.target?.tagName || '').toLowerCase()
  const editing = tag === 'input' || tag === 'textarea'
  if ((e.ctrlKey || e.metaKey) && e.key === 'Enter') {
    e.preventDefault()
    saveAndNext()
  } else if ((e.ctrlKey || e.metaKey) && e.key.toLowerCase() === 's') {
    e.preventDefault()
    saveGrade()
  } else if (e.altKey && e.key.toLowerCase() === 'f') {
    e.preventDefault()
    const it = detail.value.items?.[focusedIdx.value]
    if (it) setScore(it, it.full_score)
  } else if (e.altKey && e.key.toLowerCase() === 'z') {
    e.preventDefault()
    const it = detail.value.items?.[focusedIdx.value]
    if (it) setScore(it, 0)
  } else if (!editing && /^[1-9]$/.test(e.key)) {
    // 数字键：聚焦到第 N 题（批改时快速跳题）
    const i = Number(e.key) - 1
    if (i < (detail.value.items?.length || 0)) {
      focusedIdx.value = i
      document.querySelectorAll('.q-item')[i]?.scrollIntoView({ behavior: 'smooth', block: 'center' })
    }
  }
}

function fillDetail(d, sid) {
  detail.value = d
  current.value = { id: sid, submission_id: sid }
  Object.keys(scores).forEach(k => delete scores[k])
  Object.keys(comments).forEach(k => delete comments[k])
  ;(d.items || []).forEach(it => {
    // 保持 null（未批改）而非默认 0：否则「批改进度」会把未评的题算成已批
    scores[it.answer_id] = it.score ?? null
    comments[it.answer_id] = it.teacher_comment || ''
  })
}

async function select(item) {
  if (!item) return
  const sid = item.submission_id ?? item.id
  if (!sid) {
    ElMessage.error('该记录缺少提交 ID，请刷新列表')
    return
  }
  current.value = { ...item, id: sid, submission_id: sid }
  detailLoading.value = true
  detail.value = null
  router.replace({ query: { ...route.query, submission: String(sid) } })
  try {
    const res = await gradingApi.detail(sid)
    fillDetail(res.data, sid)
  } finally {
    detailLoading.value = false
  }
}

/** 支持从首页带 submission 参数直达（如 /teacher/grading?submission=33）。 */
async function focusFromQuery() {
  const sid = Number(route.query.submission)
  if (!sid) return
  const hit = list.value.find(i => (i.submission_id ?? i.id) === sid)
  if (hit) {
    await select(hit)
  } else {
    try {
      const res = await gradingApi.detail(sid)
      fillDetail(res.data, sid)
      current.value = {
        id: sid, submission_id: sid,
        student_name: res.data?.student?.name || '-',
        task_title: res.data?.task_title || '-',
      }
    } catch (e) {
      // 区分错误类型：404 才是「不存在/已批改」；其余一律「加载失败」
      const status = e?.response?.status ?? e?.data?.code
      if (status === 404) {
        ElMessage.warning('未找到该提交记录，可能已完成批改')
        router.replace({ query: {} })
      } else {
        ElMessage.error(`批改详情加载失败（${status || '网络异常'}），请稍后重试`)
      }
    }
  }
}

async function saveGrade(silent = false) {
  saving.value = true
  try {
    const answers = (detail.value.items || []).map(it => ({
      answer_id: it.answer_id,
      score: Number(scores[it.answer_id]) || 0,
      teacher_comment: comments[it.answer_id] || '',
      is_correct: (Number(scores[it.answer_id]) || 0) >= (it.full_score ?? 0),
    }))
    await gradingApi.grade(detail.value.submission_id, { answers })
    if (!silent) ElMessage.success('批改结果已保存')
    await refreshAll()
    return true
  } catch (e) {
    ElMessage.error(`保存失败：${e?.message || e}`)
    return false
  } finally {
    saving.value = false
  }
}

/** 保存当前并自动跳到下一份，减少「回列表找下一份」的往返 */
async function saveAndNext() {
  const ok = await saveGrade(true)
  if (!ok) return
  const next = nextItem.value
  ElMessage.success(`已保存，正在打开 ${next?.student_name || '下一份'}`)
  if (next) await select(next)
}

async function reject() {
  const { value } = await ElMessageBox.prompt('请输入打回原因', '打回重做', {
    inputPlaceholder: '如：第 3 题计算过程缺失，请重新作答',
  })
  await gradingApi.reject(detail.value.submission_id, { reason: value })
  ElMessage.success('已打回，学生可重新提交')
  detail.value = null
  current.value = null
  router.replace({ query: {} })
  await refreshAll()
}

async function publish() {
  await ElMessageBox.confirm('发布后学生即可看到最终成绩，确认发布？', '提示', { type: 'info' })
  await gradingApi.publish(detail.value.submission_id)
  ElMessage.success('成绩已发布')
  detail.value = null
  current.value = null
  router.replace({ query: {} })
  await refreshAll()
}

onMounted(async () => {
  await Promise.all([loadOptions(), refreshAll()])
  await focusFromQuery()
  window.addEventListener('keydown', onKeydown)
})

onBeforeUnmount(() => {
  window.removeEventListener('keydown', onKeydown)
})
</script>

<style scoped>
.header-actions { display: flex; align-items: center; gap: 12px; }
.queue-summary { font-size: 13px; color: #606266; }
.queue-summary b { color: #2f6fd0; }
.queue-summary b.warn { color: #e6a23c; }

.gc-stats { display: flex; gap: 12px; flex-wrap: wrap; margin-bottom: 16px; }
.gc-stat { min-width: 120px; padding: 10px 14px; }
.gc-stat .stat-label { font-size: 12px; margin-top: 2px; }
.filter-card { margin-bottom: 16px; }
.filter-card :deep(.el-form-item) { margin-bottom: 8px; }
.queue-head-actions { display: flex; align-items: center; gap: 8px; }

.flex-between, .row-between { display: flex; align-items: center; justify-content: space-between; }
.mb10 { margin-bottom: 10px; }
.ml4 { margin-left: 4px; }
.tip { color: #909399; font-size: 12px; }

.queue-card :deep(.el-card__body) { padding-top: 12px; }
.sub-list { max-height: calc(100vh - 300px); min-height: 320px; overflow-y: auto; }
.sub-item {
  cursor: pointer; border: 1px solid #ebeef5; border-radius: 8px;
  margin-bottom: 8px; padding: 10px 12px; transition: all .18s;
}
.sub-item:hover { border-color: #a5c4f0; background: #f7fafd; }
.sub-item.active {
  border-color: var(--el-color-primary); background: var(--el-color-primary-light-9);
  box-shadow: inset 3px 0 0 var(--el-color-primary);
}
.name-line { display: flex; align-items: center; gap: 6px; min-width: 0; }
.name { font-weight: 600; font-size: 14px; }

.batch-bar {
  display: flex; align-items: center; justify-content: space-between; gap: 8px;
  background: #f0f6ff; border: 1px solid #d9e8ff; border-radius: 6px;
  padding: 6px 10px; margin-bottom: 10px;
}
.batch-actions { display: flex; gap: 6px; }
.load-more { text-align: center; padding: 8px 0; }
.kb-tip { line-height: 1.8; font-size: 12px; }
.task {
  margin: 4px 0 6px; color: #606266; font-size: 12px;
  overflow: hidden; text-overflow: ellipsis; white-space: nowrap;
}
.score { color: var(--el-color-primary); font-weight: 600; font-size: 13px; }

/* ---- 批改工作区 ---- */
.grading-card :deep(.el-card__header) { padding: 12px 18px; }
.student-info { display: flex; align-items: baseline; gap: 10px; min-width: 0; }
.student-name { font-size: 16px; }
.task-name {
  color: #909399; font-size: 13px; overflow: hidden;
  text-overflow: ellipsis; white-space: nowrap; max-width: 320px;
}
.head-tags { display: flex; gap: 6px; flex-shrink: 0; }

.progress-bar {
  position: sticky; top: 0; z-index: 3; background: #fff;
  padding: 8px 0 10px; margin-bottom: 8px; border-bottom: 1px solid #f0f2f5;
}
.progress-info { display: flex; justify-content: space-between; font-size: 13px; margin-bottom: 6px; }

.q-item {
  padding: 12px 14px; border: 1px solid #ebeef5; border-radius: 8px; margin-bottom: 12px;
  transition: border-color .2s, background .2s;
}
.q-item.scored { border-left: 3px solid #67c23a; background: #fbfefb; }
.q-head { display: flex; align-items: center; gap: 8px; margin-bottom: 10px; flex-wrap: wrap; }
.q-no {
  width: 24px; height: 24px; line-height: 24px; text-align: center;
  background: #2f6fd0; color: #fff; border-radius: 50%; font-size: 12px; font-weight: 600;
  flex-shrink: 0;
}
.q-score-panel { margin-left: auto; display: flex; align-items: center; gap: 8px; }
.full-score { font-size: 12px; color: #909399; }

.q-body { display: flex; gap: 14px; }
.q-col.q-detail { flex: 1; min-width: 0; }
.q-col.q-grade { width: 260px; flex-shrink: 0; }
.content, .correct, .kp, .ai-comment, .err-points {
  margin: 5px 0; line-height: 1.65; font-size: 13px;
}
.content .ans {
  display: inline-block; background: #f5f7fa; padding: 1px 8px; border-radius: 4px;
  color: #303133;
}
.correct .std {
  display: inline-block; background: #f0f9eb; color: #529b2e;
  padding: 1px 8px; border-radius: 4px; font-weight: 600;
}
.ai-comment { color: #2f6fd0; background: #f0f6ff; padding: 6px 10px; border-radius: 6px; }
.err-points { color: #f56c6c; }

.footer-bar {
  position: sticky; bottom: 0; z-index: 3; background: #fff;
  padding: 12px 0 4px; border-top: 1px solid #ebeef5;
  display: flex; align-items: center; justify-content: space-between; gap: 12px;
  flex-wrap: wrap;
}
.footer-total { font-size: 14px; }
.total { color: var(--el-color-primary); font-size: 20px; }
.footer-actions { display: flex; gap: 8px; flex-wrap: wrap; }

@media (max-width: 1100px) {
  .q-body { flex-direction: column; }
  .q-col.q-grade { width: 100%; }
}
</style>
