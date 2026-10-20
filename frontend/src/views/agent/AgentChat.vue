<template>
  <div class="chat-page">
    <aside class="side">
      <div class="engine-status" :class="{ on: status.llm_enabled }">
        <div class="st-title">
          <el-icon><Cpu /></el-icon> AI 引擎状态
        </div>
        <div class="st-row"><span>模型</span><b>{{ status.model || '未配置' }}</b></div>
        <div class="st-row"><span>编排</span><b>{{ status.orchestrator_mode === 'langgraph' ? 'LangGraph' : '顺序编排' }}</b></div>
        <div class="st-row"><span>向量库</span><b>{{ status.vector_db || '-' }}</b></div>
        <div class="st-row"><span>Agent</span><b>{{ status.agents || 0 }} 个</b></div>
        <el-alert v-if="status.tip" type="warning" :closable="false" show-icon style="margin-top:8px">
          <template #title><span style="font-size:12px">{{ status.tip }}</span></template>
        </el-alert>
      </div>

      <div class="side-block">
        <div class="sb-title">试试这样问</div>
        <div v-for="q in samples" :key="q" class="sample" @click="ask(q)">{{ q }}</div>
      </div>

      <el-button :icon="Delete" style="width:100%" @click="clear">清空对话</el-button>
    </aside>

    <section class="main">
      <div ref="scrollBox" class="messages">
        <div v-if="messages.length === 0" class="welcome">
          <el-icon :size="54" color="#2f6fd0"><MagicStick /></el-icon>
          <h2>你好，{{ userStore.realName }}！我是你的 AI 教学助手</h2>
          <p>我可以帮你出题、组卷、批改、规划学习、解答疑惑、整理笔记</p>
        </div>

        <div v-for="(m, i) in messages" :key="i" class="msg" :class="m.role">
          <div class="bubble" v-if="m.role === 'user'">{{ m.content }}</div>
          <div class="bubble ai" v-else>
            <div v-if="m.thinking" class="typing">
              <span></span><span></span><span></span>
            </div>
            <template v-else>
              <div class="markdown-body" v-html="renderMd(m.content)"></div>

              <div v-if="m.data?.paper" class="result-block">
                <div class="rb-title">试卷预览（{{ m.data.paper.item_count }} 题 / {{ m.data.paper.total_score }} 分）</div>
                <div v-for="(it, n) in m.data.paper.items" :key="n" class="paper-item">
                  {{ n + 1 }}. {{ stripHtml(it.stem).slice(0, 60) }}
                  <el-tag size="small" style="margin-left:6px">{{ it.score }}分</el-tag>
                </div>
                <div v-if="m.data.knowledge_coverage" class="rb-note">
                  知识点覆盖 {{ m.data.knowledge_coverage.total_points }} 个 ·
                  {{ m.data.knowledge_coverage.balance }}
                </div>
              </div>

              <div v-if="m.data?.questions?.length" class="result-block">
                <div v-for="(q, n) in m.data.questions" :key="n" class="paper-item">
                  {{ n + 1 }}. {{ stripHtml(q.stem).slice(0, 70) }}
                </div>
              </div>

              <div v-if="m.data?.related_questions?.length" class="result-block">
                <div class="rb-title">同类练习</div>
                <div v-for="(q, n) in m.data.related_questions" :key="n" class="paper-item">
                  {{ n + 1 }}. {{ stripHtml(q.stem).slice(0, 60) }}
                  <el-button link type="primary" size="small" @click="toggleA(i, n)">
                    {{ expanded[`${i}-${n}`] ? '收起' : '看答案' }}
                  </el-button>
                  <div v-if="expanded[`${i}-${n}`]" class="answer-box">
                    <div><b>答案：</b>{{ q.answer }}</div>
                    <div v-if="q.analysis"><b>解析：</b>{{ q.analysis }}</div>
                  </div>
                </div>
              </div>

              <div v-if="m.data?.study_tips?.length" class="result-block">
                <div class="rb-title">学习建议</div>
                <ul style="margin:0;padding-left:18px">
                  <li v-for="(t, n) in m.data.study_tips" :key="n">{{ t }}</li>
                </ul>
              </div>

              <div v-if="m.data?.weak_points?.length" class="result-block">
                <div class="rb-title">薄弱知识点</div>
                <el-tag v-for="w in m.data.weak_points" :key="w.name" size="small"
                        type="danger" style="margin:2px">{{ w.name }} {{ w.mastery }}%</el-tag>
              </div>

              <div v-if="m.data?.daily_plan?.length" class="result-block">
                <div class="rb-title">学习计划</div>
                <div v-for="d in m.data.daily_plan.slice(0, 5)" :key="d.date" class="plan-day">
                  <b>{{ d.date }}</b>（{{ d.duration }}分钟）
                  <ul style="margin:4px 0 0;padding-left:18px">
                    <li v-for="(t, n) in d.tasks" :key="n">{{ t.content }}</li>
                  </ul>
                </div>
              </div>

              <div v-if="m.data?.references?.length" class="refs">
                参考：
                <el-tag v-for="r in m.data.references" :key="r.type + r.id" size="small"
                        style="margin:2px" type="info">{{ r.type }}·{{ r.name }}</el-tag>
              </div>

              <div class="msg-meta">
                <el-tag size="small" effect="plain">{{ agentLabel(m.agent) }}</el-tag>
                <span v-if="m.duration">{{ m.duration }}ms</span>
                <el-tag v-if="m.fallback" size="small" type="warning" effect="plain">规则引擎降级</el-tag>
              </div>
            </template>
          </div>
        </div>
      </div>

      <div class="input-bar">
        <div class="filters">
          <el-select v-model="ctx.grade_id" placeholder="年级（选填）" clearable size="small" style="width:140px">
            <el-option v-for="g in grades" :key="g.id" :label="g.name" :value="g.id" />
          </el-select>
          <el-select v-model="ctx.subject_id" placeholder="学科（选填）" clearable size="small" style="width:140px">
            <el-option v-for="s in subjects" :key="s.id" :label="s.name" :value="s.id" />
          </el-select>
        </div>
        <div class="input-row">
          <el-input ref="inputRef" v-model="input" type="textarea" :rows="2" resize="none" maxlength="500"
                    placeholder="描述你的需求，Enter 发送，Shift+Enter 换行"
                    @keydown.enter.exact.prevent="send" />
          <el-button type="primary" :loading="loading" :icon="Promotion" @click="send">
            {{ loading ? 'AI 思考中（最长约 60 秒）' : '发送' }}
          </el-button>
        </div>
        <div class="tip">{{ input.length }}/500 · AI 生成内容仅供参考，请结合教材核实</div>
      </div>
    </section>
  </div>
