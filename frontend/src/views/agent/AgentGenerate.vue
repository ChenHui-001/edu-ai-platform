<template>
  <div class="page-container">
    <div class="page-header">
      <h2 class="page-title">AI 出题组卷工作台</h2>
      <div>
        <el-tag v-if="engine" :type="engine.llm_enabled ? 'success' : 'warning'" effect="dark">
          {{ engine.llm_enabled ? `${engineProvider} 已接入` : '规则引擎模式' }}
        </el-tag>
        <el-button :icon="Cpu" @click="statusDrawer = true">引擎状态</el-button>
      </div>
    </div>

    <!-- 未启用 AI：给管理员配置入口 -->
    <el-alert v-if="engine && !engine.llm_enabled" type="warning" :closable="false" show-icon class="mb12">
      <template #title>
        AI 未启用，当前走规则引擎降级。
        <el-link v-if="isAdmin" type="primary" :underline="false" @click="goConfig">
          前往 AI 大模型配置
        </el-link>
        <template v-else>请联系管理员在「AI 大模型配置」中启用。</template>
      </template>
    </el-alert>

    <el-row :gutter="16">
      <!-- 左：功能选择 -->
      <el-col :xs="24" :sm="24" :md="7" :lg="6">
        <el-card shadow="never">
          <template #header><b>选择能力</b></template>
          <el-menu :default-active="active" @select="onSelect" class="agent-menu">
            <el-menu-item v-for="a in visibleAgents" :key="a.name" :index="a.name">
              <el-icon><component :is="iconOf(a.name)" /></el-icon>
              <span>{{ a.display_name || a.name }}</span>
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
      <el-col :xs="24" :sm="24" :md="17" :lg="18">
        <el-card shadow="never">
          <template #header>
            <!-- name 是英文 code（question_generator），中文在 display_name -->
            <b>{{ currentAgent?.display_name || currentAgent?.name }} 工作台</b>
          </template>

          <!-- 出题 Agent -->
          <template v-if="active === 'question_generator'">
            <el-form label-width="100px">
              <el-row :gutter="12">
                <el-col :xs="24" :sm="12" :md="8">
                  <el-form-item label="学科">
                    <el-select v-model="qForm.subject_id" filterable style="width:100%" @change="onSubjectChange">
                      <!-- 未选年级时按年级分组：Subject 同名几十条，平铺无法区分 -->
                      <template v-if="qForm.grade_id">
                        <el-option v-for="s in genSubjects" :key="s.id" :label="s.name" :value="s.id" />
                      </template>
                      <template v-else>
                        <el-option-group v-for="g in genSubjectGroups" :key="g.id" :label="g.label">
                          <el-option v-for="s in g.options" :key="s.id" :label="s.name" :value="s.id" />
                        </el-option-group>
                      </template>
                    </el-select>
                  </el-form-item>
                </el-col>
                <el-col :xs="24" :sm="12" :md="8">
                  <el-form-item label="年级">
                    <el-select v-model="qForm.grade_id" clearable style="width:100%"
                               @change="onGradeChange">
                      <el-option v-for="g in grades" :key="g.id" :label="g.name" :value="g.id" />
                    </el-select>
                  </el-form-item>
                </el-col>
                <el-col :xs="24" :sm="12" :md="8">
                  <el-form-item label="知识点">
                    <el-select v-model="qForm.knowledge_point_ids" multiple filterable collapse-tags
                               style="width:100%">
                      <el-option v-for="k in kps" :key="k.id" :label="k.name" :value="k.id" />
                    </el-select>
                  </el-form-item>
                </el-col>
              </el-row>
              <el-row :gutter="12">
                <el-col :xs="24" :sm="12" :md="8">
                  <el-form-item label="题型">
                    <!-- 后端 question_type 是单值，多选只会取第一个、误导用户；
                         值必须用后端枚举（constants/question.js 的 key），
                         不能用 calculate/proof/essay 这类历史别名。 -->
                    <el-select v-model="qForm.question_type" style="width:100%">
                      <el-option v-for="(l, v) in QUESTION_TYPE_LABELS" :key="v" :label="l" :value="v" />
                    </el-select>
                  </el-form-item>
                </el-col>
                <el-col :xs="24" :sm="12" :md="8">
                  <el-form-item label="难度">
                    <!-- 后端 data.get('difficulty', 'medium') 在显式传 null 时拿到 None，
                         去掉 clearable 保证难度始终有合法值 -->
                    <el-select v-model="qForm.difficulty" style="width:100%">
                      <el-option label="简单" value="easy" />
                      <el-option label="中等" value="medium" />
                      <el-option label="困难" value="hard" />
                    </el-select>
                  </el-form-item>
                </el-col>
                <el-col :xs="24" :sm="12" :md="8">
                  <el-form-item label="数量">
                    <!-- 后端 execute 静默把 count 截到 10，前端不要放开到 30 -->
                    <el-input-number v-model="qForm.count" :min="1" :max="10" style="width:100%" />
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
            <!-- 学科兜底：自然语言解析不出学科时后端直接报「无法识别学科」，
                 此前本页没有任何输入能自救，功能等于不可用。这里给一组
                 年级/学科下拉，选了就直接作为 grade_id/subject_id 传给后端，
                 Agent 不再依赖文本解析猜学科。 -->
            <el-form :inline="true" class="mb8">
              <el-form-item label="年级">
                <el-select v-model="paperGradeId" clearable placeholder="按需求文本自动识别"
                           style="width:180px" @change="onPaperGradeChange">
                  <el-option v-for="g in grades" :key="g.id" :label="g.name" :value="g.id" />
                </el-select>
              </el-form-item>
              <el-form-item label="学科">
                <el-select v-model="paperSubjectId" clearable filterable
                           placeholder="按需求文本自动识别" style="width:180px">
                  <el-option v-for="s in paperSubjects" :key="s.id" :label="s.name" :value="s.id" />
                </el-select>
              </el-form-item>
            </el-form>
            <el-input v-model="paperReq" type="textarea" :rows="3"
                      placeholder="如：生成七年级数学一元一次方程试卷，10 题，选择题 6 道 + 填空 4 道，难度中等，限时 30 分钟" />
            <div class="mt8">
              <!-- 按钮只放得下摘要，完整需求用 tooltip 给出，避免看不全 -->
              <el-tooltip v-for="t in paperTemplates" :key="t" :content="t"
                          placement="top" :show-after="300">
                <el-button size="small" class="mr4" @click="paperReq = t">
                  {{ templateLabel(t) }}
                </el-button>
              </el-tooltip>
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
              {{ running ? 'AI 生成中，请勿刷新页面' : '开始生成' }}
            </el-button>
            <el-tooltip :content="'后台任务：提交后立即返回，页面可关闭，稍后回来查看结果'" placement="top">
              <el-checkbox v-model="asyncMode" :disabled="running || !asyncSupported">后台生成</el-checkbox>
            </el-tooltip>
            <el-button :icon="Refresh" @click="result = null">清空结果</el-button>
          </div>
        </el-card>

        <!-- 结果区 -->
        <el-card shadow="never" class="mt16" v-if="result && !hasNoOutput(result)">
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
                  <p class="stem" v-html="safeStem(row.stem)"></p>
                  <p v-if="parse(row.options)" class="opts">
                    <span v-for="o in parse(row.options)" :key="o.key" class="opt">{{ o.key }}. {{ o.text }}</span>
                  </p>
                  <p class="answer">答案：{{ fmtAnswer(row.answer) }}</p>
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
              <el-button type="success" :loading="saving" @click="saveAll">保存到我的私有题库</el-button>
              <span class="tip">保存为你的私有题（private），仅你本人可见与选用</span>
            </div>
          </template>

          <!-- 试卷结果：字段名必须与 PaperComposerAgent 返回结构对齐。
               后端是 item_count / difficulty_report / knowledge_coverage{对象}，
               旧版写 question_count / difficulty_distribution / analysis，
               导致整屏显示「-」和 [object Object]。 -->
          <template v-else-if="result.paper">
            <el-descriptions :column="2" border>
              <el-descriptions-item label="试卷名称">{{ result.paper.name }}</el-descriptions-item>
              <el-descriptions-item label="题量">{{ result.paper.item_count ?? result.paper.items?.length ?? '-' }}</el-descriptions-item>
              <el-descriptions-item label="难度分布">{{ difficultyText }}</el-descriptions-item>
              <el-descriptions-item label="总分">{{ result.paper.total_score ?? '-' }}</el-descriptions-item>
              <el-descriptions-item label="知识点覆盖" :span="2">{{ coverageText }}</el-descriptions-item>
              <el-descriptions-item label="难度分析" :span="2">{{ difficultyAnalysisText }}</el-descriptions-item>
            </el-descriptions>

            <div v-if="result.paper.items?.length" class="mt12">
              <p class="hint-title">题目预览（{{ result.paper.items.length }} 题）</p>
              <el-table :data="result.paper.items" border size="small" max-height="320">
                <el-table-column type="index" label="#" width="50" />
                <el-table-column label="题型" width="120">
                  <template #default="{ row }">{{ TYPES[row.type] || row.type || '-' }}</template>
                </el-table-column>
                <el-table-column label="题干" min-width="260" show-overflow-tooltip>
                  <template #default="{ row }">{{ strip(row.stem) }}</template>
                </el-table-column>
                <el-table-column label="难度" width="90">
                  <template #default="{ row }">{{ { easy: '简单', medium: '中等', hard: '困难' }[row.difficulty] || row.difficulty || '-' }}</template>
                </el-table-column>
                <el-table-column prop="score" label="分值" width="70" align="center" />
              </el-table>
            </div>

            <div class="action-bar">
              <el-button v-if="result.paper.id" type="primary" @click="openPaper(result.paper.id)">
                查看 / 编辑试卷
              </el-button>
              <el-tag v-else type="info" size="small">预览态（未落库）</el-tag>
            </div>
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
        <el-descriptions-item label="提供商">{{ engineProvider }}</el-descriptions-item>
        <el-descriptions-item label="模型">{{ engineModel }}</el-descriptions-item>
        <el-descriptions-item label="API Key">
          <el-tag :type="engineKeyType" size="small">{{ engineKeyLabel }}</el-tag>
        </el-descriptions-item>
        <el-descriptions-item label="大模型">
          {{ engine.llm_enabled ? `${engineProvider} / ${engineModel}` : '未启用（规则引擎）' }}
        </el-descriptions-item>
        <el-descriptions-item label="向量库">
          <el-tag :type="engine.vector_db === 'chroma' ? 'success' : 'warning'" size="small">
            {{ engine.vector_db === 'chroma' ? 'ChromaDB' : 'SQL 检索' }}
          </el-tag>
        </el-descriptions-item>
        <el-descriptions-item label="调度器">{{ engine.scheduler_running ? '运行中' : '已停止' }}</el-descriptions-item>
        <el-descriptions-item v-if="!engine.llm_enabled" label="配置">
          <el-link v-if="isAdmin" type="primary" :underline="false" @click="goConfig">
            前往 AI 大模型配置
          </el-link>
          <span v-else>请联系管理员在「AI 大模型配置」中启用</span>
        </el-descriptions-item>
      </el-descriptions>
    </el-drawer>
  </div>
