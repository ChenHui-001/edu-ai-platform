<template>
  <div class="page-container">
    <div class="page-header">
      <h2 class="page-title">知识诊断</h2>
      <div>
        <el-button v-if="session" :icon="Refresh" @click="resetAll">重新诊断</el-button>
        <el-button v-if="session" :icon="Refresh" :loading="loading" @click="refreshSession">
          刷新进度
        </el-button>
      </div>
    </div>

    <el-alert
      type="info"
      show-icon
      :closable="false"
      class="mb16"
      title="诊断结果只用于定位薄弱起点与先修路径，不会改写正式掌握度"
      description="系统按先修关系逐层追问：答错会回溯更基础的先修点，连续答对达到确认次数才判定掌握。"
    />

    <!-- 诊断设置 -->
    <el-row v-if="!session" :gutter="16">
      <el-col :xs="24" :lg="16">
        <el-card shadow="never" v-loading="loading">
          <template #header><b>选择诊断范围</b></template>
          <el-form label-width="96px">
            <el-form-item label="学科">
              <el-select v-model="subjectId" style="width:220px" placeholder="选择学科"
                         @change="onSubjectChange">
                <el-option v-for="s in subjects" :key="s.id" :label="s.name" :value="s.id" />
              </el-select>
              <span class="tip ml8">仅列出本年级、且已有题目的知识点</span>
            </el-form-item>
            <el-form-item label="检索">
              <el-input v-model="keyword" placeholder="按知识点或章节名称过滤"
                        clearable style="width:280px" @keyup.enter="loadTargets"
                        @clear="loadTargets" />
              <el-button class="ml8" :loading="targetsLoading" @click="loadTargets">查询</el-button>
            </el-form-item>
            <el-form-item label="目标知识点">
              <div class="target-box" v-loading="targetsLoading">
                <div class="target-toolbar">
                  <el-checkbox
                    :model-value="allChecked"
                    :indeterminate="someChecked"
                    @change="toggleAll"
                  >全选当前结果</el-checkbox>
                  <span class="tip">已选 {{ targetIds.length }} / {{ targets.length }}</span>
                </div>
                <el-checkbox-group v-model="targetIds" class="target-list">
                  <el-checkbox v-for="t in targets" :key="t.id" :value="t.id" class="target-item">
                    <span class="target-name">{{ t.name }}</span>
                    <span class="tip">{{ t.chapter || '未分章节' }} · {{ t.question_count }} 题</span>
                  </el-checkbox>
                </el-checkbox-group>
                <el-empty v-if="!targetsLoading && !targets.length" :image-size="60"
                          description="该学科暂无可诊断知识点" />
              </div>
            </el-form-item>
            <el-form-item label="诊断模式">
              <el-radio-group v-model="mode">
                <el-radio value="target">目标诊断（围绕所选知识点及其先修）</el-radio>
                <el-radio value="screen">范围筛查（在所选知识点内快速排查）</el-radio>
              </el-radio-group>
            </el-form-item>
            <el-row :gutter="16">
              <el-col :span="12">
                <el-form-item label="最大题量">
                  <el-input-number v-model="limit" :min="1" :max="100" style="width:100%" />
                </el-form-item>
              </el-col>
              <el-col :span="12">
                <el-form-item label="确认次数">
                  <el-input-number v-model="confirmCount" :min="1" :max="10" style="width:100%" />
                </el-form-item>
              </el-col>
            </el-row>
            <el-form-item>
              <el-button type="primary" :loading="starting" :disabled="!targetIds.length"
                         @click="startSession">开始诊断</el-button>
              <span class="tip ml8">最多选择 30 个目标知识点</span>
            </el-form-item>
          </el-form>
        </el-card>
      </el-col>

      <el-col :xs="24" :lg="8">
        <el-card shadow="never" class="mb16">
          <template #header><b>诊断规则</b></template>
          <ul class="rule-list">
            <li>硬先修优先于软先修，先补基础再判断目标。</li>
            <li>连续答对 3 题（可调）才判为掌握；中途答错会清零重测。</li>
            <li>答错后自动加入直接先修点，定位「根因」而不是只记错题。</li>
            <li>诊断只给出建议路径，不写入正式掌握度。</li>
          </ul>
        </el-card>
        <el-card shadow="never">
          <template #header><b>两种模式</b></template>
          <p class="mode-desc"><b>目标诊断：</b>适合「这一章没学懂」，系统会向下追溯先修链，题量默认 16。</p>
          <p class="mode-desc"><b>范围筛查：</b>适合开学/单元前摸底，只在所选知识点内排查，题量默认 40。</p>
        </el-card>
      </el-col>
    </el-row>

    <!-- 诊断进行中 / 结果 -->
    <template v-else>
      <el-card shadow="never" class="mb16">
        <div class="progress-head">
          <div>
            <b>诊断进度</b>
            <el-tag size="small" class="ml8" effect="plain">
              {{ session.mode === 'screen' ? '范围筛查' : '目标诊断' }}
            </el-tag>
            <span class="tip ml8">{{ subjectName }} · 会话 #{{ session.id }}</span>
          </div>
          <span class="tip">已作答 {{ session.asked }} / {{ session.limit }} 题</span>
        </div>
        <el-progress :percentage="Math.min(100, session.progress || 0)" :stroke-width="10" />
      </el-card>

      <el-row :gutter="16">
        <el-col :xs="24" :lg="15">
          <el-card v-if="current" shadow="never" v-loading="answering">
            <template #header>
              <div class="q-head">
                <b>第 {{ session.asked + 1 }} 题</b>
                <div>
                  <el-tag v-if="current.chapter" size="small" type="info" effect="plain">
                    {{ current.chapter }}
                  </el-tag>
                  <el-tag size="small" class="ml8" effect="plain">{{ current.name }}</el-tag>
                </div>
              </div>
            </template>

            <div class="q-stem">{{ current.question.stem }}</div>

            <el-radio-group
              v-if="['single', 'multiple', 'judge'].includes(current.question.type)"
              v-model="answer" class="option-list"
            >
              <el-radio
                v-for="opt in current.question.options"
                :key="opt.key"
                :value="opt.key"
                class="option-item"
              >
                <b>{{ opt.key }}.</b> {{ opt.text }}
              </el-radio>
              <el-empty v-if="!current.question.options.length" :image-size="50"
                        description="该题缺少选项，可直接跳过" />
            </el-radio-group>

            <el-input
              v-else-if="current.question.type === 'blank'"
              v-model="answer"
              placeholder="填写答案"
              class="answer-input"
              @keyup.enter="submit()"
            />

            <template v-else>
              <el-input v-model="answer" type="textarea" :rows="3"
                        placeholder="可写出你的解答过程（本题按自评计分）" />
              <div class="self-tip">本题没有可自动判分的标准答案，请完成后按真实情况自评。</div>
            </template>

            <div class="q-actions">
              <el-button v-if="current.question.type !== 'short'" type="primary"
                         :loading="answering" @click="submit()">提交答案</el-button>
              <template v-else>
                <el-button type="success" :loading="answering" @click="submit('correct')">
                  我已掌握
                </el-button>
                <el-button type="danger" plain :loading="answering" @click="submit('wrong')">
                  还没掌握
                </el-button>
              </template>
              <el-button :disabled="answering" @click="submit('skip')">跳过本题</el-button>
            </div>

            <el-alert v-if="feedback" class="mt12" :closable="false" show-icon
                      :type="feedbackType" :title="feedbackTitle">
              <div v-if="feedback.reference_answer" class="feedback-row">
                <b>参考答案：</b>{{ formatAnswer(feedback.reference_answer) }}
              </div>
              <div v-if="feedback.analysis" class="feedback-row">
                <b>解析：</b>{{ feedback.analysis }}
              </div>
              <div class="feedback-row">
                知识点「{{ current.name }}」需要连续答对 {{ session.confirm }} 题才会判为掌握。
              </div>
            </el-alert>

            <div v-if="feedback" class="q-actions">
              <el-button v-if="pendingNext" type="primary" @click="goNext">下一题</el-button>
              <el-button v-else type="success" @click="finish">查看诊断结果</el-button>
            </div>
          </el-card>

          <el-card v-else shadow="never">
            <el-empty :image-size="80" description="本次诊断已结束">
              <el-button type="primary" @click="finish">查看诊断结果</el-button>
            </el-empty>
          </el-card>
        </el-col>

        <el-col :xs="24" :lg="9">
          <el-card shadow="never" class="mb16">
            <template #header><b>实时画像</b></template>
            <div class="mini-stats">
              <div class="mini-stat">
                <span class="mini-value" style="color:var(--el-color-success)">
                  {{ summary.counts?.mastered || 0 }}
                </span>
                <span class="tip">已掌握</span>
              </div>
              <div class="mini-stat">
                <span class="mini-value" style="color:var(--el-color-warning)">
                  {{ summary.counts?.shaky || 0 }}
                </span>
                <span class="tip">待确认</span>
              </div>
              <div class="mini-stat">
                <span class="mini-value" style="color:var(--el-color-danger)">
                  {{ summary.counts?.weak || 0 }}
                </span>
                <span class="tip">薄弱</span>
              </div>
              <div class="mini-stat">
                <span class="mini-value">{{ summary.counts?.untested || 0 }}</span>
                <span class="tip">未测</span>
              </div>
            </div>
            <el-divider />
            <div class="section-title">薄弱根因</div>
            <div v-if="summary.roots?.length" class="root-list">
              <div v-for="r in summary.roots" :key="r.id" class="root-item">
                <el-tag type="danger" size="small" effect="plain">{{ r.name }}</el-tag>
                <span v-if="r.pending_prereqs?.length" class="tip">
                  待测先修：{{ r.pending_prereqs.map(p => p.name).join('、') }}
                </span>
                <span v-else class="tip">先修已排查</span>
              </div>
            </div>
            <div v-else class="tip">暂无根因，继续作答后生成。</div>
          </el-card>

          <el-card shadow="never">
            <template #header><b>章节排查</b></template>
            <div v-if="summary.chapters?.length" class="chapter-list">
              <div v-for="c in summary.chapters" :key="c.chapter" class="chapter-item">
                <div class="chapter-head">
                  <span>{{ c.chapter }}</span>
                  <span class="tip">薄弱 {{ c.weak }} / 待确认 {{ c.shaky }} / 掌握 {{ c.mastered }}</span>
                </div>
                <el-progress
                  :percentage="chapterPercent(c)"
                  :stroke-width="6"
                  :color="chapterColor(c)"
                />
              </div>
            </div>
            <div v-else class="tip">暂无章节数据。</div>
          </el-card>
        </el-col>
      </el-row>

      <el-card v-if="summary.finished" shadow="never" class="mt16">
        <template #header>
          <div class="flex-between">
            <b>诊断结果与建议路径</b>
            <div>
              <el-tag v-if="summary.limit_reached" type="warning" size="small">已达到题量上限</el-tag>
              <el-tag v-else type="success" size="small">诊断完成</el-tag>
            </div>
          </div>
        </template>

        <el-row :gutter="12" class="mb16">
          <el-col :span="6" v-for="card in summaryCards" :key="card.key">
            <div class="stat-card--flat">
              <div class="stat-value" :style="{ color: card.color }">{{ card.value }}</div>
              <div class="stat-label">{{ card.label }}</div>
            </div>
          </el-col>
        </el-row>

        <div class="section-title">建议学习顺序</div>
        <div v-if="summary.path?.length" class="path-list">
          <div v-for="(p, idx) in summary.path" :key="p.id" class="path-row">
            <span class="path-index">{{ idx + 1 }}</span>
            <el-tag size="small" :type="statusTag(p.status)">{{ statusLabel(p.status) }}</el-tag>
            <span class="path-name">{{ p.name }}</span>
            <el-tag v-if="p.is_root" size="small" type="danger" effect="plain">根因</el-tag>
            <el-tag v-if="p.is_target" size="small" effect="plain">目标</el-tag>
            <span class="tip">{{ p.chapter || '未分章节' }}</span>
          </div>
        </div>
        <div v-else class="tip">本次没有需要补学的节点。</div>

        <el-row :gutter="16" class="mt16">
          <el-col :span="12">
            <div class="section-title">待测先修</div>
            <div v-if="summary.pending?.length" class="tag-wrap">
              <el-tag v-for="p in summary.pending" :key="p.id" type="warning" effect="plain">
                {{ p.name }}
              </el-tag>
            </div>
            <div v-else class="tip">无。</div>
          </el-col>
          <el-col :span="12">
            <div class="section-title">已掌握</div>
            <div v-if="summary.mastered?.length" class="tag-wrap">
              <el-tag v-for="p in summary.mastered" :key="p.id" type="success" effect="plain">
                {{ p.name }}
              </el-tag>
            </div>
            <div v-else class="tip">暂无。</div>
          </el-col>
        </el-row>

        <el-alert class="mt16" type="warning" :closable="false" show-icon
                  title="诊断结论不写入正式掌握度"
                  description="如需巩固，可前往「学习路径」按建议顺序练习，或在「掌握图谱」查看正式学习数据。" />
        <div class="mt12">
          <el-button type="primary" @click="resetAll">再测一次</el-button>
          <el-button @click="goLearning">去学习路径</el-button>
        </div>
      </el-card>
    </template>
  </div>
