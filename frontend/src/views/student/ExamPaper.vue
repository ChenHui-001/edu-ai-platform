<template>
  <div class="exam-page" v-loading="loading">
    <template v-if="state === 'answering'">
      <!-- 顶部答题栏 -->
      <div class="bar">
        <div class="bar-info">
          <span class="title">{{ task.title }}</span>
          <el-tag size="small" type="danger">限时 {{ task.duration }} 分钟</el-tag>
          <el-tag size="small">总分 {{ task.total_score }}</el-tag>
        </div>
        <div class="bar-progress">
          <span>已答 {{ answeredCount }}/{{ items.length }}</span>
          <el-progress :percentage="progress" :stroke-width="10" style="width:140px" />
        </div>
        <div class="bar-actions">
          <span class="countdown" :class="{ warn: remain < 300, urgent: remain < 60 }">
            <el-icon><Timer /></el-icon>
            <span class="cd-label">剩余</span> {{ formatTime(remain) }}
          </span>
          <el-badge :value="items.length - answeredCount" :hidden="answeredCount === items.length"
                    type="warning">
            <el-button type="danger" plain :icon="DocumentChecked"
                       @click="submitVisible = true">交卷</el-button>
          </el-badge>
        </div>
      </div>

      <!-- 题号导航 -->
      <div class="nav-bar">
        <span class="nav-label">题号</span>
        <span
          v-for="(it, i) in items" :key="it.paper_item_id"
          class="nav-item" :class="[stateOf(i), { current: activeIndex === i }]"
          @click="scrollTo(i)"
        >{{ i + 1 }}</span>
      </div>

      <!-- 题目 -->
      <div class="body">
        <div v-for="(it, i) in items" :key="it.paper_item_id" :ref="(el) => setItemRef(el, i)"
             class="q-card" :class="{ answered: isAnswered(it) }">
          <div class="q-head">
            <span class="q-no">{{ i + 1 }}</span>
            <el-tag size="small">{{ TYPE_LABEL[it.type] || it.type }}</el-tag>
            <span class="q-score">{{ it.score }} 分</span>
            <el-tag v-if="answered.includes(it.paper_item_id)" size="small" type="success" effect="plain">已答</el-tag>
          </div>
          <div class="q-stem" v-html="it.stem"></div>

          <!-- 选择题 -->
          <el-radio-group v-if="['single','judge'].includes(it.type)"
                          v-model="answers[it.paper_item_id]" class="opts">
            <el-radio v-for="o in parseOpts(it.options)" :key="o.key" :value="o.key" border class="opt">
              {{ o.key }}. {{ o.text }}
            </el-radio>
          </el-radio-group>

          <el-checkbox-group v-else-if="it.type === 'multiple'"
                              v-model="multiAnswers[it.paper_item_id]" class="opts">
            <el-checkbox v-for="o in parseOpts(it.options)" :key="o.key" :value="o.key" border class="opt">
              {{ o.key }}. {{ o.text }}
            </el-checkbox>
          </el-checkbox-group>

          <!-- 填空 / 主观 -->
          <el-input v-else-if="it.type === 'blank'" v-model="answers[it.paper_item_id]"
                    placeholder="请输入答案" />
          <el-input v-else v-model="answers[it.paper_item_id]" type="textarea" :rows="4"
                    :placeholder="`请作答（${(answers[it.paper_item_id] || '').length} 字）`" />
        </div>
      </div>
    </template>

    <!-- 结果页 -->
    <template v-else-if="state === 'result'">
      <div class="result-hero" :class="result.is_passed ? 'pass' : 'fail'">
        <div class="hero-score">{{ result.score }}</div>
        <div class="hero-label">分</div>
        <div class="hero-meta">
          <span>总分 {{ task.total_score }}</span>
          <span>客观题 {{ result.objective_score }}</span>
          <span v-if="result.class_rank">班级排名 第 {{ result.class_rank }} 名</span>
          <el-tag :type="result.is_passed ? 'success' : 'danger'" size="large">
            {{ result.is_passed ? '合格' : '未合格' }}
          </el-tag>
        </div>
        <div class="hero-actions">
          <el-button @click="$router.push('/student/exams')">返回列表</el-button>
          <el-button type="primary" @click="$router.push('/student/wrong')">查看错题本</el-button>
        </div>
      </div>

      <div class="result-body">
        <el-alert v-if="hasSubjective && !result.published"
                  type="info" :closable="false" show-icon class="mb8"
                  title="主观题已提交，等待教师批改；成绩发布后可在成绩中心查看最终分数" />
        <el-alert v-if="hasSubjective && !result.published"
                  type="info" :closable="false" show-icon class="mb8"
                  title="主观题已提交，等待教师批改；成绩发布后可在成绩中心查看最终分数" />
        <div class="summary-bar" v-if="grading">
          正确 {{ grading.correct_count }}/{{ grading.total }} 题 ·
          正确率 {{ grading.accuracy }}% · 得分率 {{ grading.score_rate }}%
        </div>

        <div v-for="(it, i) in items" :key="it.paper_item_id" class="r-card"
             :class="isRight(it) ? 'ok' : 'ng'">
          <div class="r-head">
            <span class="r-no">{{ i + 1 }}</span>
            <el-icon class="r-icon"><CircleCheckFilled v-if="isRight(it)" /><CircleCloseFilled v-else /></el-icon>
            <span class="r-score">{{ scoreOf(it) }}/{{ it.score }}</span>
            <el-tag size="small" :type="isRight(it) ? 'success' : 'danger'">
              {{ isRight(it) ? '正确' : '错误' }}
            </el-tag>
          </div>
          <div class="q-stem" v-html="it.stem"></div>
          <div class="r-answers">
            <div><b>你的答案：</b>{{ myAnswer(it) || '未作答' }}</div>
            <div v-if="it.answer" style="color:#67c23a"><b>正确答案：</b>{{ fmt(it.answer) }}</div>
          </div>
          <div v-if="it.analysis" class="r-analysis"><b>解析：</b>{{ it.analysis }}</div>
        </div>
      </div>
    </template>

    <el-empty v-else-if="!loading" description="任务不可用" />

    <!-- 交卷确认 -->
    <el-dialog v-model="submitVisible" title="确认交卷" width="440px">
      <p>你已完成 <b>{{ answeredCount }}</b> / {{ items.length }} 题。</p>
      <el-alert v-if="answeredCount < items.length" type="warning" :closable="false" show-icon
                class="mb8"
                :title="`还有 ${items.length - answeredCount} 题未作答，未答题计 0 分`" />
      <el-alert v-if="hasSubjective" type="info" :closable="false" show-icon
                title="含主观题，交卷后需教师批改，成绩稍后发布" />
      <el-input v-if="task.anti_cheat && switchCount > 0" type="textarea" :rows="2" readonly
                style="margin-top:10px" :model-value="`检测到答题期间切换页面 ${switchCount} 次，已记录`" />
      <template #footer>
        <el-button @click="submitVisible = false">继续答题</el-button>
        <el-button type="primary" @click="doSubmit">确认交卷</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { computed, nextTick, onBeforeUnmount, onMounted, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { CircleCheckFilled, CircleCloseFilled, DocumentChecked, Timer } from '@element-plus/icons-vue'
import { taskApi } from '@/api'

const route = useRoute()
const router = useRouter()
const taskId = route.params.taskId

const TYPE_LABEL = {
  single: '单选题', multiple: '多选题', judge: '判断题', blank: '填空题',
  short: '简答题', calc: '计算题', material: '材料分析题', composition: '作文题'
}

const loading = ref(false)
const state = ref('answering')
const task = ref({})
const items = ref([])
const answers = ref({})
const multiAnswers = ref({})
const remain = ref(0)
const switchCount = ref(0)
const result = ref({})
const grading = ref(null)
const submitVisible = ref(false)
const itemRefs = ref([])
const submitted = ref(false)
const activeIndex = ref(0)          // 当前可视题号（导航同步高亮）
const draftTipShown = ref(false)    // 草稿提示只弹一次
const hasSubjective = computed(() =>
  items.value.some(it => !['single', 'multiple', 'judge', 'blank'].includes(it.type)))

const answered = computed(() => {
  const ids = []
  items.value.forEach(it => {
    const v = it.type === 'multiple'
      ? (multiAnswers.value[it.paper_item_id] || []).length
      : (answers.value[it.paper_item_id] || '').toString().trim().length
    if (v > 0) ids.push(it.paper_item_id)
  })
  return ids
})

const answeredCount = computed(() => answered.value.length)
const progress = computed(() =>
  items.value.length ? Math.round((answeredCount.value / items.value.length) * 100) : 0)

let timer = null
let heartbeatTimer = null
const start = ref(0)

/** 当前可视题目同步到题号导航。
 * 内容区是 .el-main 内部滚动，普通 window scroll 监听收不到；
 * 用**捕获阶段**监听（第三个参数 true）可捕获任意滚动容器的 scroll，
 * 这是最可靠的兼容写法（IntersectionObserver 实测也未触发）。 */
function onScroll() {
  if (state.value !== 'answering') return
  // 直接查 DOM：函数式 ref 曾因未传索引而失效（:ref="setItemRef" 收不到 i），
  // itemRefs 恒空导致本函数第一行就 return、点击题号也不跳转。
  const cards = document.querySelectorAll('.q-card')
  if (!cards.length) return
  const anchor = window.innerHeight * 0.35
  let idx = 0
  cards.forEach((el, i) => {
    if (el.getBoundingClientRect().top <= anchor) idx = i
  })
  activeIndex.value = idx
}

function setItemRef(el, i) { if (el) itemRefs.value[i] = el }
function scrollTo(i) {
  document.querySelectorAll('.q-card')[i]?.scrollIntoView({ behavior: 'smooth', block: 'start' })
}
function stateOf(i) {
  const it = items.value[i]
  if (!answered.value.includes(it.paper_item_id)) return 'todo'
  return answers.value[it.paper_item_id] || multiAnswers.value[it.paper_item_id] ? 'done' : 'todo'
}
function isAnswered(it) { return answered.value.includes(it.paper_item_id) }
function isRight(it) {
  const a = result.value.answers || []
  return a.some(x => x.paper_item_id === it.paper_item_id && x.is_correct)
}
function scoreOf(it) {
  const a = (result.value.answers || []).find(x => x.paper_item_id === it.paper_item_id)
  return a ? a.score : 0
}
function myAnswer(it) {
  return it.type === 'multiple'
    ? (multiAnswers.value[it.paper_item_id] || []).join('')
    : answers.value[it.paper_item_id]
}
function parseOpts(v) {
  if (!v) return []
  if (Array.isArray(v)) return v
  try { return JSON.parse(v) } catch { return [] }
}
function fmt(v) { return Array.isArray(v) ? v.join('') : v }

function formatTime(s) {
  const m = Math.floor(s / 60), sec = s % 60
  return `${String(m).padStart(2, '0')}:${String(sec).padStart(2, '0')}`
}

// 草稿：刷新不丢答案
const draftKey = `answer_draft_${taskId}`
function saveDraft() {
  localStorage.setItem(draftKey, JSON.stringify({
    answers: answers.value, multiAnswers: multiAnswers.value, savedAt: Date.now()
  }))
}
function loadDraft() {
  try {
    const d = localStorage.getItem(draftKey)
    if (!d) return false
    const p = JSON.parse(d)
    // 30 分钟内的草稿才恢复
    if (Date.now() - p.savedAt > 30 * 60 * 1000) { localStorage.removeItem(draftKey); return false }
    answers.value = p.answers || {}
    multiAnswers.value = p.multiAnswers || {}
    return true
  } catch { return false }
}

async function load() {
  loading.value = true
  try {
    const res = await taskApi.taskPaper(taskId)
    task.value = res.data.task
    items.value = res.data.items

    if (loadDraft()) ElMessage.success('已恢复未提交的草稿答案')

    remain.value = (task.value.duration || 60) * 60
    start.value = Date.now()

    // 倒计时
    timer = setInterval(() => {
      remain.value--
      if (remain.value <= 0) {
        clearInterval(timer)
        ElMessage.warning('考试时间到，系统自动交卷')
        doSubmit(true)
      }
    }, 1000)

    // 心跳：保存时长 + 切屏检测
    heartbeatTimer = setInterval(() => sendHeartbeat(false), 30000)

    // 防切屏（仅在开启防作弊时监听）
    if (task.value.anti_cheat) {
      document.addEventListener('visibilitychange', onVisibility)
    }
    // 捕获阶段监听：任何滚动容器（含 .el-main）的 scroll 都能收到
    window.addEventListener('scroll', onScroll, true)
    nextTick(() => onScroll())
  } catch (e) {
    state.value = 'empty'
  } finally {
    loading.value = false
  }
}

function onVisibility() {
  if (document.hidden && state.value === 'answering') {
    sendHeartbeat(true)
    ElMessage.warning('检测到切换页面，已记录本次操作')
  }
}

async function sendHeartbeat(isSwitch) {
  if (state.value !== 'answering') return
  try {
    const elapsed = Math.floor((Date.now() - start.value) / 1000)
    const res = await taskApi.heartbeat(taskId, { switch: isSwitch, duration_seconds: elapsed })
    switchCount.value = res.data.switch_count
    saveDraft()
    if (!draftTipShown.value) {
      draftTipShown.value = true
      ElMessage.info('答案已自动保存草稿，刷新页面不会丢失')
    }
  } catch (e) { /* 心跳失败静默 */ }
}

async function doSubmit(auto = false) {
  if (submitted.value) return
  submitted.value = true
  submitVisible.value = false
  clearInterval(timer)
  clearInterval(heartbeatTimer)
  document.removeEventListener('visibilitychange', onVisibility)

  const payload = []
  items.value.forEach(it => {
    const content = it.type === 'multiple'
      ? (multiAnswers.value[it.paper_item_id] || [])
      : (answers.value[it.paper_item_id] || '')
    if (content !== '' && (Array.isArray(content) ? content.length : true)) {
      payload.push({ paper_item_id: it.paper_item_id, content })
    }
  })

  try {
    const elapsed = Math.floor((Date.now() - start.value) / 1000)
    const res = await taskApi.submit(taskId, {
      answers: payload, duration_seconds: elapsed, attempt: 1
    })
    result.value = res.data
    grading.value = res.data.grading
    state.value = 'result'
    localStorage.removeItem(draftKey)
    window.scrollTo({ top: 0 })
    // 结果页需要答案解析，重新拉一次试卷
    const fresh = await taskApi.taskPaper(taskId)
    items.value = fresh.data.items
    ElMessage.success(auto ? '已自动交卷' : '交卷成功')
  } catch (e) {
    submitted.value = false
    ElMessage.error(`交卷失败：${e.message}`)
  }
}

onMounted(load)

onBeforeUnmount(() => {
  clearInterval(timer)
  clearInterval(heartbeatTimer)
  document.removeEventListener('visibilitychange', onVisibility)
  window.removeEventListener('scroll', onScroll, true)
  if (state.value === 'answering') saveDraft()
})
</script>

<style scoped>
.mb8 { margin-bottom: 8px; }
.mb8 { margin-bottom: 8px; }
.exam-page { min-height: 100%; background: #f4f6fa; padding-bottom: 40px; }
.bar {
  position: sticky; top: 0; z-index: 10; background: #fff; padding: 12px 20px;
  display: flex; align-items: center; justify-content: space-between; gap: 16px;
  box-shadow: 0 1px 6px rgba(0,0,0,.06); flex-wrap: wrap;
}
.bar-info { display: flex; align-items: center; gap: 10px; }
.title { font-weight: 600; font-size: 15px; }
.bar-progress { display: flex; align-items: center; gap: 10px; font-size: 13px; color: #606266; }
.bar-actions { display: flex; align-items: center; gap: 14px; }
.countdown { font-size: 18px; font-weight: 600; color: #2f6fd0; font-variant-numeric: tabular-nums; }
.countdown.warn { color: #f56c6c; }
.countdown.urgent { animation: pulse 1s ease-in-out infinite; }
.cd-label { font-size: 12px; font-weight: 400; color: #909399; margin-right: 2px; }
@keyframes pulse {
  0%, 100% { opacity: 1; }
  50% { opacity: .45; }
}
.countdown.urgent { animation: pulse 1s ease-in-out infinite; }
.cd-label { font-size: 12px; font-weight: 400; color: #909399; margin-right: 2px; }
@keyframes pulse {
  0%, 100% { opacity: 1; }
  50% { opacity: .45; }
}

.nav-bar {
  background: #fff; padding: 10px 20px; display: flex; align-items: center; gap: 6px;
  flex-wrap: wrap; position: sticky; top: 61px; z-index: 9; border-bottom: 1px solid #ebeef5;
}
.nav-label { font-size: 13px; color: #909399; margin-right: 4px; }
.nav-item {
  width: 30px; height: 30px; line-height: 30px; text-align: center; border-radius: 4px;
  background: #f0f2f5; font-size: 13px; cursor: pointer; user-select: none;
}
.nav-item.done { background: #67c23a; color: #fff; }
.nav-item.current {
  background: #2f6fd0; color: #fff; font-weight: 600;
  box-shadow: 0 0 0 2px rgba(47,111,208,.35);
}
.nav-item:hover { outline: 2px solid #2f6fd0; }

.body { max-width: 900px; margin: 0 auto; padding: 20px; }
.q-card {
  background: #fff; border-radius: 8px; padding: 18px 20px; margin-bottom: 16px;
  box-shadow: 0 1px 4px rgba(0,0,0,.05); border-left: 3px solid transparent;
}
.q-card.answered { border-left-color: #67c23a; }
.q-head { display: flex; align-items: center; gap: 10px; margin-bottom: 12px; }
.q-no {
  width: 26px; height: 26px; line-height: 26px; text-align: center;
  background: #2f6fd0; color: #fff; border-radius: 50%; font-size: 13px; font-weight: 600;
}
.q-score { font-size: 12px; color: #909399; }
.q-stem { line-height: 1.8; margin-bottom: 14px; font-size: 15px; }
.opts { display: flex; flex-direction: column; gap: 8px; width: 100%; }
.opt { width: 100%; height: auto; min-height: 38px; padding: 10px 14px; margin: 0 !important; }
.opt :deep(.el-radio__label) { white-space: normal; line-height: 1.6; }

.result-hero {
  text-align: center; padding: 40px 20px; color: #fff;
  background: linear-gradient(135deg, #67c23a, #95d475);
}
.result-hero.fail { background: linear-gradient(135deg, #f56c6c, #f78989); }
.hero-score { font-size: 64px; font-weight: 700; line-height: 1; }
.hero-label { font-size: 16px; opacity: .9; margin-top: 4px; }
.hero-meta { display: flex; justify-content: center; gap: 20px; align-items: center; margin-top: 16px; flex-wrap: wrap; }
.hero-actions { margin-top: 24px; display: flex; justify-content: center; gap: 12px; }
.result-body { max-width: 900px; margin: 20px auto; padding: 0 20px; }
.summary-bar {
  background: #ecf5ff; color: #2f6fd0; padding: 10px 16px; border-radius: 6px; margin-bottom: 16px;
}
.r-card {
  background: #fff; border-radius: 8px; padding: 16px 20px; margin-bottom: 14px;
  border-left: 3px solid #f56c6c;
}
.r-card.ok { border-left-color: #67c23a; }
.r-head { display: flex; align-items: center; gap: 10px; margin-bottom: 10px; }
.r-no { font-weight: 600; color: #909399; }
.r-icon { font-size: 18px; }
.r-card.ok .r-icon { color: #67c23a; }
.r-card:not(.ok) .r-icon { color: #f56c6c; }
.r-score { font-weight: 600; }
.r-answers { margin-top: 10px; line-height: 1.9; font-size: 14px; }
.r-analysis {
  margin-top: 10px; padding: 10px; background: #f5f7fa; border-radius: 4px;
  font-size: 13px; line-height: 1.7; color: #606266;
}
</style>