</template>

<script setup>
import { nextTick, onMounted, ref } from 'vue'
import MarkdownIt from 'markdown-it'
import { Delete, Promotion } from '@element-plus/icons-vue'
import { agentApi, eduApi } from '@/api'
import { useUserStore } from '@/store/user'

const userStore = useUserStore()
const md = new MarkdownIt()

const input = ref('')
const messages = ref([])
const loading = ref(false)
const status = ref({})
const grades = ref([])
const subjects = ref([])
const expanded = ref({})
const scrollBox = ref()
const ctx = ref({ grade_id: null, subject_id: null })

const samples = [
  '帮我出一套七年级数学有理数单元测试卷',
  '什么是艾宾浩斯遗忘曲线',
  '帮我规划一周的复习计划',
  '这道题为什么错了：2x + 3 = 7'
]

const AGENT_LABEL = {
  question_generator: '题库生成', paper_composer: '智能组卷',
  grading_assistant: '智能批改', study_planner: '学习规划',
  tutor: '答疑助教', note_organizer: '笔记整理', router: '需求路由'
}

function agentLabel(n) { return AGENT_LABEL[n] || n || 'AI 助手' }
function renderMd(t) { return md.render(t || '') }
function stripHtml(s) { return String(s || '').replace(/<[^>]*>/g, '') }
function toggleA(i, n) { expanded.value[`${i}-${n}`] = !expanded.value[`${i}-${n}`] }

async function scrollBottom() {
  await nextTick()
  if (scrollBox.value) scrollBox.value.scrollTop = scrollBox.value.scrollHeight
}

async function send() {
  const text = input.value.trim()
  if (!text || loading.value) return
  input.value = ''
  messages.value.push({ role: 'user', content: text })
  const idx = messages.value.length
  messages.value.push({ role: 'ai', thinking: true, content: '' })
  loading.value = true
  scrollBottom()
  try {
    const res = await agentApi.chat({
      message: text, grade_id: ctx.value.grade_id, subject_id: ctx.value.subject_id
    })
    const d = res.data
    messages.value[idx] = {
      role: 'ai',
      content: d.answer || '（无内容返回）',
      data: d.data,
      agent: d.agent,
      duration: d.duration_ms,
      fallback: d.is_fallback
    }
  } catch (e) {
    messages.value[idx] = { role: 'ai', content: `请求失败：${e.message}` }
  } finally {
    loading.value = false
    scrollBottom()
  }
}