</template>

<script setup>
import { computed, onMounted, ref } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { Refresh } from '@element-plus/icons-vue'
import { knowledgeApi } from '@/api'
import { fetchSubjects, currentGradeId, resolveSubjectId } from '@/utils/subject'

const router = useRouter()
const gradeId = currentGradeId()

const loading = ref(false)
const starting = ref(false)
const answering = ref(false)
const targetsLoading = ref(false)

const subjects = ref([])
const subjectId = ref(null)
const keyword = ref('')
const targets = ref([])
const targetIds = ref([])
const mode = ref('target')
const limit = ref(16)
const confirmCount = ref(3)

const session = ref(null)
const current = ref(null)
const answer = ref('')
const feedback = ref(null)
const pendingNext = ref(null)
const summary = ref({})

const subjectName = computed(() => (
  subjects.value.find(s => s.id === subjectId.value)?.name || '本学科'
))

const allChecked = computed(() => (
  targets.value.length > 0 && targetIds.value.length === targets.value.length
))
const someChecked = computed(() => (
  targetIds.value.length > 0 && targetIds.value.length < targets.value.length
))

const feedbackType = computed(() => {
  if (!feedback.value) return 'info'
  if (feedback.value.result === 'correct') return 'success'
  if (feedback.value.result === 'wrong') return 'error'
  return 'info'
})

