<template>
  <div class="page-container">
    <div class="page-header">
      <h2 class="page-title">AI 出题组卷工作台</h2>
      <div>
        <el-tag v-if="engine" :type="engine.llm_enabled ? 'success' : 'warning'" effect="dark">
          {{ engine.llm_enabled ? `${engine.llm_provider} 已接入` : '规则引擎模式' }}
        </el-tag>
        <el-button :icon="Cpu" @click="statusDrawer = true">引擎状态</el-button>
      </div>
    </div>

    <el-row :gutter="16">
      <!-- 左：功能选择 -->
      <el-col :span="6">
        <el-card shadow="never">
          <template #header><b>选择能力</b></template>
          <el-menu :default-active="active" @select="onSelect" class="agent-menu">
            <el-menu-item v-for="a in agents" :key="a.code" :index="a.code">
              <el-icon><component :is="iconOf(a.code)" /></el-icon>
              <span>{{ a.name }}</span>
            </el-menu-item>
          </el-menu>

          <el-divider />
          <div class="hint-box">
            <p class="hint-title">当前 Agent</p>
            <p class="hint-desc">{{ currentAgent?.description }}</p>
          </div>
        </el-card>
      </el-col>

      <!-- 右：输入 + 结果 -->
      <el-col :span="18">
        <el-card shadow="never">
          <template #header>
            <b>{{ currentAgent?.name }} 工作台</b>
          </template>

          <!-- 出题 Agent -->
          <template v-if="active === 'question_generator'">
            <el-form label-width="100px">
              <el-row :gutter="12">
                <el-col :span="8">
                  <el-form-item label="学科">
                    <el-select v-model="qForm.subject_id" style="width:100%" @change="onSubjectChange">
                      <el-option v-for="s in subjects" :key="s.id" :label="s.name" :value="s.id" />
                    </el-select>
                  </el-form-item>
                </el-col>
                <el-col :span="8">
                  <el-form-item label="年级">
                    <el-select v-model="qForm.grade_id" clearable style="width:100%">
                      <el-option v-for="g in grades" :key="g.id" :label="g.name" :value="g.id" />
                    </el-select>
                  </el-form-item>
                </el-col>
                <el-col :span="8">
                  <el-form-item label="知识点">
                    <el-select v-model="qForm.knowledge_point_ids" multiple filterable collapse-tags
                               style="width:100%">
                      <el-option v-for="k in kps" :key="k.id" :label="k.name" :value="k.id" />
                    </el-select>
                  </el-form-item>
                </el-col>
              </el-row>
              <el-row :gutter="12">
                <el-col :span="8">
                  <el-form-item label="题型">
                    <el-select v-model="qForm.question_types" multiple collapse-tags style="width:100%">
                      <el-option v-for="(l, v) in TYPES" :key="v" :label="l" :value="v" />
                    </el-select>
                  </el-form-item>
                </el-col>
                <el-col :span="8">
                  <el-form-item label="难度">
                    <el-select v-model="qForm.difficulty" clearable style="width:100%">
                      <el-option label="简单" value="easy" />
                      <el-option label="中等" value="medium" />
                      <el-option label="困难" value="hard" />
                    </el-select>
                  </el-form-item>
                </el-col>
                <el-col :span="8">
                  <el-form-item label="数量">
                    <el-input-number v-model="qForm.count" :min="1" :max="30" style="width:100%" />
                  </el-form-item>
                </el-col>
              </el-row>
              <el-form-item label="额外要求">
                <el-input v-model="qForm.requirements" type="textarea" :rows="2"
                          placeholder="如：侧重实际应用，难度适中偏难" />
              </el-form-item>
            </el-form>
          </template>

          <!-- 组卷 Agent -->
          <template v-else-if="active === 'paper_composer'">
            <el-alert type="info" :closable="false" class="mb12"
                      title="用自然语言描述组卷需求，AI 自动解析题型、难度、数量并完成抽题" />
            <el-input v-model="paperReq" type="textarea" :rows="3"
                      placeholder="如：生成七年级数学一元一次方程试卷，10 题，选择题 6 道 + 填空 4 道，难度中等，限时 30 分钟" />
            <div class="mt8">
              <el-button v-for="t in paperTemplates" :key="t" size="small" class="mr4" @click="paperReq = t">
                {{ t.slice(0, 14) }}…
              </el-button>
            </div>
          </template>

          <!-- 其他 Agent 通用 -->
          <template v-else-if="active === 'note_organizer' || active === 'tutor'">
            <el-form label-width="90px">
              <el-form-item v-if="active === 'note_organizer'" label="笔记 ID">
                <el-input-number v-model="genericForm.note_id" :min="1" style="width:200px" />
                <span class="tip ml8">可在「学习笔记」页面查看笔记 ID</span>
              </el-form-item>
              <el-form-item v-else label="问题">
                <el-input v-model="genericForm.question" type="textarea" :rows="4"
                          placeholder="如：为什么一元二次方程的判别式能判断根的个数？" />
              </el-form-item>
              <el-form-item v-if="active === 'tutor'" label="知识点">
                <el-input v-model="genericForm.knowledge_point" placeholder="可选，如：二次函数" />
              </el-form-item>
            </el-form>
          </template>

          <!-- 学习规划 / 批改 -->
          <template v-else-if="active === 'study_planner'">
            <el-form label-width="100px">
              <el-row :gutter="12">
                <el-col :span="12">
                  <el-form-item label="学生 ID">
                    <el-input-number v-model="genericForm.student_id" :min="1" style="width:100%" />
                  </el-form-item>
                </el-col>
                <el-col :span="12">
                  <el-form-item label="规划天数">
                    <el-input-number v-model="genericForm.days" :min="1" :max="30" style="width:100%" />
                  </el-form-item>
                </el-col>
              </el-row>
              <el-form-item label="每日时长">
                <el-input-number v-model="genericForm.daily_minutes" :min="15" :max="300" :step="15" />
                <span class="tip ml8">分钟</span>
              </el-form-item>
            </el-form>
          </template>

          <div class="action-bar">
            <el-button type="primary" :icon="MagicStick" :loading="running" @click="run">
              {{ running ? 'AI 生成中（约 20-60 秒，请勿刷新）' : '开始生成' }}
            </el-button>
            <el-button :icon="Refresh" @click="result = null">清空结果</el-button>
          </div>
        </el-card>

        <!-- 结果区 -->
        <el-card shadow="never" class="mt16" v-if="result">
          <template #header>
            <div class="flex-between">
              <b>生成结果</b>
              <el-tag v-if="isFallback" type="warning" size="small">规则引擎降级模式</el-tag>
            </div>
          </template>

          <!-- 题目列表 -->
          <template v-if="result.questions?.length">
            <el-table :data="result.questions" border>
              <el-table-column type="expand">
                <template #default="{ row }">
                  <p class="stem" v-html="row.stem"></p>
                  <p v-if="parse(row.options)" class="opts">
                    <span v-for="o in parse(row.options)" :key="o.key" class="opt">{{ o.key }}. {{ o.text }}</span>
                  </p>
                  <p class="answer">答案：{{ JSON.stringify(row.answer) }}</p>
                  <p v-if="row.analysis" class="analysis">解析：{{ row.analysis }}</p>
                </template>
              </el-table-column>
              <el-table-column label="题型" width="100">
                <template #default="{ row }">
                  <el-tag size="small">{{ TYPES[row.type] || row.type }}</el-tag>
                </template>
              </el-table-column>
              <el-table-column prop="stem" label="题干" min-width="280" show-overflow-tooltip>
                <template #default="{ row }">{{ strip(row.stem) }}</template>
              </el-table-column>
              <el-table-column label="难度" width="90">
                <template #default="{ row }">
                  <el-tag size="small" :type="{ easy: 'success', medium: 'warning', hard: 'danger' }[row.difficulty]">
                    {{ { easy: '简单', medium: '中等', hard: '困难' }[row.difficulty] }}
                  </el-tag>
                </template>
              </el-table-column>
              <el-table-column prop="score" label="分值" width="70" align="center" />
            </el-table>
            <div class="action-bar mt12">
              <el-button type="success" :loading="saving" @click="saveAll">一键保存到题库</el-button>
              <span class="tip">保存后题目进入「待审核」状态，审核通过即可组卷使用</span>
            </div>
          </template>

          <!-- 试卷结果 -->
          <template v-else-if="result.paper">
            <el-descriptions :column="2" border>
              <el-descriptions-item label="试卷名称">{{ result.paper.name }}</el-descriptions-item>
              <el-descriptions-item label="题量">{{ result.paper.question_count || result.items?.length || '-' }}</el-descriptions-item>
              <el-descriptions-item label="难度分布">{{ fmt(result.difficulty_distribution) }}</el-descriptions-item>
              <el-descriptions-item label="总分">{{ result.paper.total_score || '-' }}</el-descriptions-item>
              <el-descriptions-item label="知识点覆盖" :span="2">{{ result.knowledge_coverage || '-' }}</el-descriptions-item>
              <el-descriptions-item label="难度分析" :span="2">{{ result.analysis || '-' }}</el-descriptions-item>
            </el-descriptions>
          </template>

          <!-- 通用文本结果 -->
          <template v-else>
            <pre class="text-result">{{ textResult }}</pre>
          </template>
        </el-card>
      </el-col>
    </el-row>

    <el-drawer v-model="statusDrawer" title="AI 引擎状态" size="400px">
      <el-descriptions :column="1" border v-if="engine">
        <el-descriptions-item label="编排模式">
          <el-tag :type="engine.orchestrator_mode === 'langgraph' ? 'success' : 'warning'" size="small">
            {{ engine.orchestrator_mode }}
          </el-tag>
        </el-descriptions-item>
        <el-descriptions-item label="大模型">
          {{ engine.llm_enabled ? `${engine.llm_provider} / ${engine.llm_model}` : '未配置（规则引擎）' }}
        </el-descriptions-item>
        <el-descriptions-item label="向量库">
          <el-tag :type="engine.vector_db === 'chroma' ? 'success' : 'warning'" size="small">
            {{ engine.vector_db === 'chroma' ? 'ChromaDB' : 'SQL 检索' }}
          </el-tag>
        </el-descriptions-item>
        <el-descriptions-item label="调度器">{{ engine.scheduler_running ? '运行中' : '已停止' }}</el-descriptions-item>
      </el-descriptions>
    </el-drawer>
  </div>