function ask(q) { input.value = q; send() }

function clear() {
  messages.value = []
  sessionStorage.removeItem('edu_chat')
}

onMounted(async () => {
  const saved = sessionStorage.getItem('edu_chat')
  if (saved) { try { messages.value = JSON.parse(saved) } catch {} }
  const s = await agentApi.status()
  status.value = s.data
  const g = await eduApi.grades()
  grades.value = g.data
  const sub = await eduApi.subjects({ distinct: true })
  subjects.value = sub.data
})
</script>

<style scoped>
.chat-page { display: flex; height: calc(100vh - 60px); background: var(--page-bg); }
.side {
  width: 250px; background: #fff; border-right: 1px solid #ebeef5;
  padding: 14px; display: flex; flex-direction: column; gap: 14px; overflow-y: auto;
}
.engine-status {
  padding: 12px; border-radius: 8px; background: #fdf6ec; border: 1px solid #f5dab1;
}
.engine-status.on { background: #f0f9eb; border-color: #e1f3d8; }
.st-title { display: flex; align-items: center; gap: 6px; font-weight: 600; margin-bottom: 8px; font-size: 13px; }
.st-row { display: flex; justify-content: space-between; font-size: 12px; margin-bottom: 4px; color: #606266; }
.st-row b { color: #303133; font-weight: 500; }
.side-block { flex: 1; }
.sb-title { font-size: 12px; color: #909399; margin-bottom: 8px; }
.sample {
  padding: 8px 10px; margin-bottom: 6px; border-radius: 6px; background: #f5f7fa;
  font-size: 12px; cursor: pointer; line-height: 1.5;
}
.sample:hover { background: #ecf5ff; color: #2f6fd0; }
.main { flex: 1; display: flex; flex-direction: column; min-width: 0; }
.messages { flex: 1; overflow-y: auto; padding: 20px; }
.welcome { text-align: center; padding: 80px 20px; color: #909399; }
.welcome h2 { color: #303133; font-size: 20px; margin: 16px 0 8px; }
.msg { display: flex; margin-bottom: 18px; }
.msg.user { justify-content: flex-end; }
.bubble {
  max-width: 78%; padding: 12px 16px; border-radius: 10px; background: #2f6fd0;
  color: #fff; line-height: 1.7; white-space: pre-wrap;
}
.bubble.ai {
  background: #fff; color: #303133; max-width: 88%; width: 88%;
  box-shadow: 0 1px 4px rgba(0,0,0,.06); border: 1px solid #ebeef5;
}
.bubble.ai :deep(.markdown-body h1),
.bubble.ai :deep(.markdown-body h2),
.bubble.ai :deep(.markdown-body h3) { font-size: 15px; margin: 12px 0 6px; }
.typing { display: flex; gap: 5px; padding: 6px 0; }
.typing span {
  width: 7px; height: 7px; border-radius: 50%; background: #909399;
  animation: bounce 1.4s infinite ease-in-out;
}
.typing span:nth-child(2) { animation-delay: .2s; }
.typing span:nth-child(3) { animation-delay: .4s; }
@keyframes bounce { 0%,80%,100% { transform: scale(.6); opacity:.5 } 40% { transform: scale(1); opacity:1 } }
.result-block {
  margin-top: 12px; padding: 10px 12px; background: #f8fafc;
  border-radius: 6px; border-left: 3px solid #2f6fd0; font-size: 13px;
}
.rb-title { font-weight: 600; margin-bottom: 6px; color: #2f6fd0; }
.paper-item { margin-bottom: 5px; line-height: 1.6; }
.rb-note { margin-top: 6px; color: #909399; font-size: 12px; }
.answer-box { margin-top: 5px; padding: 8px; background: #fff; border-radius: 4px; font-size: 12px; }
.plan-day { margin-bottom: 8px; font-size: 12px; }
.refs { margin-top: 10px; font-size: 12px; color: #909399; }
.msg-meta {
  display: flex; align-items: center; gap: 8px; margin-top: 10px;
  padding-top: 8px; border-top: 1px solid #f0f0f0; font-size: 11px; color: #c0c4cc;
}
.input-bar { padding: 12px 20px 14px; background: #fff; border-top: 1px solid #ebeef5; }
.filters { display: flex; gap: 8px; margin-bottom: 8px; }
.input-row { display: flex; gap: 10px; align-items: flex-end; }
.tip { font-size: 11px; color: #c0c4cc; margin-top: 6px; text-align: right; }
@media (max-width: 900px) { .side { display: none; } .bubble { max-width: 94%; } }
</style>