const feedbackTitle = computed(() => {
  if (!feedback.value) return ''
  if (feedback.value.result === 'correct') return '回答正确'
  if (feedback.value.result === 'wrong') return '回答错误，已加入先修复查'
  return '已跳过本题'
})

const summaryCards = computed(() => [
  { key: 'mastered', label: '已掌握', value: summary.value.counts?.mastered || 0, color: '#67c23a' },
  { key: 'shaky', label: '待确认', value: summary.value.counts?.shaky || 0, color: '#e6a23c' },
  { key: 'weak', label: '薄弱', value: summary.value.counts?.weak || 0, color: '#f56c6c' },
  { key: 'untested', label: '未测', value: summary.value.counts?.untested || 0, color: '#909399' }
])

function statusLabel(status) {
  return { mastered: '已掌握', shaky: '待确认', weak: '薄弱', unknown: '未测' }[status] || '未测'
}

function statusTag(status) {
  return { mastered: 'success', shaky: 'warning', weak: 'danger', unknown: 'info' }[status] || 'info'
}

function chapterPercent(c) {
  if (!c.total) return 0
  return Math.round((c.mastered / c.total) * 100)
}

function chapterColor(c) {
  if (c.weak) return '#f56c6c'
  if (c.shaky) return '#e6a23c'
  return '#67c23a'
}

