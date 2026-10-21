<template>
  <div class="page-container">
    <div class="page-header">
      <h2 class="page-title">随机练习</h2>
      <el-button :icon="Refresh" @click="loadSubjects">刷新</el-button>
    </div>

    <!-- 配置区 -->
    <el-card v-if="!paper" shadow="never" class="filter-card">
      <el-form :model="form" label-width="100px">
        <el-row :gutter="16">
          <el-col :span="12">
            <el-form-item label="学科">
              <el-select v-model="form.subject_id" placeholder="选择学科" style="width:100%"
                         @change="onSubjectChange">
                <el-option v-for="s in subjects" :key="s.id" :label="s.name" :value="s.id" />
              </el-select>
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="年级">
              <el-select v-model="form.grade_id" placeholder="全部年级" clearable style="width:100%">
                <el-option v-for="g in grades" :key="g.id" :label="g.name" :value="g.id" />
              </el-select>
            </el-form-item>
          </el-col>
        </el-row>

        <el-form-item label="题目数量">
          <el-slider v-model="form.count" :min="3" :max="30" show-input style="max-width:400px" />
        </el-form-item>

        <el-form-item label="题型">
          <el-checkbox-group v-model="form.question_types">
            <el-checkbox v-for="(l, v) in TYPES" :key="v" :label="v">{{ l }}</el-checkbox>
          </el-checkbox-group>
        </el-form-item>

        <el-form-item label="难度">
          <el-radio-group v-model="form.difficulty">
            <el-radio-button value="">不限</el-radio-button>
            <el-radio-button value="easy">简单</el-radio-button>
            <el-radio-button value="medium">中等</el-radio-button>
            <el-radio-button value="hard">困难</el-radio-button>
          </el-radio-group>
        </el-form-item>

        <el-form-item label="限定知识点">
          <el-select v-model="form.knowledge_point_ids" multiple filterable collapse-tags
                     placeholder="不选则全学科范围" style="width:100%">
            <el-option v-for="k in kps" :key="k.id" :label="k.name" :value="k.id" />
          </el-select>
        </el-form-item>

        <el-form-item>
          <el-button type="primary" :icon="MagicStick" :loading="generating" @click="createPractice">
            生成练习
          </el-button>
          <el-button @click="resetForm">重置</el-button>
        </el-form-item>
      </el-form>
    </el-card>

    <!-- 答题区 -->
    <template v-else>
      <el-card shadow="never" class="practice-head">
        <div class="flex-between">
          <div>
            <h3 class="practice-title">{{ paper.name }}</h3>
            <p class="tip">
              共 {{ paper.items.length }} 题 · 满分 {{ paper.total_score }} 分
              <span v-if="paper.duration"> · 建议用时 {{ paper.duration }} 分钟</span>
            </p>
          </div>
          <div>
            <el-button :icon="Clock" @click="showHistory">练习历史</el-button>
            <el-button :icon="Close" @click="exitPractice">结束练习</el-button>
          </div>
        </div>
        <el-progress :percentage="progress" :stroke-width="6" class="mt8" />
      </el-card>

      <el-card v-for="(q, idx) in paper.items" :key="q.question_id" shadow="never" class="q-card">
        <div class="q-head">
          <b>第 {{ idx + 1 }} 题</b>
          <el-tag size="small" class="ml4">{{ TYPES[q.type] || q.type }}</el-tag>
          <span class="score-tag ml8">{{ q.score }} 分</span>
          <span class="tip ml8">{{ idx < answeredCount ? `已完成 ${answeredCount} 题` : '未作答' }}</span>
          <el-button class="fav-btn" :icon="favoritedSet.has(q.question_id) ? StarFilled : Star"
                     :type="favoritedSet.has(q.question_id) ? 'warning' : 'default'"
                     size="small" circle @click="toggleFavorite(q)" />
        </div>

        <p class="stem" v-html="safeStem(q.stem)"></p>

        <!-- 单选 / 判断 -->
        <el-radio-group v-if="q.type === 'single' || q.type === 'judge'"
                        v-model="answers[q.question_id]" class="opt-group">
          <el-radio v-for="o in parse(q.options)" :key="o.key" :value="o.key" class="opt-item">
            {{ o.key }}. {{ o.text }}
          </el-radio>
        </el-radio-group>

        <!-- 多选 -->
        <el-checkbox-group v-else-if="q.type === 'multiple'"
                           v-model="multiAnswers[q.question_id]" class="opt-group">
          <el-checkbox v-for="o in parse(q.options)" :key="o.key" :value="o.key" class="opt-item">
            {{ o.key }}. {{ o.text }}
          </el-checkbox>
        </el-checkbox-group>

        <!-- 填空 -->
        <el-input v-else-if="q.type === 'fill'" v-model="fillAnswers[q.question_id]"
                  type="textarea" :rows="2" placeholder="请填写答案" />

        <!-- 主观题 -->
        <el-input v-else v-model="textAnswers[q.question_id]" type="textarea" :rows="4"
                  placeholder="请输入你的解答过程" />

        <!-- 结果区 -->
        <div v-if="result" class="result-box">
          <p>
            <b>正确答案：</b>
            <span class="text-success">{{ format(q.answer) }}</span>
          </p>
          <p><b>我的答案：</b>{{ format(myAnswer(q)) }}</p>
          <p>
            <b>结果：</b>
            <el-tag :type="isCorrect(q) ? 'success' : 'danger'" size="small">
              {{ isCorrect(q) ? '正确' : '错误' }}
            </el-tag>
            <span class="ml8">得分 {{ results[q.question_id]?.score ?? 0 }} / {{ q.score }}</span>
          </p>
          <p v-if="results[q.question_id]?.ai_comment" class="ai-comment">
            <b>AI 评语：</b>{{ results[q.question_id].ai_comment }}
          </p>
        </div>
      </el-card>

      <div class="footer-bar" v-if="!result">
        <span>已作答 {{ answeredCount }} / {{ paper.items.length }} 题</span>
        <el-button type="primary" :loading="submitting" @click="submitPractice">提交并查看结果</el-button>
      </div>

      <div class="footer-bar" v-else>
        <span>本次得分：<b class="total">{{ totalScore }}</b> / {{ paper.total_score }}</span>
        <el-button type="primary" @click="newPractice">再来一组</el-button>
      </div>
    </template>

    <!-- 历史 -->
    <el-drawer v-model="historyDrawer" title="练习历史" size="55%">
      <el-table v-loading="historyLoading" :data="history" border stripe>
        <el-table-column prop="name" label="练习名称" min-width="180" show-overflow-tooltip />
        <el-table-column label="得分" width="130">
          <template #default="{ row }">
            <span :class="row.score >= 60 ? 'text-success' : 'text-danger'">{{ row.score ?? '-' }}</span>
            <span class="tip"> / {{ row.total_score }}</span>
          </template>
        </el-table-column>
        <el-table-column label="正确率" width="120">
          <template #default="{ row }">{{ row.accuracy }}%</template>
        </el-table-column>
        <el-table-column prop="created_at" label="时间" width="170" />
        <el-table-column label="操作" width="100">
          <template #default="{ row }">
            <el-button link type="primary" @click="viewHistory(row)">详情</el-button>
          </template>
        </el-table-column>
      </el-table>
    </el-drawer>

    <!-- 番茄钟（练习时显示） -->
    <PomodoroTimer v-if="paper" @focus-complete="onFocusComplete" />
  </div>