</template>

<script setup>
import { ref, reactive, computed, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { MagicStick, Refresh, Cpu, Notebook, Tickets, EditPen, Calendar, ChatDotRound, Collection } from '@element-plus/icons-vue'
import { agentApi, eduApi, questionApi } from '@/api'

const TYPES = {
  single: '单选题', multiple: '多选题', judge: '判断题', fill: '填空题',
  short: '简答题', calculate: '计算题', proof: '证明题', essay: '论述题'
}

const agents = ref([])
const engine = ref(null)
const subjects = ref([])
const grades = ref([])
const kps = ref([])
const active = ref('question_generator')
const result = ref(null)
const running = ref(false)
const saving = ref(false)
const statusDrawer = ref(false)
const paperReq = ref('')

const qForm = reactive({
  subject_id: null, grade_id: null, knowledge_point_ids: [], question_types: ['single'],
  difficulty: 'medium', count: 5, requirements: ''
})
const genericForm = reactive({ note_id: null, question: '', knowledge_point: '', student_id: null, days: 7, daily_minutes: 90 })

const paperTemplates = [
  '生成七年级数学一元一次方程试卷，10 题，选择题 6 道 + 填空 4 道，难度中等',
  '生成八年级物理期中试卷，20 题，限时 60 分钟',
  '生成九年级英语完形填空专项卷，15 题，难度偏难'
]

const currentAgent = computed(() => agents.value.find(a => a.code === active.value))
const isFallback = computed(() => result.value?.is_fallback === true)

const textResult = computed(() => {
  if (!result.value) return ''
  if (result.value.answer) return result.value.answer
  if (result.value.summary) return JSON.stringify(result.value, null, 2)
  return JSON.stringify(result.value, null, 2)
})

function iconOf(code) {
  return {
    question_generator: Notebook, paper_composer: Tickets, grading_assistant: EditPen,
    study_planner: Calendar, tutor: ChatDotRound, note_organizer: Collection
  }[code] || MagicStick
}

function strip(s) { return String(s || '').replace(/<[^>]+>/g, '') }
function parse(v) { if (!v) return null; try { return typeof v === 'string' ? JSON.parse(v) : v } catch { return null } }
function fmt(o) {
  if (!o) return '-'
  return typeof o === 'object' ? JSON.stringify(o) : String(o)
}

function onSelect(idx) { active.value = idx; result.value = null }

async function onSubjectChange() {
  if (!qForm.subject_id) { kps.value = []; return }
  const res = await eduApi.knowledgeList({ subject_id: qForm.subject_id, page_size: 200 })
  kps.value = res.data?.items || res.data || []
}

async function run() {
  running.value = true
  result.value = null
  try {
    let res
    if (active.value === 'question_generator') {
      if (!qForm.subject_id) { ElMessage.warning('请选择学科'); return }
      // 后端契约是单值 type / knowledge_point_id（此前发复数数组被
      // 静默忽略，所选题型/知识点永远不生效，全部按默认 single 生成）
      res = await agentApi.questionGenerator({
        ...qForm,
        type: qForm.question_types?.[0] || 'single',
        knowledge_point_id: qForm.knowledge_point_ids?.[0] || undefined,
      })
    } else if (active.value === 'paper_composer') {
      if (!paperReq.value) { ElMessage.warning('请输入组卷需求'); return }
      res = await agentApi.paperComposer({ requirement: paperReq.value })
    } else if (active.value === 'note_organizer') {
      if (!genericForm.note_id) { ElMessage.warning('请输入笔记 ID'); return }
      res = await agentApi.noteOrganizer({ note_id: genericForm.note_id })
    } else if (active.value === 'tutor') {
      if (!genericForm.question) { ElMessage.warning('请输入问题'); return }
      res = await agentApi.tutor(genericForm)
    } else if (active.value === 'study_planner') {
      res = await agentApi.studyPlanner(genericForm)
    } else {
      res = await agentApi.grading(genericForm)
    }
    result.value = res.data || {}
    ElMessage.success(res.data.message || '生成完成')
  } finally {
    running.value = false
  }
}

async function saveAll() {
  const qs = result.value.questions || []
  if (!qs.length) return
  // 二次确认：写入题库对全校教师可见，属于不可逆的公共数据变更
  try {
    await ElMessageBox.confirm(
      `将把 ${qs.length} 道题写入题库，入库后所有教师均可选用。请先核对题目与答案。`,
      '确认入库', { type: 'warning', confirmButtonText: '确认入库', cancelButtonText: '再检查一下' })
  } catch { return }
  saving.value = true
  try {
    let okCount = 0
    for (const q of qs) {
      try {
        await questionApi.create({ ...q, subject_id: q.subject_id || qForm.subject_id,
          grade_id: q.grade_id || qForm.grade_id, knowledge_point_ids: q.knowledge_point_ids || qForm.knowledge_point_ids })
        okCount++
      } catch { /* 单条失败继续 */ }
    }
    ElMessage.success(`成功保存 ${okCount}/${qs.length} 道题目`)
  } finally {
    saving.value = false
  }
}

onMounted(async () => {
  const [a, s, g, st] = await Promise.all([
    agentApi.list(), agentApi.status(), eduApi.subjects(), eduApi.grades()
  ])
  agents.value = a.data || []
  engine.value = st.data
  subjects.value = s.data || []
  grades.value = g.data || []
})
</script>

<style scoped>
.flex-between { display: flex; align-items: center; justify-content: space-between; }
.mb12 { margin-bottom: 12px; }
.mt8 { margin-top: 8px; }
.mt12 { margin-top: 12px; }
.mt16 { margin-top: 16px; }
.ml8 { margin-left: 8px; }
.mr4 { margin-right: 4px; }
.tip { font-size: 12px; color: #909399; }
.agent-menu { border-right: none; }
.agent-menu :deep(.el-menu-item) { height: 44px; }
.action-bar { display: flex; align-items: center; gap: 10px; margin-top: 16px; }
.hint-box { background: #f7f9fc; padding: 10px; border-radius: 8px; }
.hint-title { margin: 0 0 4px; font-weight: 600; font-size: 13px; }
.hint-desc { margin: 0; font-size: 12px; color: #909399; line-height: 1.6; }
.stem { line-height: 1.7; margin: 6px 0; }
.opts { margin: 4px 0; }
.opt { display: inline-block; margin-right: 18px; }
.answer { color: #67c23a; margin: 4px 0; }
.analysis { color: #909399; font-size: 13px; margin: 4px 0; }
.text-result {
  background: #f7f8fa; padding: 14px; border-radius: 8px; white-space: pre-wrap;
  font-family: inherit; font-size: 13px; line-height: 1.8; margin: 0; max-height: 500px; overflow: auto;
}
</style>