function formatAnswer(value) {
  if (value === null || value === undefined || value === '') return '-'
  if (typeof value === 'object') return JSON.stringify(value)
  return String(value)
}

async function loadSubjects() {
  subjects.value = await fetchSubjects({ gradeId, distinct: true })
  if (!subjects.value.length) return
  const math = subjects.value.find(s => s.name.includes('数学'))
  subjectId.value = (math || subjects.value[0]).id
  await onSubjectChange()
}

async function onSubjectChange() {
  targetIds.value = []
  await loadTargets()
}

async function loadTargets() {
  if (!subjectId.value || !gradeId) return
  targetsLoading.value = true
  try {
    const resolved = resolveSubjectId(subjects.value, subjectId.value, gradeId)
    const res = await knowledgeApi.diagnosisTargets({
      grade_id: gradeId,
      subject_id: resolved,
      keyword: keyword.value || undefined
    })
    targets.value = res.data?.items || []
    targetIds.value = targetIds.value.filter(id => targets.value.some(t => t.id === id))
  } finally {
    targetsLoading.value = false
  }
}

function toggleAll(checked) {
  targetIds.value = checked ? targets.value.map(t => t.id) : []
}

function resetAll() {
  session.value = null
  current.value = null
  answer.value = ''
  feedback.value = null
  pendingNext.value = null
  summary.value = {}
  limit.value = 16
  confirmCount.value = 3
  mode.value = 'target'
}