</template>

<script setup>
import { ref, reactive, computed, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import { MagicStick, Refresh, Clock, Close, Star, StarFilled } from '@element-plus/icons-vue'
import TYPES, { questionTypeLabel } from '@/constants/question'
import { taskApi, learningApi, eduApi } from '@/api'
import { fetchSubjects, currentGradeId, resolveSubjectId } from '@/utils/subject'
import PomodoroTimer from '@/components/PomodoroTimer.vue'
import { sanitizeHtml } from '@/utils/sanitize'

// 题干由教师/AI 录入，后端不做净化就落库，直接 v-html 会执行其中的脚本。
// 统一走白名单净化后再渲染（同 MyNotes 的正文处理）。
function safeStem(s) { return sanitizeHtml(s) }


const route = useRoute()
const router = useRouter()


const subjects = ref([])
const grades = ref([])
const kps = ref([])
const paper = ref(null)
const history = ref([])
const results = ref({})
const submitting = ref(false)
const generating = ref(false)
const historyLoading = ref(false)
const historyDrawer = ref(false)

const answers = ref({})
const multiAnswers = ref({})
const fillAnswers = ref({})
const textAnswers = ref({})
const result = ref(false)

const favoritedSet = ref(new Set()) // 已收藏的 question_id 集合

const form = reactive({
  subject_id: null, grade_id: null, count: 10,
  question_types: ['single', 'multiple', 'judge', 'fill'],
  difficulty: '', knowledge_point_ids: []
})

const answeredCount = computed(() => {
  if (!paper.value) return 0
  return paper.value.items.filter(q => isAnswered(q)).length
})
const progress = computed(() => {
  if (!paper.value) return 0
  return Math.round((answeredCount.value / paper.value.items.length) * 100)
})
const totalScore = computed(() => {
  if (!paper.value) return 0
  return Object.values(results.value).reduce((s, r) => s + (r.score || 0), 0).toFixed(1)
})

function parse(v) {
  if (!v) return []
  try { const r = typeof v === 'string' ? JSON.parse(v) : v; return Array.isArray(r) ? r : [] }
  catch { return [] }
}
function format(v) {
  if (v === null || v === undefined || v === '') return '-'
  if (typeof v === 'object') return Array.isArray(v) ? v.join('') : JSON.stringify(v)
  return String(v)
}

function myAnswer(q) {
  if (q.type === 'single' || q.type === 'judge') return answers.value[q.question_id] || ''
  if (q.type === 'multiple') return multiAnswers.value[q.question_id] || []
  if (q.type === 'fill') return fillAnswers.value[q.question_id] || ''
  return textAnswers.value[q.question_id] || ''
}

function isAnswered(q) {
  const a = myAnswer(q)
  return Array.isArray(a) ? a.length > 0 : String(a || '').trim().length > 0
}

function isCorrect(q) {
  return results.value[q.question_id]?.is_correct === true
}

async function onSubjectChange() {
  if (!form.subject_id) { kps.value = []; return }
  // 知识点按学科+年级配套取，否则查的是最低年级的知识点，下拉为空
  const sid = resolveSubjectId(subjects.value, form.subject_id, form.grade_id || currentGradeId())
  const res = await eduApi.knowledgeList({ subject_id: sid, page_size: 200 })
  kps.value = res.data?.items || res.data || []
}

async function loadSubjects() {
  // 只列本年级学科（全量会有 7 个同名「数学」），并把年级默认对齐学生年级。
  // 后端 create_practice 会按 subject_id + grade_id 双重过滤抽题，
  // 传去重代表 id（指向一年级）会让七年级学生抽到一年级题。
  const gid = currentGradeId()
  const [s, g] = await Promise.all([fetchSubjects({ gradeId: gid }), eduApi.grades()])
  subjects.value = s
  grades.value = g.data || []
  if (!form.grade_id && gid) form.grade_id = gid
}

function resetForm() {
  Object.assign(form, {
    subject_id: null, grade_id: null, count: 10,
    question_types: ['single', 'multiple', 'judge', 'fill'], difficulty: '', knowledge_point_ids: []
  })
  kps.value = []
}

async function createPractice() {
  if (!form.subject_id) return ElMessage.warning('请选择学科')
  generating.value = true
  try {
    const gradeId = form.grade_id || currentGradeId()
    const res = await taskApi.practice({
      ...form,
      grade_id: gradeId,
      subject_id: resolveSubjectId(subjects.value, form.subject_id, gradeId)
    })
    const { task_id } = res.data
    const p = await taskApi.practicePaper(task_id)
    paper.value = { ...p.data, task_id }
    answers.value = {}
    multiAnswers.value = {}
    fillAnswers.value = {}
    textAnswers.value = {}
    results.value = {}
    result.value = false
    ElMessage.success(res.data.message || `已生成 ${p.data.items.length} 道练习题`)
    loadFavoriteStatus()
  } finally {
    generating.value = false
  }
}

async function loadFavoriteStatus() {
  if (!paper.value?.items?.length) return
  // 批量接口一次拉全卷状态（原先逐题串行，30 题 = 30 个请求）
  try {
    const res = await learningApi.checkFavoritesBatch(
      paper.value.items.map(q => q.question_id))
    const m = res.data || {}
    favoritedSet.value = new Set(
      paper.value.items.map(q => q.question_id).filter(id => m[String(id)]?.favorited))
  } catch { /* 状态拉取失败不影响作答，静默降级为全未收藏 */ }
}

async function toggleFavorite(q) {
  if (favoritedSet.value.has(q.question_id)) {
    await learningApi.removeFavoriteByQid(q.question_id)
    favoritedSet.value.delete(q.question_id)
    favoritedSet.value = new Set(favoritedSet.value)
    ElMessage.info('已取消收藏')
  } else {
    await learningApi.addFavorite({ question_id: q.question_id })
    favoritedSet.value.add(q.question_id)
    favoritedSet.value = new Set(favoritedSet.value)
    ElMessage.success('已收藏')
  }
}

function onFocusComplete(info) {
  ElMessage.success(`专注完成！已累计完成 ${info.pomodoros} 个番茄钟`)
}

async function submitPractice() {
  if (answeredCount.value === 0) return ElMessage.warning('请至少作答一道题')
  await ElMessageBox.confirm(`已作答 ${answeredCount.value}/${paper.value.items.length} 题，确认提交？`,
    '提示', { type: 'info' })
  submitting.value = true
  try {
    const answers_ = paper.value.items.map(q => ({
      question_id: q.question_id,
      paper_item_id: q.paper_item_id,
      content: myAnswer(q)
    }))
    const res = await taskApi.submit(paper.value.task_id, { answers: answers_ })
    const d = res.data || {}
    results.value = {}
    ;(d.results || []).forEach(r => { results.value[r.question_id] = r })
    result.value = true
    ElMessage.success(res.data.message || '提交完成')
  } finally {
    submitting.value = false
  }
}

function exitPractice() {
  ElMessageBox.confirm('确认结束本次练习？已作答内容将丢失。', '提示', { type: 'warning' })
    .then(() => { paper.value = null })
    .catch(() => {})
}

function newPractice() {
  paper.value = null
  answers.value = {}
  multiAnswers.value = {}
  fillAnswers.value = {}
  textAnswers.value = {}
  results.value = {}
  result.value = false
}

function showHistory() { historyDrawer.value = true; loadHistory() }

async function loadHistory() {
  historyLoading.value = true
  try {
    const res = await taskApi.practiceHistory({ page: 1, page_size: 50 })
    history.value = res.data?.items || []
  } finally {
    historyLoading.value = false
  }
}

async function viewHistory(row) {
  // 原调用 taskApi.submissionDetailByTask?.(...) —— 该方法不存在，
  // optional call 恒 undefined，res 未使用（死代码）。
  // 现在 practice/history 已返回 submission_id，未交卷的练习直接引导重做。
  historyDrawer.value = false
  if (row.submission_id) {
    router.push({ name: 'ExamPaper', params: { taskId: row.task_id } })
    return
  }
  ElMessage.info(`练习「${row.name}」尚未提交，得分 ${row.score ?? '-'}，正确率 ${row.accuracy ?? 0}%`)
}

// 承接掌握图谱 / 学习路径的「去练习」跳转：预选学科与知识点
onMounted(() => {
  loadSubjects()
  const q = route.query
  if (q.subject) {
    form.subject_id = Number(q.subject)
  }
  if (q.kp) {
    selectedKps.value = [Number(q.kp)]
  }
})
</script>

<style scoped>
.flex-between { display: flex; align-items: center; justify-content: space-between; align-items: flex-start; }
.mt8 { margin-top: 8px; }
.ml4 { margin-left: 4px; }
.ml8 { margin-left: 8px; }
.tip { font-size: 12px; color: #909399; }
.practice-title { margin: 0 0 4px; font-size: 17px; }
.q-card { margin-bottom: 14px; }
.q-head { display: flex; align-items: center; margin-bottom: 10px; }
.fav-btn { margin-left: auto; }
.score-tag { color: var(--el-color-primary); font-weight: 600; }
.stem { line-height: 1.9; font-size: 15px; margin: 10px 0; }
.opt-group { display: flex; flex-direction: column; gap: 8px; align-items: flex-start; }
.opt-item { height: auto; align-items: flex-start; white-space: normal; }
.result-box {
  background: #f7f9fc; border-radius: 8px; padding: 12px; margin-top: 12px;
}
.result-box p { margin: 5px 0; }
.text-success { color: #67c23a; }
.text-danger { color: #f56c6c; }
.ai-comment { color: #2f6fd0; }
.footer-bar {
  position: sticky; bottom: 0; background: #fff; padding: 14px 0;
  border-top: 1px solid #ebeef5; display: flex; align-items: center;
  justify-content: space-between; font-size: 15px;
}
.total { color: var(--el-color-primary); font-size: 22px; }
.filter-card :deep(.el-form-item) { margin-bottom: 16px; }
</style>