</template>

<script setup>
import { ref, reactive, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import { MagicStick, Refresh, Cpu, Notebook, Tickets, EditPen, Calendar, ChatDotRound, Collection } from '@element-plus/icons-vue'
import { agentApi, eduApi, questionApi } from '@/api'
import { useUserStore } from '@/store/user'
import { sanitizeHtml } from '@/utils/sanitize'
// 题型唯一真源：项目规范禁止页面内再定义本地映射。
import TYPES, { QUESTION_TYPE_LABELS } from '@/constants/question'

// 题干由教师/AI 录入，后端不做净化就落库，直接 v-html 会执行其中的脚本。
// 统一走白名单净化后再渲染（同 MyNotes 的正文处理）。
function safeStem(s) { return sanitizeHtml(s) }

const router = useRouter()
const userStore = useUserStore()
const isAdmin = computed(() => userStore.isAdmin === true)
// 状态卡展示 DB 实际配置（后端 /agent/status 返回 provider/model/key_configured）
const engineProvider = computed(() =>
  engine.value?.provider || engine.value?.llm_provider || '-')
const engineModel = computed(() =>
  engine.value?.model || engine.value?.llm_model || '未配置')
const engineKeyConfigured = computed(() => {
  const v = engine.value?.key_configured
  return typeof v === 'boolean' ? v : null
})
const engineKeyLabel = computed(() => {
  if (engineKeyConfigured.value === true) return '已配置'
  if (engineKeyConfigured.value === false) return '未配置'
  return '未知'
})
const engineKeyType = computed(() => {
  if (engineKeyConfigured.value === true) return 'success'
  if (engineKeyConfigured.value === false) return 'danger'
  return 'info'
})
function goConfig() { router.push('/admin/ai-config') }


// 本页有输入表单、后端有对应接口的 Agent。
// /agent/list 会额外返回 router（内部编排）与 lesson_planner（无前端接口/
// 无表单）、grading_assistant（需要 items 但本页无输入区）：这几个点进去
// 右侧一片空白，且 run() 会误调 /agent/grading 空参数，故不下发到菜单。
const agents = ref([])
const SUPPORTED_AGENTS = [
  'question_generator', 'paper_composer', 'study_planner',
  'tutor', 'note_organizer',
]
const visibleAgents = computed(() =>
  agents.value.filter(a => SUPPORTED_AGENTS.includes(a.name)))
const engine = ref(null)
const subjects = ref([])
const grades = ref([])
const kps = ref([])
const active = ref('question_generator')
const result = ref(null)
const running = ref(false)
// 后台任务模式：提交到 /agent/jobs 后轮询，避免长连接被网关截断
const asyncMode = ref(false)
const jobId = ref(null)
const saving = ref(false)
const statusDrawer = ref(false)
const paperReq = ref('')
// 组卷页的学科兜底：不填就靠 AI 从需求文本解析，填了直接传给后端。
// 注意 Subject 唯一键是 (grade_id, name)，同名多条，必须按年级过滤，
// 否则选中代表记录会把卷子挂到最低年级（与出题页同样的坑）。
const paperGradeId = ref(null)
const paperSubjectId = ref(null)
const paperSubjects = computed(() => {
  if (!paperGradeId.value) return subjects.value
  return subjects.value.filter(s => s.grade_id === paperGradeId.value)
})
function onPaperGradeChange() {
  const keep = subjects.value.some(
    s => s.id === paperSubjectId.value && s.grade_id === paperGradeId.value)
  if (!keep) paperSubjectId.value = null
}
function paperParams() {
  return {
    request: paperReq.value,           // 后端契约是 request，不是 requirement
    grade_id: paperGradeId.value || undefined,
    subject_id: paperSubjectId.value || undefined,
  }
}

const qForm = reactive({
  subject_id: null, grade_id: null, knowledge_point_ids: [],
  // 后端 question_type 只收单值，原先是数组多选但只取 [0]
  question_type: 'single',
  difficulty: 'medium', count: 5, requirements: ''
})
const genericForm = reactive({ note_id: null, question: '', knowledge_point: '', student_id: null, days: 7, daily_minutes: 90 })

const paperTemplates = [
  '生成七年级数学一元一次方程试卷，10 题，选择题 6 道 + 填空 4 道，难度中等',
  '生成八年级物理期中试卷，20 题，限时 60 分钟',
  '生成九年级英语完形填空专项卷，15 题，难度偏难'
]

const currentAgent = computed(() => agents.value.find(a => a.name === active.value))
// 后端异步任务仅支持出题 / 组卷：其余 Agent 勾选后台生成会 400
const asyncSupported = computed(() => ['question_generator', 'paper_composer'].includes(active.value))
const isFallback = computed(() =>
  result.value?.is_fallback === true || result.value?.fallback === true)

// 组卷报告是嵌套对象，模板里直接插值会显示 [object Object]。
// 与 AgentChat / PaperWizard 的消费口径保持一致。
const DIFF_LABELS = { easy: '简单', medium: '中等', hard: '困难' }
const difficultyText = computed(() => {
  const d = result.value?.difficulty_report?.distribution
  if (!d || typeof d !== 'object') return '-'
  const parts = Object.entries(d).map(([k, v]) => `${DIFF_LABELS[k] || k} ${v} 题`)
  return parts.length ? parts.join(' / ') : '-'
})
const coverageText = computed(() => {
  const c = result.value?.knowledge_coverage
  if (!c) return '-'
  if (typeof c === 'string') return c
  return `覆盖 ${c.total_points ?? 0} 个知识点 · ${c.balance || '暂无均衡性数据'}`
})
const difficultyAnalysisText = computed(() => {
  const r = result.value?.difficulty_report
  if (!r) return result.value?.analysis || '-'
  const parts = Object.entries(r.ratio || {})
    .map(([k, v]) => `${DIFF_LABELS[k] || k} 占比 ${v}%`)
  if (r.avg_score != null) parts.push(`平均每题 ${r.avg_score} 分`)
  return parts.length ? parts.join(' · ') : '-'
})

const textResult = computed(() => {
  const r = result.value
  if (!r) return ''
  // 优先展示人类可读字段。旧实现命中 summary 时误把「整个结果对象」
  // JSON.stringify 出来，用户看到的是一大坨调试信息而不是总结文本。
  for (const k of ['answer', 'summary', 'content', 'text', 'message']) {
    if (typeof r[k] === 'string' && r[k].trim()) return r[k]
  }
  return JSON.stringify(r, null, 2)
})

function iconOf(code) {
  return {
    question_generator: Notebook, paper_composer: Tickets, grading_assistant: EditPen,
    study_planner: Calendar, tutor: ChatDotRound, note_organizer: Collection
  }[code] || MagicStick
}

function strip(s) { return String(s || '').replace(/<[^>]+>/g, '') }
function parse(v) { if (!v) return null; try { return typeof v === 'string' ? JSON.parse(v) : v } catch { return null } }
function fmtAnswer(v) {
  if (v === null || v === undefined || v === '') return '-'
  if (Array.isArray(v)) return v.join('、')
  if (typeof v === 'object') return JSON.stringify(v)
  return String(v)
}
function openPaper(id) { router.push(`/teacher/papers/${id}/edit`) }
function templateLabel(t) { return t.length > 16 ? `${t.slice(0, 16)}…` : t }

function onSelect(idx) { active.value = idx; result.value = null }

/**
 * 出题用的学科列表。
 *
 * 这里是「学科 → 知识点 → 出题」的入口，必须拿到**精确的 subject_id**，
 * 不能用 distinct 去重后的代表记录：Subject 的唯一键是 (grade_id, name)，
 * 代表 id 永远指向最低年级，选中它会去查一年级的知识点。
 * 实测由此产生过脏数据 —— 七年级「一元一次方程」的 5 道题被挂到
 * 「20以内加减法」(一年级知识点) 上，掌握图谱/复习计划全部算错。
 *
 * 所以：选了年级就只列该年级的学科；没选年级时列出全部（同名多行是准确的，
 * 用户选哪一行就对应哪个年级）。年级变化时清空已选的学科与知识点。
 */
const genSubjects = computed(() => {
  const all = subjects.value
  const gid = qForm.grade_id
  if (!gid) return all
  return all.filter(s => s.grade_id === gid)
})

// 未选年级时按 grade_id 分组展示（旧的注释宣称分组、代码却只平铺，
// 结果下拉里出现几十条同名「数学」，用户根本选不对年级）。
const genSubjectGroups = computed(() => {
  const byGrade = new Map()
  for (const s of subjects.value) {
    const gid = s.grade_id || 0
    if (!byGrade.has(gid)) byGrade.set(gid, [])
    byGrade.get(gid).push(s)
  }
  return [...byGrade.entries()]
    .sort((a, b) => a[0] - b[0])
    .map(([gid, options]) => ({
      id: gid,
      label: grades.value.find(g => g.id === gid)?.name || '其他年级',
      options,
    }))
})

function onGradeChange() {
  // 年级变了，原学科/知识点必然不属于新年级，必须清空避免跨年级脏数据
  const keep = subjects.value.some(
    s => s.id === qForm.subject_id && s.grade_id === qForm.grade_id)
  if (!keep) {
    qForm.subject_id = null
    kps.value = []
  }
  qForm.knowledge_point_ids = []
}

async function onSubjectChange() {
  if (!qForm.subject_id) { kps.value = []; return }
  // 必须带上年级：只按 subject_id 查时，若该 id 属于别的年级就会装错知识点
  const params = { subject_id: qForm.subject_id, params_limit: 300 }
  if (qForm.grade_id) params.grade_id = qForm.grade_id
  const res = await eduApi.knowledgeList(params)
  kps.value = res.data?.items || res.data || []
}

/** 轮询后台任务直到完成（最长 5 分钟，2s 间隔） */
async function pollJob(id, timeoutMs) {
  const deadline = Date.now() + timeoutMs
  while (Date.now() < deadline) {
    await new Promise(r => setTimeout(r, 2000))
    const res = await agentApi.job(id)
    const j = res.data || {}
    if (j.status === 'success') return j.result
    if (j.status === 'failed') throw new Error(j.error || '生成失败')
  }
  throw new Error(`任务超时（${Math.round(timeoutMs / 60000)} 分钟），请到任务列表查看`)
}

// 智能批改等 Agent 拿不到 items 时会返回空对象/空列表，旧实现无条件弹
// 「生成完成」——用户看到成功却一条都没批，是典型的谎报成功。
function hasNoOutput(payload) {
  if (!payload || typeof payload !== 'object') return true
  const items = payload.items
  if (Array.isArray(items)) return items.length === 0
  return Object.keys(payload).length === 0
}

async function run() {
  // 后台模式：提交任务 + 轮询（不占用 HTTP 长连接）。
  // 仅出题/组卷有后端异步任务；此前分支引用不存在的 mode/pForm，
  // 一旦勾选「后台生成」必抛 ReferenceError，且结果赋值 nameshadowing。
  if (asyncMode.value) {
    if (!asyncSupported.value) {
      ElMessage.warning('该功能暂不支持后台生成，将直接同步生成')
      asyncMode.value = false
    } else {
      running.value = true
      try {
        const isQuestion = active.value === 'question_generator'
        const agent = isQuestion ? 'question' : 'paper'
        const params = isQuestion
          ? {
              ...qForm,
              type: qForm.question_type,
              knowledge_point_ids: qForm.knowledge_point_ids
            }
          : paperParams()
        const res = await agentApi.createJob({ agent, params })
        jobId.value = res.data?.job_id
        ElMessage.success(`任务已提交（#${jobId.value}），正在后台生成…`)
        // 后端超时阈值：出题 300s、组卷 900s。前端略宽一点，
        // 否则前端先放弃而后台线程仍在跑，教师重试会重复生成。
        const waitMs = isQuestion ? 6 * 60 * 1000 : 15 * 60 * 1000
        const jobResult = await pollJob(jobId.value, waitMs)
        result.value = jobResult?.data || jobResult || {}
        if (hasNoOutput(result.value)) {
          ElMessage.warning('任务已结束但未产出内容，请调整条件后重试')
        } else {
          ElMessage.success('后台生成完成')
        }
      } catch (e) {
        ElMessage.error(e.message || '后台任务失败')
      } finally {
        running.value = false
      }
      return
    }
  }
  running.value = true
  result.value = null
  try {
    let res
    if (active.value === 'question_generator') {
      if (!qForm.subject_id) { ElMessage.warning('请选择学科'); return }
      // 题型单值；知识点后端同时认 knowledge_point_ids（数组优先）与
      // knowledge_point_id，发数组才能让多选真正全部生效。
      res = await agentApi.questionGenerator({
        ...qForm,
        type: qForm.question_type,
        knowledge_point_ids: qForm.knowledge_point_ids,
      })
    } else if (active.value === 'paper_composer') {
      // 二选一即可：写了需求文本让 AI 解析，或直接选学科走规则组卷。
      // 只认文本会把「已选学科」的用户也挡在门外，正是「无学科选择框可自救」
      // 的另一半原因（后端其实只要 subject_id 有值就能出卷）。
      if (!paperReq.value && !paperSubjectId.value) {
        ElMessage.warning('请输入组卷需求，或选择年级与学科'); return
      }
      res = await agentApi.paperComposer(paperParams())
    } else if (active.value === 'note_organizer') {
      if (!genericForm.note_id) { ElMessage.warning('请输入笔记 ID'); return }
      res = await agentApi.noteOrganizer({ note_id: genericForm.note_id })
    } else if (active.value === 'tutor') {
      if (!genericForm.question) { ElMessage.warning('请输入问题'); return }
      res = await agentApi.tutor(genericForm)
    } else if (active.value === 'study_planner') {
      res = await agentApi.studyPlanner(genericForm)
    } else {
      // 菜单已过滤未实现的能力；兜底避免残留入口静默调错接口 / 发空参数
      ElMessage.warning('该能力暂未开放，请在对应功能页使用')
      return
    }
    result.value = res.data || {}
    if (hasNoOutput(result.value)) {
      ElMessage.warning('生成结束但未产出内容，请调整条件后重试')
    } else {
      // 拦截器交回的是信封本身，业务文案在 res.message 而不是 res.data.message
      ElMessage.success(res.message || '生成完成')
    }
  } finally {
    running.value = false
  }
}

function escapeHtml(s) {
  return String(s || '').replace(/[&<>"']/g, (c) => ({
    '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;'
  }[c]))
}