async function startSession() {
  if (!targetIds.value.length) {
    ElMessage.warning('请先选择目标知识点')
    return
  }
  if (targetIds.value.length > 30) {
    ElMessage.warning('单次诊断最多选择 30 个目标知识点')
    return
  }
  starting.value = true
  try {
    const res = await knowledgeApi.createDiagnosisSession({
      subject_id: resolveSubjectId(subjects.value, subjectId.value, gradeId),
      target_kp_ids: targetIds.value,
      mode: mode.value,
      limit: limit.value,
      confirm: confirmCount.value
    })
    applySession(res.data)
    ElMessage.success('诊断会话已创建')
  } finally {
    starting.value = false
  }
}

function applySession(data) {
  session.value = data
  summary.value = data.summary || {}
  current.value = data.next || null
  pendingNext.value = null
  answer.value = ''
  feedback.value = null
}

async function refreshSession() {
  if (!session.value) return
  loading.value = true
  try {
    const res = await knowledgeApi.diagnosisSession(session.value.id)
    applySession(res.data)
  } finally {
    loading.value = false
  }
}

async function submit(override) {
  if (!current.value) return
  if (!override && !String(answer.value || '').trim()) {
    ElMessage.warning('请先作答，或选择跳过本题')
    return
  }
  answering.value = true
  try {
    const res = await knowledgeApi.answerDiagnosis(session.value.id, {
      knowledge_point_id: current.value.knowledge_point_id,
      question_id: current.value.question.id,
      answer: answer.value,
      result: override
    })
    feedback.value = res.data
    summary.value = res.data.summary || summary.value
    session.value.asked = res.data.asked
    session.value.progress = Math.min(
      100,
      Math.round((res.data.asked / Math.max(1, session.value.limit)) * 1000) / 10
    )
    pendingNext.value = res.data.next || null
    if (!pendingNext.value) session.value.finished = true
  } finally {
    answering.value = false
  }
}