/** 从（可能来自 AI 的）题目对象里解析创建参数：题库 V2 只接受单值 knowledge_point_id。 */
function buildQuestionPayload(q) {
  const kpIds = Array.isArray(q.knowledge_point_ids)
    ? q.knowledge_point_ids
    : (q.knowledge_point_id ? [q.knowledge_point_id] : (qForm.knowledge_point_ids || []))
  const kpId = kpIds[0] ?? null
  // 年级兜底：先取题目自带，再用表单；表单没填年级时按学科反查所属年级
  let gradeId = q.grade_id || qForm.grade_id
  if (!gradeId && (q.subject_id || qForm.subject_id)) {
    const sid = q.subject_id || qForm.subject_id
    gradeId = subjects.value.find(s => s.id === sid)?.grade_id || null
  }
  const payload = {
    ...q,
    knowledge_point_id: kpId,
    grade_id: gradeId,
    subject_id: q.subject_id || qForm.subject_id || null,
    // AI 结果来自公共/生成场景，统一保存为当前用户私有题，避免公共题审核语义
    bank_type: 'private'
  }
  // 兼容旧字段：V2 create 只认 knowledge_point_id，多余数组字段会导致校验/落库异常
  delete payload.knowledge_point_ids
  return payload
}

// 单请求最多带多少道（与后端 BATCH_CREATE_LIMIT=50 对齐），超出分片提交
const BATCH_SAVE_CHUNK = 50

async function saveAll() {
  const qs = result.value.questions || []
  if (!qs.length) return
  // 二次确认：明确保存到「我的私有题库」，避免误解为公共题库
  try {
    await ElMessageBox.confirm(
      `将把 ${qs.length} 道 AI 生成题保存到你自己的私有题库（private），保存后仅你本人可见与选用。请先核对题目与答案。`,
      '确认保存', { type: 'warning', confirmButtonText: '保存到私有题库', cancelButtonText: '再检查一下' })
  } catch { return }
  saving.value = true
  let okCount = 0
  const failures = []
  try {
    const payloads = qs.map(buildQuestionPayload)
    // 走批量新增接口：一次请求建多题。此前是逐题串行 POST，
    // 20 道题要 20 次往返，且每道都要重新校验年级/学科/知识点。
    for (let start = 0; start < payloads.length; start += BATCH_SAVE_CHUNK) {
      const chunk = payloads.slice(start, start + BATCH_SAVE_CHUNK)
      try {
        const res = await questionApi.batchCreate(chunk)
        const body = res?.data || {}
        const done = Array.isArray(body.done) ? body.done.length : 0
        const skipped = Array.isArray(body.skipped) ? body.skipped : []
        okCount += done
        skipped.forEach((s) => {
          failures.push({
            // 后端 index 是分片内 1 起的序号，换算成整批的序号
            index: start + Number(s.index || 0),
            reason: s.reason || '未通过校验'
          })
        })
      } catch (e) {
        // 拦截器 reject 的是 Error（错误文案已写进 e.message），没有 axios response
        const reason = e?.message || e?.response?.data?.message || String(e)
        for (let i = 0; i < chunk.length; i++) {
          failures.push({ index: start + i + 1, reason })
        }
      }
    }
  } finally {
    saving.value = false
  }
  // 成功数 + 失败数对不上总数，说明后端漏回了结果：必须提示，不能当成全成功
  const missing = qs.length - okCount - failures.length
  if (missing > 0) {
    failures.push({ index: null, reason: `${missing} 道题未收到后端结果，请刷新题库核对` })
  }
  if (!failures.length) {
    ElMessage.success(`已全部保存 ${okCount} 道题到你的私有题库`)
    return
  }
  // shown 是 join 后的 HTML 字符串，用它的 .length 和条数比较是错的，
  // 「另有 N 条失败」永远算不出来。单独记实际展示条数。
  const limit = Math.min(failures.length, 10)
  const shown = failures.slice(0, limit)
    .map(f => (f.index == null
      ? escapeHtml(f.reason)
      : `第 ${f.index} 题：${escapeHtml(f.reason)}`)).join('<br/>')
  const more = failures.length > limit
    ? `<br/>…另有 ${failures.length - limit} 条失败` : ''
  ElMessageBox.alert(
    `${shown}${more}`,
    `保存结果：成功 ${okCount}/${qs.length} 道，失败 ${failures.length} 道`,
    { type: 'warning', dangerouslyUseHTMLString: true }
  )
}

onMounted(async () => {
  // 这四个请求的顺序必须与解构顺序严格对应。此前解构写成 [a, s, g, st]，
  // 赋值却按 (list, engine, subjects, grades) 错位取用：
  //   engine ← grades 列表 → 引擎状态恒显示「规则引擎模式」
  //   subjects ← /agent/status 对象 → 学科下拉为空
  //   grades ← 学科列表（含 57 条同名）→ 年级下拉装满学科名
  // 另外 /agent/list 返回的是 {agents: [...]}，不是数组，
  // 直接赋给 agents 会让 v-for 遍历对象、computed 里的 .find 抛 TypeError。
  const [list, status, subs, grs] = await Promise.all([
    agentApi.list(), agentApi.status(),
    // 这里**不能**用 distinct：出题必须拿到「学科+年级」配套的精确 id。
    // 去重后的代表 id 指向最低年级，会让知识点下拉装错年级。
    // 下拉重复由 genSubjects 按年级过滤解决（未选年级时按年级分组展示）。
    eduApi.subjects(), eduApi.grades()
  ])
  agents.value = list.data?.agents || (Array.isArray(list.data) ? list.data : [])
  engine.value = status.data
  subjects.value = subs.data || []
  grades.value = grs.data || []
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