function goNext() {
  if (!pendingNext.value) return
  current.value = pendingNext.value
  pendingNext.value = null
  answer.value = ''
  feedback.value = null
}

async function finish() {
  if (!session.value) return
  try {
    const res = await knowledgeApi.diagnosisSummary(session.value.id)
    summary.value = res.data || {}
    current.value = null
    pendingNext.value = null
  } catch {
    summary.value = { ...summary.value, finished: true }
  }
}

function goLearning() {
  router.push('/student/path')
}

onMounted(async () => {
  if (!gradeId) {
    ElMessage.warning('当前账号未设置年级，无法使用知识诊断')
    return
  }
  await loadSubjects()
})
</script>

<style scoped>
.mb16 { margin-bottom: 16px; }
.mt12 { margin-top: 12px; }
.mt16 { margin-top: 16px; }
.ml8 { margin-left: 8px; }
.tip { color: var(--el-text-color-secondary); font-size: 12px; }
.flex-between { display: flex; align-items: center; justify-content: space-between; }
.target-box {
  width: 100%;
  border: 1px solid var(--el-border-color-light);
  border-radius: 6px;
  padding: 10px 12px;
}
.target-toolbar {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding-bottom: 8px;
  border-bottom: 1px dashed var(--el-border-color-lighter);
}
.target-list {
  display: flex;
  flex-direction: column;
  max-height: 320px;
  overflow-y: auto;
  padding-top: 8px;
}
.target-item { width: 100%; height: 30px; }
.target-name { margin-right: 10px; }
.rule-list { margin: 0; padding-left: 18px; line-height: 1.9; font-size: 13px; }
.mode-desc { margin: 0 0 8px; font-size: 13px; line-height: 1.7; }
.progress-head {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 8px;
}
.q-head { display: flex; justify-content: space-between; align-items: center; }
.q-stem { font-size: 15px; line-height: 1.8; margin-bottom: 16px; white-space: pre-wrap; }
.option-list { display: flex; flex-direction: column; align-items: stretch; gap: 8px; }
.option-item {
  height: auto;
  padding: 8px 12px;
  border: 1px solid var(--el-border-color-light);
  border-radius: 6px;
  margin-right: 0;
  white-space: normal;
}
.option-item :deep(.el-radio__label) { white-space: normal; line-height: 1.6; }
.answer-input { max-width: 360px; }
.self-tip { margin-top: 8px; font-size: 12px; color: var(--el-color-warning); }
.q-actions { margin-top: 16px; display: flex; gap: 8px; }
.feedback-row { margin-top: 6px; font-size: 13px; line-height: 1.7; }
.mini-stats { display: flex; justify-content: space-between; }
.mini-stat { display: flex; flex-direction: column; align-items: center; gap: 4px; }
.mini-value { font-size: 22px; font-weight: 600; }
.section-title { font-weight: 600; margin: 12px 0 8px; }
.root-list { display: flex; flex-direction: column; gap: 8px; }
.root-item { display: flex; flex-direction: column; gap: 4px; }
.chapter-list { display: flex; flex-direction: column; gap: 12px; }
.chapter-head {
  display: flex;
  justify-content: space-between;
  font-size: 13px;
  margin-bottom: 4px;
}
.path-list { display: flex; flex-direction: column; gap: 8px; }
.path-row { display: flex; align-items: center; gap: 8px; font-size: 13px; }
.path-index {
  width: 22px;
  height: 22px;
  border-radius: 50%;
  background: var(--el-color-primary-light-9);
  color: var(--el-color-primary);
  display: inline-flex;
  align-items: center;
  justify-content: center;
  font-size: 12px;
}
.path-name { font-weight: 500; }
.tag-wrap { display: flex; flex-wrap: wrap; gap: 6px; }
</style>
